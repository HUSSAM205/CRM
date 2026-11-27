# Model card

Data: Free Financial Transactions 50M (ziadatalabs), commit `98cf38f9…`, SHA-256 `b18c8359…7c17`, CC BY-NC 4.0. This is **synthetic** data.

| Model | Status (quality gate) | Use in the app | Algorithm and hyperparameters | Training data | Metrics | Artifact |
|---|---|---|---|---|---|---|
| **GBR PersonaLedger (E2-B)** | **ACCEPTED** (beats every baseline on validation and test on Dataset B; bootstrap CI excludes 0) | next-month estimate for **in-domain** series (≥ 12 months, no zero month), with an 80% range | HistGradientBoosting, absolute error, depth 3, lr 0.05, 300 iterations, seed 42; 8 scale-free features (ratios to historical mean, history length, month) | Dataset B, 226,445 rows (train + validation refit), targets ≤ 2026-12 | test MAE 971.34 vs 1,022.66 (historical median); R² 0.232; range coverage 77.7%; on Dataset A MAE 36.3 (worse than zero, hence the domain guard) | `artifacts/forecasting/gbr_personaledger/v_20261127T113730Z` (320 kB, checksum) |
| Forecast outlook | **deployed** (deterministic) for series outside the E2-B domain | next-month "typical spending" + 80% interval | expanding median; interval = validation residual quantiles in 5 bins | none learned; interval calibrated on validation 2026-01..04 (80,000 cells) | test MAE 26.546, MASE 0.554, interval coverage 81.9% | `artifacts/forecasting/outlook/v_20261127T060820Z` |
| GBR (E2) | **REJECTED** (does not beat zero); kept by the frozen HW2 rule | shown for the record only | HistGradientBoosting, absolute error, lr 0.05, 100 iterations, depth 3, seed 42; features lag 1–3, rolling mean 6, month | 20,000 series; 360,000 rows (refit 440,000), targets 2024-07..2026-04 | validation MAE 26.554; test 27.194 / 0.570 | `artifacts/forecasting/gbr/v_20261127T033218Z_d8ea2159` (100 trees, 800 leaves) |
| GBR seasonal (E2 ablation) | REJECTED | none | as above + lag 12 | same | test 26.232 / 0.551 | `artifacts/forecasting/gbr_seasonal/…` |
| GBR extended (E2-QG) | REJECTED | none (not saved) | absolute error, depth 6, lr 0.1, 300 iterations; 11 past-only features | same | validation 25.843; test predicts 0 everywhere | — |
| Isolation Forest, global | **PARTIAL**: operational, weak (F1 0.041 at k on A; chance level on B identity theft, E3-B) | ranks unusual-transaction review candidates | 100 trees, max_samples 256, contamination auto, seed 42; 5 account-relative features | 10,000 accounts, 223,654 history rows | AUC 0.587; FPR 0.97% @k | `artifacts/anomaly/isolation_forest_global/v_20261127T033806Z_ef2215e8` |
| Robust z-score | PARTIAL (shown alongside) | second score in alerts | median / MAD of log amount from the user's own history | user's history at run time | AUC 0.581 | config only |
| IF per account (HW2 5.5) | REJECTED for deployment (weakest; cannot score unseen accounts) | none | per account, 100 trees | about 22 rows per account | AUC 0.559 | config only |

**Reproducibility:** every artifact has a `metadata.json` with algorithm, hyperparameters, seed, dataset hash, periods, row counts, metrics, feature schema, library versions and creation time; deployed entries carry a checksum. `python scripts/verify_artifacts.py` reloads each one in a fresh process and checks that its predictions are identical.

**Intended use:** education and personal budgeting reference. **Not for** fraud decisions, credit, investment or any automated decision about a person.

**Ethical note:** the data contain no demographic attributes; no fairness analysis was possible or attempted.
