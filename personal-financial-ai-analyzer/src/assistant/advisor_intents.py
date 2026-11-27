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
                   "recommendations", "scenario", "affordability", "recurring", "budget_remaining", "forecast_info",
                   "largest_category", "highest_months", "unknown_category", "account_reference",
                   "savings_capacity", "flag_explanation", "indicator_explanation"}


@dataclass
class AssistantContext:
    clean: pl.DataFrame
    goals: list[S.Goal] = field(default_factory=list)
    user: UserFacts = field(default_factory=UserFacts)


def _rel_month(avail: list[str], rel: int | None) -> str | None:
    if rel is None:
        return None
    y, mo = map(int, avail[-1].split("-"))
    k = y * 12 + mo - 1 + rel
    return f"{k // 12:04d}-{k % 12 + 1:02d}"


def execute(intent: Intent, s, account: str, currency: str, months: list[str | None], avail: list[str],
            budgets: dict | None, ctx: AssistantContext | None, forecast: dict | None = None) -> dict:
    base = {"intent": intent.name, "scope": {"account": account, "currency": currency,
                                             "period": [avail[0], avail[-1]]}}
    rel = _rel_month(avail, intent.relative)
    if rel and not months:
        months = [rel]
    if intent.name == "account_reference":
        same = intent.detail and intent.detail.strip().lower() == account.lower()
        return {**base, "error": "same_account" if same else "other_account"}
    if intent.name == "unknown_category":
        cats = sorted(s.category.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
                      ["merchant_category"].unique().to_list())
        return {**base, "error": "unknown_category", "asked": intent.category, "categories": cats}
    if intent.name == "largest_category":
        c = s.category.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
        if months:
            c = c.filter(pl.col("month") == months[0])
        t = c.group_by("merchant_category").agg(pl.col("net_spending_cents").sum()).sort("net_spending_cents", descending=True)
        if t.is_empty() or t["net_spending_cents"][0] <= 0:
            return {**base, "error": "message", "message": "There is no category spending in that period."}
        return {**base, "month": months[0] if months else None, "category": t["merchant_category"][0],
                "net_spending_cents": int(t["net_spending_cents"][0]),
                "share": float(t["net_spending_cents"][0] / t.filter(pl.col("net_spending_cents") > 0)["net_spending_cents"].sum())}
    if intent.name == "highest_months":
        m = I.monthly_series(s, account, currency).sort("expenses_cents", descending=True).head(3)
        return {**base, "months": list(zip(m["month"], m["expenses_cents"]))}
    if intent.name == "budget_remaining":
        if not budgets:
            return {**base, "error": "no_budgets_set"}
        last = avail[-1]
        c = s.category.filter((pl.col("account_id") == account) & (pl.col("currency") == currency) & (pl.col("month") == last))
        spent = dict(zip(c["merchant_category"], c["net_spending_cents"]))
        rows = [{"category": k, "budget_cents": int(b), "spent_cents": int(spent.get(k, 0)),
                 "remaining_cents": int(b) - int(spent.get(k, 0))} for k, b in sorted(budgets.items()) if b > 0]
        return {**base, "month": last, "rows": rows}
    if intent.name == "forecast_info":
        return {**base, **(forecast or {"eligible": False, "message": "No forecast information is available."})}
    if intent.name in ("income", "cash_flow"):
        cf = I.cash_flow(s, account, currency)
        if intent.name == "income" and intent.detail == "change" and not months and cf.height >= 6:
            a, b = int(cf.tail(6).head(3)["income_cents"].sum()), int(cf.tail(3)["income_cents"].sum())
            return {**base, "month": None, "change": True, "prior": a, "recent": b,
                    "prior_months": [cf.tail(6)["month"][0], cf.tail(6)["month"][2]], "recent_months": [cf.tail(3)["month"][0], cf.tail(3)["month"][-1]]}
        if intent.name == "cash_flow" and intent.detail == "categories":
            c = s.category.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
            win = cf.tail(6)["month"].to_list() if not months else months
            t = (c.filter(pl.col("month").is_in(win)).group_by("merchant_category").agg(pl.col("net_spending_cents").sum())
                  .sort("net_spending_cents", descending=True).head(3))
            return {**base, "month": None, "categories": True, "window": [win[0], win[-1]],
                    "top": list(zip(t["merchant_category"], t["net_spending_cents"]))}
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
    if intent.name == "flag_explanation":                    # MA3-06: evidence behind each review candidate
        from src.models.anomaly.anomaly_scoring import review_candidates
        r = review_candidates(ctx.clean, account, currency)
        if not r["ok"]:
            return {**base, "error": "message", "message": r["message"]}
        c = r["candidates"].head(3)
        return {**base, "label": r["label"], "not_fraud": r["not_fraud"], "method": r["method"], "window": r["window"],
                "count": r["candidates"].height,
                "items": [{"date": str(x["transaction_timestamp"])[:10], "category": x["merchant_category"],
                           "amount": x["amount"], "usual": x["usual_amount_in_your_history"],
                           "explanation": x["explanation"], "surfaced_by": x["surfaced_by"]} for x in c.iter_rows(named=True)]}
    if intent.name == "indicator_explanation":                # MA3-07: formula, value and reading of an indicator
        rows = I.indicators(ctx.clean, s, account, currency, budgets)
        asked = (intent.detail or "").lower()
        alias = {"savings rate": "net inflow ratio", "saving rate": "net inflow ratio", "stability": "spending stability",
                 "recurring burden": "recurring payment burden"}
        key = alias.get(asked, asked)
        hit = [x for x in rows if key and key in x["indicator"].lower()]
        return {**base, "indicators": hit or rows, "specific": bool(hit)}
    fc = build_context(ctx.clean, s, account, currency, ctx.user)
    if intent.name == "savings_capacity":                     # MA3-05: surplus from recorded data, unknowns stated
        surplus, basis = fc.monthly_surplus_cents
        return {**base, "surplus_cents": surplus, "basis": basis, "window": [fc.window[0], fc.window[-1]],
                "unknowns": fc.unknowns(), "essential_cents": fc.avg_essential_cents,
                "discretionary_cents": fc.avg_discretionary_cents}
    if intent.name == "savings_goals":
        if not ctx.goals:
            return {**base, "error": "no_goals"}
        return {**base, "plans": [S.plan(g, fc.window[-1], fc) for g in ctx.goals]}
    if intent.name == "recommendations":
        recs = R.generate(ctx.clean, s, fc, budgets, ctx.goals, fc.window[-1])
        return {**base, "recommendations": [{k: r[k] for k in ("rank", "title", "monthly_impact_cents", "evidence")}
                                            for r in recs[:3]], "total": len(recs)}
    if intent.name == "recurring":
        rec = I.recurring_candidates(I.scope(ctx.clean, account, currency))
        return {**base, "candidates": [{k: r[k] for k in ("merchant_category", "period", "typical_amount_cents",
                                                          "median_interval_days", "occurrences", "confidence")}
                                       for r in rec.iter_rows(named=True)]}
    if intent.name == "scenario":
        if intent.detail and intent.detail.endswith("?"):
            return {**base, "error": "scenario_params"}
        if intent.detail and intent.percent:
            which, way = intent.detail.split("_")
            sign = 1 if way == "up" else -1
            sc = (SC.Scenario(income_change_pct=sign * intent.percent) if which == "income"
                  else SC.Scenario(expense_change_pct=sign * intent.percent))
            desc = f"your {which} {'rise' if sign > 0 else 'fall'} by {intent.percent:g}%"   # full clause
            r = SC.simulate(fc, sc)
            return {**base, "description": desc, **{k: r[k] for k in ("label", "baseline", "scenario",
                                                                     "difference_monthly_cents",
                                                                     "difference_over_horizon_cents", "horizon_months")},
                    "savings_after_horizon_cents": r["path"][-1]["savings_pot_cents"]}
        if intent.category and intent.percent:
            sc = SC.Scenario(category_cuts_pct={intent.category: intent.percent})
            desc = f"you reduce {intent.category} by {intent.percent:g}%"
        elif intent.amount:
            sc = SC.Scenario(extra_saving_cents=int(round(intent.amount * 100)))
            desc = f"you save {intent.amount:,.2f} {currency} more each month"
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
    if err == "other_account":
        return ("I can only answer about the account selected in the sidebar. Select the other account there "
                "(if it is in your uploaded file) and ask again.")
    if err == "same_account":
        return "You are already viewing that account; ask your question without the account ID."
    if err == "unknown_category":
        return (f"I don't know a category called '{r['asked']}' in this account. Your categories are: "
                f"{', '.join(r['categories'])}. Which one did you mean?")
    if err == "no_budgets_set":
        return "No budgets are set yet. Open the Budget page to accept or edit the suggested budgets."
    if err == "scenario_params":
        return ("Please say what to change, for example: What if I reduce dining by 10%? What if I save 200 more "
                "every month? What if my income drops 10%? What happens if my expenses increase by 5%?")
    if i == "largest_category":
        when = f"in {r['month']}" if r["month"] else f"from {r['scope']['period'][0]} to {r['scope']['period'][1]}"
        return (f"Your largest expense category {when} was {r['category']}: {m(r['net_spending_cents'])} "
                f"({r['share']:.0%} of category spending).")
    if i == "highest_months":
        return "Your highest-spending months: " + "; ".join(f"{mm} {m(v)}" for mm, v in r["months"]) + "."
    if i == "budget_remaining":
        over = [x for x in r["rows"] if x["remaining_cents"] < 0]
        return (f"Budget remaining in {r['month']}: " + "; ".join(
            f"{x['category']} {m(x['remaining_cents'])} left of {m(x['budget_cents'])}" if x["remaining_cents"] >= 0
            else f"{x['category']} over by {m(-x['remaining_cents'])}" for x in r["rows"]) + "."
            + (f" {len(over)} categor{'y is' if len(over) == 1 else 'ies are'} over budget." if over else ""))
    if i == "recurring":
        if not r["candidates"]:
            return "No payments repeat with a similar amount at a regular weekly or monthly interval."
        return ("Recurring payment candidates (not confirmed subscriptions): " + "; ".join(
            f"{c['merchant_category']} about {m(c['typical_amount_cents'])} {c['period']} (every "
            f"{c['median_interval_days']:g} days, {c['occurrences']}×, {c['confidence']} confidence)"
            for c in r["candidates"]) + ".")
    if i == "forecast_info":
        if not r.get("eligible"):
            return f"No estimate is shown: {r.get('message', 'insufficient history')}"
        return (f"{r.get('forecast_category', 'Estimate')}. The estimate for {r['target_month']} comes from {r['method']} "
                f"({r['model_status']}), using your history "
                f"{r['historical_window']}. Evidence: {r['evidence']} Limitations: {r['limitations']}")
    if i == "income" and r.get("change"):
        a, b = r["prior"], r["recent"]
        trend = "higher than" if b > a else "lower than" if b < a else "the same as"
        return (f"Recorded inflows {r['recent_months'][0]}..{r['recent_months'][1]}: {m(b)}, {trend} "
                f"{r['prior_months'][0]}..{r['prior_months'][1]} ({m(a)}). Inflows are not known to be salary.")
    if i == "cash_flow" and r.get("categories"):
        return (f"Categories with the most spending {r['window'][0]}..{r['window'][1]} (they reduce your cash flow most): "
                + "; ".join(f"{c} {m(v)}" for c, v in r["top"]) + ".")
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
        return (f"{r['label']}: if {r['description']}, your monthly net changes from "
                f"{m(r['baseline']['monthly_net_cents'])} to {m(r['scenario']['monthly_net_cents'])} "
                f"({m(r['difference_monthly_cents'])} per month, {m(r['difference_over_horizon_cents'])} over "
                f"{r['horizon_months']} months)."
                + (f" Money set aside after {r['horizon_months']} months: {m(r['savings_after_horizon_cents'])}."
                   if r["scenario"]["monthly_saving_cents"] else ""))
    if i == "affordability":
        return f"{r['summary']} {' '.join(r['effects'])} Unknown: {'; '.join(r['missing'][:2])}."
    if i == "savings_capacity":
        w = f"{r['window'][0]}..{r['window'][1]}"
        if r["surplus_cents"] > 0:
            head = (f"On average you had {m(r['surplus_cents'])} per month left over in {w} ({r['basis']}). If that "
                    "pattern continues, that is roughly the most you could set aside each month.")
        else:
            head = (f"In {w} your average expenses were higher than the money coming in by {m(-r['surplus_cents'])} per "
                    f"month ({r['basis']}), so there is no surplus to set aside at the current pattern. Non-essential "
                    f"spending averaged {m(r['discretionary_cents'])} per month; see the Financial advisor page for options.")
        return head + f" This is transaction-derived, not a bank balance. Unknown: {'; '.join(r['unknowns'][:3])}."
    if i == "flag_explanation":
        parts = [f"{x['date']} {x['category']} {x['amount']:,.2f} {currency} (usual about {x['usual']:,.2f}): "
                 f"{x['explanation']} [surfaced by {x['surfaced_by']}]" for x in r["items"]]
        return (f"{r['label']} {r['count']} transaction(s) in {r['window']} were flagged because they differ from your "
                f"own history. " + " | ".join(parts) + f". Method: {r['method']}. {r['not_fraud']}")
    if i == "indicator_explanation":
        def one(x):
            v = "not available" if x["value"] is None else f"{x['value']:g}"
            return f"{x['indicator']}: {v}. Formula: {x['formula']}. How to read it: {x['reading']}."
        if r["specific"]:
            return " ".join(one(x) for x in r["indicators"])
        return ("Indicators for this account (no combined score is computed): " + " ".join(one(x) for x in r["indicators"]))
    return None
