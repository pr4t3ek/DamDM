from flask import Blueprint, jsonify, render_template, request

from services import split_service
from services.data_service import get_summary
from services.nav import get_nav_context

split_bp = Blueprint("split", __name__, url_prefix="/split")


@split_bp.route("/")
def index():
    return render_template(
        "split.html",
        summary=get_summary(),
        months=split_service.available_months(),
        defaults=split_service.default_boundaries(),
        nav=get_nav_context("split.index"),
    )


@split_bp.route("/data")
def data():
    d = split_service.default_boundaries()
    return jsonify(split_service.build_split(
        train_start=request.args.get("train_start") or d["train_start"],
        train_end=request.args.get("train_end") or d["train_end"],
        valid_start=request.args.get("valid_start") or d["valid_start"],
        valid_end=request.args.get("valid_end") or d["valid_end"],
        test_start=request.args.get("test_start") or d["test_start"],
        test_end=request.args.get("test_end") or d["test_end"],
    ))
