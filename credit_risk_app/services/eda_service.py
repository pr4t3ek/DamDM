"""
Live aggregation helpers for the Exploratory Data Analysis page.

Everything here operates on the single in-memory DataFrame cached by
data_service.get_df() (~1.5M rows, loaded once per process) and returns
plain JSON-serializable dicts ready to hand to Plotly on the client side.
No aggregate is precomputed at prepare-time — pandas groupby/value_counts
over 1.5M rows runs in well under a second, so it's simpler and more
flexible to filter and aggregate live per request.
"""
import numpy as np
import pandas as pd

from services.data_service import get_df

TARGET = "roll_to_90p_6m"

DPD_BUCKET_EDGES = [-1, 0, 29, 59, 89, 119, 10_000]
DPD_BUCKET_LABELS = ["0 (current)", "1-29", "30-59", "60-89", "90-119", "120+"]

PAYMENT_RATIO_BUCKET_EDGES = [-np.inf, 0.5, 0.8, 1.0, np.inf]
PAYMENT_RATIO_BUCKET_LABELS = ["<0.5", "0.5-0.8", "0.8-1.0", ">1.0"]

UTILIZATION_BUCKET_EDGES = [-np.inf, 0.3, 0.5, 0.7, 0.9, 1.1, np.inf]
UTILIZATION_BUCKET_LABELS = ["<0.3", "0.3-0.5", "0.5-0.7", "0.7-0.9", "0.9-1.1", ">1.1"]

MOB_BUCKET_EDGES = [-1, 6, 12, 24, 36, 10_000]
MOB_BUCKET_LABELS = ["0-6m", "7-12m", "13-24m", "25-36m", "36m+"]

NUMERIC_FEATURES_FOR_CORR = [
    "months_on_book", "current_balance", "credit_limit_or_original_amount",
    "utilization_ratio", "emi_due", "payment_ratio", "amount_past_due", "dpd",
    "recent_bounce_count_3m", "balance_to_income_ratio",
]

CATEGORICAL_VARS = ["product", "state", "city_tier", "customer_type", "account_status"]
NUMERIC_VARS = NUMERIC_FEATURES_FOR_CORR


def apply_filters(df, product=None, lender_id=None, customer_type=None,
                   city_tier=None, date_from=None, date_to=None):
    mask = pd.Series(True, index=df.index)
    if product:
        mask &= df["product"] == product
    if lender_id:
        mask &= df["lender_id"] == lender_id
    if customer_type:
        mask &= df["customer_type"] == customer_type
    if city_tier:
        mask &= df["city_tier"] == city_tier
    if date_from:
        mask &= df["month_end_date"] >= pd.Timestamp(date_from)
    if date_to:
        mask &= df["month_end_date"] <= pd.Timestamp(date_to)
    return df.loc[mask]


def _event_rate_by(df, group_col, top_n=None):
    g = df.groupby(group_col, observed=True)[TARGET]
    out = g.agg(observations="count", events="sum").reset_index()
    out["event_rate"] = (100 * out["events"] / out["observations"]).round(3)
    out = out.sort_values("observations", ascending=False)
    if top_n:
        out = out.head(top_n)
    return out.to_dict(orient="records")


def _bucket_event_rate(df, col, edges, labels):
    bucketed = pd.cut(df[col].astype(float), bins=edges, labels=labels)
    g = df.assign(_bucket=bucketed).groupby("_bucket", observed=True)[TARGET]
    out = g.agg(observations="count", events="sum").reindex(labels).reset_index()
    out.columns = ["bucket", "observations", "events"]
    out["event_rate"] = (100 * out["events"] / out["observations"]).round(3)
    out = out.fillna(0)
    return out.to_dict(orient="records")


def _histogram(series, bins=25):
    s = series.dropna().astype(float)
    if len(s) == 0:
        return dict(counts=[], bin_edges=[])
    counts, edges = np.histogram(s, bins=bins)
    return dict(counts=counts.tolist(), bin_edges=[round(float(e), 4) for e in edges])


def get_filter_options():
    df = get_df()
    return dict(
        products=sorted(df["product"].dropna().unique().tolist()),
        lenders=sorted(df["lender_id"].dropna().unique().tolist()),
        customer_types=sorted(df["customer_type"].dropna().unique().tolist()),
        city_tiers=sorted(df["city_tier"].dropna().unique().tolist()),
    )


def target_analysis(**filters):
    df = apply_filters(get_df(), **filters)
    n = len(df)
    positive = int(df[TARGET].sum())
    monthly = (
        df.assign(month=df["month_end_date"].dt.to_period("M").astype(str))
        .groupby("month", observed=True)[TARGET]
        .agg(observations="count", events="sum")
        .reset_index()
    )
    monthly["event_rate"] = (100 * monthly["events"] / monthly["observations"]).round(3)
    monthly = monthly.sort_values("month")
    return dict(
        n=n,
        positive=positive,
        negative=n - positive,
        event_rate=round(100 * positive / n, 3) if n else None,
        monthly_roll_rate=monthly.to_dict(orient="records"),
        product_roll_rate=_event_rate_by(df, "product"),
    )


def delinquency_analysis(**filters):
    df = apply_filters(get_df(), **filters)
    return dict(
        dpd_distribution=_bucket_event_rate(df, "dpd", DPD_BUCKET_EDGES, DPD_BUCKET_LABELS),
        account_status_distribution=_event_rate_by(df, "account_status"),
        amount_past_due_histogram=_histogram(df["amount_past_due"]),
    )


def payment_behavior_analysis(**filters):
    df = apply_filters(get_df(), **filters)
    n = len(df)
    return dict(
        payment_ratio_histogram=_histogram(df["payment_ratio"]),
        bounce_rate=round(100 * df["bounce_flag"].astype(float).mean(), 3) if n else None,
        partial_payment_rate=round(100 * df["partial_payment_flag"].astype(float).mean(), 3) if n else None,
        recent_bounce_count_distribution=(
            df["recent_bounce_count_3m"].value_counts().sort_index().rename_axis("count").reset_index(name="observations").to_dict(orient="records")
        ),
        risk_by_payment_ratio_bucket=_bucket_event_rate(
            df, "payment_ratio", PAYMENT_RATIO_BUCKET_EDGES, PAYMENT_RATIO_BUCKET_LABELS
        ),
    )


def utilization_analysis(**filters):
    df = apply_filters(get_df(), **filters)
    util_buckets = pd.cut(df["utilization_ratio"], bins=UTILIZATION_BUCKET_EDGES, labels=UTILIZATION_BUCKET_LABELS)
    dpd_by_bucket = (
        df.assign(_bucket=util_buckets)
        .groupby("_bucket", observed=True)["dpd"]
        .mean()
        .reindex(UTILIZATION_BUCKET_LABELS)
        .round(2)
        .reset_index()
    )
    dpd_by_bucket.columns = ["bucket", "avg_dpd"]
    return dict(
        utilization_histogram=_histogram(df["utilization_ratio"]),
        risk_by_utilization_bucket=_bucket_event_rate(
            df, "utilization_ratio", UTILIZATION_BUCKET_EDGES, UTILIZATION_BUCKET_LABELS
        ),
        avg_dpd_by_utilization_bucket=dpd_by_bucket.fillna(0).to_dict(orient="records"),
    )


def affordability_analysis(**filters):
    df = apply_filters(get_df(), **filters)
    return dict(
        balance_to_income_histogram=_histogram(df["balance_to_income_ratio"]),
        emi_due_histogram=_histogram(df["emi_due"]),
        current_balance_histogram=_histogram(df["current_balance"]),
        ead_estimate_histogram=_histogram(df["ead_estimate"]),
    )


def portfolio_analysis(**filters):
    df = apply_filters(get_df(), **filters)
    mob_buckets = pd.cut(df["months_on_book"].astype(float), bins=MOB_BUCKET_EDGES, labels=MOB_BUCKET_LABELS)
    return dict(
        by_product=_event_rate_by(df, "product"),
        by_state=_event_rate_by(df, "state", top_n=15),
        by_city_tier=_event_rate_by(df, "city_tier"),
        by_customer_type=_event_rate_by(df, "customer_type"),
        by_lender=_event_rate_by(df, "lender_id"),
        by_months_on_book=(
            df.assign(_bucket=mob_buckets)
            .groupby("_bucket", observed=True)[TARGET]
            .agg(observations="count", events="sum")
            .reindex(MOB_BUCKET_LABELS)
            .assign(event_rate=lambda x: (100 * x["events"] / x["observations"]).round(3))
            .fillna(0)
            .reset_index()
            .rename(columns={"_bucket": "bucket"})
            .to_dict(orient="records")
        ),
    )


def correlation_analysis(**filters):
    df = apply_filters(get_df(), **filters)
    corr = df[NUMERIC_FEATURES_FOR_CORR + [TARGET]].astype(float).corr().round(3)
    return dict(
        columns=corr.columns.tolist(),
        matrix=corr.values.tolist(),
    )


def variable_vs_target(varname, **filters):
    df = apply_filters(get_df(), **filters)
    if varname not in NUMERIC_VARS and varname not in CATEGORICAL_VARS:
        raise ValueError(f"Unknown variable: {varname}")
    if varname in CATEGORICAL_VARS:
        return dict(kind="categorical", data=_event_rate_by(df, varname, top_n=20))
    s = df[varname].astype(float)
    try:
        bucketed = pd.qcut(s, q=8, duplicates="drop")
    except ValueError:
        bucketed = pd.cut(s, bins=8)
    labels = [str(b) for b in bucketed.cat.categories]
    g = df.assign(_bucket=bucketed.cat.rename_categories(labels)).groupby("_bucket", observed=True)[TARGET]
    out = g.agg(observations="count", events="sum").reset_index()
    out.columns = ["bucket", "observations", "events"]
    out["event_rate"] = (100 * out["events"] / out["observations"]).round(3)
    return dict(kind="numeric", data=out.to_dict(orient="records"))
