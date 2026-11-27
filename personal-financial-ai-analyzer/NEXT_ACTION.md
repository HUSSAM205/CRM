# Next Action

1. **Gate 4/6:** `scripts/build_aggregates.py`. Use account-partitioned guarded workers to build:
   * the account × currency × month table (all accounts);
   * a seeded subset of eligible series plus their transactions for the anomaly experiment.

   Checkpoint each partition.
2. **Gate 6:** `scripts/create_splits.py`. Produce split metadata with actual counts and the account-disjoint holdout.
3. **Gates 7–9:** forecasting and anomaly modules, experiments and leakage regression tests.

Constraints: D-11 memory budget; no `balance_after` in features; selection on validation only.
