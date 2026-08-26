from flask import Blueprint, jsonify, render_template, request

from services.data_service import get_summary, query_observations
from services.nav import get_nav_context
from services.variable_dictionary import VARIABLE_DICTIONARY

data_bp = Blueprint("data", __name__, url_prefix="/data")


@data_bp.route("/")
def index():
    summary = get_summary()
    numeric_vars = [v for v in VARIABLE_DICTIONARY if v["dtype"] in ("integer", "decimal")]
    categorical_vars = [v for v in VARIABLE_DICTIONARY if v["dtype"] == "category"]
    binary_vars = [v for v in VARIABLE_DICTIONARY if "boolean" in v["dtype"]]
    rows, total = query_observations(page=1, page_size=25)
    return render_template(
        "data.html",
        summary=summary,
        numeric_vars=numeric_vars,
        categorical_vars=categorical_vars,
        binary_vars=binary_vars,
        rows=rows,
        total=total,
        page=1,
        page_size=25,
        nav=get_nav_context("data.index"),
    )


@data_bp.route("/query")
def query():
    """JSON endpoint backing the client-side filter/pagination controls."""
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 25))
    rows, total = query_observations(
        customer_id=request.args.get("customer_id") or None,
        trade_id=request.args.get("trade_id") or None,
        product=request.args.get("product") or None,
        lender_id=request.args.get("lender_id") or None,
        date_from=request.args.get("date_from") or None,
        date_to=request.args.get("date_to") or None,
        page=page,
        page_size=page_size,
    )
    return jsonify(rows=rows, total=total, page=page, page_size=page_size)
