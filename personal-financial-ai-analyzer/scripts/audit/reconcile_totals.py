"""Audit: independent full-scale reconciliation of the derived monthly tables against the raw file.

Path A (independent): PyArrow, row group by row group, straight from data/raw (no project code):
    completed rows -> cents = round(amount*100) -> sum by (currency, transaction_type)
Path B (pipeline output): sum of every data/processed/monthly/part_*.parquet column by currency.
Checks (exact integer equality, per currency):
    income   = credit + deposit + interest        outflow = debit + withdrawal
    fee      = fee     refund = refund            transfer = transfer
    expenses = outflow + fee - refund              net = income - expenses
    category tables: sum(net_spending) + fee == expenses
    excluded_status_records == count of non-completed raw rows
Writes reports/audit/reconciliation.json
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


def raw_totals() -> tuple[dict, dict, int]:
    pf = pq.ParquetFile(ROOT / "data/raw/transactions_50M.parquet")
    sums: dict = defaultdict(int)
    noncompleted: dict = defaultdict(int)
    rows = 0
    for i in range(pf.metadata.num_row_groups):
        t = pf.read_row_group(i, columns=["transaction_type", "amount", "currency", "status"])
        rows += t.num_rows
        done = pc.equal(t["status"], "completed")
        nc = t.filter(pc.invert(done)).group_by(["currency"]).aggregate([([], "count_all")])
        for cur, n in zip(nc["currency"].to_pylist(), nc["count_all"].to_pylist()):
            noncompleted[cur] += n
        c = t.filter(done)
        cents = pc.cast(pc.round(pc.multiply(c["amount"], 100.0), 0), pa.int64())
        g = pa.table({"currency": c["currency"], "type": c["transaction_type"], "cents": cents}) \
            .group_by(["currency", "type"]).aggregate([("cents", "sum")])
        for cur, typ, s in zip(g["currency"].to_pylist(), g["type"].to_pylist(), g["cents_sum"].to_pylist()):
            sums[(cur, typ)] += s
    return sums, noncompleted, rows


def pipeline_totals() -> tuple[dict, dict]:
    cols = ["income_cents", "outflow_cents", "fee_cents", "refund_cents", "transfer_cents", "expenses_cents",
            "net_cash_flow_cents", "excluded_status_records"]
    out: dict = defaultdict(lambda: defaultdict(int))
    for f in sorted((ROOT / "data/processed/monthly").glob("part_*.parquet")):
        t = pq.read_table(f, columns=["currency", *cols]).group_by(["currency"]).aggregate([(c, "sum") for c in cols])
        for r in t.to_pylist():
            for c in cols:
                out[r["currency"]][c] += r[f"{c}_sum"]
    cat: dict = defaultdict(int)
    for f in sorted((ROOT / "data/processed/monthly_category").glob("part_*.parquet")):
        t = pq.read_table(f, columns=["currency", "net_spending_cents"]).group_by(["currency"]).aggregate(
            [("net_spending_cents", "sum")])
        for r in t.to_pylist():
            cat[r["currency"]] += r["net_spending_cents_sum"]
    return out, cat


def main() -> None:
    t0 = time.time()
    raw, noncompleted, rows = raw_totals()
    t1 = time.time()
    pipe, cat = pipeline_totals()
    checks, ok = [], True
    for cur in sorted(pipe):
        r = lambda *ts: sum(raw.get((cur, x), 0) for x in ts)  # noqa: E731
        exp = {"income_cents": r("credit", "deposit", "interest"), "outflow_cents": r("debit", "withdrawal"),
               "fee_cents": r("fee"), "refund_cents": r("refund"), "transfer_cents": r("transfer")}
        exp["expenses_cents"] = exp["outflow_cents"] + exp["fee_cents"] - exp["refund_cents"]
        exp["net_cash_flow_cents"] = exp["income_cents"] - exp["expenses_cents"]
        exp["excluded_status_records"] = noncompleted[cur]
        for k, v in exp.items():
            good = pipe[cur][k] == v
            ok &= good
            checks.append({"currency": cur, "measure": k, "independent_raw": v, "pipeline": pipe[cur][k], "equal": good})
        good = cat[cur] + pipe[cur]["fee_cents"] == pipe[cur]["expenses_cents"]
        ok &= good
        checks.append({"currency": cur, "measure": "sum(category net)+fee == expenses",
                       "independent_raw": pipe[cur]["expenses_cents"], "pipeline": cat[cur] + pipe[cur]["fee_cents"],
                       "equal": good})
    res = {"overall": "PASS" if ok else "FAIL", "raw_rows_read": rows, "raw_seconds": round(t1 - t0, 1),
           "total_seconds": round(time.time() - t0, 1), "checks": checks}
    (ROOT / "reports/audit/reconciliation.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k != "checks"}))
    print(sum(c["equal"] for c in checks), "of", len(checks), "checks equal")
    for c in checks:
        if not c["equal"]:
            print("MISMATCH", c)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
