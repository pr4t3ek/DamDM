"""
Delinquency-journey statistics and the educational cohort lookup behind the
Credit Risk Journey simulator.

The simulator deliberately does NOT score anything. It looks up the observed
historical roll rate for accounts matching the selected characteristics, so
every number shown traces back to real rows in the dataset. A trained model
arrives later (Milestone 3) on its own page.
"""
import pandas as pd

from services.data_service import get_df

TARGET = "roll_to_90p_6m"

STAGES = [
    dict(key="CURRENT", label="Current", dpd_range=(0, 0),
         description="Paying on time. No amount overdue."),
    dict(key="EARLY", label="Early Delinquency", dpd_range=(1, 29),
         description="Missed or short-paid this cycle, but under 30 days late."),
    dict(key="DPD30", label="30+ DPD", dpd_range=(30, 59),
         description="A full billing cycle missed. Formal collections usually begin."),
    dict(key="DPD60", label="60+ DPD", dpd_range=(60, 89),
         description="Two cycles missed. Escalated collections, higher provisioning."),
    dict(key="DPD90", label="90+ DPD", dpd_range=(90, 100_000),
         description="Serious delinquency / default. This is what the model predicts."),
]

DPD_CHOICES = [
    dict(value="0", label="0 — Current"),
    dict(value="15", label="15 — Early (1-29)"),
    dict(value="45", label="45 — 30+ DPD"),
    dict(value="75", label="75 — 60+ DPD"),
]
PAYMENT_RATIO_CHOICES = [
    dict(value="0.3", label="< 0.5 — paying under half"),
    dict(value="0.65", label="0.5 - 0.8 — partial"),
    dict(value="0.9", label="0.8 - 1.0 — nearly full"),
    dict(value="1.05", label="> 1.0 — full or extra"),
]
UTILIZATION_CHOICES = [
    dict(value="0.2", label="< 0.3 — low"),
    dict(value="0.4", label="0.3 - 0.5 — moderate"),
    dict(value="0.6", label="0.5 - 0.7 — elevated"),
    dict(value="0.8", label="0.7 - 0.9 — high"),
    dict(value="1.0", label="> 0.9 — maxed out"),
]
BOUNCE_CHOICES = [
    dict(value="0", label="0 bounces"),
    dict(value="1", label="1 bounce"),
    dict(value="2", label="2+ bounces"),
]


def _stage_mask(df, lo, hi):
    d = df["dpd"].astype(float)
    return (d >= lo) & (d <= hi)


def stage_stats():
    df = get_df()
    out = []
    for s in STAGES:
        lo, hi = s["dpd_range"]
        sub = df[_stage_mask(df, lo, hi)]
        n = len(sub)
        events = int(sub[TARGET].sum()) if n else 0
        cure = sub["cure_3m"].astype(float).mean() if n else None
        out.append(dict(
            key=s["key"], label=s["label"], description=s["description"],
            observations=n,
            share=round(100 * n / len(df), 2) if len(df) else 0,
            events=events,
            roll_rate=round(100 * events / n, 2) if n else None,
            cure_rate=round(100 * cure, 2) if cure is not None and n else None,
        ))
    return out


def _bucket_masks(df, dpd, payment_ratio, utilization, bounces):
    d = df["dpd"].astype(float)
    if dpd == 0:
        dpd_mask = d == 0
    elif dpd < 30:
        dpd_mask = (d > 0) & (d < 30)
    elif dpd < 60:
        dpd_mask = (d >= 30) & (d < 60)
    else:
        dpd_mask = (d >= 60) & (d < 90)

    p = df["payment_ratio"].astype(float)
    if payment_ratio < 0.5:
        p_mask = p < 0.5
    elif payment_ratio < 0.8:
        p_mask = (p >= 0.5) & (p < 0.8)
    elif payment_ratio <= 1.0:
        p_mask = (p >= 0.8) & (p <= 1.0)
    else:
        p_mask = p > 1.0

    u = df["utilization_ratio"].astype(float)
    if utilization < 0.3:
        u_mask = u < 0.3
    elif utilization < 0.5:
        u_mask = (u >= 0.3) & (u < 0.5)
    elif utilization < 0.7:
        u_mask = (u >= 0.5) & (u < 0.7)
    elif utilization < 0.9:
        u_mask = (u >= 0.7) & (u < 0.9)
    else:
        u_mask = u >= 0.9

    b = df["recent_bounce_count_3m"].astype(float)
    b_mask = b >= 2 if bounces >= 2 else b == bounces

    return dpd_mask, p_mask, u_mask, b_mask


def cohort_lookup(dpd=0.0, payment_ratio=1.0, utilization=0.4, bounces=0):
    """Observed roll rate for the cohort matching all four characteristics."""
    df = get_df()
    baseline = round(100 * df[TARGET].mean(), 3)

    dpd_mask, p_mask, u_mask, b_mask = _bucket_masks(df, dpd, payment_ratio, utilization, bounces)
    full = dpd_mask & p_mask & u_mask & b_mask
    sub = df[full]
    n = len(sub)
    rate = round(100 * sub[TARGET].mean(), 3) if n else None

    # Each factor on its own, to show which one is doing the work.
    contributions = []
    for name, mask in [
        ("Current DPD", dpd_mask), ("Payment ratio", p_mask),
        ("Utilization", u_mask), ("Recent bounces", b_mask),
    ]:
        s = df[mask]
        contributions.append(dict(
            factor=name,
            observations=int(len(s)),
            roll_rate=round(100 * s[TARGET].mean(), 3) if len(s) else None,
        ))

    return dict(
        cohort_observations=n,
        cohort_roll_rate=rate,
        baseline_roll_rate=baseline,
        lift=round(rate / baseline, 2) if rate and baseline else None,
        contributions=contributions,
        sparse=n < 200,
    )


def choices():
    return dict(
        dpd=DPD_CHOICES,
        payment_ratio=PAYMENT_RATIO_CHOICES,
        utilization=UTILIZATION_CHOICES,
        bounces=BOUNCE_CHOICES,
    )
