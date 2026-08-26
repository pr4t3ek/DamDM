from flask import Blueprint, jsonify, render_template, request

from services import eda_service
from services.data_service import get_summary
from services.nav import get_nav_context

eda_bp = Blueprint("eda", __name__, url_prefix="/eda")

SECTIONS = {
    "target": eda_service.target_analysis,
    "delinquency": eda_service.delinquency_analysis,
    "payment": eda_service.payment_behavior_analysis,
    "utilization": eda_service.utilization_analysis,
    "affordability": eda_service.affordability_analysis,
    "portfolio": eda_service.portfolio_analysis,
    "correlation": eda_service.correlation_analysis,
}


def _filters_from_request():
    return dict(
        product=request.args.get("product") or None,
        lender_id=request.args.get("lender_id") or None,
        customer_type=request.args.get("customer_type") or None,
        city_tier=request.args.get("city_tier") or None,
        date_from=request.args.get("date_from") or None,
        date_to=request.args.get("date_to") or None,
    )


@eda_bp.route("/")
def index():
    return render_template(
        "eda.html",
        summary=get_summary(),
        options=eda_service.get_filter_options(),
        numeric_vars=eda_service.NUMERIC_VARS,
        categorical_vars=eda_service.CATEGORICAL_VARS,
        nav=get_nav_context("eda.index"),
    )


@eda_bp.route("/data/<section>")
def section_data(section):
    fn = SECTIONS.get(section)
    if fn is None:
        return jsonify(error=f"Unknown section: {section}"), 404
    return jsonify(fn(**_filters_from_request()))


@eda_bp.route("/data/variable/<varname>")
def variable_data(varname):
    try:
        return jsonify(eda_service.variable_vs_target(varname, **_filters_from_request()))
    except ValueError as exc:
        return jsonify(error=str(exc)), 404
