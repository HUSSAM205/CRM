"""Rule-based intent detection for the financial assistant (HW1 S8, HW2 5.7). No LLM.

HW2 intents (unchanged): total_spending, category_spending, month_comparison, budget_status, forecast.
Master-audit intents (same deterministic approach): income, cash_flow, spending_trend, unusual_transactions,
savings_goals, recommendations, scenario, affordability. Questions about fraud, investments, stocks, credit or
loans are deliberately unsupported (fixed reply).
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
    amount: float | None = None
    percent: float | None = None


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


_OUT_OF_SCOPE = re.compile(r"\b(fraud|stocks?|shares|invest\w*|crypto\w*|bitcoin|loan|mortgage|credit score|tax)\b")
_AMOUNT = re.compile(r"(?<![\d-])(\d{1,12}(?:[.,]\d{1,2})?)(?!\s*%)(?![\d-])")
_PERCENT = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*(?:%|percent)")


def _amount(t: str) -> float | None:
    """First money-like number that is not a year or a month reference."""
    clean = _MONTH_RE.sub(" ", t)
    for m in _AMOUNT.finditer(clean):
        v = float(m.group(1).replace(",", "."))
        return v
    return None


def detect(text: str, categories: list[str]) -> Intent:
    t = text.lower().strip()
    if _OUT_OF_SCOPE.search(t):
        return Intent("unsupported")
    months = find_months(t)
    pct = _PERCENT.search(t)
    if re.search(r"\bcan i afford\b|\bafford\b", t):
        return Intent("affordability", amount=_amount(t), category=find_category(t, categories))
    if re.search(r"\bwhat if\b|\bsimulat", t):
        return Intent("scenario", category=find_category(t, categories), amount=_amount(_PERCENT.sub(" ", t)),
                      percent=float(pct.group(1)) if pct else None)
    if re.search(r"\b(unusual|anomal\w*|suspicious|odd|strange)\b", t):
        return Intent("unusual_transactions")
    if re.search(r"\b(goals?|on track)\b", t):
        return Intent("savings_goals")
    if re.search(r"\b(recommend\w*|advice|advise|suggest\w*|tips?|how (can|could) i save|where (can|could|should) i cut)\b", t):
        return Intent("recommendations")
    if re.search(r"\b(trends?|trending|increasing|decreasing|going up|going down|changed?|changes)\b", t):
        return Intent("spending_trend")
    if re.search(r"\b(cash ?flow|net flow|surplus|deficit)\b", t):
        return Intent("cash_flow", months)
    if re.search(r"\b(income|inflows?|earn\w*|receive\w*|received|salary|paid in)\b", t):
        return Intent("income", months)
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
