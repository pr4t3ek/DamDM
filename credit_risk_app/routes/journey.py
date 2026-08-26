from flask import Blueprint, jsonify, render_template, request

from services import journey_service
from services.data_service import get_summary
from services.nav import get_nav_context

journey_bp = Blueprint("journey", __name__)


@journey_bp.route("/business-problem")
def business_problem():
    return render_template(
        "business_problem.html",
        summary=get_summary(),
        stages=journey_service.stage_stats(),
        nav=get_nav_context("journey.business_problem"),
    )


@journey_bp.route("/journey")
def index():
    return render_template(
        "journey.html",
        summary=get_summary(),
        stages=journey_service.stage_stats(),
        choices=journey_service.choices(),
        nav=get_nav_context("journey.index"),
    )


@journey_bp.route("/journey/cohort")
def cohort():
    return jsonify(journey_service.cohort_lookup(
        dpd=float(request.args.get("dpd", 0)),
        payment_ratio=float(request.args.get("payment_ratio", 1.0)),
        utilization=float(request.args.get("utilization", 0.4)),
        bounces=int(float(request.args.get("bounces", 0))),
    ))
