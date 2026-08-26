from flask import Blueprint, render_template, request

from services import scenario_service
from services.model_service import is_trained
from services.nav import get_nav_context

scenario_bp = Blueprint("scenario", __name__, url_prefix="/scenario")


@scenario_bp.route("/")
def index():
    if not is_trained():
        return render_template("model_missing.html", nav=get_nav_context("scenario.index"))
    selected = request.args.get("scenario", "dpd_up")
    if selected not in scenario_service.SCENARIOS:
        selected = "dpd_up"
    result = scenario_service.run_scenario(selected)
    return render_template(
        "scenario.html",
        scenarios=scenario_service.SCENARIOS,
        selected=selected,
        result=result,
        nav=get_nav_context("scenario.index"),
    )
