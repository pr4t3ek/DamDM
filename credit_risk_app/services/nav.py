"""
Shared navigation model for the slide-deck-style UI.

Mirrors the 25-slide flow from the project spec. Only the items marked
built=True have a working route in this milestone; the rest render as
disabled "coming soon" entries in the sidebar so the full intended scope
stays visible, and are picked up in later milestones (see ROADMAP.md).
"""

NAV_ITEMS = [
    dict(order=1, title="Executive Overview", endpoint="overview.index", built=True),
    dict(order=2, title="Business Problem", endpoint="journey.business_problem", built=True),
    dict(order=3, title="Credit Risk Journey", endpoint="journey.index", built=True),
    dict(order=4, title="Data Overview", endpoint="data.index", built=True),
    dict(order=5, title="Variable Explorer", endpoint="variables.index", built=True),
    dict(order=6, title="Data Quality", endpoint="quality.index", built=True),
    dict(order=7, title="Exploratory Data Analysis", endpoint="eda.index", built=True),
    dict(order=8, title="Feature Engineering", endpoint="features.index", built=True),
    dict(order=9, title="Leakage & Governance", endpoint="governance.index", built=True),
    dict(order=10, title="OOT Split", endpoint="split.index", built=True),
    dict(order=11, title="Baseline Model", endpoint="model_baseline.index", built=True),
    dict(order=12, title="Advanced Models", endpoint="model_advanced.index", built=True),
    dict(order=13, title="Model Screening", endpoint="model_screening.index", built=True),
    dict(order=14, title="ROC / AUC", endpoint="model_roc.index", built=True),
    dict(order=15, title="KS Analysis", endpoint="model_ks.index", built=True),
    dict(order=16, title="Lift & Gains", endpoint="model_lift.index", built=True),
    dict(order=17, title="What-If Simulator", endpoint="simulator.index", built=True),
    dict(order=18, title="Account 360", endpoint="account.index", built=True),
    dict(order=19, title="Portfolio Scenario Simulator", endpoint="scenario.index", built=True),
    dict(order=20, title="Explainability", endpoint="explain.index", built=True),
    dict(order=21, title="Collection Queue", endpoint="collection.index", built=True),
    dict(order=22, title="Risk Metrics", endpoint="risk_metrics.index", built=True),
    dict(order=23, title="Academic Interpretation", endpoint="academic.index", built=True),
    dict(order=24, title="Final Recommendation", endpoint="recommendation.index", built=True),
    dict(order=25, title="Download / Report", endpoint="download.index", built=True),
]


def built_items():
    return [i for i in NAV_ITEMS if i["built"]]


def get_nav_context(current_endpoint):
    built = built_items()
    idx = next((i for i, item in enumerate(built) if item["endpoint"] == current_endpoint), None)
    prev_item = built[idx - 1] if idx is not None and idx > 0 else None
    next_item = built[idx + 1] if idx is not None and idx < len(built) - 1 else None
    return dict(
        all_items=NAV_ITEMS,
        current_endpoint=current_endpoint,
        progress_current=(idx + 1) if idx is not None else None,
        progress_total=len(built),
        total_slides=len(NAV_ITEMS),
        prev_item=prev_item,
        next_item=next_item,
    )
