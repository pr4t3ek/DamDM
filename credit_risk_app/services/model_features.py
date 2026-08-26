"""
Shared feature-list constants for the model pipeline — used by
scripts/train_models.py, scripts/score_oot.py, and any service that needs
to build a row in the exact shape the trained pipelines expect.
"""
from services.variable_dictionary import FEATURE_COLS

TARGET = "roll_to_90p_6m"
THRESHOLD = 0.5

CATEGORICAL_COLS = ["product", "state", "city_tier", "customer_type", "account_status"]
NUMERIC_BASE_COLS = [c for c in FEATURE_COLS if c not in CATEGORICAL_COLS]
ENGINEERED_COLS = [
    "dpd_change_1m", "utilization_change_1m", "payment_ratio_change_1m", "balance_change_1m",
    "dpd_avg_3m", "utilization_avg_3m", "payment_ratio_avg_3m", "balance_avg_3m",
    "payment_ratio_std_3m", "utilization_std_3m", "balance_std_3m",
    "dpd_max_3m", "delinquent_months_3m", "partial_payment_months_3m", "bounce_months_3m",
    "utilization_rising_flag", "dpd_rising_flag", "payment_ratio_falling_flag", "months_observed",
]
NUMERIC_COLS = NUMERIC_BASE_COLS + ENGINEERED_COLS
ALL_FEATURE_COLS = CATEGORICAL_COLS + NUMERIC_COLS

MODEL_DISPLAY_NAMES = {
    "logistic_regression": "Logistic Regression",
    "decision_tree": "Decision Tree",
    "random_forest": "Random Forest",
    "xgboost": "XGBoost",
}
