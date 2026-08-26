"""
Explainability for the recommended model: global feature/permutation
importance, SHAP-based global signal, and per-account reason codes.

Global computations run on a fixed-seed sample of the OOT test set (not the
full 222K rows) — fast enough to compute live per page load (SHAP: <1s for
2,000 rows; permutation importance: <1s for 37 features on 4,000 rows) and
representative enough for a global-importance view, not a precise ranking.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from services.model_features import ALL_FEATURE_COLS, TARGET
from services.model_service import get_model, get_results
from services.simulator_service import load_model
from services import scenario_service

SAMPLE_SIZE = 3000
SAMPLE_SEED = 42

_shap_explainer = None
_shap_cache = None
_sample_cache = None


def _get_sample():
    global _sample_cache
    if _sample_cache is None:
        df = scenario_service.get_test_df()
        _sample_cache = df.sample(min(SAMPLE_SIZE, len(df)), random_state=SAMPLE_SEED).reset_index(drop=True)
    return _sample_cache


def _feature_names(preprocessor):
    cat_names = list(preprocessor.named_transformers_["cat"].named_steps["onehot"].get_feature_names_out(
        ["product", "state", "city_tier", "customer_type", "account_status"]
    ))
    numeric_names = [c for c in ALL_FEATURE_COLS if c not in
                      ["product", "state", "city_tier", "customer_type", "account_status"]]
    return cat_names + numeric_names


def native_importance(top_n=20):
    """Reuses the model's own gain-based importance, already computed in train_models.py."""
    best_key = get_results()["best_model_key"]
    model = get_model(best_key)
    return model.get("feature_importance", [])[:top_n]


def permutation_importance(top_n=20):
    best_key = get_results()["best_model_key"]
    preprocessor, model = load_model(best_key)
    sample = _get_sample()
    y = sample[TARGET].to_numpy()

    def auc_of(X_raw):
        Xt = preprocessor.transform(X_raw)
        p = model.predict_proba(Xt)[:, 1]
        return roc_auc_score(y, p)

    baseline_auc = auc_of(sample[ALL_FEATURE_COLS])
    rng = np.random.default_rng(SAMPLE_SEED)
    drops = []
    for col in ALL_FEATURE_COLS:
        Xp = sample[ALL_FEATURE_COLS].copy()
        Xp[col] = rng.permutation(Xp[col].to_numpy())
        drops.append(dict(feature=col, auc_drop=round(float(baseline_auc - auc_of(Xp)), 5)))
    drops.sort(key=lambda d: -d["auc_drop"])
    return dict(baseline_auc=round(float(baseline_auc), 4), drops=drops[:top_n])


def _get_shap():
    """SHAP values for the fixed sample, computed once per process."""
    global _shap_cache
    if _shap_cache is None:
        best_key = get_results()["best_model_key"]
        preprocessor, _ = load_model(best_key)
        sample = _get_sample()
        X = preprocessor.transform(sample[ALL_FEATURE_COLS])
        explainer = _get_shap_explainer(best_key)
        values = explainer.shap_values(X)
        _shap_cache = dict(values=values, feature_names=_feature_names(preprocessor), X=X, sample=sample)
    return _shap_cache


def shap_global_importance(top_n=20):
    cache = _get_shap()
    mean_abs = np.abs(cache["values"]).mean(axis=0)
    order = np.argsort(-mean_abs)[:top_n]
    return [dict(feature=cache["feature_names"][i], mean_abs_shap=round(float(mean_abs[i]), 5)) for i in order]


def _get_shap_explainer(model_key):
    global _shap_explainer
    if _shap_explainer is None:
        _, model = load_model(model_key)
        import shap
        _shap_explainer = shap.TreeExplainer(model)
    return _shap_explainer


def account_reason_codes(record: dict, top_n=6):
    """Per-account SHAP contributions for a single feature record, translated to plain language."""
    best_key = get_results()["best_model_key"]
    preprocessor, _ = load_model(best_key)
    names = _feature_names(preprocessor)
    X = preprocessor.transform(pd.DataFrame([record])[ALL_FEATURE_COLS])

    explainer = _get_shap_explainer(best_key)
    values = explainer.shap_values(X)[0]
    base_value = explainer.expected_value
    if isinstance(base_value, (list, np.ndarray)):
        base_value = base_value[0]

    order = np.argsort(-np.abs(values))[:top_n]
    codes = []
    for i in order:
        codes.append(dict(
            feature=names[i], contribution=round(float(values[i]), 4),
            direction="raises risk" if values[i] > 0 else "lowers risk",
        ))
    return dict(base_value=round(float(base_value), 4), total_shap=round(float(values.sum()), 4), codes=codes)
