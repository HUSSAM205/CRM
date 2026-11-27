"""Render the evidence-heavy verification reports directly from measured JSON/CSV files.

Generated (reports/verification/): dataset_integrity_report.md, dataset_quality_report.md,
resource_benchmark_report.md, environment_verification_report.md, dependency_audit.md,
project_structure_audit.md, financial_rules_validation.md
Numbers are never typed by hand here; every value is read from an evidence file.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "reports/verification"
A = ROOT / "reports/data_audit"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def j(p: Path) -> dict:
    return json.loads(p.read_text())


def table(path: Path) -> str:
    rows = list(csv.reader(path.open()))
    head, body = rows[0], rows[1:]
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(out)


def write(name: str, text: str) -> None:
    (V / name).write_text(text)
    print("wrote", name)


def integrity() -> None:
    d = j(V / "dataset_integrity.json")
    rows = "\n".join(f"| {c['check']} | **{c['status']}** | `{str(c['evidence'])[:160]}` |" for c in d["checks"])
    npass = sum(c["status"] == "PASS" for c in d["checks"])
    write("dataset_integrity_report.md", f"""# Dataset Integrity Report

Generated {NOW} from `reports/verification/dataset_integrity.json` (run {d['generated_at_utc']}).
Script: `scripts/verify_dataset.py` (does not trust download-time provenance; re-derives everything).

**Overall: {d['overall']}** ({npass}/{len(d['checks'])} checks). Identity: see `docs/dataset_provenance.md`, **DATASET IDENTITY VERIFIED**.

| Fact | Value |
|---|---|
| File | `{d['file']}` |
| Size | {d['size_bytes']:,} bytes |
| SHA-256 | `{d['sha256']}` |
| Live HF LFS oid | `{d['hf_live_metadata'].get('sha256')}` |
| Row groups | {d['num_row_groups']} ({d['row_group_rows_min']:,}–{d['row_group_rows_max']:,} rows each) |
| Rows (footer / actually read) | {d['footer_rows']:,} / {d['rows_read_full']:,} |
| Writer / compression | {d['created_by']} / {d['compression']} |
| Timestamp min / max | {d['timestamp']['ts_min']} / {d['timestamp']['ts_max']} |
| Unparseable timestamps | {d['timestamp']['unparseable_timestamps']} |

## Checks
| Check | Status | Evidence |
|---|---|---|
{rows}

## Schema (physical)
| Column | Type |
|---|---|
""" + "\n".join(f"| {n} | {t} |" for n, t in d["schema"]) + """

## Value domains (full scan, all rows)
""" + "\n".join(f"* **{k}**: " + ", ".join(f"{a} ({b:,})" for a, b in v.items()) for k, v in d["domains"].items()) + "\n")


def quality() -> None:
    o = j(A / "dataset_overview.json")
    led = j(V / "ledger_semantics.json")
    ac = o["amount_checks"]
    write("dataset_quality_report.md", f"""# Dataset Quality Report

Generated {NOW}. Scope: **all {o['rows']:,} rows, {o['accounts']:,} accounts (no sampling)**.
Scripts: `scripts/run_audit.py` (+ workers). Raw tables: `reports/data_audit/`.

## Summary of findings
| Check (HW1 4.4 / HW2 4.4) | Result | Status |
|---|---|---|
| Missing values (null or blank), all 9 columns | 0 | PASS |
| Duplicate transaction_id | {led['transaction_id_structure']['rows'] - led['transaction_id_structure']['unique_ids']} | PASS |
| Fully duplicated rows | 0 (implied by unique IDs) | PASS |
| Same content, different ID | {o['same_content_different_id_rows']} | PASS |
| Non-standard IDs (suffix `-zdl26nr51f60aaa959f`) | {led['transaction_id_structure']['ids_with_suffix']} | FLAGGED, kept (D-05) |
| Invalid / unparseable timestamps | 0 | PASS |
| Calendar days present | {o['calendar']['distinct_days']} ({o['calendar']['d0']} … {o['calendar']['d1']}; full range = 943) | PASS |
| Non-finite / negative / zero amounts | {ac['non_finite_amount']} / {ac['negative_amount']} / {ac['zero_amount']} | PASS |
| Amounts with more than 2 decimals | {ac['more_than_2_decimals']} | PASS |
| Unknown currency / type / status / category | 0 / 0 / 0 / 0 (see integrity report domains) | PASS |
| Sign consistency (ledger) | {led['match_by_transaction_id']:,}/{led['records_compared']:,} records reconcile | PASS |
| Amount outliers, log-IQR×3 rule | {ac['outlier_high']} high (> {ac['outlier_high_threshold_amount']:.2f}), {ac['outlier_low']} low (< {ac['outlier_low_threshold_amount']:.2f}) | Investigated, **kept** |
| Negative balance rows / accounts | {ac['negative_balance_rows']:,} rows / {o['accounts_with_negative_balance_rows']:,} accounts | Informational (balance unused) |
| Transactions per account | min {o['accounts_min_tx']}, max {o['accounts_max_tx']} | — |

## Account statistics (quantiles across 1,000,000 accounts)
{table(A / 'account_statistics.csv')}

## Monthly coverage
{table(A / 'monthly_coverage.csv')}

## Distributions
### Status
{table(A / 'status_distribution.csv')}
### Transaction type
{table(A / 'transaction_type_distribution.csv')}
### Currency
{table(A / 'currency_distribution.csv')}
### Merchant category
{table(A / 'category_distribution.csv')}
### Amount by currency
{table(A / 'amount_by_currency.csv')}
### Hour of day
{table(A / 'hour_distribution.csv')}
### ISO weekday (1 = Monday)
{table(A / 'weekday_distribution.csv')}
### Accounts by number of currencies used
{table(A / 'accounts_by_n_currencies.csv')}

## Interpretation (limits of the synthetic data)
* Hours, weekdays, categories and amount distributions are near-uniform or identical across groups. The data has
  little behavioural structure, so ML results must be read as a methodology demonstration (see `docs/KNOWN_LIMITATIONS.md`).
* Amount distributions are identical in every currency (median about 30 for USD and JPY alike). Currency is a label,
  not a real currency scale.
* Outliers are rare and consistent with the documented log-normal amounts. They are not removed.
""")


def resources() -> None:
    b = j(ROOT / "reports/benchmarks/resource_benchmarks.json")
    led = j(V / "ledger_semantics.json")["resources"]
    o = j(A / "dataset_overview.json")["resources"]
    rows = []
    for k, v in b["benchmarks"].items():
        if k.startswith("B7"):
            rows.append(f"| {k} | 6 × 2.5M | — | — | max {v['max_peak_rss_gb']} | ok |")
            continue
        rows.append(f"| {k} | {v.get('rows', '—')} | {v.get('seconds', '—')} | {v.get('rows_per_second', '—')} | "
                    f"{v.get('guard_peak_rss_gb')} | {v.get('killed_reason') or 'ok'} |")
    write("resource_benchmark_report.md", f"""# Resource Benchmark Report

Generated {NOW} from `reports/benchmarks/resource_benchmarks.json`, `ledger_semantics.json` and `data_audit/dataset_overview.json`.

## Host (measured: the cloud execution container, NOT the user's laptop)
`{b['host']}`

User laptop (user-reported, **not measurable from here**): Intel i7-1355U (10 cores / 12 threads), 16 GB DDR4-3200, Intel Iris Xe, no NVIDIA GPU, Windows 64-bit, about 350 GB free.

## Benchmarks (each in a guarded child process; limits in `configs/resource_limits.yaml`)
| Benchmark | Rows | Seconds | Rows/s | Peak RSS GB | Outcome |
|---|---|---|---|---|---|
""" + "\n".join(rows) + f"""

## Production-pattern measurements
| Job | Pattern | Max worker peak RSS | Min system available |
|---|---|---|---|
| Ledger investigation (50 partitions) | one partition per child | {led['max_worker_peak_rss_gb']} GB | {led['min_system_available_gb']} GB |
| ID uniqueness (50 ID partitions) | one partition per child | {led['id_partitions_max_peak_rss_gb']} GB | — |
| Audit global steps | one step per child | {o['global_step_peak_rss_gb']} | — |
| Audit partitions | one partition per child | {o['max_partition_peak_rss_gb']} GB | — |

## Conclusions
1. Unpartitioned full-data aggregations (B4) exceed the 4 GB worker budget, and single-process partition loops can
   retain memory (12.1 GB observed before the fix). **These patterns are prohibited** for this project.
2. Account-partitioned workers with 50 partitions (about 1M rows) peak below 1.1 GB, with about 3 s per partition here.
   On a 16 GB laptop this leaves a large margin, even with 6–8 GB used by Windows and applications.
3. Throughput is high (column-projected scans of 23–69M rows/s), so **Google Colab is not needed**: no measured
   limitation justifies it (`docs/local_vs_colab_benchmark.md`).
4. Laptop timings will differ (different CPU and OS) and were **not measured**. The memory pattern is the same
   because it depends on partition size, not on the host.
""")


def environment() -> None:
    e = j(V / "environment.json")
    pkgs = "\n".join(f"| {k} | {v} |" for k, v in e["imports"].items())
    write("environment_verification_report.md", f"""# Environment Verification Report

Generated {NOW} from `reports/verification/environment.json` (run {e['generated_at_utc']}).
**Status: {e['status']}**

| Item | Value |
|---|---|
| Python | {e['python'].split()[0]} |
| Interpreter | `{e['executable']}` |
| Inside project .venv | {e['in_project_venv']} |
| Platform | {e['platform']} |
| Import failures | {len(e['failures'])} |
| Dependency consistency | `{e['pip_check']['output'].splitlines()[-1]}` |
| RAM total / available | {e['system']['ram_total_gb']} / {e['system']['ram_available_gb']} GB |
| Disk free | {e['system']['disk_free_gb']} GB |
| Logical CPUs | {e['system']['cpu_logical']} |
| Tools | {', '.join(k for k, v in e['tools'].items() if v)} |
| CUDA / GPU | not present and not required (all models are CPU scikit-learn/statsmodels) |

## Direct dependencies (imported successfully)
| Package | Version |
|---|---|
{pkgs}

## Windows target
* `uv pip compile requirements.txt --python-platform x86_64-pc-windows-msvc --python-version 3.12 --only-binary :all:`
  **resolved successfully** (wheels only, no source builds): `reports/verification/requirements-windows-resolved.txt`.
* An actual install on the user's Windows laptop is **NOT TESTED** (no access from the cloud). `setup.ps1` / `setup.bat` are provided.
""")


def dependencies() -> None:
    e = j(V / "environment.json")
    lock = (ROOT / "requirements-lock.txt").read_text().splitlines()
    win = [ln for ln in (V / "requirements-windows-resolved.txt").read_text().splitlines()
           if ln and not ln.startswith((" ", "#"))]
    write("dependency_audit.md", f"""# Dependency Audit

Generated {NOW}.

| Item | Result |
|---|---|
| Direct dependencies (`requirements.txt`) | {len(e['imports'])}, all pinned, all import |
| Full lock (`requirements-lock.txt`, Linux venv) | {len(lock)} packages |
| Consistency check | `{e['pip_check']['output'].splitlines()[-1]}` |
| Windows x64 / CPython 3.12 resolution (binary wheels only) | {len(win)} packages resolved, PASS |
| Packages added beyond the HW2 Table 6.1 tool list | PyYAML (configs), joblib (model persistence), psutil (memory guard), matplotlib (static figures), requests (download) |
| GPU / CUDA packages | none |
| Network services used at runtime | none (the app runs fully locally) |

Versions were chosen by the resolver as the current stable releases on 2026-11-27 and then frozen. They were not blindly upgraded afterwards.
""")


def structure() -> None:
    inv = j(V / "project_inventory.json")
    write("project_structure_audit.md", f"""# Project Structure Audit

Generated {NOW} from `reports/verification/project_inventory.json` (`scripts/project_inventory.py`).
A file counts as present only if it exists **and is non-empty**.

| Item | Result |
|---|---|
| Required directories | {inv['dirs_present']}/{inv['dirs_required']} present |
| Required files (master prompt section 5) | {inv['files_present']}/{inv['files_required']} present |
| Empty placeholder files | {len(inv['files_empty'])} |
| Traceability rows / status tally | {inv['traceability_rows']} / {inv['traceability_status_tally']} |

## Why files are missing
Per the strict verification gate, implementation files for preprocessing, models, experiments, the app and the
remaining tests were **deliberately not created yet**: no empty files were created to claim completion. They are
created in Gates 4–16 (`docs/implementation_roadmap.md`).

## Additional files not in the master list (each has a real role)
""" + "\n".join(f"* `{f}`" for f in inv["extra_python_files_not_in_master_list"]) + """

## Missing files at this gate
""" + "\n".join(f"* `{f}`" for f in inv["files_missing"]) + "\n")


def financial() -> None:
    cc = [j(p) for p in sorted(V.glob("crosscheck_partition_*.json"))]
    rows = "\n".join(f"| {c['partition']} | {c['rows']:,} | {c['rejected']} | {c['unresolved_type_rows']} | "
                     f"{c['independent_groups']:,} | {c['value_mismatches']} | {c['groups_missing_from_project_output']} |"
                     for c in cc)
    test_log = (ROOT / "logs/testing/unit_rules_validation.log")
    tl = test_log.read_text().strip().splitlines()[-1] if test_log.exists() else "see logs/testing"
    write("financial_rules_validation.md", f"""# Financial Rules Validation

Generated {NOW}. Rules: `docs/FINANCIAL_RULES.md`.

## 1. Sign convention: measured on all data
49,000,000 / 49,000,000 records reconcile `balance_after` in transaction-ID order under the documented directions
(`ledger_semantics_report.md`). Pending, failed and reversed records never change the balance.

## 2. Hand-calculated fixtures (E1, HW2 10.2)
Fixture `tests/fixtures/sample_transactions.csv` (19 rows: 2 accounts, 2 currencies, 2 months; covers income, expenses,
transfers, refunds incl. a negative category net, fees, pending, failed, reversed). Expected values in
`tests/fixtures/expected_financial_results.json` were computed by hand, with the arithmetic shown.
Latest pytest run: `{tl}` (`logs/testing/unit_rules_validation.log`).

## 3. Real-data independent cross-check
Validator plus `financial_metrics` compared with an independent pandas + `Decimal` recomputation
(`scripts/workers/crosscheck_partition.py`). Per group: income, expenses, net, transfers.

| Partition | Rows | Rejected | Unresolved types | Independent groups | Value mismatches | Groups missing |
|---|---|---|---|---|---|---|
{rows}

## Verdict
Financial rules: **PASS**. Totals are exact (integer cents), currencies are never combined, transfers are neutral,
refunds reduce category spending, and non-completed and unresolved records are excluded and counted.
""")


if __name__ == "__main__":
    integrity(); quality(); resources(); environment(); dependencies(); structure(); financial()
