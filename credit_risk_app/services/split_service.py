"""
Out-of-time split logic for the behavioral risk model.

The split is chronological by month_end_date, never random: the target looks
6 months forward, and the mart is panel data (many monthly rows per trade),
so a random split would leak both future information and account identity
across partitions.

Observations inside the target's 6-month forward window at the end of the
dataset are right-censored and excluded entirely — see compute_label_maturity
in scripts/prepare_data.py.
"""
import pandas as pd

from services.data_service import get_df, get_summary

TARGET = "roll_to_90p_6m"


def available_months():
    """Months with a fully matured target label, oldest first."""
    maturity = get_summary()["label_maturity"]
    months = [m["month"] for m in get_summary()["monthly_roll_rate"]]
    return [m for m in months if m <= maturity["last_mature_month"]]


def default_boundaries():
    """A 70/15/15 chronological split over the mature months."""
    months = available_months()
    n = len(months)
    train_end_idx = int(n * 0.70) - 1
    valid_end_idx = int(n * 0.85) - 1
    return dict(
        train_start=months[0],
        train_end=months[train_end_idx],
        valid_start=months[train_end_idx + 1],
        valid_end=months[valid_end_idx],
        test_start=months[valid_end_idx + 1],
        test_end=months[-1],
    )


def _period_stats(df, start_month, end_month):
    months = df["month_end_date"].dt.to_period("M").astype(str)
    mask = (months >= start_month) & (months <= end_month)
    sub = df.loc[mask]
    n = len(sub)
    events = int(sub[TARGET].sum()) if n else 0
    return dict(
        start=start_month,
        end=end_month,
        n_months=len(set(months[mask])) if n else 0,
        observations=n,
        accounts=int(sub["trade_id"].nunique()) if n else 0,
        customers=int(sub["customer_id"].nunique()) if n else 0,
        events=events,
        event_rate=round(100 * events / n, 3) if n else None,
    )


def build_split(train_start, train_end, valid_start, valid_end, test_start, test_end):
    df = get_df()
    maturity = get_summary()["label_maturity"]
    months = df["month_end_date"].dt.to_period("M").astype(str)

    periods = dict(
        train=_period_stats(df, train_start, train_end),
        validation=_period_stats(df, valid_start, valid_end),
        test=_period_stats(df, test_start, test_end),
    )

    # Panel data: the same trade appearing in two partitions would leak account
    # identity across the split, so report it explicitly rather than assume.
    def trades(start, end):
        mask = (months >= start) & (months <= end)
        return set(df.loc[mask, "trade_id"].unique())

    tr, va, te = trades(train_start, train_end), trades(valid_start, valid_end), trades(test_start, test_end)

    excluded = _period_stats(df, maturity["first_immature_month"], maturity["data_max_month"])

    warnings = []
    if train_end >= valid_start:
        warnings.append("Training period overlaps the validation period — periods must be strictly chronological.")
    if valid_end >= test_start:
        warnings.append("Validation period overlaps the OOT test period — periods must be strictly chronological.")
    for name, p in periods.items():
        if p["observations"] == 0:
            warnings.append(f"The {name} period contains no observations.")
        elif p["events"] == 0:
            warnings.append(f"The {name} period contains no positive events — metrics will be undefined.")
    if test_end > maturity["last_mature_month"]:
        warnings.append(
            f"The OOT test period extends past {maturity['last_mature_month']}, into months whose "
            f"{maturity['horizon_months']}-month outcome window is not yet complete. Those labels are "
            "right-censored and will understate the true event rate."
        )

    return dict(
        periods=periods,
        overlap=dict(
            train_validation=len(tr & va),
            train_test=len(tr & te),
            validation_test=len(va & te),
        ),
        excluded_immature=excluded,
        maturity=maturity,
        warnings=warnings,
        monthly_roll_rate=get_summary()["monthly_roll_rate"],
    )
