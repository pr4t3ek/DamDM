from flask import Blueprint, jsonify, render_template, request

from services import feature_service
from services.nav import get_nav_context

features_bp = Blueprint("features", __name__, url_prefix="/features")


@features_bp.route("/")
def index():
    if not feature_service.is_built():
        return render_template("features_missing.html", nav=get_nav_context("features.index"))
    cache = feature_service.get_cache()
    trade_id, rows = feature_service.sample_trade()
    return render_template(
        "features.html",
        cache=cache,
        sample_trade_id=trade_id,
        sample_rows=rows,
        feature_names=list(cache["features"].keys()),
        nav=get_nav_context("features.index"),
    )


@features_bp.route("/sample")
def sample():
    trade_id, rows = feature_service.sample_trade(request.args.get("trade_id") or None)
    return jsonify(trade_id=trade_id, rows=rows)
