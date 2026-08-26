from flask import Blueprint, render_template, request

from services import model_service
from services.nav import get_nav_context

model_lift_bp = Blueprint("model_lift", __name__, url_prefix="/model")


@model_lift_bp.route("/lift")
def index():
    if not model_service.is_trained():
        return render_template("model_missing.html", nav=get_nav_context("model_lift.index"))
    results = model_service.get_results()
    selected = request.args.get("model", results["best_model_key"])
    if selected not in results["models"]:
        selected = results["best_model_key"]
    model = results["models"][selected]
    return render_template(
        "model_lift.html",
        models=dict(model_service.ordered_models()),
        selected=selected,
        model=model,
        decile_table=model["metrics"]["test"]["decile_table"],
        nav=get_nav_context("model_lift.index"),
    )
