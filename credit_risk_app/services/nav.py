"""
Shared navigation model for the slide-deck-style UI.

All 26 slides (the original 25-slide spec plus the Cost-Benefit Analyzer)
are built. Each item also carries a `section`: "main" is the 10-slide live
walkthrough for a time-boxed presentation -- clicking Next in order covers
the whole talk -- and "appendix" is supporting detail kept a click away for
follow-up questions, not part of the timed walk. The split is purely
presentational: every page is still a normal route, reachable directly.
"""

NAV_ITEMS = [
    # -- Main: the live 10-12 minute walkthrough. In presentation order --
    # clicking "Next" from Executive Overview through Final Recommendation
    # is the whole live talk, start to finish. ROC/AUC sits between Model
    # Screening and Lift & Gains -- the same model-evaluation slot it holds
    # in the milestone build order -- and Portfolio Scenario Simulator /
    # Collection Queue moved to the appendix, alongside the rest of the
    # Milestone 4 interactive tools.
    dict(order=1, title="Executive Overview", endpoint="overview.index", built=True, section="main"),
    dict(order=2, title="Data Overview", endpoint="data.index", built=True, section="main"),
    dict(order=3, title="Data Quality", endpoint="quality.index", built=True, section="main"),
    dict(order=4, title="OOT Split", endpoint="split.index", built=True, section="main"),
    dict(order=5, title="Model Screening", endpoint="model_screening.index", built=True, section="main"),
    dict(order=6, title="ROC / AUC", endpoint="model_roc.index", built=True, section="main"),
    dict(order=7, title="Lift & Gains", endpoint="model_lift.index", built=True, section="main"),
    dict(order=8, title="What-If Simulator", endpoint="simulator.index", built=True, section="main"),
    dict(order=9, title="Cost-Benefit Analyzer", endpoint="costbenefit.index", built=True, section="main"),
    dict(order=10, title="Final Recommendation", endpoint="recommendation.index", built=True, section="main"),

    # -- Appendix: supporting detail and backup for follow-up questions.
    # Not part of the timed live walkthrough, but a click away if asked.
    dict(order=11, title="Business Problem", endpoint="journey.business_problem", built=True, section="appendix"),
    dict(order=12, title="Credit Risk Journey", endpoint="journey.index", built=True, section="appendix"),
    dict(order=13, title="Variable Explorer", endpoint="variables.index", built=True, section="appendix"),
    dict(order=14, title="Exploratory Data Analysis", endpoint="eda.index", built=True, section="appendix"),
    dict(order=15, title="Feature Engineering", endpoint="features.index", built=True, section="appendix"),
    dict(order=16, title="Leakage & Governance", endpoint="governance.index", built=True, section="appendix"),
    dict(order=17, title="Baseline Model", endpoint="model_baseline.index", built=True, section="appendix"),
    dict(order=18, title="Advanced Models", endpoint="model_advanced.index", built=True, section="appendix"),
    dict(order=19, title="KS Analysis", endpoint="model_ks.index", built=True, section="appendix"),
    dict(order=20, title="Portfolio Scenario Simulator", endpoint="scenario.index", built=True, section="appendix"),
    dict(order=21, title="Collection Queue", endpoint="collection.index", built=True, section="appendix"),
    dict(order=22, title="Account 360", endpoint="account.index", built=True, section="appendix"),
    dict(order=23, title="Explainability", endpoint="explain.index", built=True, section="appendix"),
    dict(order=24, title="Risk Metrics", endpoint="risk_metrics.index", built=True, section="appendix"),
    dict(order=25, title="Academic Interpretation", endpoint="academic.index", built=True, section="appendix"),
    dict(order=26, title="Download / Report", endpoint="download.index", built=True, section="appendix"),
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
