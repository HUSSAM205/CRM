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
    relative: int | None = None          # 0 = latest month in the data ("this month"), -1 = the month before
    detail: str | None = None            # sub-question: e.g. "categories", "change", "model", "expense_up"


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
_AMBIGUOUS = re.compile(r"^\s*(spending|spend|spent|expenses?|money|budgets?|costs?)\s*[?.!]*\s*$")
_INDICATOR = re.compile(r"\b(financial indicators?|indicators?|savings? rate|net inflow ratio|spending stability|"
                        r"stability|cash[- ]?flow consistency|recurring (payment )?burden|budget adherence)\b")
_PERCENT = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*(?:%|percent)")


def _amount(t: str) -> float | None:
    """First money-like number that is not a year or a month reference."""
    clean = _MONTH_RE.sub(" ", t)
    for m in _AMOUNT.finditer(clean):
        v = float(m.group(1).replace(",", "."))
        return v
    return None


_OTHER_ACCOUNT = re.compile(r"\b(another|other|someone else'?s?|my (wife|husband|partner|friend)'?s?) (account|user|person)\b"
                            r"|\b(acc-\d+|pl-user-\d+|account (id|number) \w+)\b")


def detect(text: str, categories: list[str]) -> Intent:
    t = text.lower().strip()
    if _OUT_OF_SCOPE.search(t):
        return Intent("unsupported")
    acc_ref = _OTHER_ACCOUNT.search(t)
    if acc_ref:
        return Intent("account_reference", detail=acc_ref.group(0))
    months = find_months(t)
    rel = 0 if re.search(r"\bthis month\b", t) else -1 if re.search(r"\b(last|previous) month\b", t) else None
    pct = _PERCENT.search(t)
    if re.search(r"\bcan i afford\b|\bafford\b", t):
        return Intent("affordability", amount=_amount(t), category=find_category(t, categories))
    if re.search(r"\bwhat (if|happens if)\b|\bsimulat", t):
        up = re.search(r"\b(increase|increases|rise|rises|go up|goes up|grow|grows|higher)\b", t)
        down = re.search(r"\b(decrease|decreases|drop|drops|fall|falls|go down|goes down|lower|reduce|cut)\b", t)
        which = ("income" if re.search(r"\b(income|salary|inflows?)\b", t) else
                 "expenses" if re.search(r"\b(expenses?|spending|costs?)\b", t) and not find_category(t, categories) else None)
        detail = f"{which}_{'up' if up else 'down' if down else '?'}" if which else None
        return Intent("scenario", category=find_category(t, categories), amount=_amount(_PERCENT.sub(" ", t)),
                      percent=float(pct.group(1)) if pct else None, detail=detail)
    if _AMBIGUOUS.match(t):
        return Intent("clarify", detail=t.strip(" ?.!"))           # one bare word: ask, never guess (MA3)
    if re.search(r"\bwhy\b", t) and re.search(r"\b(flag\w*|unusual|marked|highlighted|alert\w*|anomal\w*|stand out)\b", t):
        return Intent("flag_explanation")
    if re.search(r"\b(unusual|anomal\w*|suspicious|odd|strange)\b", t):
        return Intent("unusual_transactions")
    ind = _INDICATOR.search(t)
    if ind and (re.search(r"\b(explain\w*|what (is|does|are)|meaning|mean|define|definition|how is)\b", t)):
        return Intent("indicator_explanation", detail=ind.group(0))
    if re.search(r"\bhow much (can|could) i (save|set aside|put aside)\b|\bsavings? capacity\b|\bwhat can i (save|set aside)\b", t):
        return Intent("savings_capacity")
    if re.search(r"\b(recur\w*|subscriptions?|repeat\w*|regular payments?)\b", t):
        return Intent("recurring")
    if re.search(r"\bbudgets?\b", t) and re.search(r"\b(remain\w*|left|how much budget)\b", t):
        return Intent("budget_remaining")
    if re.search(r"\b(forecast|prediction|estimate|model)\b", t) and re.search(
            r"\b(reliable|accurate|accuracy|which model|what model|why no|why is there no|trust)\b", t):
        return Intent("forecast_info")
    if re.search(r"\b(largest|biggest|top|highest|most) (expense |spending )?categor", t) or \
            re.search(r"\bwhere do i spend (the )?most\b", t):
        return Intent("largest_category", months, relative=rel)
    if re.search(r"\b(highest|most expensive|biggest|top)[- ](spending )?months?\b", t) or (
            re.search(r"\b(which|what) months?\b", t) and re.search(r"\b(highest|most|biggest|largest|top|peak)\b", t)):
        return Intent("highest_months")
    if re.search(r"\b(goals?|on track)\b", t):
        return Intent("savings_goals")
    if re.search(r"\b(recommend\w*|advice|advise|suggest\w*|tips?|how (can|could) i save|where (can|could|should) i cut)\b", t):
        return Intent("recommendations")
    if re.search(r"\b(income|inflows?|earn\w*|salary)\b", t) and re.search(r"\b(change\w*|trend\w*|increas\w*|decreas\w*)\b", t):
        return Intent("income", months, relative=rel, detail="change")
    if re.search(r"\b(trends?|trending|increasing|decreasing|going up|going down|changed?|changes)\b", t):
        return Intent("spending_trend")
    if re.search(r"\b(cash ?flow|net flow|surplus|deficit)\b", t):
        return Intent("cash_flow", months, relative=rel,
                      detail="categories" if re.search(r"\bcategor", t) else None)
    if re.search(r"\b(income|inflows?|earn\w*|receive\w*|received|salary|paid in)\b", t):
        return Intent("income", months, relative=rel,
                      detail="change" if re.search(r"\b(change|changed|trend|increase|decrease)\b", t) else None)
    spend_words = re.search(r"\b(spend|spent|spending|expenses?|cost)\b", t)
    if re.search(r"\b(compare|comparison|versus|vs\.?)\b", t) and len(months) >= 2:
        return Intent("month_comparison", months[:2])
    rels = [0 if m.group(1) == "this" else -1 for m in re.finditer(r"\b(this|last|previous) month\b", t)]
    if re.search(r"\b(compare|comparison|versus|vs\.?)\b", t) and len(months) + len(rels) >= 2:
        return Intent("month_comparison", months[:1], detail="rel:" + ",".join(str(r) for r in rels[:2 - len(months[:1])]))
    if (re.search(r"\bbudgets?\b", t) and re.search(r"\b(exceed|exceeding|over|status|within|limit|am i)\b", t)) or \
            re.search(r"\b(exceed\w*|over) (their |my |the )?(limits?|budgets?)\b", t):
        return Intent("budget_status", months)
    if re.search(r"\b(next month|forecast|predict|expected|expect)\b", t) and spend_words:
        return Intent("forecast")
    if spend_words:
        cat = find_category(t, categories)
        if cat:
            return Intent("category_spending", months, cat, relative=rel)
        named = re.search(r"\bon ([a-z][a-z &-]{2,30}?)(?:\s+(?:in|this|last|during|for)\b|\?|$)", t)
        if named and named.group(1).strip() not in ("average", "total", "it", "them"):
            return Intent("unknown_category", category=named.group(1).strip())     # ask, never guess
        return Intent("total_spending", months, relative=rel)
    return Intent("unsupported")
