# Credit Risk Analytics Dashboard — Roadmap

Full 28-phase build plan for the Flask app described in the project spec
("Predicting Serious Delinquency in Active Credit Accounts Using Behavioral
Risk Analytics"). Built incrementally, milestone by milestone, with each
milestone shipped as a runnable, verified checkpoint rather than attempting
all 28 phases in one pass.

Convention: each phase below is marked with its status. When a phase is
completed, note **FILES CREATED / MODIFIED** and **FUNCTIONALITY ADDED**
inline, matching the project spec's own tracking convention.

## Milestone 1 — Data-Understanding Arc (DONE)

- [x] **Phase 0 — Architecture & scaffold.** Flask app skeleton
  (`credit_risk_app/`), slide-deck chrome (sidebar nav, progress bar,
  prev/next, keyboard arrow navigation), professional banking-dashboard
  CSS design system.
  Files: `app.py`, `config.py`, `services/nav.py`, `services/data_service.py`,
  `templates/base.html`, `static/css/style.css`, `static/js/nav.js`.
- [x] **Data foundation.** git-lfs installed, scoped pull of
  `behavior_risk_mart_part_{01,02,03}.csv` (~296MB → 1,514,045 rows),
  concatenated/type-coerced/cached into Parquet + JSON summary.
  Files: `scripts/prepare_data.py`.
- [x] **Phase 1 — Executive Overview** (`/`). Business problem, objective,
  target, prediction horizon, unit of analysis, methodology, and 6 KPI
  cards computed from the real dataset.
- [x] **Phase 3 — Data Overview** (`/data/`). Dataset dimensions, variable
  type breakdown, and a searchable/filterable/paginated Data Explorer table
  (server-side query endpoint, no client-side load of 1.5M rows).
- [x] **Phase 4 — Variable Explorer** (`/variables/`). All 31 columns,
  grouped by role, with business meaning, data type, expected risk
  direction, and modeling-use classification. Also shipped as a standalone
  `docs/variable_dictionary.md` reference doc.
- [x] **Phase 5 — Data Quality Dashboard** (`/quality/`). 7 automatic
  validation checks (duplicate IDs, utilization/DPD/payment-ratio anomalies,
  invalid dates, missing target, negative balances) with green/amber/red
  status, plus missingness, dtypes, and numeric summary tables.
- [x] **Phase 8 — Leakage & Governance** (`/governance/`). Every variable
  classified Safe / Potentially Risky / Exclude with the data dictionary's
  own leakage-rule text as justification; final 18-column feature set
  called out explicitly.
- [x] Model recommendation documented (champion/challenger: Logistic
  Regression + WOE baseline vs. Decision Tree / Random Forest / XGBoost
  challengers, evaluated OOT) — see `docs/variable_dictionary.md` and the
  Executive Overview methodology section. Not yet trained.

**Key numbers confirmed from real data**: 1,514,045 observations, 56,539
accounts, 23,405 customers, 18 lenders, 9 products, Jan 2023–Mar 2026 (39
months). Primary target `roll_to_90p_6m` event rate: **9.6%**. Data is
clean (0 missing values, 0 duplicate IDs, 0 out-of-range values in the
checks run so far).

## Milestone 2 — Explore & Prepare (NOT STARTED)

- [ ] Phase 2 — Business Problem & Credit Risk Journey slide, with an
  educational (non-model-backed) delinquency-journey simulator.
- [ ] Phase 6 — Exploratory Data Analysis: target analysis, delinquency
  analysis, payment behavior, utilization analysis, affordability analysis,
  customer/portfolio analysis, correlation/relationship explorer. Needs
  Plotly wired in for interactive charts (not required by Milestone 1).
- [ ] Phase 7 — Behavioral Feature Engineering Lab: trend, rolling,
  volatility, stress, and momentum features per `trade_id`.
- [ ] Phase 9 — Out-of-Time Split simulator (train/validation/OOT test by
  `month_end_date`, with per-period account/observation/event-rate stats).

## Milestone 3 — Modeling & Evaluation (NOT STARTED)

- [ ] Phase 10 — Baseline Logistic Regression model (coefficients, odds
  ratios, AUC/Gini/KS/precision/recall/F1, confusion matrix, plain-language
  explanation).
- [ ] Phase 11 — Advanced models: Decision Tree, Random Forest, Gradient
  Boosting/XGBoost, each with train/validation/OOT performance and feature
  importance.
- [ ] Phase 12 — Model Screening comparison dashboard (OOT AUC/Gini/KS/
  top-decile capture/precision@10%), selectable final model.
- [ ] Phase 13 — ROC/AUC analysis with an interactive threshold slider.
- [ ] Phase 14 — KS analysis dashboard.
- [ ] Phase 15 — Lift & Gains analysis, decile table, top-10% capture.

**Note carried from planning**: since `roll_to_90p_6m` is a 6-month-forward
label, verify whether the most recent few months in the dataset have a
genuinely matured outcome window before trusting their label as ground
truth (Milestone 1's quality check found 0% missing across the full pulled
dataset, since this is a synthetic/simulated case-study dataset rather than
a live production pull — but this should still be re-verified before OOT
splitting in Milestone 3, and is the standard practice for any real-world
version of this pipeline).

## Milestone 4 — Interactive Decision Support (NOT STARTED)

- [ ] Phase 16 — What-If Risk Simulator, backed by the actual trained model.
- [ ] Phase 17 — Account 360 / Risk Explorer with monthly behavioral
  timeline.
- [ ] Phase 18 — Portfolio Scenario Simulator (utilization/payment/bounce/
  DPD shock scenarios).
- [ ] Phase 19 — Explainability (global importance, permutation importance,
  SHAP if feasible, per-account reason codes).
- [ ] Phase 20 — Credit Risk Metrics Dashboard (PD/EAD/LGD/EL vs. model
  metrics vs. portfolio metrics, clearly distinguished).
- [ ] Phase 21 — Collection Queue Prioritization simulator (capacity-based
  ranking, capture rate, exposure covered).

## Milestone 5 — Governance, Narrative & Reporting (NOT STARTED)

- [ ] Phase 22 — Model Governance page (target/window definitions, feature
  list, exclusions, validation methodology, model version, assumptions,
  limitations).
- [ ] Phase 23 — Academic Interpretation slide (classification framing,
  why OOT validation, why AUC alone is insufficient, why Gini/KS/top-decile
  capture matter, class imbalance, interpretability).
- [ ] Phase 24 — Final Recommendation (best model, OOT performance,
  strongest drivers, recommended operating threshold, business
  recommendation).
- [ ] Phase 25 — Download/Reporting (CSV/Excel/PDF export of EDA summary,
  variable dictionary, model comparison, decile table, high-risk account
  list).
- [ ] README with setup instructions; final polish pass on Phases 27/28
  (navigation robustness, error handling for missing values/unseen
  categories, reproducibility).

## How to run what's built so far

```bash
git lfs pull --include="Raw Data and Data Dictionary/02_Data_Mart/behavior_risk_mart_part_*.csv"
python3 -m venv .venv && source .venv/bin/activate
pip install -r credit_risk_app/requirements.txt
python credit_risk_app/scripts/prepare_data.py   # builds parquet + summary cache (one-time)
python credit_risk_app/app.py                    # serves on http://localhost:5000
```
