"""Full-dataset audit (HW1 4.4 / HW2 4.4) — every row, no sampling, memory-guarded, resumable.

Steps (each in a guarded child process, see src/utils/resource_monitor.py):
  1. scripts/workers/audit_global.py      -> global distributions and value checks
  2. scripts/workers/audit_partition.py   -> per-account statistics, 50 partitions, checkpointed
  3. combine                              -> reports/data_audit/*
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.configuration import load_config  # noqa: E402
from src.utils.resource_monitor import limits, run_guarded, run_partitions, system_snapshot  # noqa: E402

OUT = ROOT / "reports/data_audit"
CK = ROOT / "checkpoints/verification/audit"
TRAIN_END = "2025-12"  # HW2 Table 8.1 training period end, used for leakage-safe eligibility counts


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    before = system_snapshot()
    g_done = OUT / "global_stats.json"
    step_peaks = {}
    for step in ["missing", "distributions", "calendar", "amounts"]:  # 'amounts' needs calendar output
        marker = OUT / f"_step_{step}.json"
        if marker.exists():
            step_peaks[step] = "checkpointed"
            continue
        g = run_guarded([sys.executable, "scripts/workers/audit_global.py", str(OUT), step], cwd=ROOT)
        step_peaks[step] = g.peak_rss_gb
        print(f"[global:{step}] ok={g.ok} {g.seconds}s peak_rss={g.peak_rss_gb}GB", flush=True)
        if not g.ok:
            raise SystemExit(f"global audit step {step} failed: {g.killed_reason or g.stderr_tail}")
    n_parts = limits()["partitioning"]["account_partitions"]
    recs = run_partitions(ROOT / "scripts/workers/audit_partition.py", n_parts, CK,
                          ROOT / "logs/execution/audit_partitions.jsonl")
    parts = [json.loads((CK / f"part_{p:03d}.json").read_text()) for p in range(n_parts)]
    acc = pl.concat([pl.read_parquet(CK / f"part_{p:03d}.parquet") for p in range(n_parts)])

    q = [0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0]
    num = ["n_tx", "n_completed", "active_months_any", "active_spending_months", "n_currencies",
           "n_categories", "max_gap_days", "negative_balance_rows"]
    pl.DataFrame([{"metric": c, **{f"q{x}": float(acc[c].quantile(x)) for x in q},
                   "mean": float(acc[c].mean())} for c in num]).write_csv(OUT / "account_statistics.csv")
    for c in ["n_tx", "active_months_any", "active_spending_months", "n_currencies"]:
        acc[c].value_counts().sort(c).write_csv(OUT / f"accounts_by_{c}.csv")

    mac = (pl.concat([pl.read_parquet(CK / f"part_{p:03d}.months.parquet") for p in range(n_parts)])
             .group_by("month").agg(pl.col("active_accounts").sum()))
    cov = pl.read_csv(OUT / "monthly_coverage_base.csv").join(mac, on="month", how="left").sort("month")
    cov.write_csv(OUT / "monthly_coverage.csv")
    glob = json.loads(g_done.read_text())
    dup_content = sum(p["same_content_different_id_rows"] for p in parts)
    led = ROOT / "reports/verification/ledger_semantics.json"
    ids = json.loads(led.read_text())["transaction_id_structure"] if led.exists() else None
    pl.DataFrame([
        {"check": "duplicate transaction_id rows", "value": (glob["rows"] - ids["unique_ids"]) if ids else None,
         "source": "ledger_semantics.json transaction_id_structure (full scan)"},
        {"check": "fully identical rows (all 9 columns)", "value": (glob["rows"] - ids["unique_ids"]) if ids else None,
         "source": "implied: identical rows would share a transaction_id; ids are unique"},
        {"check": "same content (8 non-id columns), different transaction_id",
         "value": dup_content, "source": "audit_partition.py n_unique per account partition"},
        {"check": "ids with non-standard suffix -zdl26nr51f60aaa959f",
         "value": ids["ids_with_suffix"] if ids else None, "source": "ledger_semantics.json"},
    ]).write_csv(OUT / "duplicate_analysis.csv")

    cfg = load_config("dataset")
    overview = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "scope": "all rows (no sampling)",
        "rows": glob["rows"], "columns": len(glob["columns"]), "accounts": acc.height,
        "calendar": glob["calendar"], "amount_checks": glob["amount_checks"],
        "same_content_different_id_rows": dup_content,
        "accounts_min_tx": int(acc["n_tx"].min()), "accounts_max_tx": int(acc["n_tx"].max()),
        "accounts_with_negative_balance_rows": int((acc["negative_balance_rows"] > 0).sum()),
        "advertised": cfg["advertised"],
        "resources": {"system_before": before, "system_after": system_snapshot(),
                      "global_step_peak_rss_gb": step_peaks,
                      "max_partition_peak_rss_gb": max(r.get("peak_rss_gb", 0) for r in recs)},
    }
    (OUT / "dataset_overview.json").write_text(json.dumps(overview, indent=2, default=str))
    print(json.dumps(overview, indent=2, default=str))


if __name__ == "__main__":
    main()
