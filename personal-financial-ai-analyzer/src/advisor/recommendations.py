"""Evidence-based recommendations with a documented ranking (master audit 8.5, 8.8, 8.9).

Each recommendation carries the 12 required fields. Ranking is a fixed rule, not an AI score:
  1. urgency tier: 1 = a problem now (budget exceeded, negative recent cash flow, goal not supported),
                   2 = an opportunity;
  2. estimated monthly impact (larger first);
  3. evidence sufficiency (high > medium > low).
A recommendation is only produced when its evidence exists; otherwise nothing is shown.
"""
from __future__ import annotations

import polars as pl

from src.advisor.context import CFG, FinancialContext
from src.advisor.savings import Goal, plan
from src.analytics import insights as I
from src.analytics.aggregation import Summaries
from src.budget.budget_alerts import budget_status

_EVID = {"high": 0, "medium": 1, "low": 2}


def _suff(months: int) -> str:
    return "high" if months >= 12 else "medium" if months >= 6 else "low"


def _rec(**k) -> dict:
    k.setdefault("progress_tracking", "")
    return k


def generate(clean: pl.DataFrame, s: Summaries, ctx: FinancialContext, budgets: dict[str, int] | None = None,
             goals: list[Goal] | None = None, start_month: str | None = None) -> list[dict]:
    cur, recs = ctx.currency, []
    money = lambda c: f"{c / 100:,.2f} {cur}"  # noqa: E731
    suff = _suff(ctx.months_observed)
    r = CFG["reduction"]
    # 1. discretionary categories running above their own longer-run level
    for c in CFG["discretionary_categories"]:
        recent, prior = ctx.category_avg_recent_cents.get(c, 0), ctx.category_prior_avg_cents.get(c, 0)
        excess = recent - prior
        n_prior = max(min(ctx.months_observed, r["long_run_months"]) - 3, 0)
        if prior > 0 and excess >= r["min_excess_cents"] and excess / prior * 100 >= r["min_excess_pct"]:
            recs.append(_rec(
                tier=2, title=f"Bring {c} spending back to your earlier level",
                issue=f"Your {c} spending in the last 3 months is above your own average of the {n_prior} months before.",
                evidence=f"Average of the last 3 months: {money(recent)} per month; average of the {n_prior} "
                         f"months before: {money(prior)} per month (+{excess / prior:.0%}).",
                action=f"Aim for about {money(prior)} per month on {c}.",
                monthly_impact_cents=int(excess), annual_impact_cents=int(excess * 12),
                calculation=f"{money(recent)} − {money(prior)} = {money(excess)} per month; × 12 = {money(excess * 12)} per year.",
                assumptions=["the recent level would otherwise continue", f"{c} is discretionary spending (configurable)"],
                horizon="next 3 months", drawbacks="Less spending on something you value; your own earlier level is "
                                                      "the target, not an outside standard.",
                alternatives=[f"Halve the gap: {money(prior + excess // 2)} per month (saves {money(excess // 2)})",
                              "Set a budget for this category on the Budget page"],
                evidence_sufficiency=suff, progress_tracking=f"{c} spending per month vs {money(prior)}"))
    # 2. budgets exceeded in the latest month
    if budgets:
        last = ctx.window[-1] if ctx.window else None
        cat = s.category.filter((pl.col("account_id") == ctx.account) & (pl.col("currency") == cur)
                                & (pl.col("month") == last))
        spent = dict(zip(cat["merchant_category"], cat["net_spending_cents"]))
        for c, b in budgets.items():
            st = budget_status(spent.get(c, 0), b)
            if st["level"] == "exceeded":
                over = spent[c] - b
                recs.append(_rec(
                    tier=1, title=f"{c}: over budget in {last}", issue=st["message"],
                    evidence=f"Spent {money(spent[c])} against a budget of {money(b)} in {last}.",
                    action=f"Review {c} payments in {last} on the Transactions page, or adjust the budget if it "
                           "was unrealistic.", monthly_impact_cents=int(over), annual_impact_cents=int(over * 12),
                    calculation=f"{money(spent[c])} − {money(b)} = {money(over)} over budget.",
                    assumptions=["the budget reflects what you intend to spend"], horizon="this month",
                    drawbacks="A single month can be unusual (e.g. an annual payment).",
                    alternatives=["Raise the budget to a level you can keep", "Spread a one-off payment over months"],
                    evidence_sufficiency="high", progress_tracking=f"{c} budget progress on the Budget page"))
    # 3. recent negative cash flow
    cf = I.cash_flow(s, ctx.account, cur)
    if cf.height >= 3:
        last3 = cf.tail(3)
        if (last3["net_cents"] < 0).all() and last3["income_cents"].sum() > 0:
            gap = int(-last3["net_cents"].mean())
            recs.append(_rec(
                tier=1, title="Expenses exceeded recorded inflows for 3 months",
                issue="Recorded inflows did not cover expenses in each of the last 3 months.",
                evidence="; ".join(f"{m}: net {money(n)}" for m, n in zip(last3["month"], last3["net_cents"])),
                action="Check whether inflows are missing from this file (other accounts) and review the largest "
                       "expense categories.", monthly_impact_cents=gap, annual_impact_cents=gap * 12,
                calculation=f"average monthly shortfall = {money(gap)}",
                assumptions=["this file contains all relevant inflows and expenses"], horizon="next 3 months",
                drawbacks="Transfers and other accounts are not visible; the shortfall may be covered elsewhere.",
                alternatives=["Upload the other accounts' exports", "Use a What-if scenario to test changes"],
                evidence_sufficiency="medium", progress_tracking="monthly net cash flow on the Analytics page"))
    # 4. recurring payment candidates
    rec = I.recurring_candidates(I.scope(clean, ctx.account, cur))
    if rec.height:
        tot = ctx.recurring_monthly_cents
        recs.append(_rec(
            tier=2, title="Review recurring payments",
            issue=f"{rec.height} payment(s) repeat at a regular interval.",
            evidence="; ".join(f"{x['merchant_category']} {money(x['typical_amount_cents'])} {x['period']} "
                               f"({x['occurrences']}×, {x['confidence']} confidence)" for x in rec.iter_rows(named=True)),
            action="Confirm each one is still needed; cancel those that are not.",
            monthly_impact_cents=tot, annual_impact_cents=tot * 12,
            calculation=f"upper bound if all were cancelled: {money(tot)} per month (weekly × 52/12).",
            assumptions=["candidates are detected from amount and timing; they may not be subscriptions"],
            horizon="this month", drawbacks="Some recurring payments are essential (rent, insurance).",
            alternatives=["Switch to a cheaper plan", "Pause instead of cancel"], evidence_sufficiency="medium",
            progress_tracking="recurring payment burden indicator on the Analytics page"))
    # 5. savings goals not supported by history
    for g in goals or []:
        p = plan(g, start_month or (ctx.window[-1] if ctx.window else "2026-01"), ctx)
        req = p["required_monthly_cents"] or g.monthly_contribution_cents
        surplus, basis = ctx.monthly_surplus_cents
        if req and req > max(surplus, 0):
            short = req - max(surplus, 0)
            recs.append(_rec(
                tier=1, title=f"Goal '{g.name}' needs more than your average surplus",
                issue=p["feasibility"] or "", evidence=f"Required {money(req)} per month; average surplus "
                                                       f"{money(surplus)} ({basis}).",
                action="Extend the target date, lower the target, or free up spending (see category suggestions).",
                monthly_impact_cents=int(short), annual_impact_cents=int(short * 12),
                calculation=f"{money(req)} − {money(max(surplus, 0))} = {money(short)} monthly shortfall.",
                assumptions=p["assumptions"], horizon=f"until {g.target_month or p['completion_month']}",
                drawbacks="A longer timeline delays the goal.",
                alternatives=[f"{money(a['monthly_cents'])}/month → done {a['completion_month']}" for a in p["alternatives"]],
                evidence_sufficiency=suff, progress_tracking=f"'{g.name}' progress on the Advisor page"))
    recs.sort(key=lambda x: (x["tier"], -x["monthly_impact_cents"], _EVID[x["evidence_sufficiency"]]))
    for i, x in enumerate(recs, 1):
        x["rank"] = i
    return recs


RANKING_RULE = ("Ranked by (1) urgency tier: problems now before opportunities, (2) estimated monthly impact, "
                "(3) evidence sufficiency. No AI-generated priority score is used.")
