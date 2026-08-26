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

## Milestone 4 — Interactive Decision Support (DONE)

All five pages score live through the actual persisted XGBoost pipeline
(`models/xgboost_{model,preprocessor}.pkl`) — nothing here is a hand-written
rule. One foundational fix made this possible: the model is trained with
`class_weight="balanced"`, which shifts raw probabilities well above the
true ~9.6% base rate (mean OOT score ≈0.43) to make the minority class
learnable. Every page that shows a risk band uses **percentile rank against
the real OOT score distribution** (`services/simulator_service.py`), not an
absolute probability cutoff, which would have been meaningless at that scale.

- [x] **Phase 16 — What-If Risk Simulator** (`/simulator/`). 8 sliders + 2
  toggles, scored live; non-exposed inputs held at the dataset's median/mode
  "typical account," with engineered features an input directly implies
  (e.g. `dpd` → `dpd_avg_3m`, `account_status`) kept consistent. Before→after
  comparison against the baseline account.
- [x] **Phase 17 — Account 360** (`/account/`). Full monthly history for any
  `trade_id`, live score, a standardized-deviation driver diagnostic (z-score
  vs. portfolio median so currency/ratio/count features are comparable), and
  a DPD/utilization/payment-ratio timeline chart. Reuses the right-censoring
  fix from Milestone 2: months past the label-maturity cutoff show "N/A,"
  not a confident (and wrong) "No roll."
- [x] **Phase 18 — Portfolio Scenario Simulator** (`/scenario/`). 4 shocks
  (utilization +10pp, payment ratio -15%, +1 bounce, DPD +15d, sustained)
  re-score the full 221,904-row OOT population. Shocks propagate into the
  3-month rolling counterpart of the shocked field (not just the raw
  snapshot) — feature importance shows those rolling features are what the
  model actually weighs, so a raw-only shock barely moved anything.
- [x] **Phase 19 — Explainability** (`/explain/`). Three independent global
  views (native gain-based, permutation importance, SHAP mean |value| via
  `shap.TreeExplainer`, all computed live in under 2s on a 3,000-row sample)
  that agree with each other, plus per-account SHAP reason codes translated
  to plain language with a +/++/+++ strength indicator.
- [x] **Phase 20 — Credit Risk Metrics Dashboard** (`/risk-metrics/`). Three
  visually distinct sections: financial metrics (the dataset's own
  `pd_12m_proxy`/`ead_estimate`/`lgd_estimate`/`expected_loss_estimate`
  fields — display-only, never model inputs), portfolio metrics (observed
  delinquency/roll/cure rates), model metrics (this model's OOT performance).
- [x] **Phase 21 — Collection Queue Prioritization** (`/collections/`).
  Capacity selector (5/10/20/30%) against the cached, ranked OOT scores;
  accounts contacted, bad accounts captured, capture rate, exposure covered,
  paginated ranked table. Surfaces a real finding: capture rate and exposure
  covered diverge sharply (25% of bad accounts vs. under 3% of dollar
  exposure at 10% capacity) because high-risk accounts skew toward smaller
  balances — a risk-ranked queue and an exposure-ranked queue are not the
  same list.

Files: `scripts/score_oot.py` (scores the full OOT test set once, cached to
`data/oot_scored.parquet`), `services/model_features.py` (feature-list
constants shared by `train_models.py`, `score_oot.py`, and every service
below — extracted during this milestone to stop three copies drifting),
`services/{simulator,account,scenario,explain,collection,risk_metrics}_service.py`,
`routes/{simulator,account,scenario,explain,collection,risk_metrics}.py`,
matching templates and `static/js/*.js`.

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
python credit_risk_app/scripts/score_oot.py      # scores the OOT test set for Account 360/Collections/Explainability (one-time, after train_models.py)
python credit_risk_app/app.py                    # serves on http://localhost:5000
```
