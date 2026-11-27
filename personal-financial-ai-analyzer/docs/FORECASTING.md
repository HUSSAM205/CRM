# Forecasting

## 1. Academic experiment E2 (HW2 5.4, frozen)

* **Panel:** 20,000 eligible account–currency series (at least 12 active training months).
* **Split:** train 2024-01..2025-12, validation 2026-01..04, test 2026-05..07.
* **Rolling origin:** one month ahead.
* **Models:** naive, seasonal naive, 3-month moving average (MA3), ETS(A,N,N), and GBR (HistGradientBoosting, 32-point grid on validation).
* **HW2 rule:** keep an advanced model only if it beats the best baseline on validation MAE **and** MASE.
* **Result:** GBR kept. Validation MAE 26.554 / MASE 0.551 vs MA3 42.507 / 0.845. Test MAE 27.194 / MASE 0.570.

This experiment and its artifacts are unchanged (`reports/experiments/forecasting/`).

## 2. Quality-gate experiment E2-QG (master audit, separate)

`scripts/research/forecast_quality_gate.py`. The protocol is written in the file's docstring and was fixed before any test number of this experiment existed.

* **Extra baselines:**
  * zero: diagnostic only, because it ignores the user's data;
  * historical median: expanding median of all prior months;
  * rolling 6-month median.
* **Extra ML candidate:** GBR with extended past-only features (rolling median, rolling standard deviation, zero share over 6 months, expanding mean and median, active months so far), chosen on validation from a 16-point grid.
* **Gate:** an ML model is ACCEPTED only if it beats **every** deterministic baseline, including zero, on validation MAE and MASE.

| Primary panel | Validation MAE | Validation MASE | Test MAE | Test MASE | Status |
|---|---|---|---|---|---|
| zero (diagnostic) | 24.697 | 0.511 | 25.374 | 0.532 | baseline |
| GBR extended | 25.843 | 0.536 | 25.374 | 0.532 | **REJECTED** (after the refit it predicts 0 for 100% of test cells) |
| historical median | 26.474 | 0.545 | 26.546 | 0.554 | **product outlook** |
| GBR (E2) | 26.554 | 0.551 | 27.194 | 0.570 | **REJECTED** |
| MA3 | 42.507 | 0.845 | 39.259 | 0.821 | baseline |

* **Robustness:** the same verdicts hold on the seed-43, seed-44, account-disjoint and full-population panels (106,945 series).
* **Full table:** `reports/experiments/forecasting_quality_gate/model_comparison.csv` (also `reports/final_master_audit/MODEL_COMPARISON.csv`).

### Why the models fail (investigation, primary panel)

* **No learnable signal:**
  * the mean within-series lag-1 autocorrelation is −0.044;
  * every feature–target Spearman correlation has |ρ| ≤ 0.133 (lags −0.008 to −0.014).
* **Intermittent targets with a shift:**
  * 45.5% of training cells are zero, against 62.7% in validation and 62.1% in test;
  * 2.3% of training cells are negative (refunds exceed purchases).
* **Consequence:** an absolute-error learner converges to the median, which drifts to 0. Seed 43 GBR and the refit extended GBR become constant 0.
* **Not caused by an implementation defect:**
  * aggregation reconciles exactly (9,488/9,488 checks);
  * a reloaded model gives identical predictions;
  * eligibility uses training months only;
  * the leakage tests pass;
  * the hyperparameter grids, including squared-error loss and depth 6, do not change the verdict.

## 3. What the product shows (D-22)

* **"Typical spending for next month"** = the median of the user's monthly expenses so far. This is the best data-dependent deterministic baseline on validation.
* **The user's own 10th–90th percentile range,** which is descriptive.
* **An 80% interval calibrated on the benchmark,** from validation residual quantiles in 5 bins of the point value. It covered 80.0% of validation cells and **81.9% of test cells**; on the other panels it covered 81.5–82.0%. For a user's own data it is indicative only.
* **A banner:** "Machine-learning forecasting: NOT EFFECTIVE on the evaluation data".
* **The HW2 GBR estimate,** in an expander, labelled REJECTED.
* **No history:** fewer than 12 active months gives an explicit notice.

Artifact: `artifacts/forecasting/outlook/v_20261127T060820Z/metadata.json`, with a checksum. It has no learned weights.
