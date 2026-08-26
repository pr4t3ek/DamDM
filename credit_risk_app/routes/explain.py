from flask import Blueprint, render_template, request

from services import account_service, explain_service
from services.model_service import get_results, is_trained
from services.nav import get_nav_context

explain_bp = Blueprint("explain", __name__, url_prefix="/explain")


def _readable(feature: str) -> str:
    return feature.replace("_", " ")


@explain_bp.route("/")
def index():
    if not is_trained():
        return render_template("model_missing.html", nav=get_nav_context("explain.index"))

    trade_id = request.args.get("trade_id") or account_service.sample_trade_id()
    account = account_service.get_account(trade_id)
    reason_codes = None
    if account is not None:
        rc = explain_service.account_reason_codes(account["raw_record"])
        for c in rc["codes"]:
            c["readable"] = _readable(c["feature"])
            c["strength"] = "+++" if abs(c["contribution"]) > 0.3 else ("++" if abs(c["contribution"]) > 0.1 else "+")
        reason_codes = rc

    return render_template(
        "explain.html",
        model_name=get_results()["models"][get_results()["best_model_key"]]["display_name"],
        native_importance=explain_service.native_importance(15),
        permutation=explain_service.permutation_importance(15),
        shap_importance=explain_service.shap_global_importance(15),
        account=account, searched_trade_id=trade_id, reason_codes=reason_codes,
        nav=get_nav_context("explain.index"),
    )
