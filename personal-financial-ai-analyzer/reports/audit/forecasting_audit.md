# Forecasting Audit

## Protocol checks

| Check | Result | Evidence | Status |
|---|---|---|---|
| Split: train 2024-01..2025-12, validation 2026-01..04, test 2026-05..07 | As specified (HW2 8.2) | `split_metadata.json`; test L2 | PASS |
| Eligibility: ≥ 12 active **training** months | 106,945 eligible series; uses training months only | L3 test; independent read-only count equal | PASS |
| Selection on validation only; test scored once | Selection file written before test scoring; rule frozen | `artifacts/forecasting/selection/…`; registry | PASS |
| Features past-only | Permutation test; no `balance_after`, no IDs | L1, L7 tests | PASS |
| MASE scale | In-sample training naive per series | `forecasting_metrics.py`; independent recomputation equal | PASS |
| Rolling origin | 4 validation and 3 test origins | `rolling_origin_per_month.csv` | PASS |
| Robustness | 3 seed resamples; account-disjoint panel; history-length strata | `metrics_all_runs.csv`, `test_by_history_length.csv` | PASS |

## Metrics (independently recomputed; equal to the saved values)

| Model | Val MAE | Val MASE | Test MAE | Test MASE | Test RMSE | Test R² |
|---|---|---|---|---|---|---|
| naive | 44.556 | 0.9078 | 42.945 | 0.8992 | 97.463 | −0.983 |
| seasonal naive | 50.105 | 0.9450 | 51.602 | 0.9775 | 106.675 | −1.375 |
| MA(3) (best HW2 baseline) | 42.507 | 0.8453 | 39.259 | 0.8213 | 79.534 | −0.320 |
| ETS | 41.748 | 0.8119 | 40.593 | 0.8041 | 74.518 | −0.159 |
| **gbr (selected)** | **26.554** | **0.5509** | **27.194** | **0.5702** | 71.399 | −0.064 |
| gbr_seasonal | — | — | 26.232 | 0.5506 | 72.190 | −0.088 |
| *zero (post-hoc diagnostic)* | — | — | *25.374* | *0.5323* | 72.764 | −0.105 |
| *historical median (post-hoc)* | — | — | 26.667 | 0.5566 | 71.813 | −0.076 |
| *historical mean (post-hoc)* | — | — | 40.551 | 0.7961 | 71.299 | −0.061 |

Under HW2's rule, GBR beats the best baseline (MA3) on validation MAE and MASE, so it is **kept**.

## Scientific limitations (measured in this audit)

* **The zero forecast is better** on MAE and MASE (test 25.374 vs 27.194). GBR beats zero on only **39.4%** of series. GBR predicts exactly 0 in **33.8%** of test cells (181 distinct values). 62.1% of actual test cells (62.7% of validation cells) are zero. The "improvement over baselines" reflects learning the median of intermittent series, not temporal skill. Within-series autocorrelation is about −0.044.
* **Full eligible population** (106,945 series; GBR on 1,925,010 / 2,352,790 rows): test gbr MAE 27.045 vs zero 25.438 vs MA3 39.523. The subset result **generalizes**; the 20k subset is not cherry-picked.
* **R² is negative for every model.** No model explains variance better than the series-agnostic mean.
* **Seed 43:** constant-zero GBR (F-2).
* **Panel zero-fill:** 0.70% of training cells precede an account's first record (P3).
* **Currency:** effectively USD-only (19,999 of 20,000 series).

The frozen selection rule was **not** changed after seeing these results. The zero and median baselines are reported as diagnostics and recommended for future protocols.
