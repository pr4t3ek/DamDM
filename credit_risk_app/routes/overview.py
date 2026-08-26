from flask import Blueprint, render_template

from services.data_service import get_summary
from services.nav import get_nav_context

overview_bp = Blueprint("overview", __name__)


@overview_bp.route("/")
def index():
    summary = get_summary()
    return render_template(
        "overview.html",
        summary=summary,
        nav=get_nav_context("overview.index"),
    )
