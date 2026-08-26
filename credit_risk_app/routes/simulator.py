from flask import Blueprint, jsonify, render_template, request

from services import simulator_service as sim
from services.model_service import get_results, is_trained
from services.nav import get_nav_context

simulator_bp = Blueprint("simulator", __name__, url_prefix="/simulator")

SLIDERS = [
    dict(name="dpd", label="Current DPD", min=0, max=150, step=1, default=0),
    dict(name="utilization_ratio", label="Utilization", min=0, max=1.3, step=0.01, default=0.427, is_pct=True),
    dict(name="payment_ratio", label="Payment Ratio", min=0, max=1.5, step=0.01, default=1.0),
    dict(name="amount_past_due", label="Amount Past Due", min=0, max=50000, step=500, default=0),
    dict(name="recent_bounce_count_3m", label="Recent Bounces (3m)", min=0, max=5, step=1, default=0),
    dict(name="balance_to_income_ratio", label="Balance-to-Income Ratio", min=0, max=5, step=0.05, default=1.51),
    dict(name="current_balance", label="Current Balance", min=0, max=500000, step=5000, default=74267),
    dict(name="months_on_book", label="Months on Book", min=1, max=60, step=1, default=16),
]
TOGGLES = [
    dict(name="partial_payment_flag", label="Partial payment this month"),
    dict(name="restructure_flag", label="Account restructured"),
]


@simulator_bp.route("/")
def index():
    if not is_trained():
        return render_template("model_missing.html", nav=get_nav_context("simulator.index"))
    baseline = sim.build_record()
    baseline_p = sim.score_one(baseline)
    results = get_results()
    model_name = results["models"][results["best_model_key"]]["display_name"]
    return render_template(
        "simulator.html",
        sliders=SLIDERS, toggles=TOGGLES,
        model_name=model_name,
        baseline_probability=round(baseline_p, 4),
        baseline_band=sim.risk_band(baseline_p),
        nav=get_nav_context("simulator.index"),
    )


@simulator_bp.route("/score")
def score():
    overrides = {}
    for s in SLIDERS:
        v = request.args.get(s["name"])
        if v is not None:
            overrides[s["name"]] = float(v)
    for t in TOGGLES:
        overrides[t["name"]] = 1 if request.args.get(t["name"]) == "1" else 0

    record = sim.build_record(**overrides)
    p = sim.score_one(record)
    band = sim.risk_band(p)
    return jsonify(
        probability=round(p, 4),
        percentile=sim.score_percentile(p),
        band=band,
        account_status=record["account_status"],
    )
