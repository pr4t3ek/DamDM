from flask import Blueprint, render_template, request

from services import model_service
from services.nav import get_nav_context

model_roc_bp = Blueprint("model_roc", __name__, url_prefix="/model")


@model_roc_bp.route("/roc")
def index():
    if not model_service.is_trained():
        return render_template("model_missing.html", nav=get_nav_context("model_roc.index"))
    results = model_service.get_results()
    selected = request.args.get("model", results["best_model_key"])
    if selected not in results["models"]:
        selected = results["best_model_key"]
    return render_template(
        "model_roc.html",
        models=dict(model_service.ordered_models()),
        selected=selected,
        model=results["models"][selected],
        nav=get_nav_context("model_roc.index"),
    )
