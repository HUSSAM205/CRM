# Repository Baseline (master audit 3, Phase 0)

Recorded on 2026-11-27, before any change in this audit.

| Item | Value |
|---|---|
| Branch | `claude/hopeful-noether-t6vfi7` |
| Latest commit | `2eab39451cde463fac5442e88098959a4adcda7b` (2026-11-27T12:13:33Z) |
| Remote | in sync with `origin/claude/hopeful-noether-t6vfi7`: 0 ahead, 0 behind |
| Commits on branch | 40 |
| Tracked files (project) | 1,048 |
| Python | CPython 3.12.3 (`.venv`) |
| Execution environment | Linux cloud container. **Not** the user's Windows laptop |

## Uncommitted work at the start (preserved, not discarded)

These are edits from the academic submission review, made earlier in this session:
* `README.md`
* `docs/ACADEMIC_RESULTS_UPDATE_PROPOSAL.md`, `docs/FORECASTING.md`, `docs/REPRODUCIBILITY.md`, `docs/WINDOWS_INSTALLATION.md`
* `reports/final_evidence/facts.json`, `reports/final_evidence/results_tables.md` (regenerated)
* `reports/final_master_audit/FINAL_MASTER_AUDIT.md`, `PHASE_13_ACADEMIC_TRACEABILITY.md`
* New: `reports/final_master_audit/ACADEMIC_SUBMISSION_REVIEW.md`
* `logs/application/app.log`: tracked log, appended by the test runs

## Data present locally (never in git)

| Path | Content |
|---|---|
| `data/raw/transactions_50M.parquet` | Dataset A, 1.6 GB, plus `PROVENANCE.json` |
| `data/processed/` | monthly panels, splits, series statistics |
| `data/supplementary/personaledger/` | Dataset B, 276 MB, plus derived panels |
| `data/samples/` | the demo CSVs (tracked), `ATTRIBUTION.md` |

## Saved models (`artifacts/`, registry `artifacts/metadata/model_registry.json`)

* `forecasting/gbr`, `forecasting/gbr_seasonal` and `forecasting/selection`: E2 (HW2) original, `v_20261127T033218Z`.
* `forecasting/outlook`: the deterministic product outlook (D-22).
* `forecasting/gbr_personaledger`: E2-B (supplementary).
* `anomaly/robust_zscore`, `anomaly/isolation_forest_per_account` and `anomaly/isolation_forest_global`: E3 (HW2) original, `v_20261127T033806Z`.

## Test baseline

* Development: 196 passed, 0 failed, 0 skipped (at `09c1ce4`). The suite was re-run at the start of this audit with the uncommitted doc edits: all passed.
* Fresh clone: 192 passed / 4 skipped (data-dependent; see `reports/final_master_audit/TEST_RESULTS.md`).
* Browser: 24/24 scripted tasks.

## Original submissions

* HW1 PDF: SHA-256 `2edba1b1…f439`.
* HW2 PDF: SHA-256 `09c50657…2d43`.
* Both were read only and are unchanged (`reports/final_master_audit/ACADEMIC_SUBMISSION_REVIEW.md`).
