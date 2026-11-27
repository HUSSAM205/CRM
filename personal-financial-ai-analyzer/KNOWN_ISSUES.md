# Known Issues and Defect Log

## Defects found and fixed (root cause → impact → fix → regression evidence)

| # | Found | Defect | Root cause | Impact | Fix | Regression evidence |
|---|---|---|---|---|---|---|
| K-01 | 2026-11-27 | First download attempt failed (curl exit 56) | The HF download redirects to `us.aws.cdn.hf.co`, which was not on the network allowlist | No data downloaded; no partial file accepted | Added that exact host to the `crm-financial-ai` environment | Rerun downloaded 1,594,749,644 bytes; SHA-256 matches |
| K-02 | 2026-11-27 | Ledger script crashed: `diff` on a string column | Called `diff()` on a string timestamp | Script did not run; no wrong results | Plain previous-row comparison (fixed-width strings sort chronologically) | Script runs |
| K-03 | 2026-11-27 | Ledger script crashed casting IDs | Assumed every ID is `TX` + 10 digits; 200 have a suffix | Script did not run | Use the explicit 10-digit numeric part; count suffixed IDs | 200 suffixed IDs reported; 50M unique numeric parts |
| K-04 | 2026-11-27 | `NameError`-type crash after `del df` | Patch read `df.height` after deleting `df` | Script did not run | Record the row count before freeing | Script runs |
| K-05 | 2026-11-27 | **RSS grew 3.7 → 12.1 GB** in single-process ledger run | Memory not returned to the OS between partitions inside one process | Unsafe on a 16 GB laptop | One partition per child process plus RSS and system-memory guard plus checkpoints (`src/utils/resource_monitor.py`) | Peak 0.81 GB per worker; system available ≥ 14.8 GB |
| K-06 | 2026-11-27 | Global ID `n_unique` breached the 4 GB limit | Single hash set over 50M strings | Guard killed it (by design) | ID-partitioned counting (exact: equal IDs share a partition) | Peak 0.25 GB; 50,000,000 unique |
| K-07 | 2026-11-27 | Global audit breached the 4 GB limit | Per-month distinct accounts over 50M rows in one pass | Guard killed it | Counted inside account partitions (exact, since accounts are disjoint) and global work split into steps | Steps peak ≤ 1.02 GB |
| K-08 | 2026-11-27 | Amount-quantile step at 3.61 GB (above the 3 GB soft target) | Multi-currency quantile group-by plus log quantiles in one plan | Too close to the limit | One currency at a time; log quantiles on a single projected column | 0.73 GB |
| K-09 | 2026-11-27 | `monthly_coverage.csv` gained a duplicate column on rerun | Combine step re-joined onto a file it had rewritten in place (not idempotent) | Malformed report column (values identical) | Worker writes `monthly_coverage_base.csv`; combine writes the final file | Two consecutive reruns give identical files; before-fix copy kept in scratch |
| K-10 | 2026-11-27 | Benchmark B2 errored | Two unaliased `amount` expressions | One benchmark missing | Aliases | B2: 69M rows/s, 0.47 GB |
| K-11 | 2026-11-27 | Traceability summary stated unmeasured counts (77/16/26/33) | Numbers written before tallying | Inaccurate document | Replaced with the counts measured by `project_inventory.py` (69 rows: 15/22/31/1) | `project_inventory.json` |
| K-12 | 2026-11-27 | Keyword fallback produced "uncategorized" while blanks produced "Uncategorized" | Validator lowercased every non-empty category | One fallback split into two labels (budgets and charts) | Canonical label kept after normalization | `test_fallback_label_is_canonical_whatever_its_source` |
| K-13 | 2026-11-27 | `inject()` added an `amount_cents` column to inputs without one | Unconditional recompute | Schema change in a supposedly copy-only function | Recompute only if the column exists | `test_injection_keeps_amount_cents_consistent_when_present` |
| K-14 | 2026-11-27 | Hour injection crashed (empty candidate list) | Took the minimum count before excluding the current hour | Anomaly run 1 failed; no outputs written | Exclude the current hour first, then take the least used | `test_hour_injection_when_least_used_hour_is_the_current_one` |
| K-15 | 2026-11-27 | Budget editor showed unsaved suggestions **100× too high** | Used cents instead of units for the initial value | Wrong budgets shown and stored | `/100`, plus regression test | Test fails on the pre-fix file and passes after (logged in session) |
| K-16 | 2026-11-27 | Analytics page crashed for every user | `is_between("2025-12", …)` treats strings as column names | Page unusable | `pl.lit()` bounds | `test_every_page_renders_without_exception[analytics]` |
| K-17 | 2026-11-27 | The assistant could use another account's budgets | Budget hand-off key not scoped to account and currency | Wrong budget status after switching accounts | Key `active\|account\|currency` | `test_budget_page_alerts_and_editing` |
| K-18 | 2026-11-27 | Budget values displayed rounded to whole units | `NumberColumn(step=1.0)` | Shown budget differed from the applied value | `step=0.01` | UX task 7 screenshot |
| K-19 | 2026-11-27 | Rejection reasons unreadable by screen readers | Rendered inside a canvas table | Accessibility | Plain-text list | UX tasks 2–3 |
| K-20 | 2026-11-27 | Default currency after delete was the alphabetically first one (CAD) | First-of-sorted default | Confusing empty totals | Most-used currency first | UX task 5 |
| K-21 | 2026-11-27 | Test inputs with only 10 active months (test-data error, not a code defect) | Test author error | False failure | Input corrected to 13 active months; assertions unchanged | `test_model_loading.py` |

| A-01 | 2026-11-27 (final audit) | Validator crashed on an amount beyond int64 cents | Unchecked f64→i64 cast | Upload crash (P1) | `amount_out_of_range` rejection | `test_huge_amounts_are_rejected_not_crashing` |
| A-02 | final audit | HW1 S7 date filter missing (traceability had marked it PASS) | Not implemented | Requirement gap (P2) | Date-range filter on Transactions | `test_transactions_date_filter` |
| A-03 | final audit | User strings rendered as Markdown | `st.markdown` on raw text | Injection and display issue (P2) | `md_escape`; assistant via `st.text` | `test_assistant_answer_matches_dashboard` |
| A-04 | final audit | Streamlit telemetry on; tracebacks in the browser | Defaults | Privacy (P3) | `.streamlit/config.toml` | `reports/audit/static_security_scan.txt` |
| A-05 | final audit | ISO `T` timestamps rejected | Strict format | Usability (P3) | Accept `T`; offsets still rejected | `test_iso_t_separator_accepted_and_offsets_rejected_not_shifted` |
| A-06 | final audit | Deprecated `use_container_width` | API change | Warnings (P3) | `width="stretch"` | Test log has no deprecation warnings |
| A-08 | final audit | **A fresh clone could not run** (10 test collection errors, app crash, UX 0/15) | The parent repo `.gitignore` (`data/`, `*.log`) excluded `src/data/`, samples and evidence logs | Delivery broken (P0) | Re-include rules in the project `.gitignore` | `test_repository_completeness.py`; fresh clone 3 PASS |
| A-09 | final audit | Leakage test L10 failed in a fresh clone | Incomplete skip condition | Test failure without data (P2) | Skip requires the derived data | Fresh clone 3 |
| A-10 | final audit | Browser step "change a budget" flaky | Enter pressed before the grid editor registered the text (harness) | False UX failure (P3) | 600 ms settle in the script | 15/15 ×3 |
| M-01 | master audit | UX script wrote its invalid-file fixture to `/tmp` | Hardcoded POSIX path | Browser workflow would fail on Windows (P3) | `os.tmpdir()` | Browser run 21/21 |
| M-02 | master audit | **Totals of a file with ~100,000 rows near the per-row bound wrapped to a negative number** (−8,446,744,073,709,651,616 cents) | Polars int64 sums overflow silently | Wrong totals without any error (P1) | Files whose absolute amounts sum to ≥ 2⁶² cents are refused, in `ingest()` and the app upload path | `test_file_whose_totals_would_overflow_is_refused_not_wrapped`, `test_app_upload_path_refuses_overflowing_file` (fail before, pass after) |
| M-03 | master audit | Final-audit report overstated the exact-cents bound as 9,999,999,999,999.99 (the tested bound is 999,999,999,999.99) | Report-writing error | Documentation inaccuracy (P3) | Corrected in `reports/audit/financial_calculation_audit.md` | — |
| M-04 | master audit | Forecasting ML presented as the product forecast although it does not beat a zero baseline | The HW2 selection rule has no zero/median baseline | Misleading forecast (P2, product) | E2-QG quality gate; product shows the deterministic outlook; GBR labelled REJECTED (D-22) | `test_ai_page_shows_outlook_with_quality_gate_and_unusual_label`, `test_outlook_*` |
| M-05 | master audit | Anomaly alerts lacked currency, usual amount, method and limitations; label wording | Minimal table | Insufficient evidence for the user (P3) | Evidence columns, label "Unusual transaction — review recommended.", top 5 | AppTest and browser task 9 |

Audit-method corrections: A-07 (determinism now compared by content, not IPC bytes) and A-11 (stale screenshot removed). Details: `reports/final_audit/KNOWN_ISSUES.md`.

## Open issues and limitations (not defects)

| # | Issue | Status | Handling |
|---|---|---|---|
| O-01 | Timestamps are independent of the ledger order (0 of 1M accounts consistent) | Accepted, documented | D-04; `docs/KNOWN_LIMITATIONS.md` |
| O-02 | Forecast-eligible series are effectively USD-only | Accepted, documented | D-14 |
| O-03 | Hours and categories are near-uniform, so the hour-shift and rare-category anomaly scenarios are not detectable | Measured: AUC ≈ 0.5 | Reported per scenario |
| O-08 | A zero forecast beats the selected GBR on MAE and MASE (no temporal signal in the data) | Measured, reported | D-20; `docs/final_results.md` |
| O-04 | Windows install of the pinned stack not executed (only resolution verified) | NOT TESTED | `setup.ps1` / `setup.bat` provided; user runs once |
| O-05 | User laptop hardware not measurable from the cloud container | Recorded as user-reported | Budget D-11 chosen conservatively |
| O-06 | Amount distributions are identical across currencies (synthetic labels) | Accepted | Limitation |
| O-07 | 37,742 accounts have negative running balances at some point | Informational | `balance_after` unused |
| O-09 | Seed-43 resample: both GBR variants predict a constant 0 (identical metrics) | Measured (final audit) | `reports/audit/training_audit.json` |
| O-10 | All forecasting R² are negative (best −0.061); GBR beats the zero forecast on only 39.4% of series | Measured (final audit) | `reports/audit/forecasting_audit.md` |
| O-11 | Anomaly F1@k is 0.008–0.041 at about 1% FPR (k = 241) | Measured (final audit) | `reports/audit/anomaly_detection_audit.md` |
| O-12 | 0.70% of training panel cells (3,357 of 480,000) are zero-filled before the account's first record | Measured (final audit); frozen experiment not changed | `reports/audit/panel_lifespan_check.json` |
