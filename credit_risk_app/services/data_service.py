"""
Loads the prepared behavior_risk_mart dataset and its summary cache once
per process, and provides simple query helpers for the Data Explorer page.

Both artifacts are produced by scripts/prepare_data.py and are gitignored
(regenerable) — see that script for how they're built.
"""
import json
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
PARQUET_PATH = DATA_DIR / "behavior_risk_mart.parquet"
CACHE_PATH = DATA_DIR / "summary_cache.json"

_NOT_PREPARED_MSG = (
    "{path} not found. Run `python credit_risk_app/scripts/prepare_data.py` "
    "first (requires the behavior_risk_mart_part_*.csv files to have been "
    "pulled via git-lfs)."
)

_df = None
_summary = None

EXPLORER_COLUMNS = [
    "observation_id", "month_end_date", "customer_id", "trade_id", "lender_id",
    "product", "state", "city_tier", "customer_type", "current_balance",
    "utilization_ratio", "dpd", "account_status", "payment_ratio", "roll_to_90p_6m",
]


def get_df() -> pd.DataFrame:
    global _df
    if _df is None:
        if not PARQUET_PATH.exists():
            raise FileNotFoundError(_NOT_PREPARED_MSG.format(path=PARQUET_PATH))
        _df = pd.read_parquet(PARQUET_PATH)
    return _df


def get_summary() -> dict:
    global _summary
    if _summary is None:
        if not CACHE_PATH.exists():
            raise FileNotFoundError(_NOT_PREPARED_MSG.format(path=CACHE_PATH))
        _summary = json.loads(CACHE_PATH.read_text())
    return _summary


def query_observations(customer_id=None, trade_id=None, product=None, lender_id=None,
                        date_from=None, date_to=None, page=1, page_size=25):
    df = get_df()
    mask = pd.Series(True, index=df.index)
    if customer_id:
        mask &= df["customer_id"] == customer_id
    if trade_id:
        mask &= df["trade_id"] == trade_id
    if product:
        mask &= df["product"] == product
    if lender_id:
        mask &= df["lender_id"] == lender_id
    if date_from:
        mask &= df["month_end_date"] >= pd.Timestamp(date_from)
    if date_to:
        mask &= df["month_end_date"] <= pd.Timestamp(date_to)

    filtered = df.loc[mask, EXPLORER_COLUMNS]
    total = len(filtered)
    start = max(page - 1, 0) * page_size
    page_df = filtered.iloc[start:start + page_size].copy()
    page_df["month_end_date"] = page_df["month_end_date"].dt.strftime("%Y-%m-%d")
    return page_df.to_dict(orient="records"), total
