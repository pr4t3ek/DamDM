from flask import Blueprint, render_template

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
    return render_template(
        "governance.html",
        variables=ordered,
        feature_cols=FEATURE_COLS,
        primary_target=PRIMARY_TARGET,
        secondary_targets=SECONDARY_TARGETS,
        nav=get_nav_context("governance.index"),
    )
