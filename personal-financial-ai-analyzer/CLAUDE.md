# Personal Financial AI Analyzer: notes for agents

Academic prototype (BAU, Special Topics in AI Engineering 1). The authoritative specifications are HW1 and HW2, summarized in `docs/academic_source_analysis.md`.

## On resume

1. Read `PROJECT_STATUS.md` and `NEXT_ACTION.md`.
2. Check checkpoints in `checkpoints/`. Never assume a previous process is still running.
3. If `data/raw/transactions_50M.parquet` is missing, run `python scripts/download_dataset.py`, then `python scripts/verify_dataset.py`.

## Hard rules

* Never modify `data/raw/`.
* Never use `balance_after` in calculations or features (D-03).
* Money is in integer cents. Every aggregation includes `currency`.
* Heavy data work runs through `src/utils/resource_monitor.run_partitions` or `run_guarded`: one account partition per child process, with a 4 GB hard limit. Unpartitioned full-data group-bys are prohibited (measured at more than 4 GB).
* Select models on validation (2026-01..04) only; score test (2026-05..07) once.
* Never report a metric, count or test result that was not produced by a run logged in `EXPERIMENT_REGISTRY.md`.
* Anomalies are "review candidates", never fraud.

## Commands

* Tests: `python -m pytest`
* Verification: `python scripts/verify_environment.py`, `python scripts/verify_dataset.py`
