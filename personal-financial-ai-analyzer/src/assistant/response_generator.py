"""Fixed response templates (HW2 5.7). Unsupported questions get one fixed reply."""
from __future__ import annotations

from src.assistant.intent_detection import detect
from src.assistant.query_executor import execute

UNSUPPORTED = ("Sorry, I can't answer that question. I can answer: total spending in a month, "
               "spending on a category, a comparison of two months, budget status, and next month's "
               "expected spending.")
SUPPORTED_EXAMPLES = ["How much did I spend in March?", "How much did I spend on groceries?",
                      "Compare January and February.", "Am I exceeding my budget?",
                      "What is my expected spending next month?"]


def money(cents: int, currency: str) -> str:
    return f"{cents / 100:,.2f} {currency}"


def render(r: dict, currency: str) -> str:
    if r.get("intent") == "unsupported":
        return UNSUPPORTED
    err = r.get("error")
    if err == "no_data":
        return "There is no data for the selected account and currency."
    if err == "month_not_in_data":
        return f"That month is not in your data (available: {r['available'][0]} to {r['available'][1]})."
    if err == "no_budgets":
        return "No budgets are set yet. Open the Budget page to accept or edit the suggested budgets."
    i = r["intent"]
    if i == "total_spending":
        return f"Your total spending in {r['month']} was {money(r['expenses_cents'], currency)}."
    if i == "category_spending":
        when = f"in {r['month']}" if r["month"] else f"from {r['period'][0]} to {r['period'][1]}"
        return f"Your net spending on {r['category']} {when} was {money(r['net_spending_cents'], currency)}."
    if i == "month_comparison":
        (a, b), (va, vb) = r["months"], r["expenses_cents"]
        d = r["difference_cents"]
        trend = "more" if d > 0 else "less" if d < 0 else "the same"
        tail = f" ({money(abs(d), currency)} {trend})" if d else ""
        return f"Spending: {a} {money(va, currency)}; {b} {money(vb, currency)}. {b} was {trend} than {a}{tail}."
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
        return (f"Expected spending for {r['target_month']}: {money(r['forecast_cents'], currency)} "
                f"(model: {r['model']}). This is an estimate, not a guarantee.")
    return UNSUPPORTED


def answer(question: str, summaries, account: str, currency: str, budgets=None, forecast=None) -> tuple[str, dict]:
    intent = detect(question, summaries.category["merchant_category"].unique().to_list())
    result = execute(intent, summaries, account, currency, budgets, forecast)
    return render(result, currency), result
