# Academic Source Analysis

Both academic documents were read in full, every page as a rendered image, so the tables, figures and diagrams were inspected directly rather than through extracted text.

| Doc | File | Pages | Read |
|---|---|---|---|
| HW1 | `ST_HW1_Hussam_Aburahmah_2357138_2.pdf` | 18 | pp. 1–18, all |
| HW2 | `ST_HW2_Hussam_Aburahmah_2357138_1.pdf` | 16 | pp. 1–16, all |

The PDFs were supplied as session uploads. They are **not** copied into this repository, because the originals must not be changed. Page numbers below are the printed page numbers, which match the PDF page index in both files.

## HW1: proposal and design (18 pages)

| Pages | Section | Content |
|---|---|---|
| 1–3 | Title, contents | Title "Personal Financial AI Analyzer", student and ID. Note: the contents list jumps from 2.4 to 2.6, so there is no section 2.5. |
| 4 | 1 Overview, 1.1 Need, 1.2 Problem | Web app that turns exported bank CSVs into reports. It is an educational prototype, not a bank, advisor or payment processor. The dataset's full content was **not** validated in HW1. Credits, deposits, refunds and transfers must not be assumed to be salary or spending, and internal transfers must not affect income or spending. Requirements F1–F2 start here. |
| 5 | 1.2.1–1.2.3 | F3–F9 functional requirements. Performance requirements: upload reliability, analytical correctness, classification (macro-F1), forecasts (MAE and MASE, rolling chronological), interaction. Constraints begin. |
| 6 | 1.2.3, 1.3, 1.3.1, 1.3.2 | Uploads stay local, are kept for a limited time, and go to no external LLM without consent. Economic, environmental and social impact. Three concepts. Literature-search sources. Related work on categorization. |
| 7 | 1.3.2, 1.3.3, Table 1.1 | Forecasting literature (Taylor & Letham, Hyndman & Koehler). Isolation Forest (Liu 2008/2012). RF and boosting as supervised baselines only with labels. Table 1.1 compares the concepts, and the **hybrid** design is selected. |
| 8 | 1.4 Physical architecture, Figure 1 | Diagram: User CSV upload → Schema validation / cleaning / mapping → Authorized transaction storage → Deterministic finance calculations ↔ {Forecasting and anomaly models, Grounded assistant / query layer, Web dashboard / alerts / budgets}. The upload stays separate from the public dataset. |
| 9 | Figure 2 (process flow) | Upload CSV and select account and currency → validate columns, parse timestamps, deduplicate → filter statuses and separate inflows, outflows and transfers → aggregate history and check model-input sufficiency → optional ML predictions, anomalies, category fallback → dashboard with explanations, warnings and **CSV report**. |
| 10 | 2 Work plan, 2.1 WBS figure, 2.2 Table 2.1 | WBS covers 1.1 Research and design, 1.2 Data pipeline, 1.3 Analytics and models, and 1.4 Application and evaluation. The RM is a solo project with the supervisor consulted. |
| 11 | 2.3 PN figure, 2.4 Table 2.2 Gantt | Network A→B→C→{D Financial calculations, E ML baselines}→F Integrate→G Tests→H Report. Preprocessing and financial calculations must come before end-to-end testing. 15-week Gantt. |
| 12 | 2.6 Table 2.3, Table 2.4 | Risk matrix and risks R1–R8 with mitigations. |
| 13 | 3.1 Financial data processing and AI analysis (3.1.1–3.1.3) | Validation scope. No model may reclassify income without a business rule. Tech stack. Pipeline steps (i)–(vii). Predictions are optional, and calculations and predictions are marked separately. |
| 14 | 3.1.4–3.1.6, 3.2 Dashboard and assistant (3.2.1–3.2.2) | Versioned models, input schema, 50-row sample audit, unit tests. Evaluation rules: macro-F1 only with real labels, rolling MAE and MASE, and anomaly evaluation only on labeled or generated anomalies. Dashboard requirements. Streamlit. Deterministic intents. |
| 15 | 3.2.2–3.2.6 | An LLM may come later, read-only on aggregates. UX concept. Session isolation. User-selectable retention. Materialization list. Task-based evaluation list. |
| 16 | 4 Dataset, 4.1, 4.2 Table 4.1 | Source, license CC BY-NC 4.0, access date 22 Oct 2026. Local size, hash and commit **to be recorded**. Advertised properties to verify. |
| 17 | 4.3 Table 4.2, gaps, 4.4 | Per-field treatment. Gaps: no description text, salary labels, demographics, fraud labels or budget targets. Audit metric list begins. |
| 18 | 4.4–4.6 | A random sample is not enough. Outliers are investigated, not deleted. Preprocessing steps 1–8. Leakage prevention. |

## HW2: methodology and implementation plan (16 pages)

| Pages | Section | Content |
|---|---|---|
| 1–2 | Title, contents | Chapters 4–10 and references. |
| 3 | 4, 4.1, 4.2 Table 4.1 | Same dataset. File size, hash and commit "will be recorded during the local audit". Split is "chronological, account-aware" (section 8.2). |
| 4 | Table 4.2, 4.3 gaps, 4.4 audit, 4.5 steps 1–4 | Deduplicate **by `transaction_id`**. Exclude pending, failed and reversed records from totals. |
| 5 | 4.5 steps 5–8, 4.6 leakage | Account–currency–month aggregates. Only accounts with enough consecutive active months. Scalers fitted on training data only. "Uncategorized" fallback. Splits are account-disjoint when testing cross-account generalization. |
| 6 | 5 Methodology, 5.1 pipeline, 5.2 rules, 5.3 categorization, 5.4 forecasting (baselines) | ML is used **only** for forecasting and anomaly ranking. Fixed type→meaning mapping table. Refunds reduce category spending. Only `status = completed` counts. Keyword rules for user CSVs, and no text classifier. Target: total monthly spending per account and currency. |
| 7 | 5.4 models, 5.5 anomaly, 5.6 budget, 5.7 assistant | ETS plus a gradient boosting regressor on lags 1–3, a rolling mean and month number. A model is kept only if it beats the best baseline on MAE **and** MASE. Fewer than 12 active months gives a notice. Isolation Forest per account on amount, hour, day of week, category and amount-to-category-median ratio. Robust z-score (median/MAD) baseline. "Review candidates". Budget is the median of the last 3 completed months, with 80% and 100% warnings. Five assistant intents. |
| 8 | 6.1 Table 6.1, 6.2 structure, 6.3 data handling | Python 3, pandas, Polars, PyArrow, scikit-learn, statsmodels, Streamlit, Plotly, pytest, Git. Folders ingest/, rules/, analytics/, models/, app/, tests/. Batch-read with PyArrow, then a subset of accounts with complete histories. Monthly aggregates stored as separate tables. |
| 9 | 6.4, 6.5 | Separate training scripts. Seed 42. Versioned saved models. The app only loads them. Local processing, per-user session, user-chosen retention, no raw transactions in logs or sent externally. |
| 10 | 7 Table 7.1 | Eight detected issues and resolutions. |
| 11 | 8.1 E1–E4, 8.2 Table 8.1, 8.3 Table 8.2 | Split: Train 2024-01 to 2025-12, Validation 2026-01 to 2026-04, Test 2026-05 to 2026-07. Rolling-origin one month ahead. Metrics: E1 exact match; E2 MAE, RMSE, MASE; E3 Precision@k, recall, ROC-AUC; E4 task completion rate and error count. |
| 12 | 8.4 injection, 8.5 reproducibility | 1% of test transactions in selected accounts, modified by amount ×5–10, an unusual hour or a rare category. |
| 13 | 9 Results, Tables 9.1 and 9.2 | **Empty, "to be filled".** No experiments had been completed. |
| 14 | 10.1 Table 10.1, 10.2, 10.3, 10.4 | Eight CSV validation tests. Financial correctness on small known-answer files. Robustness: rolling origin, short and long histories, injection rates of 0.5%, 1% and 2%, different seeds. Assistant tests. |
| 15 | 10.5 Status | "These tests are planned and have not been run yet." |
| 16 | References [1]–[7] | ziadatalabs dataset; Liu et al. 2008; Hyndman & Koehler 2006; Taylor & Letham 2018; Breiman 2001; Chen & Guestrin 2016; Pedregosa et al. 2011. |

## How HW1 and HW2 relate

* HW2 restates HW1 chapter 4 almost verbatim and then **narrows** HW1's design into a concrete methodology (chapters 5–10).
* HW2 does **not** repeat HW1's functional requirements F1–F9, its performance requirements, its risks or its subsystem specs. Those remain binding through HW1, as the source hierarchy requires.
* HW2 is more specific about the deduplication key, the split dates, the baselines, the model features, the budget formula, the assistant intents, the injection procedure, the test cases and seed 42.
* Where they differ, the more specific HW2 rule is applied and the HW1 requirement is kept or explained. See `requirements_conflicts.md`.

## Observations on the documents themselves (not changed, recorded only)

1. HW1 pages 6–7 contain unrendered LaTeX citation keys (`cite lesner2019`, `cite alhenshiri2026`, `cite yang2026`, `citelundberg2017`) and stray "text Environment impact" / "text Social impact" markers. HW1 has no reference list, and these keys are not in HW2's reference list. **They were not verified and are not reused as citations in this project.**
2. HW1's contents and numbering jump from section 2.4 to 2.6.
3. Both documents state that values are *provider-advertised* and that local hash and commit "will be recorded". This project records them in `docs/dataset_provenance.md`.
4. HW2 Tables 9.1 and 9.2 are empty placeholders. This project fills them only with measured results, in `reports/evaluation/` and `docs/final_results.md`.
