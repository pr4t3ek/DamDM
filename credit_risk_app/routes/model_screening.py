from flask import Blueprint, render_template

from services import model_service
from services.nav import get_nav_context

model_screening_bp = Blueprint("model_screening", __name__, url_prefix="/model")


@model_screening_bp.route("/screening")
def index():
    if not model_service.is_trained():
        return render_template("model_missing.html", nav=get_nav_context("model_screening.index"))
    results = model_service.get_results()
    rows = []
    for key, m in model_service.ordered_models():
        t = m["metrics"]["test"]
        rows.append(dict(
            key=key, display_name=m["display_name"],
            auc=t["auc"], gini=t["gini"], ks=t["ks"]["ks"],
            top_decile_capture=t["top_decile_capture"],
            precision_at_10=t["decile_table"][0]["bad_rate"],
            recall=t["recall"], precision=t["precision"],
        ))
    best_key = results["best_model_key"]
    # "Business usefulness" ranking: weight top-decile capture and KS over raw AUC,
    # since the operational use case is a prioritized queue, not a binary classifier.
    ranked = sorted(rows, key=lambda r: (r["top_decile_capture"], r["ks"]), reverse=True)
    recommended_key = ranked[0]["key"]
    return render_template(
        "model_screening.html",
        rows=rows,
        best_key=best_key,
        recommended_key=recommended_key,
        recommended=next(r for r in rows if r["key"] == recommended_key),
        nav=get_nav_context("model_screening.index"),
    )
