from flask import Blueprint, render_template, request

from services import account_service
from services.model_service import is_trained
from services.nav import get_nav_context

account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.route("/")
def index():
    if not is_trained():
        return render_template("model_missing.html", nav=get_nav_context("account.index"))
    trade_id = request.args.get("trade_id") or account_service.sample_trade_id()
    acc = account_service.get_account(trade_id)
    return render_template(
        "account.html",
        account=acc, searched_trade_id=trade_id,
        nav=get_nav_context("account.index"),
    )
