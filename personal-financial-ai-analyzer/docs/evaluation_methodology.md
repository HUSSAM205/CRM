# Evaluation Methodology

| Experiment | Protocol | Metrics |
|---|---|---|
| E1 financial | Hand fixtures; real-data `Decimal` cross-check | Exact match |
| E2 forecasting | Rolling origin, one month ahead. Validation (2026-01..04) for every choice; test (2026-05..07) scored once after refit on train + validation. Robustness: seeds 43 and 44 resamples, account-disjoint GBR, short vs long histories, per-month errors | MAE, RMSE, MASE. MASE scale = per-series in-sample naive MAE on training months; zero-scale series excluded and counted |
| E3 anomaly | Injection into test-period spending (0.5/1/2% × seeds 42/43/44); history = earlier months | Precision@k (k = positives), recall@k, ROC-AUC, average precision, Precision@50/100, recall and AUC per scenario; positive control |
| E4 tasks | 12 scripted real-browser tasks (Playwright) | Completion, errors, seconds |

Post-hoc diagnostics (`scripts/evaluate_models.py`) are clearly labelled and never used for selection.
