# Forecasting Experiments

Full method and interpretation: [`docs/FORECASTING.md`](../../docs/FORECASTING.md). Raw results:
* `reports/experiments/forecasting/` (HW2 E2, frozen);
* `reports/experiments/forecasting_quality_gate/` (E2-QG: `summary.json`, `model_comparison.csv`, `gbr_ext_grid_validation.csv`);
* figures in `reports/figures/research/qg_*.png`;
* combined table `MODEL_COMPARISON.csv`.

## Setup (verified)

* **Local coverage:** 2024-01-01..2026-07-31, all 31 months present. This exactly matches HW2 Table 8.1.
* **Eligibility:** at least 12 active **training** months, giving 106,945 series (USD 106,930, EUR 15).
* **Primary panel:** 20,000 series. Training targets 2024-07..2025-12 (360,000 rows). Validation has 4 origins × 20,000 = 80,000 cells; test has 3 × 20,000 = 60,000.
* **Rolling origin:** one month ahead; features use months < t only (L2 test).
* **Prediction counts:** valid predictions = cells for every model; failed predictions = 0 (`model_comparison.csv`).

## Results, primary panel (MAE, MASE, RMSE, R², share of zero predictions)

| Model | Validation MAE / MASE | Test MAE / MASE | Test RMSE | Test R² | Test zero-prediction share | Gate |
|---|---|---|---|---|---|---|
| zero | 24.697 / 0.511 | 25.374 / 0.532 | 72.76 | −0.105 | 100% | diagnostic baseline |
| GBR extended | 25.843 / 0.536 | 25.374 / 0.532 | 72.76 | −0.105 | 100% | **REJECTED** |
| historical median | 26.474 / 0.545 | 26.546 / 0.554 | 71.91 | −0.079 | 49.8% | **product outlook** |
| GBR (E2) | 26.554 / 0.551 | 27.194 / 0.570 | 71.40 | −0.064 | 33.8% | **REJECTED** (kept by the HW2 rule) |
| rolling median 6 | 29.976 / 0.613 | 28.172 / 0.589 | 72.10 | −0.085 | 59.0% | baseline |
| moving average 3 | 42.507 / 0.845 | 39.259 / 0.821 | 79.53 | −0.320 | 24.1% | baseline (best HW2 baseline) |
| naive | 44.556 / 0.908 | 42.945 / 0.899 | 97.46 | −0.983 | 62.3% | baseline |
| seasonal naive | 50.105 / 0.945 | 51.602 / 0.978 | 106.67 | −1.375 | 44.9% | baseline |
| ETS (E2) | 41.748 / 0.812 | 40.593 / 0.804 | 74.52 | −0.159 | — | not gated (worse than the median) |

## Robustness (validation MAE: zero / GBR extended / historical median → gate)

| Panel | Series | Values | Gate | Interval test coverage |
|---|---|---|---|---|
| seed 43 | 20,000 | 25.353 / 26.675 / 27.134 | both REJECTED | 81.7% |
| seed 44 | 20,000 | 25.434 / 26.847 / 27.192 | both REJECTED | 82.0% |
| account-disjoint | 20,000 | 25.334 / 26.645 / 27.106 | both REJECTED | 81.5% |
| all eligible | 106,945 | 25.173 / 26.133 / 26.939 | both REJECTED | 81.7% |

## Error breakdowns (test, primary; `summary.json` → `breakdowns_test`)

* **By month:** 2026-05: GBR extended 25.98, outlook 27.24, zero 25.98. Similar in June and July.
* **By spending-level quartile** (historical mean): outlook MAE 26.1–27.1. GBR extended equals zero in every quartile.
* **By history length:**
  * 12–13 active months (16,395 series): outlook 25.91;
  * 14–15 (3,242): 29.13;
  * 16+ (363): 32.07.
* **By currency:** USD 19,999 series; EUR 1 series (too few to evaluate).

## Zero-prediction investigation (master audit 7.8)

| Question | Finding |
|---|---|
| Target distribution | training: 45.5% zeros, 2.3% negative, median 5.04, 90th percentile 100.37; validation 62.7% zeros; test 62.1% zeros |
| Feature–target association | Spearman \|ρ\| ≤ 0.133 for all 11 features; lags −0.008 … −0.014; within-series lag-1 autocorrelation −0.044 |
| Hyperparameter sensitivity | E2 grid (32 configurations, both losses, depth 3/6) and E2-QG grid (16): best validation MAE 25.84, still worse than zero; squared-error loss is worse on MAE |
| Seeds | seed 43 E2 GBR is a constant 0; extended GBR after the refit is a constant 0 |
| Eligibility and aggregation | eligibility from training months only (L3); totals reconcile exactly (9,488 checks) |
| Serialization | reload gives identical predictions (`reload_identical_predictions: true`) |
| **Cause** | **data characteristics**: intermittent, unpredictable targets with an upward shift in the zero share. Not an implementation defect, and not a feature-design gap; richer features did not help |

**Decision:** forecasting ML is **NOT EFFECTIVE on this dataset**. The product keeps the best data-dependent deterministic baseline (D-22).
