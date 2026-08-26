from flask import Blueprint, render_template

from services.nav import get_nav_context
from services.variable_dictionary import VARIABLE_DICTIONARY

variables_bp = Blueprint("variables", __name__, url_prefix="/variables")

ROLE_ORDER = [
    "Identifier", "Time Key", "Candidate Feature", "Feature Flag",
    "Risk Estimate", "Target Label",
]


@variables_bp.route("/")
def index():
    ordered = sorted(
        VARIABLE_DICTIONARY,
        key=lambda v: ROLE_ORDER.index(v["role_category"]),
    )
    return render_template(
        "variables.html",
        variables=ordered,
        role_order=ROLE_ORDER,
        nav=get_nav_context("variables.index"),
    )
