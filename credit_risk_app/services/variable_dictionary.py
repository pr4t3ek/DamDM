"""
Static variable dictionary for the behavior_risk_mart table.

Content is transcribed verbatim (definitions, leakage rules, sample values)
from the project's source-of-truth data dictionary:
  Raw Data and Data Dictionary/03_Data_Dictionary/Credit_Risk_Data_Dictionary.xlsx
  (Behavior_Variables and Variable_Dictionary sheets)

This is reference data, not derived from the pulled dataset, so it lives as
plain Python rather than being computed at request time.
"""

# role_category values: Identifier, Time Key, Candidate Feature, Feature Flag,
# Risk Estimate, Target Label
#
# governance values: Safe, Potentially Risky, Exclude

VARIABLE_DICTIONARY = [
    dict(
        name="observation_id", role_category="Identifier", dtype="string",
        definition="Unique row identifier in a model-ready mart.",
        why_it_matters="Traces scored records and validation outputs back to the source row.",
        leakage_rule="Use only for tracking/reproducibility. Do not use as a model input.",
        sample_values="OBS_BEH_0000000001, OBS_BEH_0000000002",
        expected_risk_direction="N/A (identifier)",
        governance="Exclude", governance_reason="Identifier — no business meaning, risk of memorization.",
    ),
    dict(
        name="trade_id", role_category="Identifier", dtype="string",
        definition="Unique identifier for a credit account or tradeline (loan, card, or line of credit).",
        why_it_matters="Account behavior, delinquency, exposure, and payments are tracked at the tradeline level.",
        leakage_rule="Use only for tracking/reproducibility. Do not use as a model input.",
        sample_values="T000000001, T000000002",
        expected_risk_direction="N/A (identifier)",
        governance="Exclude", governance_reason="Identifier — no business meaning, risk of memorization.",
    ),
    dict(
        name="customer_id", role_category="Identifier", dtype="string",
        definition="Unique borrower identifier linking a customer across applications, bureau, tradelines, and marts.",
        why_it_matters="Credit risk is borrower-centric; needed to reconstruct a customer view and avoid double-counting.",
        leakage_rule="Use only as a join/audit key. Do not use as a predictive feature.",
        sample_values="C0000001, C0000003",
        expected_risk_direction="N/A (identifier)",
        governance="Exclude", governance_reason="Identifier — no business meaning, risk of memorization.",
    ),
    dict(
        name="lender_id", role_category="Identifier", dtype="string",
        definition="Lender identifier.",
        why_it_matters="Risk can vary by lender due to underwriting policy, risk appetite, and collections strategy.",
        leakage_rule="Usable for segmentation/validation slicing; use carefully as a predictive feature since it may encode policy rather than borrower risk.",
        sample_values="L001, L002",
        expected_risk_direction="Varies by lender policy",
        governance="Exclude", governance_reason="Identifier — kept for segmentation/joins, excluded from the feature matrix by default.",
    ),
    dict(
        name="product", role_category="Candidate Feature", dtype="category",
        definition="Credit product category (personal loan, home loan, credit card, auto loan, business loan, etc.).",
        why_it_matters="Different products have different repayment patterns, collateral, maturity, and default behavior.",
        leakage_rule="Use as a categorical feature and mandatory segmentation dimension.",
        sample_values="credit_card, auto_loan, business_loan, bnpl",
        expected_risk_direction="Varies by product type",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="month_end_date", role_category="Time Key", dtype="date",
        definition="Month-end snapshot date for the observation.",
        why_it_matters="Monthly risk models forecast from one month-end state to future delinquency.",
        leakage_rule="Used for time-based (out-of-time) splits, not fed directly into the feature matrix.",
        sample_values="2023-05-31, 2023-06-30",
        expected_risk_direction="N/A (time key)",
        governance="Exclude", governance_reason="Used to build the OOT split, not as a raw model input.",
    ),
    dict(
        name="months_on_book", role_category="Candidate Feature", dtype="integer",
        definition="Number of months since account opening at the observation month.",
        why_it_matters="Credit risk often varies strongly by account age / vintage.",
        leakage_rule="Known on or before the observation date.",
        sample_values="1, 2, 3, 4, 5",
        expected_risk_direction="Varies (vintage effect — often higher risk early, then stabilizes)",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="state", role_category="Candidate Feature", dtype="category",
        definition="Regional state / geography label.",
        why_it_matters="Regional economics and credit culture can influence delinquency and collections outcomes.",
        leakage_rule="Use for segmentation and optional macro joins; consider fairness/policy implications.",
        sample_values="Madhya Pradesh, West Bengal, Maharashtra",
        expected_risk_direction="Varies by region",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="city_tier", role_category="Candidate Feature", dtype="category",
        definition="Market tier: Tier 1, Tier 2, Tier 3, or Rural.",
        why_it_matters="Urban/rural differences can affect income stability, bureau penetration, and collections outcomes.",
        leakage_rule="Use for segmentation and monitoring.",
        sample_values="Tier 1, Tier 2, Tier 3, Rural",
        expected_risk_direction="Varies by tier",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="customer_type", role_category="Candidate Feature", dtype="category",
        definition="Borrower credit-file classification: thick_file, moderate_file, thin_file, no_hit, or dormant_file.",
        why_it_matters="Indicates whether the borrower has enough bureau history for standard credit assessment.",
        leakage_rule="Use to define the modeling population; do not assume no_hit means low or high risk automatically.",
        sample_values="thick_file, thin_file, no_hit, moderate_file",
        expected_risk_direction="Varies — not assumed higher/lower by itself",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="current_balance", role_category="Candidate Feature", dtype="decimal",
        definition="Outstanding account balance at the observation date.",
        why_it_matters="Represents current exposure and may indicate borrower leverage.",
        leakage_rule="Known on or before the observation date.",
        sample_values="18663.62, 24968.39",
        expected_risk_direction="Higher balance -> higher risk",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="credit_limit_or_original_amount", role_category="Candidate Feature", dtype="integer",
        definition="Current credit limit (revolving) or original amount (installment).",
        why_it_matters="Needed to calculate utilization and exposure intensity.",
        leakage_rule="Known on or before the observation date.",
        sample_values="41532, 837548",
        expected_risk_direction="Context-dependent (used with balance to derive utilization)",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="utilization_ratio", role_category="Candidate Feature", dtype="decimal",
        definition="Current balance divided by credit limit or original amount.",
        why_it_matters="High utilization is one of the strongest early warning signs for credit stress.",
        leakage_rule="Known on or before the observation date.",
        sample_values="0.4494, 0.6012",
        expected_risk_direction="Higher utilization -> higher risk",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="emi_due", role_category="Candidate Feature", dtype="decimal",
        definition="Scheduled payment (EMI) due for the month.",
        why_it_matters="Monthly debt obligation is central to affordability and delinquency risk.",
        leakage_rule="Known on or before the observation date.",
        sample_values="804.49, 1400.19",
        expected_risk_direction="Higher EMI burden -> higher risk (context of income)",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="payment_ratio", role_category="Candidate Feature", dtype="decimal",
        definition="Payment received divided by amount due.",
        why_it_matters="Low payment ratio signals partial payment or inability to pay.",
        leakage_rule="Known on or before the observation date.",
        sample_values="1.0501, 0.9354, 0.8192",
        expected_risk_direction="Lower payment ratio -> higher risk",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="amount_past_due", role_category="Candidate Feature", dtype="decimal",
        definition="Total overdue amount at the observation date.",
        why_it_matters="Reflects severity of delinquency in money terms.",
        leakage_rule="Known on or before the observation date.",
        sample_values="0.0, 3301.66, 2393.33",
        expected_risk_direction="Higher past-due amount -> higher risk",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="dpd", role_category="Candidate Feature", dtype="integer",
        definition="Days past due at the observation date.",
        why_it_matters="The primary operational delinquency status measure.",
        leakage_rule="Do not use future DPD when predicting from an earlier observation.",
        sample_values="0, 15, 30, 60, 120",
        expected_risk_direction="Higher DPD -> higher risk",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="account_status", role_category="Candidate Feature", dtype="category",
        definition="Current account status (e.g. CURRENT, DAYS_1_29, DPD_30, DPD_60, DPD_120).",
        why_it_matters="Summarizes lifecycle stage and operational handling.",
        leakage_rule="Beware of statuses only known after default.",
        sample_values="CURRENT, DAYS_1_29, DPD_30, DPD_60, DPD_120",
        expected_risk_direction="Worse status -> higher risk",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="bounce_flag", role_category="Feature Flag", dtype="boolean (0/1)",
        definition="Flag indicating a payment bounce / failed debit.",
        why_it_matters="Bounces are early stress signals and often precede delinquency.",
        leakage_rule="Known on or before the observation date.",
        sample_values="0, 1",
        expected_risk_direction="1 (bounced) -> higher risk",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="recent_bounce_count_3m", role_category="Candidate Feature", dtype="integer",
        definition="Count of recent payment bounces in the last 3 months.",
        why_it_matters="Recent bounces are strong early indicators of liquidity stress.",
        leakage_rule="Known on or before the observation date.",
        sample_values="0, 1, 2",
        expected_risk_direction="Higher count -> higher risk",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="partial_payment_flag", role_category="Feature Flag", dtype="boolean (0/1)",
        definition="Flag indicating less than full scheduled payment was made.",
        why_it_matters="Can signal liquidity stress even before formal delinquency worsens.",
        leakage_rule="Known on or before the observation date.",
        sample_values="0, 1",
        expected_risk_direction="1 -> higher risk",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="restructure_flag", role_category="Feature Flag", dtype="boolean (0/1)",
        definition="Flag indicating the account has been restructured or modified.",
        why_it_matters="Restructuring can signal elevated credit risk or hardship treatment.",
        leakage_rule="Avoid using future restructuring status in application-time models.",
        sample_values="0 (only value observed in dictionary samples)",
        expected_risk_direction="1 -> higher risk",
        governance="Safe", governance_reason="Known on or before the observation date; verify non-zero variance in the full pulled dataset.",
    ),
    dict(
        name="balance_to_income_ratio", role_category="Candidate Feature", dtype="decimal",
        definition="Outstanding balance divided by monthly income.",
        why_it_matters="Measures leverage relative to repayment capacity.",
        leakage_rule="Known on or before the observation date.",
        sample_values="0.5013, 0.6707",
        expected_risk_direction="Higher ratio -> higher risk",
        governance="Safe", governance_reason="Known on or before the observation date.",
    ),
    dict(
        name="ead_estimate", role_category="Risk Estimate", dtype="decimal",
        definition="Estimated exposure at default at the observation date.",
        why_it_matters="Measures how much money the lender expects to be exposed to if the account defaults.",
        leakage_rule="Avoid as a feature in pure PD models if generated from future/default assumptions.",
        sample_values="24957.14, 29526.8",
        expected_risk_direction="Portfolio exposure metric, not a raw risk driver",
        governance="Exclude", governance_reason="Derived risk-estimate/proxy field — circularity risk; use only for portfolio benchmarking.",
    ),
    dict(
        name="lgd_estimate", role_category="Risk Estimate", dtype="decimal",
        definition="Estimated loss given default at the observation date.",
        why_it_matters="Measures expected severity of loss after recoveries and collateral.",
        leakage_rule="Use in portfolio expected-loss calculations, not as a PD-model input.",
        sample_values="0.8973, 0.8992",
        expected_risk_direction="Portfolio severity metric, not a raw risk driver",
        governance="Exclude", governance_reason="Derived risk-estimate/proxy field, same family as pd_12m_proxy — excluded for consistency.",
    ),
    dict(
        name="pd_12m_proxy", role_category="Risk Estimate", dtype="decimal",
        definition="Case-study 12-month probability-of-default proxy.",
        why_it_matters="A generated risk estimate, not a raw borrower feature.",
        leakage_rule="Derived risk output/proxy; do not use as input in supervised PD/default models.",
        sample_values="0.1194, 0.121, 0.1198",
        expected_risk_direction="Portfolio benchmark score, not a raw risk driver",
        governance="Exclude", governance_reason="Explicit hard exclusion rule in the data dictionary — circularity risk.",
    ),
    dict(
        name="expected_loss_estimate", role_category="Risk Estimate", dtype="decimal",
        definition="Case-study expected loss estimate, generally combining PD, LGD, and EAD.",
        why_it_matters="Helps prioritize portfolio risk by economic impact rather than probability alone.",
        leakage_rule="Derived risk output/proxy; do not use as input in supervised PD/default models.",
        sample_values="2674.63, 3176.66",
        expected_risk_direction="Portfolio benchmark score, not a raw risk driver",
        governance="Exclude", governance_reason="Explicit hard exclusion rule in the data dictionary — circularity risk.",
    ),
    dict(
        name="roll_to_30p_3m", role_category="Target Label", dtype="boolean (0/1)",
        definition="Binary target: account rolls to 30+ DPD within the next 3 months.",
        why_it_matters="Captures short-term deterioration and early-warning risk (secondary target).",
        leakage_rule="Future performance label; never use as model input.",
        sample_values="0, 1",
        expected_risk_direction="N/A (target)",
        governance="Exclude", governance_reason="Future outcome label — secondary target, out of scope for this milestone's primary model.",
    ),
    dict(
        name="roll_to_60p_3m", role_category="Target Label", dtype="boolean (0/1)",
        definition="Binary target: account rolls to 60+ DPD within the next 3 months.",
        why_it_matters="Captures more serious short-term deterioration than 30+ DPD (secondary target).",
        leakage_rule="Future performance label; never use as model input.",
        sample_values="0, 1",
        expected_risk_direction="N/A (target)",
        governance="Exclude", governance_reason="Future outcome label — secondary target, out of scope for this milestone's primary model.",
    ),
    dict(
        name="roll_to_90p_6m", role_category="Target Label", dtype="boolean (0/1)",
        definition="Binary target: account rolls to 90+ DPD / default within the next 6 months.",
        why_it_matters="The primary severe-delinquency / default target for this project's early-warning model.",
        leakage_rule="Future performance label; never use as model input.",
        sample_values="0, 1",
        expected_risk_direction="N/A (primary target)",
        governance="Exclude", governance_reason="Future outcome label — this is the label the model predicts, never a feature.",
    ),
    dict(
        name="cure_3m", role_category="Target Label", dtype="boolean (0/1)",
        definition="Binary target: a delinquent account returns to current status within the next 3 months.",
        why_it_matters="Helps collections teams decide where intervention may work (secondary target).",
        leakage_rule="Future performance label; never use as model input.",
        sample_values="0, 1",
        expected_risk_direction="N/A (target)",
        governance="Exclude", governance_reason="Future outcome label — secondary, collections-focused target, out of scope for this milestone.",
    ),
]

PRIMARY_TARGET = "roll_to_90p_6m"
SECONDARY_TARGETS = ["roll_to_30p_3m", "roll_to_60p_3m", "cure_3m"]
IDENTIFIER_COLS = ["observation_id", "trade_id", "customer_id", "lender_id"]
TIME_COL = "month_end_date"
RISK_ESTIMATE_COLS = ["ead_estimate", "lgd_estimate", "pd_12m_proxy", "expected_loss_estimate"]
ALL_TARGET_COLS = [PRIMARY_TARGET] + SECONDARY_TARGETS

FEATURE_COLS = [
    v["name"] for v in VARIABLE_DICTIONARY
    if v["role_category"] in ("Candidate Feature", "Feature Flag")
]


def get_variable(name):
    for v in VARIABLE_DICTIONARY:
        if v["name"] == name:
            return v
    return None
