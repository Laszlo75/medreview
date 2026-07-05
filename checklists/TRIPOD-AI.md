# TRIPOD+AI — prediction/prognostic models (regression or machine learning)

Source: Collins et al., *BMJ* 2024;385:e078378. 27 items. Supersedes
TRIPOD 2015. Covers development, evaluation/validation, or updating of a
diagnostic or prognostic model, regardless of method. Reviewer: mark met /
partial / unmet with location. Starred items are the classic ML failure points.

## Title & abstract
- **1** — Title identifies the study as developing and/or evaluating a
  multivariable prediction model; names target population and outcome.
- **2** — Abstract: structured summary (TRIPOD+AI for Abstracts) — objectives,
  data source, participants, outcome, model, performance, conclusions.

## Introduction
- **3a** — Background and rationale, referencing existing models.
- **3b** — Objectives: development, evaluation, or both.

## Methods — data & participants
- **4a** — Data source(s) (cohort, registry, RCT, case-control) and rationale.
- **4b** — Study dates (start of accrual, end of follow-up).
- **5a** — Setting, eligibility, and how participants were selected.
- **5b** — Details of treatments received, if relevant.
- **6a** — Outcome defined, including how and when assessed; **no assessment
  of outcome using predictor information** (no leakage).
- **6b** — For time-to-event outcomes, time horizon of prediction stated.

## Methods — predictors & sample size
- **7a** — Predictors defined, including how and when measured.
- **7b** — Predictors assessed blinded to the outcome (or note if not).
- **8** — **Sample size / events-per-variable** justified.
- **9 \*** — How **missing data** were handled (complete-case vs multiple
  imputation; whether the outcome was included in the imputation model).

## Methods — analysis
- **10a** — How predictors were handled (categorisation, transformations,
  nonlinearity).
- **10b \*** — Model type; full model-building procedure (including predictor
  selection); **internal validation** (bootstrap/CV) and how optimism was
  addressed. For ML: hyperparameter tuning and how it avoided leakage into
  validation.
- **10c \*** — Measures used to assess and compare performance —
  **discrimination AND calibration**, plus clinical utility where claimed.
  *(Discrimination reported without calibration is the commonest gap.)*
- **10d** — For evaluation studies, how the model was applied to new data.
- **11** — How risk groups were created, if done.
- **12** — For evaluation: differences from development (setting, eligibility,
  outcome, predictors, time period).

## Methods — AI/ML specifics & open science
- **13a** — Software, packages, versions, and the compute environment.
- **13b** — Where **data** can be accessed / conditions of access.
- **13c** — Where **code** (analysis code and code to implement the model)
  can be accessed. *(Reproducibility hinges on this.)*
- **14 \*** — Fairness: whether performance was examined across relevant
  **subgroups** (e.g. by sex, ethnicity, age) and any mitigation; harms of
  the model considered.

## Results
- **15** — Participant flow; a diagram is encouraged; numbers with the outcome.
- **16** — Baseline characteristics, including number with missing data.
- **17** — For development: full model presented (regression coefficients and
  intercept, or a clear route to obtain the full model / ML artefact) so
  others can make predictions.
- **18** — Performance measures with confidence intervals (discrimination,
  calibration; utility if claimed); for evaluation, performance in the new
  data.

## Discussion
- **19 \*** — **Limitations**: overfitting, optimism, potential leakage,
  applicability, generalisability.
- **20** — Interpretation vs prior evidence; intended use and users.
- **21** — Implications for practice; whether/where the model is available.

## Other
- **22** — Funding and role of funders.
- **23** — Registration / protocol availability of the prediction-model study.

---
Red flags to surface even if an item is nominally "met": AUC/C-statistic
reported on the training data; no external/temporal validation; calibration
absent; patient-level vs record-level split leakage; clinical-utility claim
without a decision-curve/net-benefit analysis.
