"""Compute the expected on-screen values of the practical walkthrough with the app's own engine, and write
reports/demo/demo_expected.json (checked by the browser test) and docs/DEMO_WALKTHROUGH.md (for the user).
Nothing here is typed by hand: every number comes from the same functions the dashboard calls.
Data: the SYNTHETIC demo files from scripts/prepare_personal_demo.py (not real, not academic data).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.advisor import savings as S
from src.advisor.context import build_context
from src.analytics.aggregation import build_summaries, period_totals
from src.assistant.advisor_intents import AssistantContext
from src.assistant.response_generator import answer
from src.data.ingestion import ingest, read_csv_bytes, suggest_mapping
from src.data.merge import merge
from src.models.anomaly.anomaly_scoring import review_candidates
from src.models.forecasting.inference import forecast_product

P1, P2 = ROOT / "data/samples/demo_personal_part1.csv", ROOT / "data/samples/demo_personal_part2.csv"
CUR = "TRY"


def money(c: int) -> str:
    return f"{c / 100:,.2f} {CUR}"


def main() -> None:
    a, b = P1.read_bytes(), P2.read_bytes()
    mp = suggest_mapping(read_csv_bytes(a).columns)
    ra, _ = ingest(a, mp, assume_completed=True)
    rb, _ = ingest(b, mp, assume_completed=True)
    m = merge(ra.clean, ra.rejected, "part1", rb.clean, rb.rejected, "part2")
    s = build_summaries(m.clean)
    acc = s.accounts[0]
    months = s.months(acc, CUR)
    t = period_totals(s, acc, CUR, months)
    ctx = AssistantContext(clean=m.clean)
    f = forecast_product(s.monthly.filter((pl.col("account_id") == acc) & (pl.col("currency") == CUR)))
    q = {k: answer(k, s, acc, CUR, forecast=f, context=ctx)[0] for k in (
        "Which months had the highest spending?", "Compare this month with last month", "How much can I save?",
        "What payments appear to recur?", "Is the prediction reliable?", "Explain the savings rate")}
    rc = review_candidates(m.clean, acc, CUR)
    top = rc["candidates"].row(0, named=True)
    fc = build_context(m.clean, s, acc, CUR)
    goal = S.plan(S.Goal("Laptop", 6_000_000, 500_000, "2026-12"), fc.window[-1], fc)
    ef = S.emergency_fund_plan(fc, 3.0, 0, None, "essential")
    exp = {"part1_valid": ra.clean.height, "part2_valid": rb.clean.height, "added": m.added,
           "already_loaded": m.already_loaded, "total_valid": m.clean.height, "account": acc, "currency": CUR,
           "period": [months[0], months[-1]], "income": money(t["income_cents"]),
           "expenses": money(t["expenses_cents"]), "net": money(t["net_cash_flow_cents"]),
           "forecast_category": f["forecast_category"], "forecast_target": f["target_month"],
           "forecast_point": money(f["point_cents"]),
           "forecast_interval": [money(f["interval_cents"][0]), money(f["interval_cents"][1])],
           "unusual_top": {"date": str(top["transaction_timestamp"]), "category": top["merchant_category"],
                           "amount": f"{top['amount']:,.2f} {CUR}", "explanation": top["explanation"]},
           "goal_required": money(goal["required_monthly_cents"]), "goal_start": fc.window[-1],
           "emergency_fund_3m_essential": money(ef["target_cents"]), "answers": q}
    out = ROOT / "reports/demo/demo_expected.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(exp, indent=1, ensure_ascii=False), encoding="utf-8")
    doc = f"""# Practical walkthrough (synthetic personal demo)

This walkthrough uses **two invented bank exports** (`data/samples/demo_personal_part1.csv` and
`demo_personal_part2.csv`, made by `scripts/prepare_personal_demo.py`, seed 20261127). They are **synthetic**: no
real person, not academic data, not used by any experiment. Every expected value below was computed by the app's
own engine (`scripts/ux/demo_walkthrough.py` → `reports/demo/demo_expected.json`) and the browser test checks the
screen against it. Your own CSV will of course give other numbers.

| # | Do this | You should see |
|---|---|---|
| 1 | Double-click **START_HERE.bat** | a window that says `Dashboard ready: http://localhost:8501`; Chrome opens the app |
| 2 | **Transactions** → *Load demo data* | the public-dataset demo (3 synthetic accounts) — a quick look around |
| 3 | Sidebar → **Delete my data now**, then **Transactions** → upload `demo_personal_part1.csv` | preview; mapping Date/Description/Category/Amount/Currency is filled in |
| 4 | Tick *All rows in this file are completed* → **Validate and load** | Valid rows **{exp['part1_valid']}**, Rejected 0 |
| 5 | Upload `demo_personal_part2.csv`, keep **Add to the loaded transactions**, tick *completed* → **Validate and load** | *Added {exp['added']} new transaction(s) … {exp['already_loaded']} were already loaded and skipped*; Valid rows **{exp['total_valid']}** (the Nov–Dec 2025 overlap is not double-counted) |
| 6 | Upload any file again with **Replace the loaded transactions** | the button stays disabled until you tick the confirmation — only then is the data replaced (skip this to keep the demo data) |
| 7 | Sidebar: account **{acc}**, currency **{CUR}** → **Overview** | inflows **{exp['income']}**, expenses **{exp['expenses']}**, net **{exp['net']}** for {months[0]}..{months[-1]}; *Download monthly report (CSV)* |
| 8 | **Analytics** | spending by day / week / month; categories; inflows and cash flow (not a bank balance); recurring candidates (rent, subscriptions, bills); dining rising in the last 3 months; indicators with formulas |
| 9 | **Financial advisor** → *Savings goals*: name *Laptop*, target 60000, already saved 5000, target month 2026-12 → *Add goal* | required per month **{exp['goal_required']}**, milestones, status; emergency fund (3 months, essential) target **{exp['emergency_fund_3m_essential']}** |
| 10 | **Financial assistant** — ask the questions below | the answers below |
| 11 | **AI predictions** | *Type of result: {exp['forecast_category']}*; estimate for {exp['forecast_target']} **{exp['forecast_point']}** (80% range {exp['forecast_interval'][0]} – {exp['forecast_interval'][1]}); evidence and limitations |
| 12 | **AI predictions** → *Unusual transactions* | first: {exp['unusual_top']['date']} {exp['unusual_top']['category']} {exp['unusual_top']['amount']} — *{exp['unusual_top']['explanation']}*; labelled "review recommended", never fraud |
| 13 | **Transactions** → *Download these transactions (CSV)*; **Overview** → *Download monthly report (CSV)* | CSV files of exactly what is shown |
| 14 | **Settings and privacy** → *Delete all my data*; finally **STOP.bat** | everything removed from the session; the server stops |

## Assistant questions and the engine's answers

""" + "\n".join(f"* **{k}**  \n  {v}" for k, v in q.items()) + """

## Your own CSV

Any bank export with a date, an amount and a currency works (comma/semicolon/tab, UTF-8 or Windows encoding,
any ISO currency such as TRY). Map the columns on the Transactions page; if there is no status column, confirm
that all rows are completed; if amounts are signed, negative = spending. Add further exports with *Add to the
loaded transactions* — transactions already loaded are skipped and counted.
"""
    (ROOT / "docs/DEMO_WALKTHROUGH.md").write_text(doc, encoding="utf-8")
    print(json.dumps({k: v for k, v in exp.items() if k != "answers"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
