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

## 4. Experiment E2-B on Dataset B (master audit 2, separate from HW2)

Script: `scripts/research/forecast_dataset_b.py`. The protocol is fixed in its docstring. Dataset: PersonaLedger normal users (CC BY 4.0; see `DATASET_REGISTRY.md`).

* **Split** by target month: train ≤ 2026-06 (159,526 rows from 16,215 users), validation 2026-07..12 (66,919 / 11,942), test 2027-01..06 (42,565 / 9,368).
* **History:** at least 12 full months; partial first and last months are excluded.
* **Model:** scale-free HistGradientBoosting on ratios to the user's historical mean, absolute error. Selected on validation: depth 3, learning rate 0.05, 300 iterations, seed 42; fit time 1.6 s.

| Test (2027-01..06) | MAE | MASE | RMSE | R² |
|---|---|---|---|---|
| **GBR scale-free** | **971.34** | **0.781** | 1,400.2 | **+0.232** |
| historical median (best baseline) | 1,022.66 | 0.826 | 1,494.3 | 0.126 |
| historical mean | 1,038.86 | 0.828 | 1,436.9 | 0.192 |
| moving average 3 | 1,193.71 | 0.950 | 1,601.7 | −0.004 |
| seasonal naive | 1,274.41 | 0.990 | 1,814.1 | −0.288 |
| naive | 1,433.71 | 1.138 | 1,948.9 | −0.487 |
| zero | 3,520.75 | 2.823 | 3,866.5 | −4.853 |

**Gate result: ACCEPTED.** On validation, MAE was 929.71 vs 939.64 and MASE 0.737 vs 0.745 (historical median). On test, it is also better than the best baseline.

**Is the gain real?** Paired bootstrap over users, 2,000 resamples:
* validation −9.93 MAE (−1.1%), 95% CI [−11.42, −8.40];
* test −51.32 (−5.0%), CI [−55.45, −47.50].

The gain is small but distinguishable from zero.

**80% range:** multiplicative and calibrated on validation (80.0%); test coverage was **77.7%**, slightly below the target.

**Transfer to Dataset A:** test MAE 36.28 vs zero 25.37. The model is **not** usable on intermittent series. Hence a **domain guard** (D-24): use the model only when there are at least 12 months **and** no month without spending. On Dataset A's test cells the guard applies to 0% of cells, so A's behaviour is unchanged (MAE 26.546 either way).

## 5. Controlled positive control C3 (Dataset C, synthetic)

With the same HW2 GBR configuration:

| Series | GBR validation MAE | Best baseline validation MAE | Test |
|---|---|---|---|
| Structured (AR(1) φ = 0.7 + December seasonality) | 674.07 | 781.47 (MA3) | 786.75 vs 825.79 (naive) |
| Unstructured (i.i.d.) | 944.98 | 839.30 (historical median) | GBR does **not** beat it |

GBR beats the best baseline on structured series and loses on unstructured ones. **The pipeline learns when monthly structure exists.** Dataset A's failure is therefore a property of the data (`reports/experiments/dataset_c/summary.json`).

## 6. What the product shows (D-24, supersedes section 3 for in-domain series)

`inference.forecast_product`:
* **In-domain series** (≥ 12 months, no zero month): the E2-B model estimate, its 80% range, evidence and limitations.
* **Otherwise:** the deterministic historical-median outlook of section 3.
* **Fewer than 12 active months:** an insufficient-history notice.

The HW2 E2 GBR stays visible as the academic record, labelled REJECTED.
