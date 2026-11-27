# Data Engineering Audit

| # | Area | Finding (evidence) | Status |
|---|---|---|---|
| 1 | CSV ingestion | `src/data/ingestion.py`; empty, header-only, unreadable and oversize (> 50 MB, > 1M rows) files raise controlled `IngestionError`; 200k-row CSV ingested in 0.5 s (`inference_performance.json`) | PASS |
| 2 | Parquet reading | PyArrow/Polars streaming; partitioned workers ≤ 1.2 GB | PASS |
| 3 | Schema validation | Verified against the physical schema (27 checks) | PASS |
| 4 | Column mapping | Synonym suggestion plus user override; UX task 4 maps `When`→date and `Kind`→category in a real browser | PASS |
| 5 | Timestamp parsing | Strict `YYYY-MM-DD[ HH:MM:SS]`; ISO `T` separator now accepted (A-05); other formats rejected with a reason | PASS |
| 6 | Timezones | The data has no timezone information, so timestamps are treated as naive local time. Offsets (e.g. `+03:00`) are rejected as `invalid_timestamp`, never shifted silently | PASS (documented limitation) |
| 7 | Currency | 6 ISO codes; every aggregate keyed by currency (`MixedCurrencyError` test) | PASS |
| 8 | Sign convention | Measured: ledger reconciles 49,000,000/49,000,000 records | PASS |
| 9 | Refunds | Reduce same-category spending, never counted as income; net may be negative (fixture) | PASS |
| 10 | Duplicates | First `transaction_id` kept, rest rejected with a reason; same value or date with different IDs kept | PASS |
| 11 | Missing values | Each required field gives `missing_<field>`; a missing category gives "Uncategorized" | PASS |
| 12 | Invalid transactions | Every row is clean **or** rejected with a reason (row accounting test; 50M in = 50M out) | PASS |
| 13 | Account isolation | Summaries keyed by account; UX task 13 shows the second account's own totals | PASS |
| 14 | Category normalization | Lowercase plus a canonical "Uncategorized" (K-12) | PASS |
| 15 | Monthly aggregation | **Full-scale independent reconciliation**: PyArrow recomputation from the raw 50M rows against the pipeline tables gives **54/54 exact integer matches** (6 currencies × 9 measures, incl. category + fee = expenses) (`reconciliation.json`) | PASS |
| 16 | Derived features | Past-only (permutation test); `balance_after` never used | PASS |
| 17 | Saved intermediate tables | `data/processed/*` partitions; **determinism**: an interrupted-and-resumed rerun gives content-identical tables (9/9); a recomputation of untouched partitions is identical | PASS |

## Missing data versus zero

* The forecasting panel fills months without records with 0 (no spending).
* **3,357 of 480,000 training cells (0.70%)** precede an account's first record. The data cannot tell "no activity" from "account did not exist yet" (`panel_lifespan_check.json`). This is a P3 limitation; the frozen experiment was not changed.
* **3,963 of 20,000** panel accounts have no record in the final month, which is the same ambiguity.

## `balance_after`

`balance_after` is never read by calculations, features, the app or the assistant (grep and the feature-guard tests). No chronological balance history is constructed. The field is not presented as a comparable balance anywhere.
