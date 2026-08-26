from flask import Blueprint, jsonify, render_template, request

from services import collection_service
from services.model_service import is_trained
from services.nav import get_nav_context

collection_bp = Blueprint("collection", __name__, url_prefix="/collections")


@collection_bp.route("/")
def index():
    if not is_trained() or not collection_service.is_ready():
        return render_template("model_missing.html", nav=get_nav_context("collection.index"))
    capacity = int(request.args.get("capacity", 10))
    if capacity not in collection_service.CAPACITY_CHOICES:
        capacity = 10
    summary = collection_service.queue_summary(capacity)
    rows, _ = collection_service.queue_page(capacity, page=1, page_size=25)
    return render_template(
        "collection.html",
        capacities=collection_service.CAPACITY_CHOICES,
        selected=capacity,
        summary=summary,
        curve=collection_service.capacity_curve(),
        rows=rows, page=1, page_size=25,
        nav=get_nav_context("collection.index"),
    )


@collection_bp.route("/page")
def page():
    capacity = int(request.args.get("capacity", 10))
    if capacity not in collection_service.CAPACITY_CHOICES:
        capacity = 10
    page_num = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 25))
    rows, n_capacity = collection_service.queue_page(capacity, page_num, page_size)
    return jsonify(rows=rows, n_capacity=n_capacity, page=page_num, page_size=page_size)
