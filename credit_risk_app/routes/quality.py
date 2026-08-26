from flask import Blueprint, render_template

from services.data_service import get_summary
from services.nav import get_nav_context

quality_bp = Blueprint("quality", __name__, url_prefix="/quality")


@quality_bp.route("/")
def index():
    summary = get_summary()
    return render_template(
        "quality.html",
        summary=summary,
        nav=get_nav_context("quality.index"),
    )
