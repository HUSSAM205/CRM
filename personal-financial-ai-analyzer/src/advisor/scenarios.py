"""What-if scenarios (master audit 8.7): deterministic month-by-month simulation of the average monthly
budget. A simulation applies stated changes to historical averages; it is NOT a prediction."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.advisor.context import FinancialContext


@dataclass
class Scenario:
    horizon_months: int = 12
    category_cuts_pct: dict[str, float] = field(default_factory=dict)   # e.g. {"dining": 10} = spend 10% less
    extra_saving_cents: int = 0                                           # set aside each month
    income_change_pct: float = 0.0                                        # e.g. -10 = income falls 10%
    new_recurring_expense_cents: int = 0                                  # e.g. a new subscription
    starting_savings_cents: int = 0                                       # user-provided


def simulate(ctx: FinancialContext, sc: Scenario) -> dict:
    income, basis = ctx.monthly_income_basis
    exp = ctx.avg_expenses_cents
    cut = sum(ctx.category_avg_recent_cents.get(c, 0) * p / 100 for c, p in sc.category_cuts_pct.items()
              if ctx.category_avg_recent_cents.get(c, 0) > 0)
    s_income = income * (1 + sc.income_change_pct / 100)
    s_exp = exp - cut + sc.new_recurring_expense_cents
    base_net, s_net = income - exp, s_income - s_exp
    rows, b_cum, s_cum, saved = [], 0.0, 0.0, float(sc.starting_savings_cents)
    for m in range(1, sc.horizon_months + 1):
        b_cum += base_net
        s_cum += s_net
        saved += sc.extra_saving_cents
        rows.append({"month": m, "baseline_cumulative_net_cents": int(round(b_cum)),
                     "scenario_cumulative_net_cents": int(round(s_cum)), "savings_pot_cents": int(round(saved))})
    return {"label": "Simulation, not a prediction",
            "baseline": {"monthly_income_cents": int(income), "monthly_expenses_cents": int(exp),
                         "monthly_net_cents": int(base_net)},
            "scenario": {"monthly_income_cents": int(round(s_income)), "monthly_expenses_cents": int(round(s_exp)),
                         "monthly_net_cents": int(round(s_net)), "category_reduction_cents": int(round(cut)),
                         "monthly_saving_cents": sc.extra_saving_cents},
            "difference_monthly_cents": int(round(s_net - base_net)),
            "difference_over_horizon_cents": int(round((s_net - base_net) * sc.horizon_months)),
            "net_after_saving_monthly_cents": int(round(s_net - sc.extra_saving_cents)),
            "horizon_months": sc.horizon_months, "path": rows,
            "assumptions": [f"income basis: {basis}",
                            f"expenses: average of {ctx.window[0]}..{ctx.window[-1]}" if ctx.window else "no history",
                            "category cuts apply to the average of the last 3 months of that category",
                            "every month repeats the same averages; no inflation, interest or one-off events",
                            "money set aside each month is moved out of spending money, not created"]}
