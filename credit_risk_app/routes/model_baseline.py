from flask import Blueprint, render_template

from services import model_service
from services.nav import get_nav_context

model_baseline_bp = Blueprint("model_baseline", __name__, url_prefix="/model")


def _explanation_sentences(coefficients):
    drivers = [c for c in coefficients if not c["feature"].startswith(("product_", "state_"))]
    top = sorted(drivers, key=lambda c: -abs(c["coefficient"]))[:5]
    sentences = []
    for c in top:
        direction = "increases" if c["coefficient"] > 0 else "decreases"
        mult = c["odds_ratio"]
        readable = c["feature"].replace("_", " ")
        sentences.append(
            f"Higher {readable} {direction} the estimated odds of rolling to serious delinquency "
            f"(odds ratio {mult}x per standard deviation)."
        )
    return sentences


@model_baseline_bp.route("/baseline")
def index():
    if not model_service.is_trained():
        return render_template("model_missing.html", nav=get_nav_context("model_baseline.index"))
    m = model_service.get_model("logistic_regression")
    results = model_service.get_results()
    return render_template(
        "model_baseline.html",
        model=m,
        split=results["split_boundaries"],
        feature_cols=results["feature_cols"],
        explanations=_explanation_sentences(m["coefficients"]),
        nav=get_nav_context("model_baseline.index"),
    )
