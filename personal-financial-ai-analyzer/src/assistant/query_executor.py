"""Execute a detected intent against the validated summaries (HW1 F8: answers come from summaries).

Every number returned here is read from `Summaries` (the same object the dashboard displays) or
from the forecasting inference module; nothing is generated or estimated by the assistant itself.
"""
from __future__ import annotations

import polars as pl

from src.analytics.aggregation import Summaries
from src.assistant.intent_detection import Intent
from src.budget.budget_alerts import budget_status


def resolve_month(ym: tuple[int | None, int], available: list[str]) -> str | None:
    year, month = ym
    if year:
        key = f"{year:04d}-{month:02d}"
        return key if key in available else None
    matches = [m for m in available if int(m[5:7]) == month]
    return max(matches) if matches else None          # latest year that has this month


def execute(intent: Intent, s: Summaries, account: str, currency: str, budgets: dict[str, int] | None = None,
            forecast: dict | None = None) -> dict:
    avail = s.months(account, currency)
    if not avail:
        return {"intent": intent.name, "error": "no_data"}
    mon = s.monthly.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
    cat = s.category.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
    months = [resolve_month(m, avail) for m in intent.months]
    if any(m is None for m in months):
        return {"intent": intent.name, "error": "month_not_in_data", "available": [avail[0], avail[-1]]}

    if intent.name == "total_spending":
        target = months[0] if months else avail[-1]
        v = mon.filter(pl.col("month") == target)["expenses_cents"].sum()
        return {"intent": intent.name, "month": target, "expenses_cents": int(v)}
    if intent.name == "category_spending":
        c = cat.filter(pl.col("merchant_category") == intent.category)
        if months:
            c = c.filter(pl.col("month") == months[0])
        return {"intent": intent.name, "category": intent.category, "month": months[0] if months else None,
                "period": [avail[0], avail[-1]] if not months else None,
                "net_spending_cents": int(c["net_spending_cents"].sum())}
    if intent.name == "month_comparison":
        a, b = months[:2]
        va = int(mon.filter(pl.col("month") == a)["expenses_cents"].sum())
        vb = int(mon.filter(pl.col("month") == b)["expenses_cents"].sum())
        return {"intent": intent.name, "months": [a, b], "expenses_cents": [va, vb], "difference_cents": vb - va}
    if intent.name == "budget_status":
        if not budgets:
            return {"intent": intent.name, "error": "no_budgets"}
        current = avail[-1]
        rows = []
        for category, b in sorted(budgets.items()):
            spent = int(cat.filter((pl.col("month") == current) & (pl.col("merchant_category") == category))
                        ["net_spending_cents"].sum())
            rows.append({"category": category, "spent_cents": spent, "budget_cents": int(b),
                         **budget_status(spent, int(b))})
        return {"intent": intent.name, "month": current, "rows": rows}
    if intent.name == "forecast":
        return {"intent": intent.name, **(forecast or {"error": "no_forecast"})}
    return {"intent": "unsupported"}
