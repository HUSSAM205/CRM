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

## Open issues and limitations (not defects)

| # | Issue | Status | Handling |
|---|---|---|---|
| O-01 | Timestamps are independent of the ledger order (0 of 1M accounts consistent) | Accepted, documented | D-04; `docs/limitations.md` |
| O-02 | Forecast-eligible series are effectively USD-only | Accepted, documented | D-14 |
| O-03 | Hours and categories are near-uniform, so the hour-shift and rare-category anomaly scenarios may be weakly detectable | Expected; will be measured | D-09; reported per scenario |
| O-04 | Windows install of the pinned stack not executed (only resolution verified) | NOT TESTED | `setup.ps1` / `setup.bat` provided; user runs once |
| O-05 | User laptop hardware not measurable from the cloud container | Recorded as user-reported | Budget D-11 chosen conservatively |
| O-06 | Amount distributions are identical across currencies (synthetic labels) | Accepted | Limitation |
| O-07 | 37,742 accounts have negative running balances at some point | Informational | `balance_after` unused |
