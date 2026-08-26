from flask import Blueprint, render_template, request

from services import model_service
from services.nav import get_nav_context

model_advanced_bp = Blueprint("model_advanced", __name__, url_prefix="/model")

CHALLENGERS = ["decision_tree", "random_forest", "xgboost"]


@model_advanced_bp.route("/advanced")
def index():
    if not model_service.is_trained():
        return render_template("model_missing.html", nav=get_nav_context("model_advanced.index"))
    results = model_service.get_results()
    selected = request.args.get("model", "xgboost")
    if selected not in CHALLENGERS:
        selected = "xgboost"
    models = {k: results["models"][k] for k in CHALLENGERS}
    return render_template(
        "model_advanced.html",
        models=models,
        selected=selected,
        model=models[selected],
        split=results["split_boundaries"],
        nav=get_nav_context("model_advanced.index"),
    )
