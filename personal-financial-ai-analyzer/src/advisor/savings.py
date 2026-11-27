"""Savings goals (master audit 8.4, 10): deterministic plan, progress, completion estimate, alternatives and
a feasibility statement that only uses known figures. Months are calendar months 'YYYY-MM'."""
from __future__ import annotations

import math
from dataclasses import dataclass

from src.advisor.context import CFG, FinancialContext


@dataclass
class Goal:
    name: str
    target_cents: int
    saved_cents: int = 0                       # user-provided; 0 if not supplied
    target_month: str | None = None            # 'YYYY-MM'
    monthly_contribution_cents: int | None = None
    kind: str = "savings"                      # savings | emergency_fund | expense_reduction


def months_between(start: str, end: str) -> int:
    """Number of monthly contributions from the month after `start` up to and including `end`."""
    (y0, m0), (y1, m1) = map(int, start.split("-")), map(int, end.split("-"))
    return (y1 - y0) * 12 + (m1 - m0)


def add_months(month: str, k: int) -> str:
    y, m = map(int, month.split("-"))
    t = y * 12 + (m - 1) + k
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


def emergency_fund_target(ctx: FinancialContext, months: int | None = None) -> dict:
    k = months or CFG["emergency_fund_months"]
    return {"target_cents": ctx.avg_expenses_cents * k,
            "calculation": f"{k} × average monthly expenses {ctx.avg_expenses_cents / 100:,.2f} {ctx.currency} "
                           f"({ctx.window[0]}..{ctx.window[-1]})" if ctx.window else "no expense history",
            "months": k}


def emergency_fund_plan(ctx: FinancialContext, coverage_months: float, current_cents: int = 0,
                        monthly_contribution_cents: int | None = None, basis: str = "essential") -> dict:
    """User-defined emergency fund: target = coverage_months x average monthly ESSENTIAL expenses (or all
    expenses if basis='all'). Nothing is assumed about the right coverage: the user chooses it."""
    monthly = ctx.avg_essential_cents if basis == "essential" else ctx.avg_expenses_cents
    target = int(round(coverage_months * monthly))
    remaining = max(target - current_cents, 0)
    out = {"basis": basis, "coverage_months": coverage_months, "monthly_basis_cents": monthly, "target_cents": target,
           "current_cents": current_cents, "remaining_cents": remaining,
           "progress": round(min(current_cents / target, 1.0), 4) if target > 0 else None,
           "months_to_complete": None,
           "calculation": f"{coverage_months:g} × average monthly {'essential ' if basis == 'essential' else ''}expenses "
                          f"{monthly / 100:,.2f} {ctx.currency}" + (f" ({ctx.window[0]}..{ctx.window[-1]})" if ctx.window else "")}
    if target == 0:
        out["note"] = ("No essential spending was found in your categories; choose 'all expenses' or check the "
                       "category classes in configs/advisor.yaml.") if basis == "essential" else "No expense history."
    if monthly_contribution_cents and monthly_contribution_cents > 0 and remaining > 0:
        out["months_to_complete"] = math.ceil(remaining / monthly_contribution_cents)
    return out


def goal_status(p: dict, goal: Goal) -> str:
    """reached | on track | behind | no plan (no contribution and no target date)."""
    if p["remaining_cents"] == 0:
        return "reached"
    if goal.target_month and goal.monthly_contribution_cents:
        return "on track" if goal.monthly_contribution_cents >= (p["required_monthly_cents"] or 0) else "behind"
    if goal.target_month or goal.monthly_contribution_cents:
        return "partially planned"
    return "no plan"


def plan(goal: Goal, start_month: str, ctx: FinancialContext | None = None) -> dict:
    """Required monthly saving, progress, completion estimate, alternatives and feasibility."""
    remaining = max(goal.target_cents - goal.saved_cents, 0)
    out = {"goal": goal.name, "kind": goal.kind, "target_cents": goal.target_cents, "saved_cents": goal.saved_cents,
           "remaining_cents": remaining,
           "progress": round(goal.saved_cents / goal.target_cents, 4) if goal.target_cents > 0 else None,
           "start_month": start_month, "required_monthly_cents": None, "months_left": None,
           "completion_month": None, "alternatives": [], "feasibility": None, "assumptions": [
               "contributions are made at the end of each month", "no interest or investment returns are assumed",
               "the saved amount is what you entered; it is not read from your transactions"]}
    if remaining == 0:
        out["feasibility"] = "Goal already reached."
        out["status"] = "reached"
        return out
    if goal.target_month:
        n = months_between(start_month, goal.target_month)
        out["months_left"] = n
        out["required_monthly_cents"] = math.ceil(remaining / n) if n > 0 else None
        if n <= 0:
            out["feasibility"] = "The target month is not in the future; choose a later month."
    contrib = goal.monthly_contribution_cents
    if contrib and contrib > 0:
        k = math.ceil(remaining / contrib)
        out["completion_month"] = add_months(start_month, k)
        out["months_with_contribution"] = k
        out["milestones"] = []          # month in which 25/50/75/100% of the target is first reached
        for frac in (0.25, 0.5, 0.75, 1.0):
            need = frac * goal.target_cents - goal.saved_cents
            if need > 0:
                out["milestones"].append({"share": frac, "month": add_months(start_month, math.ceil(need / contrib))})
        for f in (0.5, 1.5, 2.0):
            c = max(int(round(contrib * f)), 1)
            kk = math.ceil(remaining / c)
            out["alternatives"].append({"monthly_cents": c, "months": kk, "completion_month": add_months(start_month, kk)})
    out["status"] = goal_status(out, goal)
    req = out["required_monthly_cents"] or contrib
    if req and ctx is not None and out["feasibility"] is None:
        surplus, basis = ctx.monthly_surplus_cents
        if ctx.months_observed == 0:
            out["feasibility"] = "Cannot assess: there is no transaction history for this currency."
        elif surplus <= 0:
            out["feasibility"] = (f"Not supported by your history: {basis} is {surplus / 100:,.2f} {ctx.currency} per month, "
                                  f"so saving {req / 100:,.2f} would need lower spending or additional income.")
        elif req <= surplus:
            out["feasibility"] = (f"Appears feasible from history: {req / 100:,.2f} is {req / surplus:.0%} of your "
                                  f"average monthly surplus ({basis}: {surplus / 100:,.2f} {ctx.currency}). "
                                  f"Your current balance and obligations are not known to this app.")
        else:
            out["feasibility"] = (f"Stretch: {req / 100:,.2f} exceeds your average monthly surplus "
                                  f"({surplus / 100:,.2f} {ctx.currency}, {basis}) by {(req - surplus) / 100:,.2f}.")
    return out
