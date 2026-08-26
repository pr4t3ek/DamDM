from flask import Blueprint, render_template

from services.data_service import get_summary
from services.feature_service import get_cache as get_feature_cache
from services.model_service import get_results, is_trained, ordered_models
from services.nav import get_nav_context

academic_bp = Blueprint("academic", __name__, url_prefix="/academic")


@academic_bp.route("/")
def index():
    if not is_trained():
        return render_template("model_missing.html", nav=get_nav_context("academic.index"))

    results = get_results()
    models = [dict(key=k, **m) for k, m in ordered_models()]
    summary = get_summary()

    feature_cache = get_feature_cache()
    ranked = sorted(
        ((n, s["target_corr"]) for n, s in feature_cache["features"].items() if s["target_corr"] is not None),
        key=lambda x: -abs(x[1]),
    )
    top_rolling = ranked[:3]
    weakest_delta = sorted(ranked, key=lambda x: abs(x[1]))[:3]

    return render_template(
        "academic.html",
        models=models,
        summary=summary,
        maturity=results["label_maturity"],
        top_rolling=top_rolling,
        weakest_delta=weakest_delta,
        best_key=results["best_model_key"],
        nav=get_nav_context("academic.index"),
    )
