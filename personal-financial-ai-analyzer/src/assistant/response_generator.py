"""Fixed response templates (HW2 5.7). Unsupported questions get one fixed reply."""
from __future__ import annotations

from src.assistant.advisor_intents import AssistantContext
from src.assistant.advisor_intents import render as advisor_render
from src.assistant.intent_detection import detect
from src.assistant.query_executor import execute

UNSUPPORTED = ("Sorry, I can't answer that question. I can answer: total spending in a month, "
               "spending on a category, a comparison of two months, budget status, next month's "
               "expected spending, income (recorded inflows), cash flow, spending trends, unusual transactions, "
               "savings goals, recommendations, what-if scenarios, whether a purchase is affordable, your largest "
               "category, highest-spending months, recurring payments, remaining budget, how much you could save, why a "
               "transaction was flagged, what an indicator means and how reliable the estimate is. "
               "I do not give investment, credit, tax or legal advice and I cannot judge fraud.")
SUPPORTED_EXAMPLES = ["How much did I spend in March?", "How much did I spend on groceries?",
                      "Compare January and February.", "Am I exceeding my budget?",
                      "What is my expected spending next month?", "What was my cash flow last month?",
                      "Is my spending increasing?", "Show unusual transactions", "Any recommendations?",
                      "What if I reduce dining by 10%?", "Can I afford 450?", "How much did I spend last month?",
                      "What is my largest expense category?", "What payments appear to recur?",
                      "How much budget remains?", "Is the prediction reliable?", "Compare this month with last month",
                      "Which months had the highest spending?", "How much can I save?",
                      "Why was this transaction flagged?", "Explain the savings rate"]


def money(cents: int, currency: str) -> str:
    return f"{cents / 100:,.2f} {currency}"


def render(r: dict, currency: str) -> str:
    adv = advisor_render(r, currency)
    if adv is not None:
        return adv
    if r.get("intent") == "unsupported":
        return UNSUPPORTED
    if r.get("intent") == "clarify":
        return ("Could you be more specific? For example: 'How much did I spend last month?', 'How much did I spend "
                "on groceries?', 'Compare this month with last month' or 'Am I exceeding my budget?'. I don't guess "
                "what a short question means.")
    err = r.get("error")
    if err == "no_data":
        return "There is no data for the selected account and currency."
    if err == "month_not_in_data":
        return f"That month is not in your data (available: {r['available'][0]} to {r['available'][1]})."
    if err == "no_budgets":
        return "No budgets are set yet. Open the Budget page to accept or edit the suggested budgets."
    i = r["intent"]
    tail = f" ({r['note']})" if r.get("note") else ""
    if i == "total_spending":
        return f"Your total spending in {r['month']} was {money(r['expenses_cents'], currency)}.{tail}"
    if i == "category_spending":
        when = f"in {r['month']}" if r["month"] else f"from {r['period'][0]} to {r['period'][1]}"
        return f"Your net spending on {r['category']} {when} was {money(r['net_spending_cents'], currency)}.{tail}"
    if i == "month_comparison":
        (a, b), (va, vb) = r["months"], r["expenses_cents"]
        d = r["difference_cents"]
        trend = "more" if d > 0 else "less" if d < 0 else "the same"
        tail = f" ({money(abs(d), currency)} {trend})" if d else ""
        note = f" ({r['note']})" if r.get("note") else ""
        return f"Spending: {a} {money(va, currency)}; {b} {money(vb, currency)}. {b} was {trend} than {a}{tail}.{note}"
    if i == "budget_status":
        over = [x for x in r["rows"] if x["level"] == "exceeded"]
        warn = [x for x in r["rows"] if x["level"] == "warning"]
        if not over and not warn:
            return f"In {r['month']} you are within all budgets."
        parts = [f"{x['category']}: {money(x['spent_cents'], currency)} of {money(x['budget_cents'], currency)} "
                 f"({x['ratio']:.0%})" for x in over + warn]
        return (f"In {r['month']}: {len(over)} budget(s) exceeded, {len(warn)} at 80% or more. " + "; ".join(parts) + ".")
    if i == "forecast":
        if not r.get("eligible"):
            return r.get("message", "Not enough history for a forecast.")
        if "point_cents" in r and r.get("method") == "gbr_personaledger":      # accepted model (D-24)
            lo, hi = r["interval_cents"]
            return (f"Estimated spending for {r['target_month']}: {money(r['point_cents'], currency)} "
                    f"(80% range {money(lo, currency)} to {money(hi, currency)}; model gbr_personaledger, accepted in "
                    f"experiment E2-B on synthetic data; history {r['historical_window']}). This is an estimate, "
                    f"not a guarantee.")
        if "point_cents" in r:     # deterministic outlook (D-22)
            lo, hi = r["historical_range_cents"]
            return (f"Typical spending for {r['target_month']}: {money(r['point_cents'], currency)} (median of your "
                    f"past months; usual range {money(lo, currency)} to {money(hi, currency)}). Machine-learning "
                    f"forecasting was not effective for series like yours, so this is a historical reference, "
                    f"not a prediction.")
        return (f"Expected spending for {r['target_month']}: {money(r['forecast_cents'], currency)} "
                f"(model: {r['model']}). This is an estimate, not a guarantee.")
    return UNSUPPORTED


def answer(question: str, summaries, account: str, currency: str, budgets=None, forecast=None,
           context: AssistantContext | None = None) -> tuple[str, dict]:
    """Read-only: answers from validated summaries (and, for advisor intents, the validated records of the
    SAME account and currency in `context`). The question text is only pattern-matched, never executed."""
    intent = detect(question[:500], summaries.category["merchant_category"].unique().to_list())
    result = execute(intent, summaries, account, currency, budgets, forecast, context)
    return render(result, currency), result
