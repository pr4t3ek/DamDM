"""Per-account lookup: full monthly history, live model score, and a driver diagnostic."""
import pandas as pd

from services.data_service import get_df, get_summary
from services.feature_service import get_features
from services.model_features import ALL_FEATURE_COLS, NUMERIC_COLS
from services.model_service import get_results
from services.simulator_service import risk_band, score_one, score_percentile

TIMELINE_COLS = [
    "month_end_date", "dpd", "account_status", "utilization_ratio", "payment_ratio",
    "current_balance", "amount_past_due", "bounce_flag", "partial_payment_flag", "roll_to_90p_6m",
]

# Direction a higher value moves risk: +1 raises risk, -1 is protective.
# Covers the numeric features most meaningful to show as "drivers" for an account.
RISK_DIRECTION = {
    "dpd": 1, "amount_past_due": 1, "utilization_ratio": 1, "recent_bounce_count_3m": 1,
    "balance_to_income_ratio": 1, "current_balance": 1,
    "payment_ratio": -1,
    "dpd_avg_3m": 1, "dpd_max_3m": 1, "delinquent_months_3m": 1, "partial_payment_months_3m": 1,
    "bounce_months_3m": 1, "payment_ratio_avg_3m": -1, "payment_ratio_std_3m": 1,
    "utilization_avg_3m": 1,
}

_portfolio_stats = None


def _get_portfolio_stats():
    """Median + std per driver feature, for standardizing deviations onto a comparable scale
    (a currency-scale feature and a 0-1 ratio can't be ranked by raw difference alone)."""
    global _portfolio_stats
    if _portfolio_stats is None:
        df = get_df()
        feat = get_features()
        merged = df[["observation_id"] + [c for c in NUMERIC_COLS if c in df.columns]].merge(
            feat[["observation_id"] + [c for c in NUMERIC_COLS if c in feat.columns and c not in df.columns]],
            on="observation_id", how="left",
        )
        _portfolio_stats = {
            c: dict(median=merged[c].median(), std=merged[c].std())
            for c in RISK_DIRECTION if c in merged.columns
        }
    return _portfolio_stats


def get_account(trade_id: str) -> dict | None:
    df = get_df()
    feat = get_features()
    base_rows = df[df["trade_id"] == trade_id].sort_values("month_end_date")
    if base_rows.empty:
        return None
    feat_rows = feat[feat["trade_id"] == trade_id][["observation_id"] + [c for c in feat.columns if c not in base_rows.columns]]
    merged = base_rows.merge(feat_rows, on="observation_id", how="left")

    # The target looks 6 months forward, so months within 6 months of the dataset's
    # end have no fully observed outcome yet — their stored 0/1 is not real ground
    # truth (see compute_label_maturity in prepare_data.py). Flag those explicitly
    # rather than let the timeline display a confident "No roll" that isn't earned.
    last_mature_month = get_summary()["label_maturity"]["last_mature_month"]
    timeline = merged[TIMELINE_COLS].copy()
    is_mature = timeline["month_end_date"].dt.to_period("M").astype(str) <= last_mature_month
    timeline.loc[~is_mature, "roll_to_90p_6m"] = None
    timeline["month_end_date"] = timeline["month_end_date"].dt.strftime("%Y-%m-%d")

    latest = merged.iloc[-1]
    record = {c: latest[c] for c in ALL_FEATURE_COLS}
    best_key = get_results()["best_model_key"]
    p = score_one(record, best_key)
    band = risk_band(p)

    stats = _get_portfolio_stats()
    drivers = []
    for feature, direction in RISK_DIRECTION.items():
        if feature not in latest or pd.isna(latest[feature]):
            continue
        s = stats.get(feature)
        if s is None or not s["std"]:
            continue
        account_value = float(latest[feature])
        raw_deviation = account_value - s["median"]
        z_score = (raw_deviation / s["std"]) * direction
        drivers.append(dict(
            feature=feature, account_value=round(account_value, 3),
            portfolio_median=round(float(s["median"]), 3), deviation=round(float(raw_deviation), 3),
            z_score=round(float(z_score), 2),
        ))
    drivers.sort(key=lambda d: -d["z_score"])

    return dict(
        raw_record=record,
        trade_id=trade_id,
        customer_id=str(latest["customer_id"]),
        lender_id=str(latest["lender_id"]),
        product=str(latest["product"]),
        state=str(latest["state"]),
        city_tier=str(latest["city_tier"]),
        customer_type=str(latest["customer_type"]),
        latest_month=latest["month_end_date"].strftime("%Y-%m-%d"),
        current_balance=round(float(latest["current_balance"]), 2),
        dpd=int(latest["dpd"]),
        account_status=str(latest["account_status"]),
        utilization_ratio=round(float(latest["utilization_ratio"]), 4),
        payment_ratio=round(float(latest["payment_ratio"]), 4),
        recent_bounce_count_3m=int(latest["recent_bounce_count_3m"]),
        months_on_book=int(latest["months_on_book"]),
        n_months_observed=len(merged),
        predicted_probability=round(float(p), 4),
        percentile=score_percentile(p),
        risk_band=band,
        drivers=drivers[:8],
        timeline=timeline.to_dict(orient="records"),
    )


def sample_trade_id() -> str:
    return get_df()["trade_id"].iloc[0]
