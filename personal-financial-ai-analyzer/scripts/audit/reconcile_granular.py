"""Master audit: granular independent reconciliation (raw file vs pipeline tables).

Independent path: PyArrow only (no project code), row group by row group from data/raw.
Compared with data/processed/monthly and monthly_category at three levels, exact integer equality:
  1. (currency, month): income, outflow, fee, refund, transfer, expenses, net, completed and excluded counts
  2. (currency, month, merchant_category): gross spending (debit+withdrawal), refunds, net spending
  3. distinct accounts and total record count
Writes reports/final_master_audit/financial_reconciliation.json
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
INCOME, OUTFLOW = {"credit", "deposit", "interest"}, {"debit", "withdrawal"}


def raw() -> tuple[dict, dict, dict, set, int]:
    pf = pq.ParquetFile(ROOT / "data/raw/transactions_50M.parquet")
    by_type, counts, cat = defaultdict(int), defaultdict(int), defaultdict(int)
    accounts, rows = set(), 0
    for i in range(pf.metadata.num_row_groups):
        t = pf.read_row_group(i, columns=["account_id", "transaction_type", "amount", "currency",
                                          "merchant_category", "transaction_timestamp", "status"])
        rows += t.num_rows
        accounts.update(pc.unique(t["account_id"]).to_pylist())
        month = pc.utf8_slice_codeunits(t["transaction_timestamp"], 0, 7)
        done = pc.equal(t["status"], "completed")
        base = pa.table({"currency": t["currency"], "month": month, "done": done})
        for r in base.group_by(["currency", "month", "done"]).aggregate([([], "count_all")]).to_pylist():
            counts[(r["currency"], r["month"], "completed" if r["done"] else "excluded")] += r["count_all"]
        c = t.filter(done)
        cm = month.filter(done)
        cents = pc.cast(pc.round(pc.multiply(c["amount"], 100.0), 0), pa.int64())
        tb = pa.table({"currency": c["currency"], "month": cm, "type": c["transaction_type"],
                       "cat": c["merchant_category"], "cents": cents})
        for r in tb.group_by(["currency", "month", "type"]).aggregate([("cents", "sum")]).to_pylist():
            by_type[(r["currency"], r["month"], r["type"])] += r["cents_sum"]
        sub = tb.filter(pc.is_in(tb["type"], pa.array(sorted(OUTFLOW | {"refund"}))))
        for r in sub.group_by(["currency", "month", "cat", "type"]).aggregate([("cents", "sum")]).to_pylist():
            key = "refund" if r["type"] == "refund" else "gross"
            cat[(r["currency"], r["month"], r["cat"], key)] += r["cents_sum"]
    return by_type, counts, cat, accounts, rows


def pipeline() -> tuple[dict, dict, set]:
    cols = ["income_cents", "outflow_cents", "fee_cents", "refund_cents", "transfer_cents", "expenses_cents",
            "net_cash_flow_cents", "completed_records", "excluded_status_records"]
    mon, cat, accounts = defaultdict(int), defaultdict(int), set()
    for f in sorted((ROOT / "data/processed/monthly").glob("part_*.parquet")):
        t = pq.read_table(f, columns=["account_id", "currency", "month", *cols])
        accounts.update(pc.unique(t["account_id"]).to_pylist())
        for r in t.group_by(["currency", "month"]).aggregate([(c, "sum") for c in cols]).to_pylist():
            for c in cols:
                mon[(r["currency"], r["month"], c)] += r[f"{c}_sum"]
    for f in sorted((ROOT / "data/processed/monthly_category").glob("part_*.parquet")):
        t = pq.read_table(f, columns=["currency", "month", "merchant_category", "gross_spending_cents",
                                      "refund_cents", "net_spending_cents"])
        for r in t.group_by(["currency", "month", "merchant_category"]).aggregate(
                [("gross_spending_cents", "sum"), ("refund_cents", "sum"), ("net_spending_cents", "sum")]).to_pylist():
            k = (r["currency"], r["month"], r["merchant_category"])
            cat[(*k, "gross")] += r["gross_spending_cents_sum"]
            cat[(*k, "refund")] += r["refund_cents_sum"]
            cat[(*k, "net")] += r["net_spending_cents_sum"]
    return mon, cat, accounts


def main() -> None:
    t0 = time.time()
    by_type, counts, rcat, raccounts, rows = raw()
    mon, pcat, paccounts = pipeline()
    keys = sorted({(c, m) for (c, m, _) in mon})
    mismatches, n = [], 0
    for c, m in keys:
        s = lambda ts: sum(by_type.get((c, m, x), 0) for x in ts)  # noqa: E731
        exp = {"income_cents": s(INCOME), "outflow_cents": s(OUTFLOW), "fee_cents": s({"fee"}),
               "refund_cents": s({"refund"}), "transfer_cents": s({"transfer"}),
               "completed_records": counts.get((c, m, "completed"), 0),
               "excluded_status_records": counts.get((c, m, "excluded"), 0)}
        exp["expenses_cents"] = exp["outflow_cents"] + exp["fee_cents"] - exp["refund_cents"]
        exp["net_cash_flow_cents"] = exp["income_cents"] - exp["expenses_cents"]
        for k, v in exp.items():
            n += 1
            if mon[(c, m, k)] != v:
                mismatches.append({"level": "currency_month", "key": [c, m, k], "raw": v, "pipeline": mon[(c, m, k)]})
    ckeys = sorted({k[:3] for k in pcat} | {k[:3] for k in rcat})
    for k in ckeys:
        g, r = rcat.get((*k, "gross"), 0), rcat.get((*k, "refund"), 0)
        for name, v in (("gross", g), ("refund", r), ("net", g - r)):
            n += 1
            if pcat.get((*k, name), 0) != v:
                mismatches.append({"level": "currency_month_category", "key": [*k, name], "raw": v,
                                   "pipeline": pcat.get((*k, name), 0)})
    total_records = sum(v for (c, m, k), v in mon.items() if k in ("completed_records", "excluded_status_records"))
    extra = {"raw_rows": rows, "pipeline_records": total_records, "rows_equal": rows == total_records,
             "raw_accounts": len(raccounts), "pipeline_accounts": len(paccounts),
             "accounts_equal": raccounts == paccounts}
    n += 2
    if not (extra["rows_equal"] and extra["accounts_equal"]):
        mismatches.append({"level": "global", **extra})
    res = {"overall": "PASS" if not mismatches else "FAIL", "checks": n, "mismatches": len(mismatches),
           "currency_month_keys": len(keys), "currency_month_category_keys": len(ckeys), **extra,
           "seconds": round(time.time() - t0, 1), "mismatch_detail": mismatches[:50]}
    out = ROOT / "reports/final_master_audit/financial_reconciliation.json"
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "mismatch_detail"}, indent=1))
    raise SystemExit(0 if not mismatches else 1)


if __name__ == "__main__":
    main()
