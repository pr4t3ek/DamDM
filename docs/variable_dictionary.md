# Project Overview & Variable Dictionary

## Project

**Predicting Serious Delinquency in Active Credit Accounts Using Behavioral Risk Analytics**

Financial institutions need to identify active credit accounts likely to transition into
90+ Days Past Due (DPD) within the next six months. Early prediction of serious delinquency
enables proactive intervention, reduces credit losses, and improves portfolio risk management.
This project builds a behavioral credit risk model — using repayment behavior, credit
utilization, delinquency history, and payment patterns — as the analytical core of an
Early Warning System (EWS) for proactive collections and credit monitoring.

## Which data file to use

The dataset's own data dictionary (`Raw Data and Data Dictionary/03_Data_Dictionary/
Credit_Risk_Data_Dictionary.xlsx`, `Problem_Map` sheet) maps this exact problem onto:

- **Input file(s)**: `Raw Data and Data Dictionary/02_Data_Mart/behavior_risk_mart_part_01.csv`,
  `_02.csv`, `_03.csv` — concatenate before use (same schema, row-chunked into 3 parts).
  Pulled via `git lfs pull --include="Raw Data and Data Dictionary/02_Data_Mart/behavior_risk_mart_part_*.csv"`.
- **Grain**: one row per trade-month observation (an account observed in a given month).
- **Primary key**: `observation_id`.
- **Size (as pulled)**: ~296MB combined CSV, **1,514,045 rows** across 56,539 accounts
  (`trade_id`) and 23,405 customers, spanning **2023-01-31 to 2026-03-31** (39 months).
- No other raw table is required for this project — `behavior_risk_mart` already has
  `state`, `city_tier`, and `customer_type` denormalized in from `customer_master`.

## Target variable

| Field | Value |
|---|---|
| **Primary target** | `roll_to_90p_6m` |
| Definition | Binary flag: does this account roll to 90+ DPD / default within the next 6 months? |
| Observed event rate | **9.6%** positive (145,532 of 1,514,045 rows) — imbalanced but workable directly |
| Secondary targets (out of scope for v1) | `roll_to_30p_3m` (25.9% positive), `roll_to_60p_3m`, `cure_3m` (10.2% positive) |
| Leakage rule | Future performance label — **never** used as a model input |

## Golden rule (from the data dictionary's Overview sheet)

> "Use only information available on or before the observation date. Future outcomes must
> be used only as targets."

## Variable table

All 31 columns of `behavior_risk_mart`, grouped by role.

### Identifiers (excluded from modeling — join/tracking keys only)

| Variable | Meaning |
|---|---|
| `observation_id` | Unique row identifier (primary key) |
| `trade_id` | Unique account / tradeline identifier |
| `customer_id` | Unique borrower identifier |
| `lender_id` | Lender identifier |

### Time key

| Variable | Meaning |
|---|---|
| `month_end_date` | Month-end snapshot date; used to build the out-of-time split, not fed to the model directly |

### Candidate features (used in modeling)

| Variable | Meaning | Expected risk direction |
|---|---|---|
| `product` | Credit product category (credit_card, auto_loan, personal_loan, ...) | Varies by product |
| `months_on_book` | Months since account opening | Varies (vintage effect) |
| `state` | Borrower's state | Varies by region |
| `city_tier` | Tier 1/2/3/Rural | Varies by tier |
| `customer_type` | thick_file / thin_file / no_hit / moderate_file / dormant_file | Not assumed higher/lower by itself |
| `current_balance` | Outstanding balance at observation date | Higher → higher risk |
| `credit_limit_or_original_amount` | Credit limit (revolving) or original loan amount | Used with balance to derive utilization |
| `utilization_ratio` | Balance ÷ limit | Higher → higher risk |
| `emi_due` | Scheduled monthly payment | Higher burden → higher risk |
| `payment_ratio` | Payment received ÷ amount due | Lower → higher risk |
| `amount_past_due` | Overdue amount at observation date | Higher → higher risk |
| `dpd` | Days past due | Higher → higher risk |
| `account_status` | CURRENT / DAYS_1_29 / DPD_30 / DPD_60 / DPD_120 | Worse status → higher risk |
| `recent_bounce_count_3m` | Payment bounces in last 3 months | Higher → higher risk |
| `balance_to_income_ratio` | Balance ÷ monthly income | Higher → higher risk |

### Feature flags (used in modeling)

| Variable | Meaning |
|---|---|
| `bounce_flag` | Payment bounce / failed debit this month |
| `partial_payment_flag` | Less than full scheduled payment made |
| `restructure_flag` | Account has been restructured / modified |

### Risk-estimate / proxy fields (excluded from modeling — circularity risk)

| Variable | Meaning | Why excluded |
|---|---|---|
| `pd_12m_proxy` | Case-study 12-month PD proxy | Explicit hard rule: "Derived risk output/proxy; do not use as input in supervised PD/default models." |
| `expected_loss_estimate` | PD × LGD × EAD combined estimate | Same hard exclusion rule |
| `ead_estimate` | Estimated exposure at default | Softer caution: avoid in pure PD models if generated from future/default assumptions |
| `lgd_estimate` | Estimated loss given default | Same risk-estimate family; excluded for consistency |

These four fields are legitimate to use only as a **benchmark comparison** (e.g., "does our
trained model beat naively ranking accounts by `pd_12m_proxy`?"), never as model inputs.

### Target labels

| Variable | Meaning | Scope |
|---|---|---|
| `roll_to_90p_6m` | Rolls to 90+ DPD within 6 months | **Primary target for this project** |
| `roll_to_30p_3m` | Rolls to 30+ DPD within 3 months | Secondary / future extension |
| `roll_to_60p_3m` | Rolls to 60+ DPD within 3 months | Secondary / future extension |
| `cure_3m` | Delinquent account returns to current within 3 months | Secondary, collections-focused / future extension |

## Resulting modeling feature set (v1)

18 columns: `product`, `months_on_book`, `state`, `city_tier`, `customer_type`,
`current_balance`, `credit_limit_or_original_amount`, `utilization_ratio`, `emi_due`,
`payment_ratio`, `amount_past_due`, `dpd`, `account_status`, `bounce_flag`,
`recent_bounce_count_3m`, `partial_payment_flag`, `restructure_flag`,
`balance_to_income_ratio`.

## Recommended modeling approach

Standard credit-risk champion/challenger pattern:

- **Baseline / champion**: Logistic Regression on WOE-binned features — fully interpretable,
  the textbook credit-scorecard approach.
- **Challengers**: Decision Tree, Random Forest, and Gradient Boosting / XGBoost — better
  ranking performance, evaluated for whether the added complexity is worth it.
- **Split**: out-of-time by `month_end_date` (never random), respecting the panel structure
  so the same `trade_id`/`customer_id` never appears on both sides of a split.
- **Validation focus** (per the dataset's own `Problem_Map`): out-of-time AUC, Gini, KS,
  top-decile capture, and operational queue usefulness — not raw accuracy, since the target
  is imbalanced and the business use case is a prioritized collections queue.

See `ROADMAP.md` for the full phased build plan, and the Variable Explorer / Leakage &
Governance pages in the Flask app for the same content as a live, filterable view.

---
*Source of truth: `Raw Data and Data Dictionary/03_Data_Dictionary/Credit_Risk_Data_Dictionary.xlsx`
(Overview, Problem_Map, Table_Catalog, Behavior_Variables, and Variable_Dictionary sheets).*
