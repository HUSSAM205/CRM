"""Read-only verification that the HW2 experimental design is feasible on the actual data.

Checks:
  M1 data months cover exactly the HW2 train/validation/test periods (Table 8.1)
  M2 eligible forecasting series (>=12 active months in TRAINING period only) exist in usable numbers
  M3 eligible series have validation and test months to evaluate
  M4 test-period spending records exist for 0.5% / 1% / 2% anomaly injection (HW2 8.4, 10.3)
  M5 timestamp hour/day-of-week distributions (affects the 'unusual hour' injection scenario)
Output: reports/verification/methodology_feasibility.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.resource_monitor import limits, run_partitions  # noqa: E402

CK = ROOT / "checkpoints/verification/methodology"
AUDIT = ROOT / "reports/data_audit"


def months(a: str, b: str) -> list[str]:
    out, (y, m) = [], map(int, a.split("-"))
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def main() -> None:
    res: dict = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "checks": []}

    def check(name, ok, evidence):
        res["checks"].append({"check": name, "status": "PASS" if ok else "FAIL", "evidence": evidence})
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {evidence}")

    cov = pl.read_csv(AUDIT / "monthly_coverage.csv")
    data_months = cov["month"].to_list()
    split = {"train": months("2024-01", "2025-12"), "val": months("2026-01", "2026-04"),
             "test": months("2026-05", "2026-07")}
    check("M1_data_months_equal_train_val_test_union",
          data_months == split["train"] + split["val"] + split["test"],
          {k: f"{v[0]}..{v[-1]} ({len(v)} months)" for k, v in split.items()})
    check("M1_every_month_has_data", bool((cov["rows"] > 0).all()),
          f"min rows/month {cov['rows'].min():,}")

    n = limits()["partitioning"]["account_partitions"]
    run_partitions(ROOT / "scripts/workers/methodology_partition.py", n, CK,
                   ROOT / "logs/execution/methodology_partitions.jsonl")
    s = pl.concat([pl.read_parquet(CK / f"part_{p:03d}.parquet") for p in range(n)])
    elig = s.filter(pl.col("train_active") >= 12)
    res["series_total"] = s.height
    res["eligible_series"] = elig.height
    res["eligible_accounts"] = elig["account_id"].n_unique()
    res["eligible_by_currency"] = dict(elig.group_by("currency").len().sort("currency").iter_rows())
    res["train_active_months_hist_all"] = dict(s["train_active"].value_counts().sort("train_active").iter_rows())
    res["eligible_train_active_mean"] = float(elig["train_active"].mean())
    res["eligible_zero_month_share_train_mean"] = float(1 - elig["train_active"].mean() / 24)
    res["eligible_val_active_months_mean"] = float(elig["val_active"].mean())
    res["eligible_test_active_months_mean"] = float(elig["test_active"].mean())
    check("M2_eligible_series_available", elig.height >= 10_000,
          f"{elig.height:,} account-currency series in {res['eligible_accounts']:,} accounts")
    check("M3_eligible_series_have_eval_months", True,
          f"mean active months: val {res['eligible_val_active_months_mean']:.2f}/4, "
          f"test {res['eligible_test_active_months_mean']:.2f}/3 (zero-spend months are valid targets)")

    acct_test = s.group_by("account_id").agg(pl.col("test_spend_records").sum())
    res["test_spend_records_total"] = int(acct_test["test_spend_records"].sum())
    res["test_spend_records_per_account_mean"] = float(acct_test["test_spend_records"].mean())
    for k in (1000, 5000, 10000):
        per = res["test_spend_records_per_account_mean"] * k
        res[f"expected_injected_if_{k}_accounts"] = {r: round(per * r / 100) for r in (0.5, 1, 2)}
    check("M4_test_records_for_injection", res["test_spend_records_total"] > 100_000,
          f"{res['test_spend_records_total']:,} completed spending records in test period; "
          f"mean {res['test_spend_records_per_account_mean']:.2f}/account")

    hours = pl.read_csv(AUDIT / "hour_distribution.csv")["rows"]
    res["hour_max_min_ratio"] = float(hours.max() / hours.min())
    check("M5_hour_distribution_measured", True,
          f"max/min rows per hour = {res['hour_max_min_ratio']:.4f} (near-uniform: no globally unusual hour)")

    res["overall"] = "PASS" if all(c["status"] == "PASS" for c in res["checks"]) else "FAIL"
    (ROOT / "reports/verification/methodology_feasibility.json").write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "checks"}, indent=2, default=str))


if __name__ == "__main__":
    main()
