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
(ROOT / "reports/ux_tasks/expected.json").write_text(json.dumps(exp, indent=2), encoding="utf-8")
print(json.dumps(exp, indent=2))
from src.budget.budget_calculator import suggest_budgets
bm = next(m for m in reversed(months) if any(r["spent_current_cents"] > 0 for r in suggest_budgets(s.category, acc, "USD", m).iter_rows(named=True)))
b = suggest_budgets(s.category, acc, "USD", bm)
idx = next(i for i, r in enumerate(b.iter_rows(named=True)) if r["spent_current_cents"] > 0)
exp.update(budget_month=bm, budget_row_index=idx, budget_category=b["merchant_category"][idx],
           budget_suggested=[round(v / 100, 2) for v in b["suggested_cents"]])
(ROOT / "reports/ux_tasks/expected.json").write_text(json.dumps(exp, indent=2), encoding="utf-8")
print("budget", bm, idx, b["merchant_category"][idx], b["spent_current_cents"][idx])
# second account, in the currency the sidebar selects by default (most completed records)
acc2 = s.accounts[1]
m2 = s.monthly.filter(pl.col("account_id") == acc2)
cur2 = (m2.group_by("currency").agg(pl.col("completed_records").sum())
          .sort(["completed_records", "currency"], descending=[True, False])["currency"][0])
t2 = period_totals(s, acc2, cur2, s.months(acc2, cur2))
exp.update(account2=acc2, account2_currency=cur2, account2_expenses=f"{t2['expenses_cents']/100:,.2f} {cur2}",
           account2_income=f"{t2['income_cents']/100:,.2f} {cur2}")
(ROOT / "reports/ux_tasks/expected.json").write_text(json.dumps(exp, indent=2), encoding="utf-8")
print("account2", acc2, cur2, exp["account2_expenses"])
# Advisor / assistant expectations (master audit): first account, USD (the default currency for it)
from src.advisor import savings as S
from src.advisor.context import build_context
from src.assistant.advisor_intents import AssistantContext
from src.assistant.response_generator import answer
ctx = build_context(res.clean, s, acc, "USD")
g = S.Goal("Bike", 60000, 10000, "2027-06")
p = S.plan(g, ctx.window[-1], ctx)
cf_text, _ = answer("What is my average cash flow?", s, acc, "USD", context=AssistantContext(clean=res.clean))
exp.update(advisor_surplus=f"{ctx.monthly_surplus_cents[0]/100:,.2f} USD",
           goal_required=f"{p['required_monthly_cents']/100:,.2f} USD", goal_start=ctx.window[-1],
           cashflow_answer=cf_text)
(ROOT / "reports/ux_tasks/expected.json").write_text(json.dumps(exp, indent=2), encoding="utf-8")
print("advisor", exp["advisor_surplus"], exp["goal_required"])
# Dataset B demo (master audit 2): accepted model estimate and emergency fund at 6 months coverage
from src.models.forecasting.inference import forecast_product
resB, _ = ingest((ROOT / "data/samples/demo_personaledger.csv").read_bytes())
sB = build_summaries(resB.clean)
accB = sB.accounts[0]
fB = forecast_product(sB.monthly.filter((pl.col("account_id") == accB) & (pl.col("currency") == "USD")))
efB = S.emergency_fund_plan(build_context(resB.clean, sB, accB, "USD"), 6.0, 0, None, "essential")
exp.update(b_account=accB, b_target_month=fB["target_month"], b_estimate=f"{fB['point_cents']/100:,.2f} USD",
           b_method=fB["method"], b_ef6_target=f"{efB['target_cents']/100:,.2f} USD")
(ROOT / "reports/ux_tasks/expected.json").write_text(json.dumps(exp, indent=2), encoding="utf-8")
print("datasetB", exp["b_estimate"], exp["b_method"], exp["b_ef6_target"])
# Master audit 3: append workflow, new assistant intents, forecast category
from src.data.ingestion import suggest_mapping
from src.data.merge import merge
bank = (ROOT / "data/samples/sample_bank_export.csv").read_bytes()
import io as _io
resK, _ = ingest(bank, suggest_mapping(pl.read_csv(_io.BytesIO(bank), infer_schema=False).columns), assume_completed=True)
mk = merge(res.clean, res.rejected, "demo", resK.clean, resK.rejected, "bank")
ctxA = AssistantContext(clean=res.clean)
hm_text, _ = answer("Which months had the highest spending?", s, acc, "USD", context=ctxA)
cmp_text, _ = answer("Compare this month with last month", s, acc, "USD", context=ctxA)
exp.update(append_added=mk.added, append_total_valid=mk.clean.height, bank_valid=resK.clean.height,
           highest_months_answer=hm_text, compare_answer=cmp_text)
(ROOT / "reports/ux_tasks/expected.json").write_text(json.dumps(exp, indent=2), encoding="utf-8")
print("ma3", mk.added, mk.clean.height, hm_text, cmp_text)
