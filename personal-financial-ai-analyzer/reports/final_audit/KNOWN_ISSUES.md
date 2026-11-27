# Known Issues: final audit

Priority scale:
* **P0:** delivery broken.
* **P1:** crash or incorrect result on a required path.
* **P2:** a requirement gap or security weakness.
* **P3:** minor.

The full project defect log (K-01..K-21 plus these) is in [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md).

## Defects found by this audit

| ID | P | Defect | Root cause | Fix | Regression evidence | Status |
|---|---|---|---|---|---|---|
| A-08 | **P0** | A fresh clone could not run: tests had 10 collection errors, the app crashed, UX 0/15 | The parent repo `.gitignore` (`data/`, `*.log`) excluded `src/data/`, `data/samples/`, `data/external/` and the evidence logs | Re-include rules in the project `.gitignore` | `tests/regression/test_repository_completeness.py`; fresh clone 3 PASS | Fixed (`b64e65b`) |
| A-01 | **P1** | Validator crashed on an amount beyond the int64-cents range (`92233720368547758.07`) | Unchecked f64→i64 cast | Rejection reason `amount_out_of_range` (\|x\| > 10¹²) | `test_huge_amounts_are_rejected_not_crashing` (fails before, passes after) | Fixed (`157bf5d`) |
| A-02 | P2 | HW1 S7 date filter missing (the traceability PASS was wrong) | Not implemented | Date-range filter on Transactions | `test_transactions_date_filter` | Fixed |
| A-03 | P2 | User strings rendered as Markdown (file name, categories, questions) | `st.markdown` on raw text | `md_escape`; assistant answers via `st.text` | `test_assistant_answer_matches_dashboard` (checks `at.text`) | Fixed |
| A-09 | P2 | Leakage test L10 failed in a fresh clone | Skip condition checked only the injections, not the derived data file | Skip requires both | Fresh clone 3: correctly skipped | Fixed (`0da7bbb`) |
| A-04 | P3 | Streamlit usage telemetry on; tracebacks shown in the browser | Defaults | `.streamlit/config.toml` | `static_security_scan.txt` | Fixed |
| A-05 | P3 | ISO `2026-01-05T10:00:00` timestamps rejected | Strict format only | Accept the `T` separator; offsets still rejected | `test_iso_t_separator_accepted_and_offsets_rejected_not_shifted` (fails before, passes after) | Fixed |
| A-06 | P3 | Deprecated `use_container_width` | Streamlit API change | `width="stretch"` | No deprecation warnings in the test log | Fixed |
| A-10 | P3 (test harness) | Browser step "change a budget" flaky | Enter pressed before the grid editor registered the typed text | 600 ms settle in the script; the app is unchanged (a standalone reproduction disproved an app bug) | 15/15 in 3 consecutive runs, incl. fresh clone 3 | Fixed |
| A-07 | — (audit method) | Determinism check reported a false difference | Byte-hashing IPC chunk layouts | Compare content (`DataFrame.equals` and row hashes) | 9/9 identical | Corrected |
| A-11 | P3 | Stale screenshot from a failed run | Leftover file | Removed | — | Fixed |

## Scientific findings (not defects; not hidden)

| ID | Finding | Evidence |
|---|---|---|
| F-1 | A constant **zero** forecast beats the selected GBR on MAE and MASE (test 25.374 vs 27.194). GBR beats zero on only 39.4% of series | `reports/audit/training_audit.json` |
| F-2 | Seed-43 resample: both GBR variants predict a constant 0 (which explains their identical metrics) | same |
| F-3 | All forecasting R² are negative (best −0.061) | same |
| F-4 | Anomaly F1@k is 0.008–0.041 at about 1% FPR. Not usable as a fraud detector; review candidates only | same |
| F-5 | 0.70% of training panel cells are zero-filled before the account's first record (cannot be told apart from inactivity) | `reports/audit/panel_lifespan_check.json` |

## Open items

* **Windows install: NOT TESTED** (`setup.bat` / `setup.ps1`).
* **User laptop performance: not measured** (HW1 P5 PARTIAL).
* **No human-participant usability study.**
* Streamlit has no authentication (local use only).
