# Executive Summary: Independent Final Audit

Personal Financial AI Analyzer: BAU Special Topics in AI Engineering 1 (HW1, HW2). Audit date 2026-11-27.

## Final status: **READY WITH DOCUMENTED LIMITATIONS**

It is not READY FOR SUBMISSION, for three reasons:
* HW1 P5 is PARTIAL;
* the Windows install and the user's laptop are NOT TESTED;
* the ML components meet their protocol but show no or weak scientific skill on this synthetic dataset.

No score of 100% is claimed.

## 1. What was already correct (confirmed by re-execution)

* Dataset identity: commit `98cf38f9…`, 1,594,749,644 B, SHA `b18c8359…7c17` (equal to the official LFS etag); 50,000,000 rows.
* Every financial total: an independent PyArrow recomputation of all 50M rows gives 54/54 exact matches. The ledger sign convention holds for 49M/49M records.
* Every saved forecasting and anomaly metric reproduces from scratch with Δ = 0.0. Artifacts reload and reproduce.
* Leakage controls (7/7 regression tests), the chronological split and validation-only selection.
* Memory safety: peak 1.86 GB under a 4 GB guard.
* Earlier documents already reported the unfavorable forecasting finding (zero forecast beats GBR).

## 2. What was incorrect

* **The earlier "27/27 PASS" was overstated.** A fresh clone could not run at all (A-08, P0): the parent `.gitignore` excluded `src/data/`, samples and logs.
* An overflow amount crashed the validator (A-01, P1).
* Traceability rows S7 and P1 were wrongly marked PASS.
* The leakage test failed without data (A-09).
* User strings were rendered as Markdown (A-03).

## 3. What was missing

* The HW1 S7 date filter (A-02).
* Privacy configuration: telemetry was on and tracebacks were shown (A-04).
* ISO `T` timestamp support (A-05).
* A repository-completeness regression test.

## 4. What was fixed

A-01..A-06 and A-08..A-10, each with a regression test or re-run evidence (`KNOWN_ISSUES.md`).

## 5. What was independently verified

All 16 gates A–P (`FINAL_VALIDATION_REPORT.md`): 12 PASS, 3 PARTIAL (A, M, N), 0 FAIL.

## Key numbers

* **Splits:**
  * Raw rows: train 38,758,051; validation 6,364,042; test 4,877,907.
  * Forecasting panel: 20,000 series, with 480,000 / 80,000 / 60,000 cells.
  * Anomaly: 10,000 accounts; 223,654 history rows; 24,069 scored rows.
* **Training sizes:**
  * GBR: 360,000 rows (refit 440,000). Full-population check: 1,925,010 rows.
  * ETS: 140,000 fits per run.
  * Global IF: 223,654 rows.
* **Model sizes:**
  * GBR: 100 trees, 1,500 nodes, 800 leaves.
  * Global IF: 100 trees, 15,262 nodes.
* **Timings:** GBR fit 1.5 s; 32-config grid 73.9 s; ETS 82.7 s (validation) and 59.9 s (test); anomaly 9 runs 226.9 s.
* **Forecasting (test):**
  * GBR: MAE 27.194, MASE 0.570.
  * MA(3): 39.259, 0.821.
  * Post-hoc zero forecast: 25.374, 0.532.
  * Every R² is negative.
* **Anomaly (1%, k = 241):** F1 is 0.037 for robust z, 0.008 for per-account IF and 0.041 for global IF. AUC is 0.56–0.59 and FPR about 1%. Review candidates only, never fraud.
* **Requirements:** 69 traced: 67 PASS, 1 PARTIAL, 1 N/A, 0 FAIL.
* **Tests:**
  * Development run: 125 passed.
  * Fresh clone of the final commit `ed4d45c`: 121 passed, 4 skipped.
  * UX: 15/15 real-browser tasks.

Details: [`REQUIREMENTS_TRACEABILITY.md`](REQUIREMENTS_TRACEABILITY.md), [`FINAL_TEST_RESULTS.md`](FINAL_TEST_RESULTS.md), [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md), [`FINAL_DELIVERY_CHECKLIST.md`](FINAL_DELIVERY_CHECKLIST.md). Detailed audits: [`../audit/`](../audit/).

## Remaining blockers

No technical blocker remains. Student actions:
* run the Windows install on the laptop, which also closes P5 (steps in `FINAL_DELIVERY_CHECKLIST.md`);
* write the final report, keeping implementation completeness separate from scientific validity.
