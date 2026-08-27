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

## Milestone 5 — Governance, Narrative & Reporting (DONE)

The final milestone — **all 25 planned slides are now built**, no "Soon"
badges left in the sidebar.

- [x] **Phase 22 — Model Governance** (extends the existing Leakage &
  Governance page at order=9, not a new slide — see note below). Target/
  window/grain definitions, feature count, model version and training
  timestamp, dataset version, the full OOT split and right-censoring
  exclusion window, and an explicit assumptions/limitations list (synthetic
  dataset, uncalibrated ranking-only probabilities, simplified portfolio
  shocks, no fairness/disparate-impact analysis performed).
- [x] **Phase 23 — Academic Interpretation** (`/academic/`). Seven
  viva-style questions answered with this project's own numbers rather than
  textbook generalities — e.g. "why AUC alone is insufficient" cites this
  project's own AUC-vs-top-decile-capture reasoning, "why behavioral
  features matter" cites the Feature Lab's own signal-strength numbers
  (rolling features r≈0.17 vs. single-month deltas r<0.01).
- [x] **Phase 24 — Final Recommendation** (`/recommendation/`). Executive
  synthesis: best model + OOT metrics, top 8 risk drivers, a recommended
  20%-capacity operating point (42.2% capture) shown alongside the full
  5/10/20/30% trade-off table so the choice is transparent rather than
  arbitrary, and a closing scope statement (decision-support ranking for
  human-driven collections, not an autonomous credit decision).
- [x] **Phase 25 — Download / Reporting** (`/download/`). Real CSV and
  Excel exports (openpyxl) for variable dictionary, model comparison,
  decile table, top-2,000 high-risk accounts, and EDA summary — verified by
  downloading each and checking row counts and content against source.
  Skipped bespoke PDF generation (no PDF library was already in the stack
  and adding one wasn't worth it for this scope) in favor of pointing users
  at the browser's own print-to-PDF for any full page.
- [x] **README.md** at repo root with setup instructions and an
  architecture summary.
- [x] **Edge-case pass**: bad `trade_id` on Account 360 and Explainability,
  missing/extreme What-If Simulator inputs (negative balances, DPD=99999,
  utilization=50) all verified to degrade gracefully — no 500s, sane
  output — via the existing `OneHotEncoder(handle_unknown="ignore")` /
  `SimpleImputer` pipeline plus each page's own not-found handling.

**One naming note**: the original 28-phase spec's Phase 22 ("Model
Governance") has no separate slot in the user's later 25-item slide flow —
that flow's slide 09 is "Leakage & Governance," already built in Milestone
1. Rather than invent a 26th nav slot outside that numbering, Phase 22's
content was added to the existing page instead of a new route.

Files: `routes/{academic,recommendation,download}.py`,
`templates/{academic,recommendation,download}.html`,
`services/export_service.py`, plus extensions to
`routes/governance.py` / `templates/governance.html` for the Model
Governance section. `services/collection_service.get_scored_df` and
`services/simulator_service.get_percentile_cutoffs`/`load_model` were made
public (dropped their leading underscore) as more pages started reusing
them — the same pattern already applied twice in Milestone 4.

**Full nav walk** (all 25 slides, in order) verified via Playwright with no
console errors beyond the standing favicon 404, and zero 500s in the server
log across the entire milestone.

## Post-Milestone 5 — Cost-Benefit Analyzer (DONE)

Added after the 25-slide spec was already complete, at the user's request
while prepping a time-boxed live defense of the project: a 26th slide
(`/costbenefit/`) that turns the Collection Queue capacity curve into a
rupee net-benefit figure, so the recommended operating capacity can be
chosen by ROI rather than capture rate alone.

- `services/costbenefit_service.py` — `net_benefit_curve(cost_per_fp,
  avoided_loss_per_tp)` reuses `collection_service.get_scored_df()` and
  `CAPACITY_CHOICES`, computing `TP × avoided_loss − FP × cost_per_fp` at
  each capacity level.
- **Avoided loss per true positive** defaults to a real, data-derived
  number: the mean `expected_loss_estimate` among OOT-test accounts that
  actually rolled to 90+ DPD (₹19,241, computed live via
  `default_avoided_loss_per_tp()`, not hardcoded). This required adding
  `expected_loss_estimate` to `scripts/score_oot.py`'s `DISPLAY_COLS` and
  re-running it — that field wasn't previously cached in
  `oot_scored.parquet`.
- **Cost per false positive** has no basis anywhere in the dataset — it
  defaults to a placeholder (₹200) that the page states plainly is *not*
  data-derived, must be supplied by the user, and is live-editable in a
  form on the page (GET query params, full server-side recompute — no new
  JS framework, consistent with the rest of the app).
- **Real finding surfaced on the page**: at the data-derived defaults, net
  benefit is still rising at the top of the capacity range (5→30%,
  ₹63M→₹243M, monotonically increasing) — because avoided loss per catch
  so heavily outweighs contact cost that the real constraint becomes
  operational capacity, not cost-efficiency. Tested and confirmed an
  interior optimum does appear once cost-per-contact is raised enough
  (e.g. ₹5,000 → optimum at 10% capacity, ₹32.8M net benefit, negative
  beyond 20%) — the page detects and messages both cases (rising-to-the-edge
  vs. interior-optimum vs. every-level-negative) rather than just always
  reporting "best of these 4."

Also fixed in passing: `templates/base.html`'s footer had said "Milestone 1
(data-understanding arc)" on every page since the very first build — stale
since Milestone 2 and never caught. Removed the milestone reference.

Files: `services/costbenefit_service.py`, `routes/costbenefit.py`,
`templates/costbenefit.html`, `static/js/costbenefit.js`; nav.py gained a
26th entry; `scripts/score_oot.py` and the regenerated (gitignored)
`oot_scored.parquet` gained the `expected_loss_estimate` column.

## Post-Milestone 5 — Main / Appendix nav split (DONE)

Follow-up to the Cost-Benefit Analyzer: the user has a hard 10-12 minute
live defense and asked to trim the deck for time, then clarified that
should mean grouping — not deleting — with the interactive pages (sliders,
simulators) and core data pages kept as "necessary," not appendix material.

`services/nav.py`'s `NAV_ITEMS` gained a `section` field (`"main"` or
`"appendix"`) and was **reordered, not just relabeled**: the 11 `"main"`
items are now first in the list, in the actual order they'd be presented,
so clicking **Next** from Executive Overview runs the entire live talk
start to finish without ever landing on backup material:

Executive Overview -> Data Overview -> Data Quality -> OOT Split -> Model
Screening -> Lift & Gains -> What-If Simulator -> Portfolio Scenario
Simulator -> Collection Queue -> Cost-Benefit Analyzer -> Final
Recommendation.

The other 15 (Business Problem, Credit Risk Journey, Variable Explorer,
EDA, Feature Engineering, Leakage & Governance, Baseline Model, Advanced
Models, ROC/AUC, KS Analysis, Account 360, Explainability, Risk Metrics,
Academic Interpretation, Download/Report) are `"appendix"` — unchanged
pages, same titles, same URLs, just ordered after the main 11 and visually
separated in the sidebar under an "Appendix" divider
(`templates/base.html`, two `{% for %}` loops filtered by `item.section`
instead of one). Nothing was hidden, deleted, or renamed — this is a purely
presentational reorder. All 26 slides remain built and directly reachable;
`nav.get_nav_context()`'s prev/next logic was untouched, since it already
just walks list position, which now happens to be the presentation order.

Verified: sidebar renders both section labels, Final Recommendation's Next
button correctly rolls into the first appendix item (Business Problem),
and every reordered main-section route still returns 200.

## Post-Milestone 5 — Threshold vs. Cost curve (DONE)

The user asked for a "threshold vs cost kind of thing" on the Cost-Benefit
Analyzer — the classic cost-sensitive-classification view, distinct from
the capacity-bucket table already on the page. Added as a second analysis
on the same `/costbenefit/` page rather than a new nav slide, reusing the
same two cost inputs already on the form.

`services/costbenefit_service.threshold_cost_curve(cost_per_fp,
cost_per_fn)` sweeps the model's own probability threshold (0.05 to 0.95,
step 0.05) directly against `predicted_probability` — a real decision
cutoff, not a rank/capacity bucket — and computes `total_cost = FP *
cost_per_fp + FN * cost_per_fn` at each point via vectorized boolean masks
on the already-cached OOT dataframe. `cost_per_fn` reuses the page's
existing `avoided_loss_per_tp` value rather than introducing a second
hidden assumption: missing a true bad account forfeits exactly the loss
that account would have caused.

Verified the direction is right by sweeping `cost_per_fp`: at the
data-derived default (₹200 vs. ₹19,241 avoided loss) the optimum sits at
the bottom of the swept range (0.05) — flag almost everyone, same finding
as the capacity view. At ₹5,000/FP a genuine interior optimum appears
(threshold 0.7, ₹421.4M total cost). At ₹100,000/FP the optimum sits at
the top of the range (0.95) — flag almost nobody, missing nearly every bad
account, which the page calls out explicitly as a case where minimizing
cost alone isn't the right objective. All three cases get distinct
messaging, matching the pattern already used on the capacity card.

Files: `services/costbenefit_service.py` (new function),
`routes/costbenefit.py`, `templates/costbenefit.html`,
`static/js/costbenefit.js` — all extensions of the same page built
earlier, no new route.

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
