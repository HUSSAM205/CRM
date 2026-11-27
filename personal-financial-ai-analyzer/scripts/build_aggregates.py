"""Gate 4: validate all 50M rows and build derived monthly tables, partitioned, guarded, resumable.

Writes per-partition files under data/processed/{monthly,monthly_category,series_stats} and
data/interim/rejected, plus reports/data_audit/preprocessing_summary.json.
No full second copy of the 50M clean rows is written (configs/preprocessing.yaml).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.resource_monitor import limits, run_partitions, system_snapshot  # noqa: E402

CK = ROOT / "checkpoints/preprocessing/aggregates"


def main() -> None:
    n = limits()["partitioning"]["account_partitions"]
    before = system_snapshot()
    recs = run_partitions(ROOT / "scripts/workers/aggregate_partition.py", n, CK,
                          ROOT / "logs/preprocessing/aggregate_partitions.jsonl")
    parts = [json.loads((CK / f"part_{p:03d}.json").read_text()) for p in range(n)]
    reasons: dict[str, int] = {}
    for p in parts:
        for k, v in p["reject_reasons"].items():
            reasons[k] = reasons.get(k, 0) + v
    s = lambda k: sum(p[k] for p in parts)  # noqa: E731
    summary = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "partitions": n,
               "rows_in": s("rows"), "clean": s("clean"), "rejected": s("rejected"), "reject_reasons": reasons,
               "unresolved_type_rows": s("unresolved_type_rows"), "monthly_rows": s("monthly_rows"),
               "account_currency_series": s("series"),
               "rows_accounted_for": s("clean") + s("rejected") == s("rows"),
               "max_worker_peak_rss_gb": max(r.get("peak_rss_gb", 0) for r in recs),
               "system_before": before, "system_after": system_snapshot()}
    (ROOT / "reports/data_audit/preprocessing_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    if not summary["rows_accounted_for"]:
        raise SystemExit("row accounting failed: clean + rejected != input")


if __name__ == "__main__":
    main()
