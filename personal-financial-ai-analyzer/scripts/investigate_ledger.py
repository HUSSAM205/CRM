"""Ledger-semantics investigation over EVERY account — resource-safe driver (read-only).

Hypothesis tested: when one account's records are ordered by the numeric part of transaction_id,
    delta(balance_after) == direction(type) * amount   for completed records
    delta(balance_after) == 0                          otherwise
(exact integer cents; the first record of each account has no predecessor and is excluded).
The same test is repeated with records ordered by transaction_timestamp.

Each of 50 account partitions runs in its own guarded subprocess (scripts/workers/ledger_partition.py)
with RSS/system-memory limits from configs/resource_limits.yaml and a checkpoint per partition, so
the run is resumable and memory is returned to the OS after every partition.
Outputs: reports/verification/ledger_semantics.json, ledger_by_transaction_id.csv, ledger_by_timestamp.csv
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.resource_monitor import limits, run_partitions, system_snapshot  # noqa: E402

OUT = ROOT / "reports/verification"
CK = ROOT / "checkpoints/verification/ledger"
CK_IDS = ROOT / "checkpoints/verification/ledger_ids"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n_parts = limits()["partitioning"]["account_partitions"]
    before = system_snapshot()
    recs = run_partitions(ROOT / "scripts/workers/ledger_partition.py", n_parts, CK,
                          ROOT / "logs/execution/ledger_partitions.jsonl")
    parts = [json.loads((CK / f"part_{p:03d}.json").read_text(encoding="utf-8")) for p in range(n_parts)]

    id_recs = run_partitions(ROOT / "scripts/workers/id_partition.py", n_parts, CK_IDS,
                             ROOT / "logs/execution/ledger_id_partitions.jsonl")
    idp = [json.loads((CK_IDS / f"part_{p:03d}.json").read_text(encoding="utf-8")) for p in range(n_parts)]
    ids = {k: sum(x[k] for x in idp) for k in ["rows", "ids_TX_plus_10_digits", "ids_with_suffix",
                                                "unique_ids", "unique_numeric_parts"]}
    ids["min_numeric"] = min(x["min_numeric"] for x in idp)
    ids["max_numeric"] = max(x["max_numeric"] for x in idp)
    ids["numeric_range_size"] = ids["max_numeric"] - ids["min_numeric"] + 1

    def combine(key: str) -> pl.DataFrame:
        rows = [r for p in parts for r in p[key]]
        return (pl.DataFrame(rows).group_by("transaction_type", "status")
                  .agg(pl.col("n").sum(), pl.col("match").sum())
                  .with_columns((pl.col("match") / pl.col("n")).alias("match_rate"))
                  .sort("transaction_type", "status"))

    by_id, by_ts = combine("per_type_by_id"), combine("per_type_by_timestamp")
    by_id.write_csv(OUT / "ledger_by_transaction_id.csv")
    by_ts.write_csv(OUT / "ledger_by_timestamp.csv")
    s = lambda k: sum(p[k] for p in parts)  # noqa: E731
    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "partitions": n_parts, "rows": s("rows"), "accounts": s("accounts"),
        "records_compared": int(by_id["n"].sum()),
        "match_by_transaction_id": int(by_id["match"].sum()),
        "match_by_timestamp": int(by_ts["match"].sum()),
        "match_rate_by_transaction_id": float(by_id["match"].sum() / by_id["n"].sum()),
        "match_rate_by_timestamp": float(by_ts["match"].sum() / by_ts["n"].sum()),
        "accounts_fully_reconciled_by_id": s("accounts_fully_reconciled_by_id"),
        "accounts_fully_reconciled_by_timestamp": s("accounts_fully_reconciled_by_timestamp"),
        "accounts_id_order_equals_time_order": s("accounts_id_order_equals_time_order"),
        "accounts_with_negative_balance": s("accounts_with_negative_balance"),
        "accounts_multi_currency_single_balance": s("accounts_multi_currency_single_balance"),
        "transaction_id_structure": ids,
        "resources": {
            "system_before": before, "system_after": system_snapshot(),
            "max_worker_peak_rss_gb": max(r["peak_rss_gb"] for r in recs if "peak_rss_gb" in r),
            "min_system_available_gb": min(r["min_system_available_gb"] for r in recs
                                           if "min_system_available_gb" in r),
            "id_partitions_max_peak_rss_gb": max(r["peak_rss_gb"] for r in id_recs if "peak_rss_gb" in r),
            "total_worker_seconds": round(sum(r.get("seconds", 0) for r in recs), 1),
            "limits": limits(),
        },
    }
    (OUT / "ledger_semantics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "resources"}, indent=2))
    print(json.dumps(result["resources"], indent=2, default=str))


if __name__ == "__main__":
    main()
