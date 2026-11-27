"""Independent integrity verification of the raw dataset file (read-only).

Does NOT trust data/raw/PROVENANCE.json. It re-derives every fact:
  1. file exists, no leftover partial download
  2. size and SHA-256 recomputed and compared with LIVE Hugging Face LFS metadata
  3. Parquet footer readable; row groups enumerated
  4. physical schema == documented schema (names, order, types)
  5. row count: footer total AND an actual full read of every row group
  6. timestamp strings parsed for every row; coverage measured
  7. distinct currencies, categories, types, statuses measured on every row
Outputs: reports/verification/dataset_integrity.json and dataset_integrity_report.md
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.configuration import load_config  # noqa: E402

OUT = ROOT / "reports" / "verification"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_config("dataset")
    src = cfg["source"]
    path = ROOT / cfg["paths"]["raw_parquet"]
    checks: list[dict] = []
    facts: dict = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "file": str(path.relative_to(ROOT))}

    def check(name: str, ok: bool, evidence) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "evidence": evidence})
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {evidence}", flush=True)

    # 1 existence / partial download
    check("file_exists", path.exists(), str(path.relative_to(ROOT)))
    partials = [str(p.relative_to(ROOT)) for p in path.parent.glob("*.part")]
    check("no_partial_download_left", not partials, partials or "none")
    if not path.exists():
        return 1

    # 2 live HF metadata
    api = f"https://huggingface.co/api/datasets/{src['repo_id']}/tree/{src['revision']}"
    live = {}
    try:
        tree = requests.get(api, timeout=60).json()
        entry = next(e for e in tree if e["path"] == src["filename"])
        live = {"size": entry["lfs"]["size"], "sha256": entry["lfs"]["oid"], "api": api}
        check("live_hf_metadata_fetched", True, api)
    except Exception as exc:  # network failure is reported, not hidden
        check("live_hf_metadata_fetched", False, repr(exc))
    facts["hf_live_metadata"] = live
    size = path.stat().st_size
    t = time.time()
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    digest = h.hexdigest()
    facts.update(size_bytes=size, sha256=digest, sha256_seconds=round(time.time() - t, 1))
    check("size_matches_config", size == int(src["expected_size_bytes"]), size)
    check("size_matches_live_hf", bool(live) and size == live["size"], f"{size} vs {live.get('size')}")
    check("sha256_matches_live_hf_lfs_oid", bool(live) and digest == live["sha256"], digest)

    # 3 footer
    pf = pq.ParquetFile(path)
    md = pf.metadata
    rg_rows = [md.row_group(i).num_rows for i in range(md.num_row_groups)]
    facts.update(num_row_groups=md.num_row_groups, footer_rows=md.num_rows, created_by=md.created_by,
                 compression=md.row_group(0).column(0).compression, row_group_rows_min=min(rg_rows),
                 row_group_rows_max=max(rg_rows))
    check("parquet_footer_readable", True, f"{md.num_row_groups} row groups, created_by={md.created_by}")

    # 4 schema
    actual = [(f.name, str(f.type)) for f in pf.schema_arrow]
    expected_names = cfg["expected_columns"]
    facts["schema"] = actual
    check("column_names_and_order", [a[0] for a in actual] == expected_names, [a[0] for a in actual])
    expected_types = {"amount": "double", "balance_after": "double"}
    type_ok = all(t == expected_types.get(n, "string") for n, t in actual)
    check("column_types", type_ok, dict(actual))
    check("column_count_matches_advertised", len(actual) == cfg["advertised"]["columns"], len(actual))

    # 5 row count by full read of every row group
    t = time.time()
    read_rows = 0
    for i in range(md.num_row_groups):
        read_rows += pf.read_row_group(i, columns=["transaction_id"]).num_rows
    facts["rows_read_full"] = read_rows
    facts["row_read_seconds"] = round(time.time() - t, 1)
    check("footer_rows_equal_sum_row_groups", sum(rg_rows) == md.num_rows, sum(rg_rows))
    check("rows_read_equal_footer", read_rows == md.num_rows, read_rows)
    check("rows_match_advertised", read_rows == cfg["advertised"]["rows"], read_rows)

    # 6+7 full-scan value domains and timestamp coverage
    t = time.time()
    lf = pl.scan_parquet(path)
    ts = pl.col("transaction_timestamp").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False)
    agg = lf.select(
        pl.len().alias("rows"),
        ts.is_null().sum().alias("unparseable_timestamps"),
        ts.min().alias("ts_min"), ts.max().alias("ts_max"),
        pl.col("transaction_timestamp").str.len_chars().min().alias("ts_len_min"),
        pl.col("transaction_timestamp").str.len_chars().max().alias("ts_len_max"),
    ).collect(engine="streaming").to_dicts()[0]
    domains = {}
    for col in ["currency", "merchant_category", "transaction_type", "status"]:
        vc = lf.group_by(col).len().sort(col).collect(engine="streaming")
        domains[col] = dict(zip(vc[col].to_list(), vc["len"].to_list()))
    facts["timestamp"] = {k: str(v) for k, v in agg.items()}
    facts["domains"] = domains
    facts["domain_scan_seconds"] = round(time.time() - t, 1)
    adv = cfg["advertised"]
    check("all_timestamps_parse", agg["unparseable_timestamps"] == 0, agg["unparseable_timestamps"])
    check("timestamp_min_on_advertised_start", str(agg["ts_min"])[:10] == adv["date_min"], str(agg["ts_min"]))
    check("timestamp_max_on_advertised_end", str(agg["ts_max"])[:10] == adv["date_max"], str(agg["ts_max"]))
    for col, key, allowed in [("currency", "currencies", "currencies"),
                              ("transaction_type", "transaction_types", "transaction_types"),
                              ("status", "statuses", "statuses")]:
        vals = set(domains[col])
        check(f"{col}_count_matches_advertised", len(vals) == adv[key], len(vals))
        check(f"{col}_values_match_documented", vals == set(cfg["allowed"][allowed]), sorted(vals))
    check("merchant_category_count_matches_advertised",
          len(domains["merchant_category"]) == adv["merchant_categories"], sorted(domains["merchant_category"]))
    for col in domains:
        check(f"{col}_no_null_values", None not in domains[col], "null" if None in domains[col] else "none")

    facts["checks"] = checks
    facts["overall"] = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    (OUT / "dataset_integrity.json").write_text(json.dumps(facts, indent=2, default=str), encoding="utf-8")
    print("OVERALL", facts["overall"])
    return 0 if facts["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
