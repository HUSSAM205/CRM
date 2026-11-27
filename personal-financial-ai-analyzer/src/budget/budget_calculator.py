"""Budget suggestions (HW2 5.6, HW1 F5): median of the last three COMPLETED months per category.

"Completed months" = the three calendar months immediately before the reference (current) month,
which is the latest month present in the data unless given. Months with no spending in a category
count as 0 (spending nothing is real history). Suggestions are historical heuristics, not predictions
and not financial advice; each carries a plain-language explanation.
"""
from __future__ import annotations

from statistics import median

import polars as pl

from src.experiments.data_splitting import month_range


def previous_months(month: str, n: int = 3) -> list[str]:
    y, m = map(int, month.split("-"))
    out = []
    for _ in range(n):
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
        out.append(f"{y:04d}-{m:02d}")
    return sorted(out)


def suggest_budgets(category: pl.DataFrame, account: str, currency: str, current_month: str) -> pl.DataFrame:
    hist_months = previous_months(current_month, 3)
    c = category.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
    cats = sorted(c["merchant_category"].unique().to_list())
    rows = []
    for cat in cats:
        vals = []
        for m in hist_months:
            v = c.filter((pl.col("merchant_category") == cat) & (pl.col("month") == m))["net_spending_cents"]
            vals.append(int(v.sum()) if v.len() else 0)
        sug = int(round(median(vals)))
        spent = c.filter((pl.col("merchant_category") == cat) & (pl.col("month") == current_month))["net_spending_cents"]
        rows.append({"merchant_category": cat, **{f"m{i + 1}_{m}": v for i, (m, v) in enumerate(zip(hist_months, vals))},
                     "suggested_cents": max(sug, 0), "spent_current_cents": int(spent.sum()) if spent.len() else 0,
                     "explanation": (f"Median of {', '.join(hist_months)} net spending "
                                     f"({', '.join(f'{v / 100:.2f}' for v in vals)}) = {sug / 100:.2f} {currency}"
                                     + (" (negative median floored at 0)" if sug < 0 else ""))})
    return pl.DataFrame(rows) if rows else pl.DataFrame()


def months_available(category: pl.DataFrame, account: str, currency: str) -> list[str]:
    ms = category.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))["month"]
    return month_range(ms.min(), ms.max()) if ms.len() else []
