from flask import Blueprint, render_template, request

from services import model_service
from services.nav import get_nav_context

model_ks_bp = Blueprint("model_ks", __name__, url_prefix="/model")


@model_ks_bp.route("/ks")
def index():
    if not model_service.is_trained():
        return render_template("model_missing.html", nav=get_nav_context("model_ks.index"))
    results = model_service.get_results()
    selected = request.args.get("model", results["best_model_key"])
    if selected not in results["models"]:
        selected = results["best_model_key"]
    return render_template(
        "model_ks.html",
        models=dict(model_service.ordered_models()),
        selected=selected,
        model=results["models"][selected],
        nav=get_nav_context("model_ks.index"),
    )
