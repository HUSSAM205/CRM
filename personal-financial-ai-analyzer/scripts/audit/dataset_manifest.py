"""Master audit: dataset manifest and machine-readable quality report.

Re-hashes the local file and re-reads its Parquet footer now; every other figure is taken from the
full-data audit outputs (all 50M rows, no sampling) in reports/data_audit/ and reports/verification/,
which were produced by memory-guarded partitioned scans of this same file (same SHA-256).
Writes reports/final_master_audit/DATASET_MANIFEST.json and DATA_QUALITY_REPORT.json.
"""
from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/transactions_50M.parquet"
OUT = ROOT / "reports/final_master_audit"
DA, VER = ROOT / "reports/data_audit", ROOT / "reports/verification"


def rows(name: str) -> list[dict]:
    return list(csv.DictReader(open(DA / name, encoding="utf-8")))


def main() -> None:
    t = time.time()
    h = hashlib.sha256()
    with open(RAW, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    md = pq.ParquetFile(RAW).metadata
    integ = json.loads((VER / "dataset_integrity.json").read_text(encoding="utf-8"))
    overview = json.loads((DA / "dataset_overview.json").read_text(encoding="utf-8"))
    src_cfg = __import__("yaml").safe_load((ROOT / "configs/dataset.yaml").read_text(encoding="utf-8"))["source"]
    sha = h.hexdigest()
    manifest = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset": "Free Financial Transactions 50M", "provider": "ziadatalabs",
        "source": "https://huggingface.co/datasets/ziadatalabs/FreeFinancialTransactions50M",
        "file": "transactions_50M.parquet", "local_path": "data/raw/transactions_50M.parquet (not in git)",
        "revision": src_cfg["revision"], "license": src_cfg["license"],
        "license_note": "Non-commercial use only. Commercial distribution of the data or of models trained on it "
                        "is a legal question outside this project and requires independent verification (BLOCKED).",
        "size_bytes": RAW.stat().st_size, "sha256_now": sha,
        "sha256_expected": src_cfg["expected_sha256"], "sha256_matches": sha == src_cfg["expected_sha256"],
        "size_matches": RAW.stat().st_size == src_cfg["expected_size_bytes"],
        "parquet": {"rows": md.num_rows, "row_groups": md.num_row_groups, "columns": md.num_columns,
                    "created_by": md.created_by,
                    "schema": {md.schema.column(i).name: md.schema.column(i).physical_type for i in range(md.num_columns)}},
        "seconds": round(time.time() - t, 1),
    }
    quality = {
        "scope": overview["scope"], "rows": overview["rows"], "columns": overview["columns"],
        "accounts": overview["accounts"], "calendar": overview["calendar"],
        "transactions_per_account": {"min": overview["accounts_min_tx"], "max": overview["accounts_max_tx"]},
        "missing_values": {r["column"]: {"null": int(r["null"]), "empty_string": int(r["empty_string"])}
                           for r in rows("missing_values.csv")},
        "duplicates": {r["check"]: int(r["value"]) for r in rows("duplicate_analysis.csv")},
        "amount_checks": overview["amount_checks"],
        "distributions": {
            "currency": {r["currency"]: int(r["rows"]) for r in rows("currency_distribution.csv")},
            "merchant_category": {r[list(r)[0]]: int(r["rows"]) for r in rows("category_distribution.csv")},
            "transaction_type": {r["transaction_type"]: int(r["rows"]) for r in rows("transaction_type_distribution.csv")},
            "status": {r["status"]: int(r["rows"]) for r in rows("status_distribution.csv")},
        },
        "rows_by_month": {r["month"]: int(r["rows"]) for r in rows("monthly_coverage.csv")},
        "accounts_with_negative_balance_rows": overview["accounts_with_negative_balance_rows"],
        "advertised_vs_measured": {k: {"advertised": v, "measured": {
            "rows": overview["rows"], "columns": overview["columns"],
            "currencies": len(rows("currency_distribution.csv")),
            "merchant_categories": len(rows("category_distribution.csv")),
            "transaction_types": len(rows("transaction_type_distribution.csv")),
            "statuses": len(rows("status_distribution.csv")),
            "date_min": overview["calendar"]["d0"], "date_max": overview["calendar"]["d1"]}[k]}
            for k, v in overview["advertised"].items()},
        "integrity_checks": {"passed": sum(1 for c in integ["checks"] if c["status"] == "PASS"),
                             "total": len(integ["checks"]), "overall": integ["overall"]},
        "sources": ["reports/data_audit/*", "reports/verification/dataset_integrity.json",
                    "reports/verification/ledger_semantics.json"],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "DATASET_MANIFEST.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    (OUT / "DATA_QUALITY_REPORT.json").write_text(json.dumps(quality, indent=1), encoding="utf-8")
    print(json.dumps(manifest, indent=1)[:1500]); print(json.dumps(quality["advertised_vs_measured"]), quality["integrity_checks"])


if __name__ == "__main__":
    main()
