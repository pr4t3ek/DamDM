"""
Trains the champion/challenger model set for roll_to_90p_6m and caches
everything the Milestone 3 pages need: per-period metrics, ROC/KS curves,
decile tables, coefficients/feature importances, and the fitted pipelines
themselves (for future scoring in Milestone 4's simulators).

Models: Logistic Regression (interpretable baseline) vs. Decision Tree,
Random Forest, and XGBoost (challengers) — the champion/challenger pattern
documented in docs/variable_dictionary.md and the Executive Overview page.

Split: out-of-time by month_end_date, using the same default 70/15/15
boundaries the OOT Split Simulator shows, with right-censored months
(the final 6 months — see compute_label_maturity in prepare_data.py)
excluded entirely, never trained or evaluated on.

Run after prepare_data.py and build_features.py:
    python credit_risk_app/scripts/train_models.py
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, roc_auc_score, roc_curve
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier
import joblib

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

from services.model_features import (  # noqa: E402
    ALL_FEATURE_COLS, CATEGORICAL_COLS, ENGINEERED_COLS, MODEL_DISPLAY_NAMES, NUMERIC_COLS, TARGET, THRESHOLD,
)

DATA_DIR = APP_DIR / "data"
MODELS_DIR = APP_DIR / "models"
BASE_PARQUET = DATA_DIR / "behavior_risk_mart.parquet"
FEATURES_PARQUET = DATA_DIR / "behavior_features.parquet"
SUMMARY_CACHE = DATA_DIR / "summary_cache.json"
RESULTS_CACHE = DATA_DIR / "model_results.json"


def load_data():
    print("Loading base + engineered features...")
    base = pd.read_parquet(BASE_PARQUET)
    feat = pd.read_parquet(FEATURES_PARQUET)
    feat_cols = ["observation_id"] + ENGINEERED_COLS
    df = base.merge(feat[feat_cols], on="observation_id", how="left")
    print(f"  merged shape: {df.shape}")
    return df


def default_split_boundaries(summary):
    maturity = summary["label_maturity"]
    months = [m["month"] for m in summary["monthly_roll_rate"] if m["month"] <= maturity["last_mature_month"]]
    n = len(months)
    train_end_idx = int(n * 0.70) - 1
    valid_end_idx = int(n * 0.85) - 1
    return dict(
        train_start=months[0], train_end=months[train_end_idx],
        valid_start=months[train_end_idx + 1], valid_end=months[valid_end_idx],
        test_start=months[valid_end_idx + 1], test_end=months[-1],
    ), maturity


def split_masks(df, bounds):
    months = df["month_end_date"].dt.to_period("M").astype(str)
    return dict(
        train=(months >= bounds["train_start"]) & (months <= bounds["train_end"]),
        validation=(months >= bounds["valid_start"]) & (months <= bounds["valid_end"]),
        test=(months >= bounds["test_start"]) & (months <= bounds["test_end"]),
    )


def build_preprocessor(scale_numeric: bool):
    numeric_steps = [("imputer", SimpleImputer(strategy="constant", fill_value=0))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    return ColumnTransformer([
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), CATEGORICAL_COLS),
        ("num", Pipeline(numeric_steps), NUMERIC_COLS),
    ])


def ks_stat(y_true, y_score):
    fpr, tpr, thr = roc_curve(y_true, y_score)
    idx = int(np.argmax(tpr - fpr))
    return dict(
        ks=round(float((tpr - fpr)[idx]), 4),
        threshold=round(float(thr[idx]), 4) if np.isfinite(thr[idx]) else None,
        fpr_at_ks=round(float(fpr[idx]), 4),
        tpr_at_ks=round(float(tpr[idx]), 4),
    )


def curve_points(fpr, tpr, thr, max_points=150):
    n = len(fpr)
    if n <= max_points:
        idx = np.arange(n)
    else:
        idx = np.unique(np.linspace(0, n - 1, max_points).astype(int))
    # roc_curve's first threshold is an internal sentinel (inf); clip for display.
    thr_clipped = np.clip(thr, 0, 1)
    return dict(
        fpr=[round(float(x), 5) for x in fpr[idx]],
        tpr=[round(float(x), 5) for x in tpr[idx]],
        threshold=[round(float(x), 5) for x in thr_clipped[idx]],
    )


def decile_table(y_true, y_score):
    n = len(y_true)
    order = np.argsort(-y_score)
    y_sorted = np.asarray(y_true)[order]
    total_bads = int(y_sorted.sum())
    overall_rate = total_bads / n if n else 0
    edges = np.linspace(0, n, 11).astype(int)
    rows = []
    cum_bads = 0
    for i in range(10):
        lo, hi = edges[i], edges[i + 1]
        chunk = y_sorted[lo:hi]
        bads = int(chunk.sum())
        cum_bads += bads
        rate = bads / len(chunk) if len(chunk) else 0
        rows.append(dict(
            decile=i + 1,
            accounts=int(len(chunk)),
            bad_accounts=bads,
            bad_rate=round(100 * rate, 3),
            cumulative_bads=cum_bads,
            capture_rate=round(100 * cum_bads / total_bads, 2) if total_bads else None,
            lift=round(rate / overall_rate, 2) if overall_rate else None,
        ))
    return rows


def prediction_histogram(y_score, bins=25):
    counts, edges = np.histogram(y_score, bins=bins, range=(0, 1))
    return dict(counts=counts.tolist(), bin_edges=[round(float(e), 3) for e in edges])


def class_score_distribution(y_true, y_score, bins=25):
    """Score histograms and CDFs for goods vs. bads, for the KS chart."""
    y_true = np.asarray(y_true)
    edges = np.linspace(0, 1, bins + 1)
    out = {}
    for label, name in [(0, "good"), (1, "bad")]:
        scores = y_score[y_true == label]
        counts, _ = np.histogram(scores, bins=edges)
        cdf = np.cumsum(counts) / counts.sum() if counts.sum() else np.zeros_like(counts, dtype=float)
        out[name] = dict(
            counts=counts.tolist(),
            cdf=[round(float(c), 5) for c in cdf],
        )
    out["bin_edges"] = [round(float(e), 4) for e in edges]
    ks_by_bin = np.abs(np.array(out["good"]["cdf"]) - np.array(out["bad"]["cdf"]))
    out["max_gap_bin_index"] = int(np.argmax(ks_by_bin))
    return out


def period_metrics(y_true, y_score):
    n = len(y_true)
    if n == 0 or y_true.sum() == 0 or y_true.sum() == n:
        return None
    y_pred = (y_score >= THRESHOLD).astype(int)
    auc = roc_auc_score(y_true, y_score)
    fpr, tpr, thr = roc_curve(y_true, y_score)
    cm = confusion_matrix(y_true, y_pred).tolist()
    deciles = decile_table(y_true, y_score)
    n_pos = int(np.sum(y_true))
    return dict(
        n=n,
        n_pos=n_pos,
        n_neg=n - n_pos,
        event_rate=round(100 * float(np.mean(y_true)), 3),
        auc=round(float(auc), 4),
        gini=round(float(2 * auc - 1), 4),
        ks=ks_stat(y_true, y_score),
        precision=round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        recall=round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        f1=round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        confusion_matrix=dict(tn=cm[0][0], fp=cm[0][1], fn=cm[1][0], tp=cm[1][1]),
        roc_curve=curve_points(fpr, tpr, thr),
        decile_table=deciles,
        top_decile_capture=deciles[0]["capture_rate"],
        prediction_histogram=prediction_histogram(y_score),
        class_score_distribution=class_score_distribution(y_true, y_score),
    )


def feature_names_out(preprocessor):
    names = list(preprocessor.named_transformers_["cat"].named_steps["onehot"].get_feature_names_out(CATEGORICAL_COLS))
    names += NUMERIC_COLS
    return names


def train_one(name, estimator, scale_numeric, X, y, masks, hyperparams):
    print(f"\n--- {MODEL_DISPLAY_NAMES[name]} ---")
    t0 = time.time()
    preprocessor = build_preprocessor(scale_numeric)
    X_train_t = preprocessor.fit_transform(X[masks["train"]], y[masks["train"]])
    estimator.fit(X_train_t, y[masks["train"]])
    print(f"  trained in {time.time() - t0:.1f}s")

    names = feature_names_out(preprocessor)
    result = dict(
        display_name=MODEL_DISPLAY_NAMES[name],
        hyperparameters=hyperparams,
        metrics={},
    )

    for period in ["train", "validation", "test"]:
        mask = masks[period]
        Xp = preprocessor.transform(X[mask])
        yp = y[mask].to_numpy()
        score = estimator.predict_proba(Xp)[:, 1]
        m = period_metrics(yp, score)
        if m is not None:
            result["metrics"][period] = m

    if hasattr(estimator, "coef_"):
        coefs = estimator.coef_[0]
        order = np.argsort(-np.abs(coefs))
        result["coefficients"] = [
            dict(feature=names[i], coefficient=round(float(coefs[i]), 5),
                 odds_ratio=round(float(np.exp(coefs[i])), 4))
            for i in order[:30]
        ]
    if hasattr(estimator, "feature_importances_"):
        imp = estimator.feature_importances_
        order = np.argsort(-imp)
        result["feature_importance"] = [
            dict(feature=names[i], importance=round(float(imp[i]), 5))
            for i in order[:30] if imp[i] > 0
        ]

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, MODELS_DIR / f"{name}_preprocessor.pkl")
    joblib.dump(estimator, MODELS_DIR / f"{name}_model.pkl")
    return result


def main():
    if not BASE_PARQUET.exists() or not FEATURES_PARQUET.exists():
        sys.exit("Run prepare_data.py and build_features.py first.")
    summary = json.loads(SUMMARY_CACHE.read_text())
    bounds, maturity = default_split_boundaries(summary)
    print(f"Split boundaries: {bounds}")

    df = load_data()
    masks = split_masks(df, bounds)
    for k, m in masks.items():
        print(f"  {k}: {int(m.sum()):,} rows, {int(df.loc[m, TARGET].sum()):,} events")

    X = df[ALL_FEATURE_COLS]
    y = df[TARGET].astype(int)

    neg, pos = int((y[masks["train"]] == 0).sum()), int((y[masks["train"]] == 1).sum())
    scale_pos_weight = neg / pos

    specs = [
        ("logistic_regression", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42), True,
         dict(max_iter=1000, class_weight="balanced", penalty="l2")),
        ("decision_tree", DecisionTreeClassifier(max_depth=6, min_samples_leaf=500, class_weight="balanced", random_state=42), False,
         dict(max_depth=6, min_samples_leaf=500, class_weight="balanced")),
        ("random_forest", RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_leaf=50, class_weight="balanced", n_jobs=-1, random_state=42), False,
         dict(n_estimators=200, max_depth=10, min_samples_leaf=50, class_weight="balanced")),
        ("xgboost", XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                                   scale_pos_weight=scale_pos_weight, eval_metric="auc", random_state=42, n_jobs=-1), False,
         dict(n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
              scale_pos_weight=round(scale_pos_weight, 3))),
    ]

    models = {}
    for name, estimator, scale_numeric, hyperparams in specs:
        models[name] = train_one(name, estimator, scale_numeric, X, y, masks, hyperparams)

    best = max(models.items(), key=lambda kv: kv[1]["metrics"].get("test", {}).get("auc", 0))
    print(f"\nBest model by OOT AUC: {MODEL_DISPLAY_NAMES[best[0]]} ({best[1]['metrics']['test']['auc']})")

    results = dict(
        generated_at=datetime.now(timezone.utc).isoformat(),
        target=TARGET,
        threshold=THRESHOLD,
        split_boundaries=bounds,
        label_maturity=maturity,
        feature_cols=dict(categorical=CATEGORICAL_COLS, numeric=NUMERIC_COLS, all=ALL_FEATURE_COLS),
        models=models,
        best_model_key=best[0],
    )
    RESULTS_CACHE.write_text(json.dumps(results, default=str))
    print(f"\nWrote {RESULTS_CACHE} ({RESULTS_CACHE.stat().st_size / 1e6:.1f} MB)")

    print("\n--- OOT Test summary ---")
    for name, r in models.items():
        m = r["metrics"].get("test")
        if m:
            print(f"  {r['display_name']:20s} AUC={m['auc']:.4f}  Gini={m['gini']:.4f}  KS={m['ks']['ks']:.4f}  "
                  f"Top-decile capture={m['top_decile_capture']:.1f}%")


if __name__ == "__main__":
    main()
