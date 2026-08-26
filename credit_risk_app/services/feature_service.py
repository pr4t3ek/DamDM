"""Loads the engineered behavioral features and serves sample rows for inspection."""
import json
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
FEATURES_PARQUET = DATA_DIR / "behavior_features.parquet"
FEATURES_CACHE = DATA_DIR / "features_cache.json"

_NOT_BUILT = (
    "{path} not found. Run `python credit_risk_app/scripts/build_features.py` "
    "(after prepare_data.py) to generate the behavioral features."
)

_feat = None
_cache = None


def is_built() -> bool:
    return FEATURES_PARQUET.exists() and FEATURES_CACHE.exists()


def get_features() -> pd.DataFrame:
    global _feat
    if _feat is None:
        if not FEATURES_PARQUET.exists():
            raise FileNotFoundError(_NOT_BUILT.format(path=FEATURES_PARQUET))
        _feat = pd.read_parquet(FEATURES_PARQUET)
    return _feat


def get_cache() -> dict:
    global _cache
    if _cache is None:
        if not FEATURES_CACHE.exists():
            raise FileNotFoundError(_NOT_BUILT.format(path=FEATURES_CACHE))
        _cache = json.loads(FEATURES_CACHE.read_text())
    return _cache


def sample_trade(trade_id=None, limit=24):
    """Monthly feature values for one account, so the derivations are inspectable."""
    feat = get_features()
    if not trade_id:
        trade_id = feat["trade_id"].iloc[0]
    sub = feat[feat["trade_id"] == trade_id].sort_values("month_end_date").head(limit).copy()
    if sub.empty:
        return trade_id, []
    sub["month_end_date"] = sub["month_end_date"].dt.strftime("%Y-%m-%d")
    return trade_id, sub.where(pd.notna(sub), None).to_dict(orient="records")
