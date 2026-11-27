# Preprocessing

Implementation: `src/data/preprocessing.py`, run per account partition by `scripts/workers/aggregate_partition.py`, orchestrated by `scripts/build_aggregates.py`.

HW2 §4.5 steps and where each is done:

1. Batch reading: 50 account partitions, each in a guarded child process (peak ≤ 1.2 GB).
2. Normalize and validate, logging failures: `src/data/validation.py`. Every row ends up clean or rejected with a reason.
3. Deduplicate by `transaction_id`, keeping the first. Rows sharing only value or date are kept.
4. Separate meanings and exclude non-completed rows from totals: `src/rules/*`.
5. Account × currency × month aggregates: `data/processed/monthly/`, plus category tables.
6. Eligible series (≥ 12 active training months): `scripts/create_splits.py`.
7. Past-only lags, with fitting on training targets only: `src/features/temporal_features.py`.
8. User CSV mapping with an "Uncategorized" fallback: `src/data/ingestion.py`.

Result (`reports/data_audit/preprocessing_summary.json`): 50,000,000 rows in, 50,000,000 clean, 0 rejected, 38,767,223 monthly rows. No second full copy of the data is written.
