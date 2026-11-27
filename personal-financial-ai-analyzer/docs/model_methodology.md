# Model Methodology

The design follows HW2 §5.4–5.5. Deviations and interpretations are recorded in `DECISIONS.md`.

## Forecasting (E2)

* **Target.** Monthly expenses (outflow + fee − refund) per account × currency (D-12). Months without records count as 0.
* **Eligibility.** ≥ 12 active months in the **training period** (D-08). Others get the notice "Not enough history for a forecast".
* **Baselines.**
  * naive: y(t−1)
  * seasonal naive: y(t−12)
  * MA(3): mean of y(t−3..t−1)
* **ETS.** statsmodels `ExponentialSmoothing` ETS(A,N,N), with estimated initialization, refit at every origin. Convergence warnings are counted; a failed fit falls back to naive and is counted.
* **GBR.** scikit-learn `HistGradientBoostingRegressor` on lags 1–3, `rolling_mean_6` (mean of t−6..t−1) and calendar month. `gbr_seasonal` adds `lag_12` as a separate ablation (CF-14).
  * Grid: learning rate {0.05, 0.1} × iterations {100, 300} × depth {3, 6} × loss {squared, absolute}, chosen on validation.
  * `random_state` = 42 and `early_stopping` = False, so results are deterministic.
* **Training data.** The GBR learns from targets in 2024-07..2025-12 (it needs 6 lags). For test scoring it is refit on 2024-07..2026-04.
* **Decision rule (HW2 5.4).** An advanced model is kept only if its validation MAE **and** MASE are below the best baseline's.

## Anomaly ranking (E3)

* **Records.** Completed debit, withdrawal and fee. History is train + validation months; scored records are test months.
* **Features.** log amount, hour, ISO weekday, category history share, log(amount / account-category history median).
* **Robust z-score (baseline).** z = 0.6745 × (log amount − median) / MAD over the account's history; score = |z|.
* **Isolation Forest per account (HW2 primary).** 100 trees, `max_samples=auto`, seed 42, fitted on that account's history.
* **Isolation Forest global (deployable, D-07).** Same parameters, fitted on all selected accounts' history features. This is the saved artifact the app loads.
* **Injection (HW2 8.4).** Rates 0.5%, 1% and 2%; seeds 42, 43, 44. Scenarios: amount ×U(5,10), an hour unseen in the account's history (D-09), or the least-used category.
* **Output wording.** Results are always "review candidates", never fraud.

## Known model limitations (measured)

* **Isolation Forest cannot extrapolate.** A value beyond the training range scores like the most extreme training point (unit test `test_isolation_forest_scores_are_deterministic_and_rank_outlier_first`).
* **Synthetic data.** The monthly series behave like i.i.d. noise (lag-1 autocorrelation −0.044), so no forecaster can learn temporal structure. See `docs/final_results.md`.
