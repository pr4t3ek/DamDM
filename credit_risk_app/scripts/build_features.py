"""
Behavioral feature engineering for the delinquency early-warning model.

The mart is panel data: one row per trade per month. That structure carries
signal a single snapshot cannot — whether an account is deteriorating, how
erratic its payments are, how much stress it has accumulated. This script
derives those features per trade_id and writes them alongside the base data.

Leakage rule: every window is TRAILING and includes only the observation
month and earlier. A rolling window over rows sorted by month, or a diff
against the previous month, uses no information unavailable on the
observation date. Nothing here touches a target column.

Run after prepare_data.py:
    python credit_risk_app/scripts/build_features.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
BASE_PARQUET = DATA_DIR / "behavior_risk_mart.parquet"
FEATURES_PARQUET = DATA_DIR / "behavior_features.parquet"
FEATURES_CACHE = DATA_DIR / "features_cache.json"

KEYS = ["observation_id", "trade_id", "month_end_date"]
WINDOW = 3

# name -> (family, plain-English description)
FEATURE_META = {
    "dpd_change_1m": ("Trend", "Change in DPD versus the previous month. Positive means deteriorating."),
    "utilization_change_1m": ("Trend", "Change in utilization ratio versus the previous month."),
    "payment_ratio_change_1m": ("Trend", "Change in payment ratio versus the previous month. Negative means paying less."),
    "balance_change_1m": ("Trend", "Change in outstanding balance versus the previous month."),
    "dpd_avg_3m": ("Rolling", "Average DPD over the last 3 months, including this one."),
    "utilization_avg_3m": ("Rolling", "Average utilization ratio over the last 3 months."),
    "payment_ratio_avg_3m": ("Rolling", "Average payment ratio over the last 3 months."),
    "balance_avg_3m": ("Rolling", "Average outstanding balance over the last 3 months."),
    "payment_ratio_std_3m": ("Volatility", "Standard deviation of payment ratio over 3 months. Higher means erratic repayment."),
    "utilization_std_3m": ("Volatility", "Standard deviation of utilization over 3 months."),
    "balance_std_3m": ("Volatility", "Standard deviation of balance over 3 months."),
    "dpd_max_3m": ("Stress", "Worst DPD reached in the last 3 months."),
    "delinquent_months_3m": ("Stress", "Count of the last 3 months with DPD above zero."),
    "partial_payment_months_3m": ("Stress", "Count of the last 3 months with a partial payment."),
    "bounce_months_3m": ("Stress", "Count of the last 3 months with a payment bounce."),
    "utilization_rising_flag": ("Momentum", "1 if utilization increased versus the previous month."),
    "dpd_rising_flag": ("Momentum", "1 if DPD increased versus the previous month."),
    "payment_ratio_falling_flag": ("Momentum", "1 if payment ratio fell versus the previous month."),
    "months_observed": ("Context", "How many monthly observations exist for this account up to and including this month."),
}


def build(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["trade_id", "month_end_date"]).reset_index(drop=True)
    g = df.groupby("trade_id", observed=True, sort=False)

    out = df[KEYS].copy()

    dpd = df["dpd"].astype("float64")
    util = df["utilization_ratio"].astype("float64")
    pratio = df["payment_ratio"].astype("float64")
    balance = df["current_balance"].astype("float64")

    out["dpd_change_1m"] = g["dpd"].diff().astype("float64").round(2)
    out["utilization_change_1m"] = g["utilization_ratio"].diff().round(4)
    out["payment_ratio_change_1m"] = g["payment_ratio"].diff().round(4)
    out["balance_change_1m"] = g["current_balance"].diff().round(2)

    def roll(series, how):
        s = series.groupby(df["trade_id"], observed=True, sort=False)
        r = s.rolling(WINDOW, min_periods=1)
        return getattr(r, how)().reset_index(level=0, drop=True)

    out["dpd_avg_3m"] = roll(dpd, "mean").round(3)
    out["utilization_avg_3m"] = roll(util, "mean").round(4)
    out["payment_ratio_avg_3m"] = roll(pratio, "mean").round(4)
    out["balance_avg_3m"] = roll(balance, "mean").round(2)

    out["payment_ratio_std_3m"] = roll(pratio, "std").round(4)
    out["utilization_std_3m"] = roll(util, "std").round(4)
    out["balance_std_3m"] = roll(balance, "std").round(2)

    out["dpd_max_3m"] = roll(dpd, "max")
    out["delinquent_months_3m"] = roll((dpd > 0).astype("float64"), "sum")
    out["partial_payment_months_3m"] = roll(df["partial_payment_flag"].astype("float64"), "sum")
    out["bounce_months_3m"] = roll(df["bounce_flag"].astype("float64"), "sum")

    out["utilization_rising_flag"] = (out["utilization_change_1m"] > 0).astype("int8")
    out["dpd_rising_flag"] = (out["dpd_change_1m"] > 0).astype("int8")
    out["payment_ratio_falling_flag"] = (out["payment_ratio_change_1m"] < 0).astype("int8")

    out["months_observed"] = g.cumcount() + 1

    # A first observation has no prior month, so trend/volatility are undefined
    # rather than zero. Left as NaN for the model to handle explicitly.
    return out


def summarize(feat: pd.DataFrame, base: pd.DataFrame) -> dict:
    merged = feat.merge(base[["observation_id", "roll_to_90p_6m"]], on="observation_id", how="left")
    stats = {}
    for name, (family, desc) in FEATURE_META.items():
        s = merged[name].astype("float64")
        valid = s.dropna()
        entry = dict(
            family=family,
            description=desc,
            missing_pct=round(100 * s.isna().mean(), 3),
            min=round(float(valid.min()), 4) if len(valid) else None,
            max=round(float(valid.max()), 4) if len(valid) else None,
            mean=round(float(valid.mean()), 4) if len(valid) else None,
        )
        # Correlation with the target is a quick signal-strength read; it is a
        # diagnostic only and never used as a model input.
        if len(valid) > 1 and valid.nunique() > 1:
            entry["target_corr"] = round(float(s.corr(merged["roll_to_90p_6m"].astype("float64"))), 4)
        else:
            entry["target_corr"] = None
        stats[name] = entry

    families = {}
    for name, (family, _) in FEATURE_META.items():
        families.setdefault(family, []).append(name)

    return dict(
        generated_at=datetime.now(timezone.utc).isoformat(),
        n_features=len(FEATURE_META),
        n_rows=len(feat),
        window_months=WINDOW,
        families=families,
        features=stats,
    )


def main():
    if not BASE_PARQUET.exists():
        sys.exit(f"{BASE_PARQUET} not found. Run scripts/prepare_data.py first.")
    print("Loading base dataset...")
    base = pd.read_parquet(BASE_PARQUET)
    print(f"  {base.shape[0]:,} rows")

    print(f"Building {len(FEATURE_META)} behavioral features per trade_id...")
    feat = build(base)

    feat.to_parquet(FEATURES_PARQUET, index=False)
    print(f"Wrote {FEATURES_PARQUET} ({FEATURES_PARQUET.stat().st_size / 1e6:.1f} MB)")

    print("Summarizing...")
    summary = summarize(feat, base)
    FEATURES_CACHE.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {FEATURES_CACHE}")

    print("\n--- Feature signal (correlation with roll_to_90p_6m) ---")
    ranked = sorted(
        ((n, s["target_corr"]) for n, s in summary["features"].items() if s["target_corr"] is not None),
        key=lambda x: abs(x[1]), reverse=True,
    )
    for name, corr in ranked:
        print(f"  {corr:+.4f}  {name}")


if __name__ == "__main__":
    main()
