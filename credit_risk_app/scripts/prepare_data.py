"""
One-time data preparation for the Credit Risk Analytics Dashboard.

Reads the raw behavior_risk_mart_part_{01,02,03}.csv files (pulled via
git-lfs into "Raw Data and Data Dictionary/02_Data_Mart/"), concatenates
and type-coerces them, and writes two artifacts into credit_risk_app/data/:

  - behavior_risk_mart.parquet  : the full cleaned dataset, for fast reload
  - summary_cache.json          : precomputed stats the Flask routes read
                                   instead of re-aggregating ~1.5M rows
                                   on every request

Run once before starting the app:
    python credit_risk_app/scripts/prepare_data.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = APP_DIR.parent
RAW_DATA_DIR = REPO_ROOT / "Raw Data and Data Dictionary" / "02_Data_Mart"
OUT_DIR = APP_DIR / "data"
PARQUET_PATH = OUT_DIR / "behavior_risk_mart.parquet"
CACHE_PATH = OUT_DIR / "summary_cache.json"

EXPECTED_COLUMNS = [
    "observation_id", "trade_id", "customer_id", "lender_id", "product",
    "month_end_date", "months_on_book", "state", "city_tier", "customer_type",
    "current_balance", "credit_limit_or_original_amount", "utilization_ratio",
    "emi_due", "payment_ratio", "amount_past_due", "dpd", "account_status",
    "bounce_flag", "recent_bounce_count_3m", "partial_payment_flag",
    "restructure_flag", "balance_to_income_ratio", "ead_estimate",
    "lgd_estimate", "pd_12m_proxy", "expected_loss_estimate",
    "roll_to_30p_3m", "roll_to_60p_3m", "roll_to_90p_6m", "cure_3m",
]

INT_COLS = ["months_on_book", "dpd", "recent_bounce_count_3m"]
FLAG_COLS = ["bounce_flag", "partial_payment_flag", "restructure_flag"]
TARGET_COLS = ["roll_to_30p_3m", "roll_to_60p_3m", "roll_to_90p_6m", "cure_3m"]
NUMERIC_COLS = [
    "current_balance", "credit_limit_or_original_amount", "utilization_ratio",
    "emi_due", "payment_ratio", "amount_past_due", "balance_to_income_ratio",
    "ead_estimate", "lgd_estimate", "pd_12m_proxy", "expected_loss_estimate",
]
CATEGORICAL_COLS = ["product", "state", "city_tier", "customer_type", "account_status"]


def load_raw() -> pd.DataFrame:
    part_files = sorted(RAW_DATA_DIR.glob("behavior_risk_mart_part_*.csv"))
    if not part_files:
        sys.exit(
            f"No behavior_risk_mart_part_*.csv files found under {RAW_DATA_DIR}. "
            "Run: git lfs pull --include=\"Raw Data and Data Dictionary/02_Data_Mart/"
            "behavior_risk_mart_part_*.csv\""
        )
    print(f"Loading {len(part_files)} part files: {[p.name for p in part_files]}")
    frames = [pd.read_csv(p) for p in part_files]
    df = pd.concat(frames, ignore_index=True)
    print(f"Concatenated shape: {df.shape}")
    return df


def validate_schema(df: pd.DataFrame) -> list:
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    if missing:
        sys.exit(f"Schema mismatch — missing expected columns: {missing}")
    if extra:
        print(f"WARNING: unexpected extra columns present: {extra}")
    return extra


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month_end_date"] = pd.to_datetime(df["month_end_date"], errors="coerce")
    for c in INT_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    for c in FLAG_COLS + TARGET_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    for c in NUMERIC_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in CATEGORICAL_COLS:
        df[c] = df[c].astype("category")
    return df


TARGET_HORIZON_MONTHS = 6


def pct(n, d):
    return round(100.0 * n / d, 3) if d else 0.0


def compute_label_maturity(df: pd.DataFrame) -> dict:
    """
    roll_to_90p_6m looks 6 months forward, so observations within 6 months of
    the dataset's end cannot have a fully observed outcome. Their labels are
    right-censored (under-counted toward 0) and must be excluded from modeling.
    """
    months = df["month_end_date"].dt.to_period("M")
    data_max = months.max()
    last_mature = data_max - TARGET_HORIZON_MONTHS
    immature_mask = months > last_mature
    return dict(
        horizon_months=TARGET_HORIZON_MONTHS,
        data_max_month=str(data_max),
        last_mature_month=str(last_mature),
        first_immature_month=str(last_mature + 1),
        immature_rows=int(immature_mask.sum()),
        mature_rows=int((~immature_mask).sum()),
    )


def build_quality_checks(df: pd.DataFrame) -> list:
    n = len(df)
    checks = []

    dup_ids = int(df["observation_id"].duplicated().sum())
    checks.append(dict(
        name="Duplicate observation_id",
        status="red" if dup_ids > 0 else "green",
        detail=f"{dup_ids} duplicate observation_id value(s) found.",
        count=dup_ids,
    ))

    neg_util = int((df["utilization_ratio"] < 0).sum())
    high_util = int((df["utilization_ratio"] > 2).sum())
    checks.append(dict(
        name="Utilization ratio out of range",
        status="red" if neg_util > 0 else ("amber" if high_util > 0 else "green"),
        detail=f"{neg_util} negative value(s); {high_util} value(s) above 2.0 ({pct(high_util, n)}%).",
        count=neg_util + high_util,
    ))

    neg_dpd = int((df["dpd"] < 0).sum())
    checks.append(dict(
        name="Negative DPD",
        status="red" if neg_dpd > 0 else "green",
        detail=f"{neg_dpd} negative dpd value(s) found.",
        count=neg_dpd,
    ))

    neg_pr = int((df["payment_ratio"] < 0).sum())
    high_pr = int((df["payment_ratio"] > 5).sum())
    checks.append(dict(
        name="Payment ratio anomalies",
        status="red" if neg_pr > 0 else ("amber" if high_pr > 0 else "green"),
        detail=f"{neg_pr} negative value(s); {high_pr} value(s) above 5.0 (possible data errors).",
        count=neg_pr + high_pr,
    ))

    invalid_dates = int(df["month_end_date"].isna().sum())
    today = pd.Timestamp(datetime.now(timezone.utc).date())
    future_dates = int((df["month_end_date"] > today).sum())
    checks.append(dict(
        name="Invalid / future dates",
        status="red" if invalid_dates > 0 else ("amber" if future_dates > 0 else "green"),
        detail=f"{invalid_dates} unparseable date(s); {future_dates} date(s) after today.",
        count=invalid_dates + future_dates,
    ))

    missing_target = int(df["roll_to_90p_6m"].isna().sum())
    checks.append(dict(
        name="Missing primary target (roll_to_90p_6m)",
        status="amber" if missing_target > 0 else "green",
        detail=f"{missing_target} row(s) ({pct(missing_target, n)}%) have no roll_to_90p_6m label.",
        count=missing_target,
    ))

    maturity = compute_label_maturity(df)
    immature_rows = maturity["immature_rows"]
    checks.append(dict(
        name="Right-censored target labels (immature outcome window)",
        status="red" if immature_rows > 0 else "green",
        detail=(
            f"The target needs a {TARGET_HORIZON_MONTHS}-month forward window, but the data ends "
            f"{maturity['data_max_month']}. Observations from {maturity['first_immature_month']} onward "
            f"({immature_rows:,} rows, {pct(immature_rows, n)}%) cannot have a fully observed outcome, so "
            f"their labels are systematically under-counted (the final month shows a 0% event rate). "
            f"EXCLUDE these rows from training, validation, and test — do not treat label=0 as ground truth. "
            f"Last fully mature observation month: {maturity['last_mature_month']}."
        ),
        count=immature_rows,
    ))

    neg_balance = int((df["current_balance"] < 0).sum())
    checks.append(dict(
        name="Negative current_balance",
        status="amber" if neg_balance > 0 else "green",
        detail=f"{neg_balance} negative current_balance value(s) found.",
        count=neg_balance,
    ))

    return checks


def build_summary(df: pd.DataFrame, extra_cols: list) -> dict:
    n = len(df)

    def target_stats(col):
        valid = df[col].dropna()
        n_valid = int(len(valid))
        n_missing = int(df[col].isna().sum())
        positive = int((valid == 1).sum())
        negative = int((valid == 0).sum())
        return dict(
            n_valid=n_valid, n_missing=n_missing,
            positive=positive, negative=negative,
            event_rate=pct(positive, n_valid) if n_valid else None,
        )

    missingness = {c: pct(int(df[c].isna().sum()), n) for c in df.columns}

    numeric_summary = {}
    for c in NUMERIC_COLS + INT_COLS:
        s = df[c].dropna().astype(float)
        if len(s) == 0:
            numeric_summary[c] = None
            continue
        numeric_summary[c] = dict(
            min=round(float(s.min()), 4), max=round(float(s.max()), 4),
            mean=round(float(s.mean()), 4), median=round(float(s.median()), 4),
            std=round(float(s.std()), 4),
        )

    categorical_summary = {}
    for c in CATEGORICAL_COLS:
        vc = df[c].value_counts(dropna=False)
        categorical_summary[c] = {str(k): int(v) for k, v in vc.items()}

    dtypes = {c: str(df[c].dtype) for c in df.columns}

    monthly = (
        df.assign(month=df["month_end_date"].dt.to_period("M").astype(str))
        .groupby("month", observed=True)["roll_to_90p_6m"]
        .agg(observations="count", events="sum")
        .reset_index()
        .sort_values("month")
    )
    monthly["event_rate"] = (100 * monthly["events"] / monthly["observations"]).round(3)

    dpd_positive = int((df["dpd"].fillna(0) > 0).sum())
    delinquency_rate = pct(dpd_positive, n)
    roll_valid = df["roll_to_90p_6m"].dropna()
    roll_rate = pct(int((roll_valid == 1).sum()), len(roll_valid)) if len(roll_valid) else None

    return dict(
        generated_at=datetime.now(timezone.utc).isoformat(),
        row_count=n,
        extra_columns_found=extra_cols,
        n_customers=int(df["customer_id"].nunique()),
        n_trades=int(df["trade_id"].nunique()),
        n_lenders=int(df["lender_id"].nunique()),
        n_products=int(df["product"].nunique()),
        products=sorted(df["product"].dropna().unique().tolist()),
        states=sorted(df["state"].dropna().unique().tolist()),
        city_tiers=sorted(df["city_tier"].dropna().unique().tolist()),
        customer_types=sorted(df["customer_type"].dropna().unique().tolist()),
        date_min=str(df["month_end_date"].min().date()) if df["month_end_date"].notna().any() else None,
        date_max=str(df["month_end_date"].max().date()) if df["month_end_date"].notna().any() else None,
        n_distinct_months=int(df["month_end_date"].dropna().dt.to_period("M").nunique()),
        target=dict(
            roll_to_90p_6m=target_stats("roll_to_90p_6m"),
            roll_to_30p_3m=target_stats("roll_to_30p_3m"),
            roll_to_60p_3m=target_stats("roll_to_60p_3m"),
            cure_3m=target_stats("cure_3m"),
        ),
        kpis=dict(
            total_accounts=int(df["trade_id"].nunique()),
            total_observations=n,
            delinquency_rate=delinquency_rate,
            roll_90p_6m_rate=roll_rate,
            avg_utilization=round(float(df["utilization_ratio"].mean()), 4),
            avg_dpd=round(float(df["dpd"].astype("float").mean()), 2),
        ),
        label_maturity=compute_label_maturity(df),
        monthly_roll_rate=monthly.to_dict(orient="records"),
        missingness=missingness,
        dtypes=dtypes,
        numeric_summary=numeric_summary,
        categorical_summary=categorical_summary,
        quality_checks=build_quality_checks(df),
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_raw()
    extra_cols = validate_schema(df)
    df = coerce_types(df)

    print("Writing parquet...")
    df.to_parquet(PARQUET_PATH, index=False)
    print(f"Wrote {PARQUET_PATH} ({PARQUET_PATH.stat().st_size / 1e6:.1f} MB)")

    print("Computing summary cache...")
    summary = build_summary(df, extra_cols)
    CACHE_PATH.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {CACHE_PATH}")

    print("\n--- Quality check summary ---")
    for chk in summary["quality_checks"]:
        print(f"[{chk['status'].upper():5s}] {chk['name']}: {chk['detail']}")


if __name__ == "__main__":
    main()
