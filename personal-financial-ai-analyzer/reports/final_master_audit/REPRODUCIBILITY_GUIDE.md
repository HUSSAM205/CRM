# Reproducibility Guide (new developer, 12 steps)

Run from `CRM/personal-financial-ai-analyzer`. Linux and macOS commands are shown; Windows uses the `.bat` equivalents. Details: [`docs/REPRODUCIBILITY.md`](../../docs/REPRODUCIBILITY.md).

| # | Step | Command | Verified here |
|---|---|---|---|
| 1 | Clone | `git clone https://github.com/HUSSAM205/CRM && cd CRM/personal-financial-ai-analyzer && git checkout claude/hopeful-noether-t6vfi7` | yes (fresh clones) |
| 2 | Install (Python 3.12, pinned) | `python3.12 scripts/setup_environment.py` | yes |
| 3 | Get the dataset from the official source | `.venv/bin/python scripts/download_dataset.py` (revision `98cf38f9…`; resumable) | yes (original download) |
| 4 | Verify its identity | `.venv/bin/python scripts/verify_dataset.py` and `scripts/audit/dataset_manifest.py` | yes |
| 5 | Dataset audit | `.venv/bin/python scripts/run_audit.py` | yes |
| 6 | Preprocessing (50 partitions) | `.venv/bin/python scripts/build_aggregates.py` | yes (plus a resume test) |
| 7 | Academic split | `.venv/bin/python scripts/create_splits.py` | yes |
| 8 | Train | `scripts/train_forecasting.py`, `scripts/train_anomaly.py`, `scripts/research/forecast_quality_gate.py` | yes (re-executed in the audits) |
| 9 | Reproduce metrics | `scripts/evaluate_models.py`, `scripts/audit/training_audit.py` (\|Δ\| = 0) | yes |
| 10 | Load saved models | `scripts/verify_artifacts.py` (works without the dataset, M-06) | yes |
| 11 | Start the app | `.venv/bin/python scripts/run_application.py` | yes |
| 12 | Tests | `.venv/bin/python -m pytest` | yes |

Steps 3–9 in one resumable command: `scripts/run_full_pipeline.py` (`train.bat`). Read-only verification afterwards: `audit.bat` / `audit.ps1`.

**Pinned items:**
* seeds 42 (primary) and 43/44 (robustness);
* dataset revision and SHA-256 in `configs/dataset.yaml`;
* versions in `requirements.txt` and `requirements-lock.txt`;
* feature schemas in each artifact's `feature_schema.json`;
* preprocessing settings in `configs/preprocessing.yaml`;
* model versions in `artifacts/metadata/model_registry.json`.

The 1.6 GB dataset is **not** in git. Without it, data-dependent tests skip with a stated reason and everything else works.
