"""Builds the downloadable tables for the Download/Reporting page — plain
pandas DataFrames, serialized to CSV/Excel by the route layer."""
import pandas as pd

from services.collection_service import get_scored_df
from services.data_service import get_summary
from services.model_service import get_results, ordered_models
from services.variable_dictionary import VARIABLE_DICTIONARY

HIGH_RISK_TOP_N = 2000


def variable_dictionary_df() -> pd.DataFrame:
    rows = [
        dict(
            variable=v["name"], role=v["role_category"], data_type=v["dtype"],
            definition=v["definition"], expected_risk_direction=v["expected_risk_direction"],
            governance=v["governance"], governance_reason=v["governance_reason"],
        )
        for v in VARIABLE_DICTIONARY
    ]
    return pd.DataFrame(rows)


def model_comparison_df() -> pd.DataFrame:
    rows = []
    for key, m in ordered_models():
        t = m["metrics"]["test"]
        rows.append(dict(
            model=m["display_name"], oot_auc=t["auc"], gini=t["gini"], ks=t["ks"]["ks"],
            top_decile_capture_pct=t["top_decile_capture"], precision_at_0_5=t["precision"],
            recall_at_0_5=t["recall"], f1_at_0_5=t["f1"],
            is_recommended=(key == get_results()["best_model_key"]),
        ))
    return pd.DataFrame(rows)


def decile_table_df() -> pd.DataFrame:
    results = get_results()
    best = results["models"][results["best_model_key"]]
    return pd.DataFrame(best["metrics"]["test"]["decile_table"])


def high_risk_accounts_df(n=HIGH_RISK_TOP_N) -> pd.DataFrame:
    df = get_scored_df().head(n)
    cols = [
        "risk_rank", "trade_id", "customer_id", "lender_id", "product", "state", "city_tier",
        "current_balance", "dpd", "account_status", "predicted_probability", "risk_band",
        "roll_to_90p_6m",
    ]
    return df[cols]


def eda_summary_df() -> pd.DataFrame:
    s = get_summary()
    rows = [
        dict(metric="row_count", value=s["row_count"]),
        dict(metric="n_customers", value=s["n_customers"]),
        dict(metric="n_trades", value=s["n_trades"]),
        dict(metric="n_lenders", value=s["n_lenders"]),
        dict(metric="n_products", value=s["n_products"]),
        dict(metric="date_min", value=s["date_min"]),
        dict(metric="date_max", value=s["date_max"]),
        dict(metric="delinquency_rate_pct", value=s["kpis"]["delinquency_rate"]),
        dict(metric="roll_90p_6m_rate_pct", value=s["kpis"]["roll_90p_6m_rate"]),
        dict(metric="avg_utilization", value=s["kpis"]["avg_utilization"]),
        dict(metric="avg_dpd", value=s["kpis"]["avg_dpd"]),
    ]
    for product, count in s["categorical_summary"]["product"].items():
        rows.append(dict(metric=f"product_count[{product}]", value=count))
    return pd.DataFrame(rows)


EXPORTS = {
    "variable_dictionary": ("Variable Dictionary", variable_dictionary_df),
    "model_comparison": ("Model Comparison", model_comparison_df),
    "decile_table": ("Decile Table", decile_table_df),
    "high_risk_accounts": ("High-Risk Account List", high_risk_accounts_df),
    "eda_summary": ("EDA Summary", eda_summary_df),
}
