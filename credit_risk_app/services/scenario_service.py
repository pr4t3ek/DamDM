"""
Portfolio-level what-if: apply a shock to one behavioral field across the
whole OOT test population, re-score with the real model, and compare
aggregate risk before and after.

This is a coarser tool than the What-If Simulator: a shock is applied only
to the field(s) it directly describes (e.g. Scenario A only changes
utilization_ratio), not propagated into the engineered trend/rolling
features the way a single-account simulation does. That's a deliberate
simplification for a portfolio-wide stress view, not an attempt at
per-account precision.
"""
from pathlib import Path

import pandas as pd

from services.model_features import ALL_FEATURE_COLS, ENGINEERED_COLS
from services.model_service import get_results
from services.simulator_service import account_status_from_dpd, load_model, risk_band

APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
BASE_PARQUET = DATA_DIR / "behavior_risk_mart.parquet"
FEATURES_PARQUET = DATA_DIR / "behavior_features.parquet"

SCENARIOS = {
    "utilization_up": dict(
        label="Scenario A: Utilization +10%",
        description="Every account's utilization ratio rises by 10 percentage points (capped at 150%).",
    ),
    "payment_ratio_down": dict(
        label="Scenario B: Payment Ratio -15%",
        description="Every account pays 15% less of what's due than it currently does.",
    ),
    "bounces_up": dict(
        label="Scenario C: Bounces Increase",
        description="Every account records one additional payment bounce in the last 3 months.",
    ),
    "dpd_up": dict(
        label="Scenario D: DPD Increases",
        description="Every account's days-past-due rises by 15 days, with account status updated to match.",
    ),
}

_test_df = None


def get_test_df():
    """The OOT test population, base + engineered features merged. Cached after first call."""
    global _test_df
    if _test_df is None:
        results = get_results()
        bounds = results["split_boundaries"]
        base = pd.read_parquet(BASE_PARQUET)
        feat = pd.read_parquet(FEATURES_PARQUET)
        df = base.merge(feat[["observation_id"] + ENGINEERED_COLS], on="observation_id", how="left")
        months = df["month_end_date"].dt.to_period("M").astype(str)
        mask = (months >= bounds["test_start"]) & (months <= bounds["test_end"])
        _test_df = df.loc[mask].reset_index(drop=True)
    return _test_df


def _apply_shock(df: pd.DataFrame, scenario: str) -> pd.DataFrame:
    """
    Each shock updates its headline field AND the 3-month rolling counterpart
    that goes with it — feature importance (see Advanced Models) shows those
    rolling features, not the single-month snapshot, are what the model
    actually weighs most heavily. A shock to dpd alone barely moves a
    prediction driven mostly by dpd_avg_3m/dpd_max_3m; propagating it treats
    the shock as sustained over the trailing window, which is also the more
    realistic reading of a stress scenario (a lasting shift, not one blip).
    """
    shocked = df.copy()
    if scenario == "utilization_up":
        shocked["utilization_ratio"] = (shocked["utilization_ratio"] + 0.10).clip(upper=1.5)
        shocked["utilization_avg_3m"] = (shocked["utilization_avg_3m"] + 0.10).clip(upper=1.5)
    elif scenario == "payment_ratio_down":
        shocked["payment_ratio"] = (shocked["payment_ratio"] * 0.85).clip(lower=0)
        shocked["payment_ratio_avg_3m"] = (shocked["payment_ratio_avg_3m"] * 0.85).clip(lower=0)
    elif scenario == "bounces_up":
        shocked["recent_bounce_count_3m"] = shocked["recent_bounce_count_3m"] + 1
        shocked["bounce_flag"] = 1
        shocked["bounce_months_3m"] = (shocked["bounce_months_3m"] + 1).clip(upper=3)
    elif scenario == "dpd_up":
        shocked["dpd"] = shocked["dpd"] + 15
        shocked["account_status"] = shocked["dpd"].apply(account_status_from_dpd)
        shocked["dpd_avg_3m"] = shocked["dpd_avg_3m"] + 15
        shocked["dpd_max_3m"] = shocked["dpd_max_3m"] + 15
        shocked["delinquent_months_3m"] = (shocked["delinquent_months_3m"] + 1).clip(upper=3)
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    return shocked


def _score(df: pd.DataFrame, model_key: str) -> "pd.Series":
    preprocessor, model = load_model(model_key)
    X = preprocessor.transform(df[ALL_FEATURE_COLS])
    return model.predict_proba(X)[:, 1]


def run_scenario(scenario: str) -> dict:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    df = get_test_df()
    best_key = get_results()["best_model_key"]

    baseline_scores = _score(df, best_key)
    shocked_df = _apply_shock(df, scenario)
    shocked_scores = _score(shocked_df, best_key)

    def summarize(scores, balances):
        bands = pd.Series(scores).apply(lambda p: risk_band(p)["label"])
        high_risk = int((bands.isin(["High", "Very High"])).sum())
        return dict(
            mean_probability=round(float(scores.mean()), 4),
            high_risk_accounts=high_risk,
            high_risk_share=round(100 * high_risk / len(scores), 2),
            expected_loss_proxy=round(float((scores * balances).sum()), 0),
        )

    balances = df["current_balance"].to_numpy()
    before = summarize(baseline_scores, balances)
    after = summarize(shocked_scores, balances)

    before_bands = pd.Series(baseline_scores).apply(lambda p: risk_band(p)["label"])
    after_bands = pd.Series(shocked_scores).apply(lambda p: risk_band(p)["label"])
    newly_high_risk = int((
        (~before_bands.isin(["High", "Very High"])) & (after_bands.isin(["High", "Very High"]))
    ).sum())

    return dict(
        scenario=scenario,
        label=SCENARIOS[scenario]["label"],
        description=SCENARIOS[scenario]["description"],
        n_accounts=len(df),
        before=before,
        after=after,
        newly_high_risk_accounts=newly_high_risk,
        delta=dict(
            mean_probability_pp=round((after["mean_probability"] - before["mean_probability"]) * 100, 2),
            high_risk_accounts=after["high_risk_accounts"] - before["high_risk_accounts"],
            expected_loss_proxy=round(after["expected_loss_proxy"] - before["expected_loss_proxy"], 0),
        ),
    )
