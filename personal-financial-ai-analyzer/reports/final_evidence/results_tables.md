# Results Tables (generated 2026-11-27 12:53 UTC)

Every value is read from the saved result files listed in `evidence_index.md`.

## Dataset (all 50,000,000 rows)
* File SHA-256 `b18c83595d2e7a06598c00a3cbe01eb0586b2f0b10443305c6283586c27f8c17` (HF commit `98cf38f9b2f1a9994930f52a4d490cb2b5777acc`; see `docs/dataset_provenance.md`).
* 50,000,000 rows validated: 50,000,000 clean, 0 rejected, 0 unresolved types.
* Ledger: 49,000,000/49,000,000 records reconcile in transaction-ID order, versus 2.19% in timestamp order.
* Forecast-eligible series (≥ 12 active training months): 106,945 {'EUR': 15, 'USD': 106930}.

## HW2 Table 9.1: forecasting (primary subset: 20,000 series, one-month-ahead rolling origin)
| model | split | MAE | RMSE | MASE |
|---|---|---|---|---|
| gbr | validation | 26.554 | 68.99 | 0.551 |
| gbr_seasonal | validation | 26.645 | 68.949 | 0.553 |
| ets | validation | 41.748 | 72.091 | 0.812 |
| moving_average_3 | validation | 42.507 | 79.918 | 0.845 |
| naive | validation | 44.556 | 97.418 | 0.908 |
| seasonal_naive | validation | 50.105 | 103.026 | 0.945 |
| gbr_seasonal | test | 26.232 | 72.19 | 0.551 |
| gbr | test | 27.194 | 71.399 | 0.57 |
| moving_average_3 | test | 39.259 | 79.534 | 0.821 |
| ets | test | 40.593 | 74.518 | 0.804 |
| naive | test | 42.945 | 97.463 | 0.899 |
| seasonal_naive | test | 51.602 | 106.675 | 0.978 |

* Best baseline (validation): MAE = **moving_average_3**, MASE = **moving_average_3**.
* Kept by the HW2 rule (beats the best baseline on validation MAE **and** MASE): **ets, gbr, gbr_seasonal**. Selected: **gbr** {'learning_rate': 0.05, 'max_iter': 100, 'max_depth': 3, 'loss': 'absolute_error'}.
* ETS convergence warnings counted (not hidden): 1692.

### Post-hoc diagnostic (test months; reference predictors are NOT HW2 baselines and were NOT used for selection)
| reference predictor (post-hoc, NOT used for selection) | MAE | RMSE | MASE |
|---|---|---|---|
| zero | 25.374 | 72.764 | 0.532 |
| global_train_median | 25.374 | 72.764 | 0.532 |
| series_train_median | 26.667 | 71.813 | 0.557 |
| series_train_mean | 40.551 | 71.299 | 0.796 |

* Share of test months with zero spending: 62.1%.
* Within-series autocorrelation of monthly spending (training months): lag 1 -0.044, lag 12 -0.044. That is what i.i.d. noise gives (expected ≈ −1/(n−1) = −0.043).
* A zero forecast on **validation**: MAE 24.697 and MASE 0.511, against GBR's 26.554 and 0.551.

### Robustness: test MAE across seed resamples and the account-disjoint run
| model | primary_seed42 | resample_seed43 | resample_seed44 | account_disjoint_gbr |
|---|---|---|---|---|
| naive | 42.945 | 42.705 | 43.122 | None |
| seasonal_naive | 51.602 | 51.136 | 51.301 | None |
| moving_average_3 | 39.259 | 39.164 | 39.651 | None |
| ets | 40.593 | 40.487 | 40.732 | None |
| gbr | 27.194 | 25.24 | 27.721 | 26.796 |
| gbr_seasonal | 26.232 | 25.24 | 27.707 | 26.747 |

### Short vs long histories (test)
| history | model | n_series | MAE | RMSE | MASE |
|---|---|---|---|---|---|
| short (12-13 active train months) | naive | 16395 | 42.752 | 94.542 | 0.915 |
| short (12-13 active train months) | seasonal_naive | 16395 | 50.45 | 103.931 | 0.977 |
| short (12-13 active train months) | moving_average_3 | 16395 | 39.13 | 77.479 | 0.836 |
| short (12-13 active train months) | ets | 16395 | 39.749 | 70.401 | 0.807 |
| short (12-13 active train months) | gbr | 16395 | 26.969 | 68.97 | 0.578 |
| short (12-13 active train months) | gbr_seasonal | 16395 | 26.033 | 69.788 | 0.559 |
| long (>=14 active train months) | naive | 3605 | 43.825 | 109.771 | 0.828 |
| long (>=14 active train months) | seasonal_naive | 3605 | 56.839 | 118.354 | 0.978 |
| long (>=14 active train months) | moving_average_3 | 3605 | 39.846 | 88.277 | 0.754 |
| long (>=14 active train months) | ets | 3605 | 44.428 | 90.916 | 0.792 |
| long (>=14 active train months) | gbr | 3605 | 28.22 | 81.537 | 0.533 |
| long (>=14 active train months) | gbr_seasonal | 3605 | 27.136 | 82.236 | 0.514 |

## HW2 Table 9.2: anomaly ranking (rate 1%, seed 42; 24,069 test spending records of 10,000 accounts)
| model | positives | precision_at_k | recall_at_k | roc_auc | average_precision | precision_at_100 |
|---|---|---|---|---|---|---|
| robust_zscore | 241 | 0.037 | 0.037 | 0.581 | 0.017 | 0.03 |
| isolation_forest_per_account | 241 | 0.008 | 0.008 | 0.559 | 0.011 | 0.01 |
| isolation_forest_global | 241 | 0.041 | 0.041 | 0.587 | 0.015 | 0.03 |

### By injection scenario
| model | recall_at_k_amount | roc_auc_amount | recall_at_k_category | roc_auc_category | recall_at_k_hour | roc_auc_hour |
|---|---|---|---|---|---|---|
| robust_zscore | 0.105 | 0.804 | 0.0 | 0.428 | 0.013 | 0.534 |
| isolation_forest_per_account | 0.013 | 0.636 | 0.012 | 0.499 | 0.0 | 0.552 |
| isolation_forest_global | 0.118 | 0.751 | 0.0 | 0.509 | 0.013 | 0.516 |

### Robustness over rates 0.5/1/2% and seeds 42/43/44 (mean ± sd)
| rate | model | positives_mean | precision_at_k_mean | precision_at_k_std | roc_auc_mean | roc_auc_std |
|---|---|---|---|---|---|---|
| 0.005 | isolation_forest_global | 120.0 | 0.039 | 0.005 | 0.61 | 0.056 |
| 0.005 | isolation_forest_per_account | 120.0 | 0.008 | 0.008 | 0.568 | 0.057 |
| 0.005 | robust_zscore | 120.0 | 0.039 | 0.01 | 0.588 | 0.046 |
| 0.01 | isolation_forest_global | 241.0 | 0.051 | 0.02 | 0.593 | 0.009 |
| 0.01 | isolation_forest_per_account | 241.0 | 0.012 | 0.011 | 0.56 | 0.016 |
| 0.01 | robust_zscore | 241.0 | 0.05 | 0.011 | 0.58 | 0.001 |
| 0.02 | isolation_forest_global | 481.0 | 0.086 | 0.003 | 0.624 | 0.018 |
| 0.02 | isolation_forest_per_account | 481.0 | 0.031 | 0.004 | 0.587 | 0.014 |
| 0.02 | robust_zscore | 481.0 | 0.07 | 0.007 | 0.605 | 0.009 |

### Positive control (pure amount multiplication, robust z-score)
* ×5: ROC-AUC 0.7031, Precision@k 0.0788
* ×10: ROC-AUC 0.8366, Precision@k 0.1452
* ×50: ROC-AUC 0.972, Precision@k 0.444
* ×1000: ROC-AUC 0.9988, Precision@k 0.7967

## Tests, artifacts and user tasks
* Automated tests: **196 passed** (`logs/testing/latest.log`).
* Artifacts: **PASS**. 8/8 entries load in a fresh process (`reports/verification/artifact_verification.json`).
* Real-browser user tasks: **24/24 completed**, 0 errors, mean 2.4 s per task (`reports/ux_tasks/ux_task_results.json`). This was scripted, with no human participants.

## Figures
* `reports/figures/forecasting_test_comparison.png`
* `reports/figures/forecasting_rolling_origin_mae.png`
* `reports/figures/anomaly_auc_by_scenario.png`
* `reports/figures/anomaly_positive_control.png`
* `reports/figures/data_distributions.png`
