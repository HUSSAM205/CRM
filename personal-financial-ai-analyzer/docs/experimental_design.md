# Experimental Design

This follows HW2 chapter 8. Where HW2 leaves something undefined, the interpretation is in `DECISIONS.md`. All numbers below are measured (`reports/verification/methodology_feasibility.json`).

## Split (HW2 Table 8.1): verified against data coverage

| Set | Months | Count | Use |
|---|---|---|---|
| Train | 2024-01 … 2025-12 | 24 | fitting |
| Validation | 2026-01 … 2026-04 | 4 | model and setting selection |
| Test | 2026-05 … 2026-07 | 3 | final results only |

The data months are exactly this union, with no month missing (check M1). Rolling origin: one month ahead, moving forward month by month through validation (and, for final scoring, through test, refitting on train + validation).

## E1: financial correctness

Hand-calculated fixtures, plus a real-data cross-check against an independent `Decimal` computation. **Done: PASS.**

## E2: forecasting

* Unit: account × currency series of monthly expenses (D-12).
* Eligibility: ≥ 12 active months in the training period (D-08). That gives **106,945 series** (106,930 USD, 15 EUR, D-14). Eligible series average 12.7 active training months, so about 47% of training months are zero: the series are intermittent.
* Working subset (HW2 6.3): a seeded sample of eligible series, sized from the resource benchmarks. The size is recorded in the experiment registry.
* Models: naive, seasonal naive (t−12), MA(3), ETS (statsmodels), and GBR on lags 1–3, rolling mean and month number (HW2 5.4). An additional, separately labeled ablation `gbr_seasonal` adds lag-12 (CF-14).
* Metrics: MAE, RMSE and MASE. MASE scale = in-sample MAE of the one-step naive forecast on the training months of each series.
* Decision rule: keep an advanced model only if it beats the best baseline on **both** MAE and MASE on validation.
* Robustness (HW2 10.3): short versus long histories reported separately; rolling-origin error per month; seeds 42, 43, 44.
* Secondary: an account-disjoint holdout (CF-05).

## E3: anomaly ranking

* Selected accounts: a seeded sample. At 2.42 test spending records per account, about 10,000 accounts gives about 242 positives at 1%.
* Injection (HW2 8.4) on completed test-period spending records: amount × U(5,10), an unusual hour (D-09), or a rare category (the category least used in the account's training history). Rates 0.5%, 1% and 2%; seeds 42, 43, 44. Labels are stored separately.
* Models: robust z-score (median/MAD of the account's history; baseline), per-account IF (HW2 primary), and global IF on account-relative features (deployable, D-07).
* Metrics: Precision@k (k = number of positives, D-10), recall@k, ROC-AUC, Precision@50 and @100, and recall per scenario.
* Expectation recorded **before** running: uniform hours mean the hour-shift scenario may be hard to detect. The result is reported whatever it turns out to be.

## E4: dashboard and assistant tasks

The 12 tasks from the master prompt section 24 (which includes HW1 3.2.6) are run as automated integration tests. Completion rate and errors are recorded. No claim of a study with real participants is made.
