from datetime import datetime

from flask import Blueprint, render_template

from services.data_service import get_summary
from services.model_service import get_results, is_trained
from services.nav import get_nav_context
from services.variable_dictionary import (
    FEATURE_COLS,
    PRIMARY_TARGET,
    SECONDARY_TARGETS,
    VARIABLE_DICTIONARY,
)

governance_bp = Blueprint("governance", __name__, url_prefix="/governance")

GOVERNANCE_ORDER = ["Exclude", "Potentially Risky", "Safe"]


@governance_bp.route("/")
def index():
    ordered = sorted(
        VARIABLE_DICTIONARY,
        key=lambda v: GOVERNANCE_ORDER.index(v["governance"]),
    )
    model_governance = None
    if is_trained():
        results = get_results()
        best = results["models"][results["best_model_key"]]
        model_governance = dict(
            model_name=best["display_name"],
            model_key=results["best_model_key"],
            trained_at=datetime.fromisoformat(results["generated_at"]).strftime("%Y-%m-%d %H:%M UTC"),
            split=results["split_boundaries"],
            maturity=results["label_maturity"],
            n_features=len(results["feature_cols"]["all"]),
        )
    return render_template(
        "governance.html",
        variables=ordered,
        feature_cols=FEATURE_COLS,
        primary_target=PRIMARY_TARGET,
        secondary_targets=SECONDARY_TARGETS,
        model_governance=model_governance,
        summary=get_summary(),
        nav=get_nav_context("governance.index"),
    )
