"""Budget warnings at 80% and 100% (HW2 5.6)."""
from __future__ import annotations

WARN_RATIO, LIMIT_RATIO = 0.80, 1.00


def budget_status(spent_cents: int, budget_cents: int) -> dict:
    if budget_cents <= 0:
        return {"level": "no_budget", "ratio": None, "message": "No budget set."}
    ratio = spent_cents / budget_cents
    if ratio >= LIMIT_RATIO:
        level, msg = "exceeded", f"Over budget: {ratio:.0%} used."
    elif ratio >= WARN_RATIO:
        level, msg = "warning", f"Warning: {ratio:.0%} of budget used."
    else:
        level, msg = "ok", f"{ratio:.0%} of budget used."
    return {"level": level, "ratio": ratio, "message": msg}
