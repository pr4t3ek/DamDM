from flask import Blueprint, render_template

from services import risk_metrics_service
from services.data_service import get_summary
from services.model_service import is_trained
from services.nav import get_nav_context

risk_metrics_bp = Blueprint("risk_metrics", __name__, url_prefix="/risk-metrics")


@risk_metrics_bp.route("/")
def index():
    if not is_trained():
        return render_template("model_missing.html", nav=get_nav_context("risk_metrics.index"))
    return render_template(
        "risk_metrics.html",
        financial=risk_metrics_service.financial_risk_metrics(),
        portfolio=risk_metrics_service.portfolio_risk_metrics(),
        model=risk_metrics_service.model_metrics(),
        row_count=get_summary()["row_count"],
        nav=get_nav_context("risk_metrics.index"),
    )
