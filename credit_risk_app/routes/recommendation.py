from flask import Blueprint, render_template

from services import collection_service, explain_service
from services.model_service import get_results, is_trained
from services.nav import get_nav_context

recommendation_bp = Blueprint("recommendation", __name__, url_prefix="/recommendation")

RECOMMENDED_CAPACITY = 20


@recommendation_bp.route("/")
def index():
    if not is_trained() or not collection_service.is_ready():
        return render_template("model_missing.html", nav=get_nav_context("recommendation.index"))

    results = get_results()
    best = results["models"][results["best_model_key"]]
    test = best["metrics"]["test"]

    curve = collection_service.capacity_curve()
    recommended = collection_service.queue_summary(RECOMMENDED_CAPACITY)

    drivers = explain_service.native_importance(8)
    for d in drivers:
        d["readable"] = d["feature"].replace("_", " ")

    return render_template(
        "recommendation.html",
        model_name=best["display_name"],
        test=test,
        curve=curve,
        recommended=recommended,
        drivers=drivers,
        nav=get_nav_context("recommendation.index"),
    )
