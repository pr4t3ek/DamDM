"""Collection queue prioritization, built directly from the cached OOT scores."""
from pathlib import Path

import numpy as np
import pandas as pd

from services.simulator_service import get_percentile_cutoffs

APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
OOT_SCORED_PARQUET = DATA_DIR / "oot_scored.parquet"

CAPACITY_CHOICES = [5, 10, 20, 30]

_df = None


def is_ready() -> bool:
    return OOT_SCORED_PARQUET.exists()


def _get_df() -> pd.DataFrame:
    global _df
    if _df is None:
        df = pd.read_parquet(OOT_SCORED_PARQUET).sort_values("risk_rank").reset_index(drop=True)
        cutoffs = get_percentile_cutoffs()
        bins = [-np.inf] + [c[0] for c in cutoffs] + [np.inf]
        labels = [c[1] for c in cutoffs] + ["Very High"]
        df["risk_band"] = pd.cut(df["predicted_probability"], bins=bins, labels=labels)
        _df = df
    return _df


def queue_summary(capacity_pct: int) -> dict:
    df = _get_df()
    n_total = len(df)
    n_capacity = max(1, round(n_total * capacity_pct / 100))
    top = df.iloc[:n_capacity]

    total_bads = int(df["roll_to_90p_6m"].sum())
    captured_bads = int(top["roll_to_90p_6m"].sum())
    total_exposure = float(df["current_balance"].sum())
    covered_exposure = float(top["current_balance"].sum())

    return dict(
        capacity_pct=capacity_pct,
        n_total=n_total,
        accounts_contacted=n_capacity,
        bad_accounts_captured=captured_bads,
        total_bad_accounts=total_bads,
        capture_rate=round(100 * captured_bads / total_bads, 2) if total_bads else None,
        precision=round(100 * captured_bads / n_capacity, 2),
        exposure_covered=round(covered_exposure, 0),
        total_exposure=round(total_exposure, 0),
        exposure_covered_pct=round(100 * covered_exposure / total_exposure, 2) if total_exposure else None,
    )


def queue_page(capacity_pct: int, page: int = 1, page_size: int = 25) -> tuple:
    df = _get_df()
    n_total = len(df)
    n_capacity = max(1, round(n_total * capacity_pct / 100))
    top = df.iloc[:n_capacity]
    start = max(page - 1, 0) * page_size
    page_df = top.iloc[start:start + page_size]
    return page_df.to_dict(orient="records"), n_capacity


def capacity_curve() -> list:
    """Capture rate and exposure covered at every capacity choice, for the summary chart."""
    return [queue_summary(pct) for pct in CAPACITY_CHOICES]
