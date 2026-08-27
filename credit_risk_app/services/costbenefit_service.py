"""
Cost-benefit analysis for the collections capacity queue.

Translates the capacity curve already used by Collection Queue / Final
Recommendation (accounts contacted, true/false positives per capacity
level) into a rupee net-benefit figure, so the operating threshold can be
picked by ROI rather than capture rate alone. Two assumptions drive it:

- avoided_loss_per_tp: value of correctly flagging one account that would
  have rolled to 90+ DPD. Defaulted from the data itself (mean
  expected_loss_estimate among OOT accounts that actually rolled) rather
  than invented, but it's still a case-study PD*LGD*EAD proxy, not a
  validated recovery figure -- see the caveat rendered on the page.
- cost_per_fp: cost of one unnecessary outreach contact. Not present in
  the dataset at all -- a business assumption the user must own. Defaulted
  to a placeholder (INR 200) that is always shown as editable, never
  presented as data-derived.
"""
import numpy as np

from services.collection_service import CAPACITY_CHOICES, get_scored_df

DEFAULT_COST_PER_FP = 200.0
THRESHOLD_GRID = [round(t, 2) for t in np.arange(0.05, 0.951, 0.05)]

_default_avoided_loss = None


def default_avoided_loss_per_tp() -> float:
    """Mean expected_loss_estimate among OOT accounts that actually rolled to 90+ DPD."""
    global _default_avoided_loss
    if _default_avoided_loss is None:
        df = get_scored_df()
        bads = df.loc[df["roll_to_90p_6m"] == 1, "expected_loss_estimate"]
        _default_avoided_loss = round(float(bads.mean()), 0)
    return _default_avoided_loss


def net_benefit_curve(cost_per_fp: float, avoided_loss_per_tp: float) -> dict:
    df = get_scored_df()
    n_total = len(df)
    total_bads = int(df["roll_to_90p_6m"].sum())
    rows = []
    for pct in CAPACITY_CHOICES:
        n_capacity = max(1, round(n_total * pct / 100))
        top = df.iloc[:n_capacity]
        tp = int(top["roll_to_90p_6m"].sum())
        fp = n_capacity - tp
        gross_benefit = tp * avoided_loss_per_tp
        outreach_cost = fp * cost_per_fp
        net_benefit = gross_benefit - outreach_cost
        rows.append(dict(
            capacity_pct=pct,
            accounts_contacted=n_capacity,
            true_positives=tp,
            false_positives=fp,
            capture_rate=round(100 * tp / total_bads, 2) if total_bads else None,
            precision=round(100 * tp / n_capacity, 2),
            gross_benefit=round(gross_benefit, 0),
            outreach_cost=round(outreach_cost, 0),
            net_benefit=round(net_benefit, 0),
            roi_multiple=round(gross_benefit / outreach_cost, 2) if outreach_cost else None,
        ))
    best = max(rows, key=lambda r: r["net_benefit"])
    return dict(
        rows=rows,
        best_capacity_pct=best["capacity_pct"],
        best_net_benefit=best["net_benefit"],
        cost_per_fp=cost_per_fp,
        avoided_loss_per_tp=avoided_loss_per_tp,
    )


def threshold_cost_curve(cost_per_fp: float, cost_per_fn: float) -> dict:
    """
    Classic cost-sensitive-classification view: sweep the model's own
    probability threshold (not a rank/capacity bucket) and total up
    FP*cost_per_fp + FN*cost_per_fn at each point. cost_per_fn is the same
    number as avoided_loss_per_tp on the capacity view -- missing a true
    bad account forfeits exactly the loss that account would have caused,
    so it's one assumption framed two ways, not a second hidden one.
    """
    df = get_scored_df()
    probs = df["predicted_probability"].to_numpy()
    actual = df["roll_to_90p_6m"].to_numpy()
    total_bads = int(actual.sum())
    total_goods = len(df) - total_bads

    rows = []
    for t in THRESHOLD_GRID:
        flagged = probs >= t
        tp = int((flagged & (actual == 1)).sum())
        fp = int((flagged & (actual == 0)).sum())
        fn = total_bads - tp
        total_cost = fp * cost_per_fp + fn * cost_per_fn
        rows.append(dict(
            threshold=t,
            accounts_flagged=int(flagged.sum()),
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=round(100 * tp / flagged.sum(), 2) if flagged.sum() else None,
            recall=round(100 * tp / total_bads, 2) if total_bads else None,
            total_cost=round(total_cost, 0),
        ))
    best = min(rows, key=lambda r: r["total_cost"])
    return dict(
        rows=rows,
        best_threshold=best["threshold"],
        best=best,
        cost_per_fp=cost_per_fp,
        cost_per_fn=cost_per_fn,
        total_bads=total_bads,
        total_goods=total_goods,
    )
