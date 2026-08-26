"""
Scores every observation in the out-of-time test period with the
best-performing model (per model_results.json), and caches the result as a
parquet file. This is the shared foundation for Milestone 4's Account 360,
Collection Queue, and Explainability pages — none of them need to re-run
inference themselves, they just read observation-level scores back.

Run after train_models.py:
    python credit_risk_app/scripts/score_oot.py
"""
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

from services.model_features import ENGINEERED_COLS, ALL_FEATURE_COLS  # noqa: E402

DATA_DIR = APP_DIR / "data"
MODELS_DIR = APP_DIR / "models"
BASE_PARQUET = DATA_DIR / "behavior_risk_mart.parquet"
FEATURES_PARQUET = DATA_DIR / "behavior_features.parquet"
RESULTS_CACHE = DATA_DIR / "model_results.json"
OOT_SCORED_PARQUET = DATA_DIR / "oot_scored.parquet"

DISPLAY_COLS = [
    "observation_id", "trade_id", "customer_id", "lender_id", "product", "state", "city_tier",
    "customer_type", "month_end_date", "months_on_book", "current_balance", "utilization_ratio",
    "dpd", "account_status", "payment_ratio", "amount_past_due", "ead_estimate", "roll_to_90p_6m",
]


def main():
    if not RESULTS_CACHE.exists():
        sys.exit("Run train_models.py first.")
    results = json.loads(RESULTS_CACHE.read_text())
    best_key = results["best_model_key"]
    bounds = results["split_boundaries"]
    print(f"Scoring OOT test period ({bounds['test_start']}..{bounds['test_end']}) with {best_key}")

    base = pd.read_parquet(BASE_PARQUET)
    feat = pd.read_parquet(FEATURES_PARQUET)
    df = base.merge(feat[["observation_id"] + ENGINEERED_COLS], on="observation_id", how="left")

    months = df["month_end_date"].dt.to_period("M").astype(str)
    mask = (months >= bounds["test_start"]) & (months <= bounds["test_end"])
    test_df = df.loc[mask].reset_index(drop=True)
    print(f"  {len(test_df):,} OOT rows")

    preprocessor = joblib.load(MODELS_DIR / f"{best_key}_preprocessor.pkl")
    model = joblib.load(MODELS_DIR / f"{best_key}_model.pkl")
    X = preprocessor.transform(test_df[ALL_FEATURE_COLS])
    scores = model.predict_proba(X)[:, 1]

    out = test_df[DISPLAY_COLS].copy()
    out["predicted_probability"] = scores.round(5)
    out["month_end_date"] = out["month_end_date"].dt.strftime("%Y-%m-%d")
    out = out.sort_values("predicted_probability", ascending=False).reset_index(drop=True)
    out["risk_rank"] = out.index + 1

    out.to_parquet(OOT_SCORED_PARQUET, index=False)
    print(f"Wrote {OOT_SCORED_PARQUET} ({OOT_SCORED_PARQUET.stat().st_size / 1e6:.1f} MB)")
    print(f"Scored with: {best_key}")
    print(f"Score range: {scores.min():.4f} - {scores.max():.4f}, mean {scores.mean():.4f}")


if __name__ == "__main__":
    main()
