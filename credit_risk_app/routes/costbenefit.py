from flask import Blueprint, render_template, request

from services import collection_service, costbenefit_service as cb
from services.model_service import is_trained
from services.nav import get_nav_context

costbenefit_bp = Blueprint("costbenefit", __name__, url_prefix="/costbenefit")


def _parse_float(raw, default):
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if value >= 0 else default


@costbenefit_bp.route("/")
def index():
    if not is_trained() or not collection_service.is_ready():
        return render_template("model_missing.html", nav=get_nav_context("costbenefit.index"))

    default_avoided_loss = cb.default_avoided_loss_per_tp()
    cost_per_fp = _parse_float(request.args.get("cost_per_fp"), cb.DEFAULT_COST_PER_FP)
    avoided_loss_per_tp = _parse_float(request.args.get("avoided_loss"), default_avoided_loss)

    result = cb.net_benefit_curve(cost_per_fp, avoided_loss_per_tp)
    threshold_result = cb.threshold_cost_curve(cost_per_fp, avoided_loss_per_tp)

    return render_template(
        "costbenefit.html",
        result=result,
        threshold_result=threshold_result,
        default_cost_per_fp=cb.DEFAULT_COST_PER_FP,
        default_avoided_loss=default_avoided_loss,
        nav=get_nav_context("costbenefit.index"),
    )
