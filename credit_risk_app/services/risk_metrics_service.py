"""
Assembles the three distinct metric families for the Risk Metrics Dashboard:
financial risk metrics (the dataset's own PD/EAD/LGD/EL fields — display and
portfolio benchmarking only, per the Leakage & Governance page, never model
inputs), portfolio risk metrics (observed delinquency/roll/cure rates), and
model metrics (this model's own OOT performance).
"""
from services.data_service import get_df, get_summary
from services.model_service import get_results

FINANCIAL_COLS = ["pd_12m_proxy", "ead_estimate", "lgd_estimate", "expected_loss_estimate"]


def financial_risk_metrics() -> dict:
    df = get_df()
    stats = {c: dict(mean=round(float(df[c].mean()), 4), median=round(float(df[c].median()), 4))
             for c in FINANCIAL_COLS}
    stats["total_expected_loss"] = round(float(df["expected_loss_estimate"].sum()), 0)
    stats["total_ead"] = round(float(df["ead_estimate"].sum()), 0)
    return stats


def portfolio_risk_metrics() -> dict:
    df = get_df()
    summary = get_summary()
    delinquent = df[df["dpd"] > 0]
    cure_rate = round(100 * float(delinquent["cure_3m"].mean()), 2) if len(delinquent) else None
    return dict(
        delinquency_rate=summary["kpis"]["delinquency_rate"],
        roll_90p_6m_rate=summary["kpis"]["roll_90p_6m_rate"],
        roll_30p_3m_rate=summary["target"]["roll_to_30p_3m"]["event_rate"],
        roll_60p_3m_rate=summary["target"]["roll_to_60p_3m"]["event_rate"],
        cure_rate_among_delinquent=cure_rate,
        avg_utilization=summary["kpis"]["avg_utilization"],
        avg_dpd=summary["kpis"]["avg_dpd"],
    )


def model_metrics() -> dict:
    results = get_results()
    best = results["models"][results["best_model_key"]]
    test = best["metrics"]["test"]
    return dict(
        model_name=best["display_name"],
        auc=test["auc"], gini=test["gini"], ks=test["ks"]["ks"],
        top_decile_capture=test["top_decile_capture"],
        precision=test["precision"], recall=test["recall"], f1=test["f1"],
    )
