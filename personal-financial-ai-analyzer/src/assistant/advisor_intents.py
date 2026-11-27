"""Execution of the master-audit assistant intents (income, cash flow, trend, unusual transactions, goals,
recommendations, scenarios, affordability). Pipeline per question: intent -> scope validation (one account,
one currency) -> parameter extraction -> deterministic calculation in src.analytics / src.advisor /
src.models -> fixed template. Read-only: nothing here changes budgets, goals or data."""
from __future__ import annotations

from dataclasses import dataclass, field

import polars as pl

from src.advisor import affordability as A
from src.advisor import recommendations as R
from src.advisor import savings as S
from src.advisor import scenarios as SC
from src.advisor.context import UserFacts, build_context
from src.analytics import insights as I
from src.assistant.intent_detection import Intent

ADVISOR_INTENTS = {"income", "cash_flow", "spending_trend", "unusual_transactions", "savings_goals",
                   "recommendations", "scenario", "affordability"}


@dataclass
class AssistantContext:
    clean: pl.DataFrame
    goals: list[S.Goal] = field(default_factory=list)
    user: UserFacts = field(default_factory=UserFacts)


def execute(intent: Intent, s, account: str, currency: str, months: list[str | None], avail: list[str],
            budgets: dict | None, ctx: AssistantContext | None) -> dict:
    base = {"intent": intent.name, "scope": {"account": account, "currency": currency,
                                             "period": [avail[0], avail[-1]]}}
    if intent.name in ("income", "cash_flow"):
        cf = I.cash_flow(s, account, currency)
        if months:
            row = cf.filter(pl.col("month") == months[0])
            r = row.row(0, named=True) if row.height else {"income_cents": 0, "expenses_cents": 0, "net_cents": 0}
            return {**base, "month": months[0], **{k: int(r[k]) for k in ("income_cents", "expenses_cents", "net_cents")}}
        win = cf.tail(6)
        return {**base, "month": None, "window": [win["month"][0], win["month"][-1]],
                "income_cents": int(round(float(win["income_cents"].mean()))),
                "expenses_cents": int(round(float(win["expenses_cents"].mean()))),
                "net_cents": int(round(float(win["net_cents"].mean()))),
                "negative_months": int((cf["net_cents"] < 0).sum()), "months": cf.height}
    if ctx is None:
        return {**base, "error": "needs_context"}
    if intent.name == "spending_trend":
        st = I.spending_statistics(s, account, currency)
        b = I.behaviour_changes(ctx.clean, s, account, currency)
        return {**base, "change_pct": st.get("recent_change_pct"), "basis": st.get("recent_change_basis"),
                "increasing": b["increasing"], "declining": b["declining"], "category_basis": b["basis"]}
    if intent.name == "unusual_transactions":
        from src.models.anomaly.anomaly_scoring import review_candidates
        r = review_candidates(ctx.clean, account, currency)
        if not r["ok"]:
            return {**base, "error": "message", "message": r["message"]}
        top = r["candidates"].row(0, named=True)
        return {**base, "count": r["candidates"].height, "window": r["window"], "label": r["label"],
                "not_fraud": r["not_fraud"], "top": {"date": str(top["transaction_timestamp"])[:10],
                                                     "category": top["merchant_category"], "amount": top["amount"],
                                                     "explanation": top["explanation"]}}
    fc = build_context(ctx.clean, s, account, currency, ctx.user)
    if intent.name == "savings_goals":
        if not ctx.goals:
            return {**base, "error": "no_goals"}
        return {**base, "plans": [S.plan(g, fc.window[-1], fc) for g in ctx.goals]}
    if intent.name == "recommendations":
        recs = R.generate(ctx.clean, s, fc, budgets, ctx.goals, fc.window[-1])
        return {**base, "recommendations": [{k: r[k] for k in ("rank", "title", "monthly_impact_cents", "evidence")}
                                            for r in recs[:3]], "total": len(recs)}
    if intent.name == "scenario":
        if intent.category and intent.percent:
            sc = SC.Scenario(category_cuts_pct={intent.category: intent.percent})
            desc = f"reduce {intent.category} by {intent.percent:g}%"
        elif intent.amount:
            sc = SC.Scenario(extra_saving_cents=int(round(intent.amount * 100)))
            desc = f"save {intent.amount:,.2f} {currency} more each month"
        else:
            return {**base, "error": "scenario_params"}
        r = SC.simulate(fc, sc)
        return {**base, "description": desc, **{k: r[k] for k in ("label", "baseline", "scenario",
                                                                 "difference_monthly_cents",
                                                                 "difference_over_horizon_cents", "horizon_months")},
                "savings_after_horizon_cents": r["path"][-1]["savings_pot_cents"]}
    if intent.name == "affordability":
        if intent.amount is None:
            return {**base, "error": "needs_amount"}
        r = A.assess(int(round(intent.amount * 100)), fc, "one-off", intent.category, budgets)
        return {**base, "amount_cents": r["amount_cents"], "verdict": r["verdict"], "summary": r["summary"],
                "effects": r["effects"], "missing": r["missing_information"]}
    return {"intent": "unsupported"}


def render(r: dict, currency: str) -> str | None:
    """Template for advisor intents; None if `r` is not one of them."""
    i = r.get("intent")
    if i not in ADVISOR_INTENTS:
        return None
    m = lambda c: f"{c / 100:,.2f} {currency}"  # noqa: E731
    err = r.get("error")
    if err == "needs_context":
        return "This question needs the full transaction data, which is not available here."
    if err == "message":
        return r["message"]
    if err == "no_goals":
        return "You have no savings goals yet. Add one on the Financial advisor page."
    if err == "needs_amount":
        return "How much does it cost? Ask again with the amount, for example: Can I afford 450?"
    if err == "scenario_params":
        return ("Please say what to change, for example: What if I reduce dining by 10%? "
                "or: What if I save 200 more every month?")
    if i == "income":
        if r["month"]:
            return (f"Recorded inflows in {r['month']}: {m(r['income_cents'])}. These are credits, deposits and "
                    f"interest; the data cannot show whether any of it is salary.")
        return (f"Average recorded inflows {r['window'][0]}..{r['window'][1]}: {m(r['income_cents'])} per month. "
                f"The data cannot show whether any of it is salary.")
    if i == "cash_flow":
        if r["month"]:
            return (f"Cash flow in {r['month']}: inflows {m(r['income_cents'])}, expenses {m(r['expenses_cents'])}, "
                    f"net {m(r['net_cents'])}. This is transaction-derived, not a bank balance.")
        return (f"Average monthly cash flow {r['window'][0]}..{r['window'][1]}: inflows {m(r['income_cents'])}, "
                f"expenses {m(r['expenses_cents'])}, net {m(r['net_cents'])}. {r['negative_months']} of "
                f"{r['months']} months had a negative net. Not a bank balance.")
    if i == "spending_trend":
        parts = []
        if r["change_pct"] is not None:
            parts.append(f"Spending changed {r['change_pct']:+.1f}% ({r['basis']}).")
        if r["increasing"]:
            parts.append("Increasing: " + ", ".join(f"{x['category']} {x['change_pct']:+.0f}%" for x in r["increasing"]) + ".")
        if r["declining"]:
            parts.append("Declining: " + ", ".join(f"{x['category']} {x['change_pct']:+.0f}%" for x in r["declining"]) + ".")
        if not parts:
            return "There is not enough history to describe a spending trend, or no category changed noticeably."
        return " ".join(parts) + (f" Category comparison: {r['category_basis']}." if r["category_basis"] else "")
    if i == "unusual_transactions":
        t = r["top"]
        return (f"{r['label']} {r['count']} transaction(s) in {r['window']} stand out. The most unusual: {t['date']}, "
                f"{t['category']}, {t['amount']:,.2f} {currency} ({t['explanation']}). {r['not_fraud']}")
    if i == "savings_goals":
        out = []
        for p in r["plans"]:
            s_ = f"{p['goal']}: {p['progress'] or 0:.0%} saved, {m(p['remaining_cents'])} to go"
            if p["required_monthly_cents"]:
                s_ += f", {m(p['required_monthly_cents'])} per month needed"
            if p["completion_month"]:
                s_ += f", reached {p['completion_month']} at your planned contribution"
            out.append(s_ + ".")
        return " ".join(out)
    if i == "recommendations":
        if not r["recommendations"]:
            return "No recommendation is supported by the evidence in your data right now."
        return (f"Top {len(r['recommendations'])} of {r['total']} (details on the Financial advisor page): " +
                " ".join(f"{x['rank']}. {x['title']} (about {m(x['monthly_impact_cents'])} per month)."
                         for x in r["recommendations"]))
    if i == "scenario":
        return (f"{r['label']}: if you {r['description']}, your monthly net changes from "
                f"{m(r['baseline']['monthly_net_cents'])} to {m(r['scenario']['monthly_net_cents'])} "
                f"({m(r['difference_monthly_cents'])} per month, {m(r['difference_over_horizon_cents'])} over "
                f"{r['horizon_months']} months)."
                + (f" Money set aside after {r['horizon_months']} months: {m(r['savings_after_horizon_cents'])}."
                   if r["scenario"]["monthly_saving_cents"] else ""))
    if i == "affordability":
        return f"{r['summary']} {' '.join(r['effects'])} Unknown: {'; '.join(r['missing'][:2])}."
    return None
