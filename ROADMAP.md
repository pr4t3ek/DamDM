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

## Milestone 2 — Explore & Prepare (DONE)

- [x] **Phase 2 — Business Problem & Credit Risk Journey.** Two pages:
  `/business-problem` (what DPD/delinquency/"roll" mean, why 90+ DPD is the
  threshold, reactive vs. proactive collections) and `/journey` (visual
  Current→Early→30+→60+→90+ DPD flow with real roll/cure rates per stage,
  plus an educational cohort simulator — an empirical lookup over real rows
  by DPD/payment ratio/utilization/bounces, explicitly labeled as not a
  model prediction, with a risk-band readout and a sparse-cohort warning).
  Files: `services/journey_service.py`, `routes/journey.py`,
  `templates/business_problem.html`, `templates/journey.html`,
  `static/js/journey.js`.
- [x] **Phase 6 — Exploratory Data Analysis** (`/eda/`). 7 tabs (target,
  delinquency, payment behavior, utilization, affordability, portfolio,
  correlation) plus a variable-vs-target explorer, all backed by live
  pandas aggregation over the full 1.51M-row dataset with product/lender/
  customer-type/city-tier/date filters. Plotly wired in via a locally
  bundled `plotly.min.js` (no CDN dependency).
  Files: `services/eda_service.py`, `routes/eda.py`, `templates/eda.html`,
  `static/js/eda.js`, `static/js/charts.js` (shared chart styling).
- [x] **Phase 7 — Behavioral Feature Engineering Lab** (`/features/`). 19
  trailing-window features per `trade_id` (trend, rolling, volatility,
  stress, momentum, context families) over a 3-month window, with a
  target-correlation diagnostic and per-account sample inspection.
  Files: `scripts/build_features.py`, `services/feature_service.py`,
  `routes/features.py`, `templates/features.html`, `static/js/features.js`.
- [x] **Phase 9 — Out-of-Time Split Simulator** (`/split/`). Interactive
  month-boundary pickers for train/validation/OOT test, with per-period
  account/observation/customer/event counts, overlap reporting, and
  automatic warnings for overlapping or empty periods.
  Files: `services/split_service.py`, `routes/split.py`,
  `templates/split.html`, `static/js/split.js`.

**Right-censoring found and fixed**: the note carried from Milestone 1
planning turned out to be real, not hypothetical. `roll_to_90p_6m` needs a
6-month forward window, but the data ends 2026-03; the monthly roll-rate
chart showed the rate collapsing to exactly 0% in the final month — a data
artifact, not declining risk. `scripts/prepare_data.py` now runs
`compute_label_maturity()` and flags it as a **red** quality check: 281,760
rows (18.6%), from 2025-10 onward, are right-censored and must be excluded
from modeling. The OOT Split Simulator excludes them from its default
70/15/15 boundaries and warns if a chosen test window extends into them.

**Key numbers confirmed from real data this milestone**: roll rate rises
monotonically by DPD stage — Current 7.86% → Early 13.85% → 30+ 16.37% →
60+ 18.46% → 90+ 23.11%. `cure_3m` is ~88-91% for already-delinquent
accounts. Strongest engineered-feature signal: `payment_ratio_avg_3m`
(r=-0.175) and `dpd_avg_3m` (r=+0.175) — rolling/stress features carry far
more signal than single-month deltas (all |r| < 0.01).

## Milestone 3 — Modeling & Evaluation (DONE)

All four models trained on the identical feature set (18 base + 19 engineered
= 37 inputs, one-hot + standardized), out-of-time split (train 2023-01–
2024-11, validation 2024-12–2025-04, OOT test 2025-05–2025-09), with
right-censored months excluded per Milestone 2's finding.

- [x] **Phase 10 — Baseline Model** (`/model/baseline`). Logistic Regression
  (`class_weight="balanced"`): coefficients, odds ratios, per-period metrics,
  confusion matrix, and auto-generated plain-language driver explanations.
- [x] **Phase 11 — Advanced Models** (`/model/advanced`). Decision Tree,
  Random Forest, and XGBoost, selectable via tabs: hyperparameters,
  train/validation/OOT metrics, feature importance chart, predicted-
  probability distribution.
- [x] **Phase 12 — Model Screening** (`/model/screening`). Comparison table
  across all 4 models (OOT AUC/Gini/KS/top-decile capture/precision@10%),
  with a recommendation ranked by top-decile capture + KS (business
  usefulness) rather than raw AUC alone, and the reasoning spelled out.
- [x] **Phase 13 — ROC/AUC** (`/model/roc`). Interactive ROC curve per model
  with a threshold slider that recomputes TP/FP/TN/FN/precision/recall/
  specificity/intervention-volume live from the cached curve.
- [x] **Phase 14 — KS Analysis** (`/model/ks`). Good/bad cumulative score
  distributions with the KS statistic and its threshold marked.
- [x] **Phase 15 — Lift & Gains** (`/model/lift`). Lift curve, cumulative
  gains curve, full decile table, top-10% capture highlighted.

Files: `scripts/train_models.py` (trains and caches everything below; also
persists fitted pipelines to `models/*.pkl` for Milestone 4's simulators),
`services/model_service.py`, `routes/model_*.py` (6 files),
`templates/model_*.html` (7 files, plus a shared `_macros.html` for the
metrics table and confusion matrix), `static/js/model_*.js` (5 files).

**Results (OOT test, 221,904 observations, 10.6% event rate)**:

| Model | AUC | Gini | KS | Top-Decile Capture |
|---|---|---|---|---|
| Logistic Regression | 0.7122 | 0.4245 | 0.3025 | 24.6% |
| Decision Tree | 0.6978 | 0.3956 | 0.2921 | 22.5% |
| Random Forest | 0.7094 | 0.4189 | 0.2949 | 24.5% |
| **XGBoost (recommended)** | **0.7148** | **0.4296** | **0.3065** | **25.2%** |

No leakage signatures: decile bad rate is cleanly monotonic (26.7% → 1.25%
top to bottom), and feature importance is led by real behavioral stress
signals (`dpd_max_3m`, `dpd_avg_3m`) plus sensible product-type effects
(secured loans — auto/gold/home — protective; BNPL/unsecured riskier), not
by anything identifier-like or proxy-derived. XGBoost leads on every metric
that matters for this use case; Logistic Regression stays close behind and
is the fallback where interpretability outweighs the last few points of
lift.

**Right-censoring, resolved in Milestone 2**: see above — confirmed real,
quantified (18.6% of rows), flagged in the Data Quality Dashboard, and
excluded by default in the OOT Split Simulator. Milestone 3's training runs
should build on top of the split simulator's boundaries rather than
re-deriving this from scratch.

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
python credit_risk_app/scripts/build_features.py # builds engineered features (one-time, after prepare_data.py)
python credit_risk_app/scripts/train_models.py   # trains + caches all 4 models (one-time, after build_features.py; ~3 min)
python credit_risk_app/app.py                    # serves on http://localhost:5000
```
