"""Worker: real-data cross-check of the validator and financial metrics on ONE account partition.

1. Run src.data.validation on ~1M real rows; the audit predicts 0 rejections and 0 unresolved types.
2. Compute monthly account-currency summaries with src.analytics.financial_metrics (Polars, cents).
3. Recompute the same numbers INDEPENDENTLY with pandas + Python Decimal straight from the raw rows,
   using only the written definitions (docs/FINANCIAL_RULES.md), not project code.
4. Compare every cell exactly.
usage: crosscheck_partition.py <part> <n_parts> <out_json>
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.analytics.financial_metrics import monthly_summary  # noqa: E402
from src.data.validation import validate_transactions  # noqa: E402

RAW = ROOT / "data/raw/transactions_50M.parquet"


def independent(raw: pl.DataFrame) -> dict:
    pdf = raw.to_pandas()
    pdf = pdf[pdf["status"] == "completed"]
    pdf["month"] = pdf["transaction_timestamp"].str.slice(0, 7)
    pdf["dec"] = pdf["amount"].map(lambda x: Decimal(repr(x)))
    groups = {"income": {"credit", "deposit", "interest"}, "outflow": {"debit", "withdrawal"},
              "fee": {"fee"}, "refund": {"refund"}, "transfer": {"transfer"}}
    out = {}
    for (acc, cur, mon), g in pdf.groupby(["account_id", "currency", "month"]):
        sums = {k: sum((d for d, t in zip(g["dec"], g["transaction_type"]) if t in v), Decimal(0))
                for k, v in groups.items()}
        exp = sums["outflow"] + sums["fee"] - sums["refund"]
        out[(acc, cur, mon)] = {"income": sums["income"], "expenses": exp,
                                "net": sums["income"] - exp, "transfer": sums["transfer"]}
    return out


def main() -> None:
    part, n_parts, out = int(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
    raw = (pl.scan_parquet(RAW)
             .filter(pl.col("account_id").str.slice(4).cast(pl.Int64) % n_parts == part)
             .collect(engine="streaming"))
    res = validate_transactions(raw.with_columns(pl.col("amount").cast(pl.String)))
    ms = monthly_summary(res.clean)
    ind = independent(raw)
    mism = 0
    keys_proj = set()
    for r in ms.iter_rows(named=True):
        k = (r["account_id"], r["currency"], r["month"])
        keys_proj.add(k)
        e = ind.get(k)
        if e is None:
            if r["completed_records"] > 0:
                mism += 1
            continue
        got = {"income": Decimal(r["income_cents"]) / 100, "expenses": Decimal(r["expenses_cents"]) / 100,
               "net": Decimal(r["net_cash_flow_cents"]) / 100, "transfer": Decimal(r["transfer_cents"]) / 100}
        mism += sum(got[x] != e[x] for x in got)
    missing = len(set(ind) - keys_proj)
    json.dump({"partition": part, "rows": raw.height, "clean": res.clean.height,
               "rejected": res.rejected.height, "reject_reasons": res.reason_counts,
               "unresolved_type_rows": int((res.clean["meaning"] == "unresolved").sum()),
               "summary_cells": ms.height, "independent_groups": len(ind),
               "value_mismatches": mism, "groups_missing_from_project_output": missing},
              open(out, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
