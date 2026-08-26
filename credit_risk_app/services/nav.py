"""
Shared navigation model for the slide-deck-style UI.

Mirrors the 25-slide flow from the project spec. Only the items marked
built=True have a working route in this milestone; the rest render as
disabled "coming soon" entries in the sidebar so the full intended scope
stays visible, and are picked up in later milestones (see ROADMAP.md).
"""

NAV_ITEMS = [
    dict(order=1, title="Executive Overview", endpoint="overview.index", built=True),
    dict(order=2, title="Business Problem", endpoint=None, built=False),
    dict(order=3, title="Credit Risk Journey", endpoint=None, built=False),
    dict(order=4, title="Data Overview", endpoint="data.index", built=True),
    dict(order=5, title="Variable Explorer", endpoint="variables.index", built=True),
    dict(order=6, title="Data Quality", endpoint="quality.index", built=True),
    dict(order=7, title="Exploratory Data Analysis", endpoint=None, built=False),
    dict(order=8, title="Feature Engineering", endpoint=None, built=False),
    dict(order=9, title="Leakage & Governance", endpoint="governance.index", built=True),
    dict(order=10, title="OOT Split", endpoint=None, built=False),
    dict(order=11, title="Baseline Model", endpoint=None, built=False),
    dict(order=12, title="Advanced Models", endpoint=None, built=False),
    dict(order=13, title="Model Screening", endpoint=None, built=False),
    dict(order=14, title="ROC / AUC", endpoint=None, built=False),
    dict(order=15, title="KS Analysis", endpoint=None, built=False),
    dict(order=16, title="Lift & Gains", endpoint=None, built=False),
    dict(order=17, title="What-If Simulator", endpoint=None, built=False),
    dict(order=18, title="Account 360", endpoint=None, built=False),
    dict(order=19, title="Portfolio Scenario Simulator", endpoint=None, built=False),
    dict(order=20, title="Explainability", endpoint=None, built=False),
    dict(order=21, title="Collection Queue", endpoint=None, built=False),
    dict(order=22, title="Risk Metrics", endpoint=None, built=False),
    dict(order=23, title="Academic Interpretation", endpoint=None, built=False),
    dict(order=24, title="Final Recommendation", endpoint=None, built=False),
    dict(order=25, title="Download / Report", endpoint=None, built=False),
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
