"""Compute the values the UX run must see on screen (from the deterministic core, demo file)."""
import json, sys
from pathlib import Path
import polars as pl
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.analytics.aggregation import build_summaries, period_totals
from src.data.ingestion import ingest
res, _ = ingest((ROOT / "data/samples/demo_transactions.csv").read_bytes())
s = build_summaries(res.clean)
acc = s.accounts[0]
months = s.months(acc, "USD")
t = period_totals(s, acc, "USD", months)
g = res.clean.filter((pl.col("account_id") == acc) & (pl.col("currency") == "USD") & (pl.col("merchant_category") == "groceries"))
last = months[-1]
exp = {"account": acc, "income": f"{t['income_cents']/100:,.2f} USD", "expenses": f"{t['expenses_cents']/100:,.2f} USD",
       "net": f"{t['net_cash_flow_cents']/100:,.2f} USD", "groceries_rows": g.height, "last_month": last,
       "last_month_spend": f"{period_totals(s, acc, 'USD', [last])['expenses_cents']/100:,.2f} USD",
       "invalid_file_valid_rows": 2, "invalid_file_rejected_rows": 2, "unmapped_rows": 3}
(ROOT / "reports/ux_tasks/expected.json").write_text(json.dumps(exp, indent=2))
print(json.dumps(exp, indent=2))
from src.budget.budget_calculator import suggest_budgets
bm = next(m for m in reversed(months) if any(r["spent_current_cents"] > 0 for r in suggest_budgets(s.category, acc, "USD", m).iter_rows(named=True)))
b = suggest_budgets(s.category, acc, "USD", bm)
idx = next(i for i, r in enumerate(b.iter_rows(named=True)) if r["spent_current_cents"] > 0)
exp.update(budget_month=bm, budget_row_index=idx, budget_category=b["merchant_category"][idx],
           budget_suggested=[round(v / 100, 2) for v in b["suggested_cents"]])
(ROOT / "reports/ux_tasks/expected.json").write_text(json.dumps(exp, indent=2))
print("budget", bm, idx, b["merchant_category"][idx], b["spent_current_cents"][idx])
