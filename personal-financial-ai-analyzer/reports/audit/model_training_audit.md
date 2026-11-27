# Model Training Audit

Independent re-execution: `python scripts/audit/training_audit.py`. It ran guarded: **472.7 s, peak RSS 1.859 GB, minimum system-available memory 14.48 GB, not killed** (`logs/execution/audit_training.log`). Results are in `training_audit.json`.

## What was trained, on what, and how big it is

| Model | Training data | Size of training set | Configuration | Learned parameters (measured from the saved file) | File |
|---|---|---|---|---|---|
| `gbr` (HistGradientBoostingRegressor) | Monthly net-spending panel, 20,000 eligible series (one per account, USD 19,999, EUR 1), features lag 1–3, rolling mean 6, month | 360,000 examples (train only, targets 2024-07..2025-12); **refit 440,000** (train plus validation, targets to 2026-04) | `loss=absolute_error, lr=0.05, max_iter=100, max_depth=3, early_stopping=False, random_state=42`; chosen on validation by a 32-point grid | 100 trees, 1,500 nodes, 800 leaves (800 leaf values), 5 input features | 110,992 B |
| `gbr_seasonal` | Same plus `lag_12` | Same | Same | 100 trees, 1,500 nodes, 800 leaves, 6 features | 112,160 B |
| ETS(A,N,N) | One fit per series per origin | 140,000 fits per run (20,000 × 4 validation origins, + 3 test origins) | statsmodels, default optimizer | 2 parameters per fit (level, α). Fitted at evaluation time, **not saved** (refused at inference by design, I6.4) | — |
| Baselines (naive, seasonal naive, MA3) | — | — | No training | 0 | — |
| `isolation_forest_global` (deployed) | History rows of 10,000 anomaly accounts (2024-01..2026-04) | 223,654 history rows; 24,069 scored test rows | `n_estimators=100, max_samples=auto (256), contamination=auto, random_state=42`; 5 features | 100 trees, 15,262 nodes | 1,397,341 B |
| `isolation_forest_per_account` (experiment only) | Same accounts, one forest per account | ≈22 history rows per account; 10,000 forests fitted and discarded | Same settings | Not persisted (cannot score unseen accounts, D-07) | config only |
| `robust_zscore` | Per-account and per-category medians/MAD of log amount from history | 223,654 rows | Thresholds from config | Statistics only | config only |

**Not trained on the full 50M rows.** That is by design: HW1 C3 and HW2 6.3 ask for subsets and aggregate tables. Every model trains on aggregates or account samples derived from all 50M preprocessed rows. A full-population check is reported below.

## Timings (audit re-execution, cloud container)

| Step | Seconds |
|---|---|
| GBR single fit (selected config, 360k rows) | 1.5 |
| GBR 32-config grid incl. validation predictions | 73.9 |
| GBR refit, both variants | 3.3 |
| ETS, 4 validation origins (80,000 fits) | 82.7 |
| ETS, 3 test origins (60,000 fits) | 59.9 |
| Anomaly experiment, 9 runs (3 rates × 3 seeds) | 226.9 |
| Full population GBR fit (1,925,010 rows) / refit (2,352,790 rows) | 8.1 / 9.4 |

**Why did the original forecasting run take 529 s if one fit takes 1.5 s?** Measured breakdown: primary panel 223.4 s (dominated by 140k ETS fits and the 32-fit grid), plus seed-43 panel 146.7 s, seed-44 panel 150.3 s, and account-disjoint panel 6.2 s. GBR itself is a small fraction. Monthly aggregation shrinks 50M rows to 20,000 × 31 cells, so the short fit times are expected, not a sign that training was skipped.

## Reproduction

Every saved validation and test metric for every model was recomputed from scratch in a new process. The absolute difference is **0.0** for all MAE and MASE values (14 forecasting rows), and 0.0 for ROC-AUC and precision@k (27 anomaly rows). The saved artifacts load in a fresh process and their predictions equal the recorded ones (`reports/verification/artifact_verification.json`; `verify_artifacts.py` exit 0 in this audit).

## Findings (scientific, not defects)

* **F-1:** a constant **zero** forecast beats the selected GBR on MAE and MASE (details in `forecasting_audit.md`).
* **F-2:** in the **seed-43** resample, both GBR models learned a constant prediction of exactly 0 on test (1 unique value, 100% zeros). This explains why gbr and gbr_seasonal have identical seed-43 metrics. It is not a bug: the inputs differ (`random_inputs_identical: false`), but absolute-error boosting collapses to the median, which is 0.
* **F-3:** all R² values are negative (best: validation gbr −0.061).
