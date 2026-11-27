"""Rule-based intent detection for the financial assistant (HW1 S8, HW2 5.7). No LLM.

Supported intents: total_spending, category_spending, month_comparison, budget_status, forecast.
Months are recognised by English month names (with an optional 4-digit year) or YYYY-MM.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july",
                                      "august", "september", "october", "november", "december"], 1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
_MONTH_RE = re.compile(r"\b(\d{4})-(\d{2})\b|\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) +
                       r")\b(?:\s+(\d{4}))?", re.I)


@dataclass
class Intent:
    name: str
    months: list[tuple[int | None, int]] = field(default_factory=list)   # (year or None, month)
    category: str | None = None


def find_months(text: str) -> list[tuple[int | None, int]]:
    out = []
    for m in _MONTH_RE.finditer(text):
        if m.group(1):
            out.append((int(m.group(1)), int(m.group(2))))
        else:
            out.append((int(m.group(4)) if m.group(4) else None, MONTHS[m.group(3).lower()]))
    return out


def find_category(text: str, categories: list[str]) -> str | None:
    t = text.lower()
    for c in sorted(categories, key=len, reverse=True):
        stem = c.lower().rstrip("s")
        if re.search(rf"\b{re.escape(stem)}s?\b", t):
            return c
    return None


def detect(text: str, categories: list[str]) -> Intent:
    t = text.lower().strip()
    months = find_months(t)
    spend_words = re.search(r"\b(spend|spent|spending|expenses?|cost)\b", t)
    if re.search(r"\b(compare|comparison|versus|vs\.?)\b", t) and len(months) >= 2:
        return Intent("month_comparison", months[:2])
    if re.search(r"\bbudgets?\b", t) and re.search(r"\b(exceed|exceeding|over|status|within|limit|am i)\b", t):
        return Intent("budget_status", months)
    if re.search(r"\b(next month|forecast|predict|expected|expect)\b", t) and spend_words:
        return Intent("forecast")
    if spend_words:
        cat = find_category(t, categories)
        if cat:
            return Intent("category_spending", months, cat)
        return Intent("total_spending", months)
    return Intent("unsupported")
