"""
Live single-record scoring for the What-If Risk Simulator and Portfolio
Scenario Simulator, using the actual trained model — never a manually
invented rule.

A what-if record only exposes a handful of behavioral inputs (DPD,
utilization, payment ratio, amount past due, recent bounces, partial
payment, restructure, balance-to-income, current balance, months on book).
Everything else the model needs (product, geography, credit limit, EMI,
and the 19 engineered trend/rolling/volatility/stress features) is held at
a dataset-median/mode "typical account" baseline, and the engineered
features that are *directly implied* by an exposed input are derived to
match it — e.g. setting DPD also sets dpd_avg_3m and account_status,
so the record stays internally consistent (a steady 3-month state),
rather than mixing "high DPD today" with "zero average DPD over 3 months."
"""
from pathlib import Path

import joblib
import pandas as pd

from services.model_features import ALL_FEATURE_COLS
from services.model_service import get_results

APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
MODELS_DIR = APP_DIR / "models"
OOT_SCORED_PARQUET = DATA_DIR / "oot_scored.parquet"

# Dataset medians/modes, computed once from the training population.
BASELINE_PROFILE = dict(
    product="credit_card", state="Maharashtra", city_tier="Tier 1",
    customer_type="thick_file", account_status="CURRENT",
    months_on_book=16, current_balance=74267.22, credit_limit_or_original_amount=205583.0,
    utilization_ratio=0.427, emi_due=7942.84, payment_ratio=1.0034, amount_past_due=0.0,
    dpd=0, bounce_flag=0, recent_bounce_count_3m=0, partial_payment_flag=0, restructure_flag=0,
    balance_to_income_ratio=1.5137,
    dpd_change_1m=0.0, utilization_change_1m=0.0, payment_ratio_change_1m=0.0, balance_change_1m=0.0,
    dpd_avg_3m=0.0, utilization_avg_3m=0.4315, payment_ratio_avg_3m=0.9838, balance_avg_3m=78785.75,
    payment_ratio_std_3m=0.0758, utilization_std_3m=0.1044, balance_std_3m=8253.41,
    dpd_max_3m=0.0, delinquent_months_3m=0.0, partial_payment_months_3m=1.0, bounce_months_3m=0.0,
    utilization_rising_flag=0, dpd_rising_flag=0, payment_ratio_falling_flag=0, months_observed=16,
)

# The model is trained with class_weight="balanced" (see train_models.py), which
# deliberately shifts predicted probabilities well above the true ~9.6% base rate
# to make the minority class learnable — mean OOT score is ~0.43, not ~0.10. Raw
# probability is a good ranking signal but a poor absolute one, so risk bands are
# defined by where a score falls in the OOT score distribution (percentile),
# consistent with how the rest of the app talks about risk (deciles, top-decile
# capture) rather than an arbitrary absolute cutoff.
RISK_BAND_LABELS = [
    (0.60, "Low", "Standard monitoring."),
    (0.70, "Medium", "Watch-list; consider a payment reminder."),
    (0.90, "High", "Proactive outreach recommended."),
]
VERY_HIGH_ACTION = "Priority intervention / restructuring review."

_model_cache = {}
_oot_scores = None
_percentile_cutoffs = None


def _get_oot_scores():
    global _oot_scores
    if _oot_scores is None:
        if not OOT_SCORED_PARQUET.exists():
            raise FileNotFoundError(
                f"{OOT_SCORED_PARQUET} not found. Run `python credit_risk_app/scripts/score_oot.py` first."
            )
        _oot_scores = pd.read_parquet(OOT_SCORED_PARQUET, columns=["predicted_probability"])["predicted_probability"]
    return _oot_scores


def get_percentile_cutoffs():
    """Score value at each RISK_BAND_LABELS percentile boundary, from real OOT scores."""
    global _percentile_cutoffs
    if _percentile_cutoffs is None:
        scores = _get_oot_scores()
        _percentile_cutoffs = [(scores.quantile(q), label, action) for q, label, action in RISK_BAND_LABELS]
    return _percentile_cutoffs


def account_status_from_dpd(dpd: float) -> str:
    if dpd <= 0:
        return "CURRENT"
    if dpd < 30:
        return "DAYS_1_29"
    if dpd < 60:
        return "DPD_30"
    if dpd < 90:
        return "DPD_60"
    if dpd < 120:
        return "DPD_90"
    if dpd < 150:
        return "DPD_120"
    return "DPD_150"


def load_model(key: str):
    if key not in _model_cache:
        preprocessor = joblib.load(MODELS_DIR / f"{key}_preprocessor.pkl")
        model = joblib.load(MODELS_DIR / f"{key}_model.pkl")
        _model_cache[key] = (preprocessor, model)
    return _model_cache[key]


def build_record(**overrides) -> dict:
    """Baseline profile + overrides, with directly-implied engineered features kept consistent."""
    record = dict(BASELINE_PROFILE)
    record.update(overrides)

    if "dpd" in overrides:
        dpd = float(overrides["dpd"])
        record["dpd_avg_3m"] = dpd
        record["dpd_max_3m"] = dpd
        record["delinquent_months_3m"] = 3.0 if dpd > 0 else 0.0
        record["dpd_change_1m"] = 0.0
        record["dpd_rising_flag"] = 0
        record["account_status"] = account_status_from_dpd(dpd)

    if "utilization_ratio" in overrides:
        u = float(overrides["utilization_ratio"])
        record["utilization_avg_3m"] = u
        record["utilization_change_1m"] = 0.0
        record["utilization_rising_flag"] = 0

    if "payment_ratio" in overrides:
        p = float(overrides["payment_ratio"])
        record["payment_ratio_avg_3m"] = p
        record["payment_ratio_change_1m"] = 0.0
        record["payment_ratio_falling_flag"] = 0

    if "recent_bounce_count_3m" in overrides:
        b = float(overrides["recent_bounce_count_3m"])
        record["bounce_months_3m"] = min(b, 3.0)
        record["bounce_flag"] = 1 if b > 0 else 0

    if "partial_payment_flag" in overrides:
        record["partial_payment_months_3m"] = 3.0 if overrides["partial_payment_flag"] else 0.0

    if "current_balance" in overrides:
        record["balance_avg_3m"] = float(overrides["current_balance"])
        record["balance_change_1m"] = 0.0

    if "months_on_book" in overrides:
        record["months_observed"] = overrides["months_on_book"]

    return record


def score_records(records: list, model_key: str = None) -> list:
    """Scores a list of feature dicts with the given (default: best) model. Returns probabilities."""
    if model_key is None:
        model_key = get_results()["best_model_key"]
    preprocessor, model = load_model(model_key)
    df = pd.DataFrame(records)[ALL_FEATURE_COLS]
    X = preprocessor.transform(df)
    return model.predict_proba(X)[:, 1].tolist()


def score_one(record: dict, model_key: str = None) -> float:
    return score_records([record], model_key)[0]


def risk_band(probability: float) -> dict:
    for cutoff, label, action in get_percentile_cutoffs():
        if probability <= cutoff:
            return dict(label=label, action=action)
    return dict(label="Very High", action=VERY_HIGH_ACTION)


def score_percentile(probability: float) -> float:
    """Where this score falls in the real OOT score distribution, 0-100."""
    scores = _get_oot_scores()
    return round(100 * float((scores <= probability).mean()), 1)
