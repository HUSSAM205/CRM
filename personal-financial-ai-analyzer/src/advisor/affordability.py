"""Affordability check (master audit 8.6). Conservative by design: without a known current balance and
known obligations the app never says a purchase is affordable; it reports the measurable effect instead."""
from __future__ import annotations

from src.advisor.context import CFG, FinancialContext
from src.advisor.savings import Goal


def assess(amount_cents: int | None, ctx: FinancialContext, payment: str = "one-off",
           category: str | None = None, budgets: dict[str, int] | None = None, goal: Goal | None = None) -> dict:
    if amount_cents is None or amount_cents <= 0:
        return {"needs_input": True, "message": "Enter the purchase amount (and whether it is one-off or monthly)."}
    cur = ctx.currency
    surplus, basis = ctx.monthly_surplus_cents
    out = {"needs_input": False, "amount_cents": amount_cents, "payment": payment,
           "known_context": {"average monthly surplus": f"{surplus / 100:,.2f} {cur} ({basis})",
                             "average monthly expenses": f"{ctx.avg_expenses_cents / 100:,.2f} {cur}",
                             "months of history": ctx.months_observed},
           "effects": [], "missing_information": ctx.unknowns(), "assumptions": [
               "history is representative of the coming months", "no other large purchase is planned"],
           "alternatives": []}
    monthly_equiv = amount_cents if payment == "monthly" else None
    if payment == "one-off":
        if surplus > 0:
            months = amount_cents / surplus
            out["effects"].append(f"Equals {months:.1f} month(s) of your average monthly surplus.")
            out["alternatives"].append(f"Save {surplus * 0.5 / 100:,.2f} {cur} per month (half your surplus) and buy "
                                       f"in about {amount_cents / (surplus * 0.5):.0f} month(s).")
        else:
            out["effects"].append("Your history shows no average monthly surplus to pay for it from.")
    else:
        out["effects"].append(f"Raises monthly expenses from {ctx.avg_expenses_cents / 100:,.2f} to "
                              f"{(ctx.avg_expenses_cents + amount_cents) / 100:,.2f} {cur}; surplus becomes "
                              f"{(surplus - amount_cents) / 100:,.2f}.")
    if category and budgets and budgets.get(category, 0) > 0:
        spent = ctx.category_avg_recent_cents.get(category, 0)
        new = spent + (monthly_equiv or amount_cents)
        out["effects"].append(f"{category} budget {budgets[category] / 100:,.2f}: recent average {spent / 100:,.2f} → "
                              f"{new / 100:,.2f} ({new / budgets[category]:.0%} of budget).")
    if goal is not None and goal.monthly_contribution_cents:
        delay = (amount_cents / goal.monthly_contribution_cents) if payment == "one-off" else None
        out["effects"].append(f"If paid from your '{goal.name}' savings, the goal is delayed by about "
                              f"{delay:.1f} month(s)." if delay else
                              f"A monthly payment competes with your '{goal.name}' contribution of "
                              f"{goal.monthly_contribution_cents / 100:,.2f}.")
    bal = ctx.user.current_balance_cents
    buffer = ctx.avg_expenses_cents * CFG["affordability_buffer_months"]
    if bal is None or ctx.user.monthly_obligations_cents is None:
        out["verdict"] = "cannot_confirm"
        out["summary"] = ("Cannot confirm affordability: your current balance and/or upcoming obligations are unknown "
                          "to this app. The effects below are based on your transaction history only.")
    else:
        after = bal - (amount_cents if payment == "one-off" else 0) - ctx.user.monthly_obligations_cents
        out["known_context"]["balance after purchase and this month's obligations"] = f"{after / 100:,.2f} {cur}"
        if payment == "monthly" and surplus - amount_cents < 0:
            out["verdict"], out["summary"] = "not_supported", "Not supported: the monthly cost exceeds your average surplus."
        elif after >= buffer:
            out["verdict"] = "within_known_means"
            out["summary"] = (f"Within your stated means: after paying, {after / 100:,.2f} {cur} remains, at least "
                              f"{CFG['affordability_buffer_months']} month(s) of average expenses ({buffer / 100:,.2f}).")
        else:
            out["verdict"] = "tight"
            out["summary"] = (f"Tight: {after / 100:,.2f} {cur} would remain, less than one month of average expenses "
                              f"({buffer / 100:,.2f}).")
        out["alternatives"].append("Wait until the remaining amount covers at least one month of expenses.")
    return out
