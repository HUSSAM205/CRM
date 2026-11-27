"""Advisor (master audit phase 5) on a hand-built 12-month ledger with known answers.

Months M1..M12 = 2025-07..2026-06. Each month: deposit 2,500.00; rent 1,000.00 (housing);
utilities 150.00 (M1-M9) then 300.00 (M10-M12); dining 100.00 (M1-M9) then 200.00 (M10-M12).
Expenses: M1-M9 1,250.00, M10-M12 1,500.00 -> average of the last 6 months = 1,375.00. Surplus 1,125.00.
"""
from __future__ import annotations

import polars as pl
import pytest

from src.advisor import affordability as A
from src.advisor import recommendations as R
from src.advisor import savings as S
from src.advisor import scenarios as SC
from src.advisor.context import UserFacts, build_context
from src.analytics.aggregation import build_summaries
from src.data.validation import validate_transactions

MONTHS = [f"{2025 + (6 + i) // 12}-{(6 + i) % 12 + 1:02d}" for i in range(12)]


def ledger() -> pl.DataFrame:
    rows = []
    for i, m in enumerate(MONTHS):
        late = i >= 9
        for day, typ, amt, cat in ((1, "debit", 1000.0, "housing"), (25, "deposit", 2500.0, "income"),
                                   (5, "debit", 300.0 if late else 150.0, "utilities"),
                                   (12, "debit", 200.0 if late else 100.0, "dining")):
            rows.append({"transaction_id": f"T{len(rows):04d}", "account_id": "A", "transaction_type": typ,
                         "amount": f"{amt:.2f}", "currency": "USD", "merchant_category": cat,
                         "transaction_timestamp": f"{m}-{day:02d} 10:00:00", "status": "completed"})
    return validate_transactions(pl.DataFrame(rows)).clean


@pytest.fixture(scope="module")
def env():
    c = ledger()
    s = build_summaries(c)
    return c, s, build_context(c, s, "A", "USD")


def test_context_known_values_and_unknowns(env):
    _, _, ctx = env
    assert ctx.window == MONTHS[-6:]
    assert ctx.avg_inflow_cents == 250000 and ctx.avg_expenses_cents == 137500
    assert ctx.monthly_surplus_cents[0] == 112500
    assert ctx.category_avg_recent_cents["dining"] == 20000 and ctx.category_prior_avg_cents["dining"] == 10000
    assert "current bank balance" in ctx.unknowns()


def test_user_supplied_income_and_obligations_override_recorded_inflows(env):
    c, s, _ = env
    ctx = build_context(c, s, "A", "USD", UserFacts(monthly_income_cents=200000, monthly_obligations_cents=20000))
    surplus, basis = ctx.monthly_surplus_cents
    assert surplus == 200000 - 137500 - 20000 and "user-provided" in basis


def test_savings_plan_known_answers(env):
    _, _, ctx = env
    p = S.plan(S.Goal("Trip", 500000, 100000, "2026-12", 50000), "2026-06", ctx)
    assert p["months_left"] == 6 and p["required_monthly_cents"] == 66667          # ceil(400,000 / 6)
    assert p["progress"] == 0.2 and p["completion_month"] == "2027-02"             # 400,000 / 50,000 = 8 months
    assert [a["months"] for a in p["alternatives"]] == [16, 6, 4]
    assert p["feasibility"].startswith("Appears feasible") and "59%" in p["feasibility"]
    assert S.plan(S.Goal("Done", 1000, 1000), "2026-06")["feasibility"] == "Goal already reached."
    assert "not in the future" in S.plan(S.Goal("Past", 1000, 0, "2026-06"), "2026-06", ctx)["feasibility"]


def test_emergency_fund_target(env):
    _, _, ctx = env
    assert S.emergency_fund_target(ctx)["target_cents"] == 3 * 137500


def test_scenario_is_deterministic_and_labelled_simulation(env):
    _, _, ctx = env
    r = SC.simulate(ctx, SC.Scenario(horizon_months=12, category_cuts_pct={"dining": 50}, extra_saving_cents=10000))
    assert r["label"] == "Simulation, not a prediction"
    assert r["scenario"]["category_reduction_cents"] == 10000
    assert r["difference_monthly_cents"] == 10000 and r["difference_over_horizon_cents"] == 120000
    assert r["path"][-1]["savings_pot_cents"] == 120000
    assert r["net_after_saving_monthly_cents"] == 112500 + 10000 - 10000
    inc = SC.simulate(ctx, SC.Scenario(income_change_pct=-10, new_recurring_expense_cents=5000))
    assert inc["scenario"]["monthly_net_cents"] == 225000 - 142500
    assert SC.simulate(ctx, SC.Scenario()) == SC.simulate(ctx, SC.Scenario())


def test_affordability_never_confirms_without_balance(env):
    c, s, ctx = env
    r = A.assess(225000, ctx)
    assert r["verdict"] == "cannot_confirm" and "2.0 month(s)" in r["effects"][0]
    assert A.assess(None, ctx)["needs_input"]
    known = build_context(c, s, "A", "USD", UserFacts(current_balance_cents=500000, monthly_obligations_cents=0))
    assert A.assess(225000, known)["verdict"] == "within_known_means"
    tight = build_context(c, s, "A", "USD", UserFacts(current_balance_cents=300000, monthly_obligations_cents=0))
    assert A.assess(225000, tight)["verdict"] == "tight"
    assert A.assess(200000, known, payment="monthly")["verdict"] == "not_supported"


def test_recommendations_are_evidence_based_ranked_and_never_target_essentials(env):
    c, s, ctx = env
    goals = [S.Goal("Car", 2000000, 0, "2026-09")]
    recs = R.generate(c, s, ctx, budgets={"dining": 15000}, goals=goals, start_month="2026-06")
    titles = [r["title"] for r in recs]
    required = {"tier", "title", "issue", "evidence", "action", "monthly_impact_cents", "annual_impact_cents",
                "calculation", "assumptions", "horizon", "drawbacks", "alternatives", "evidence_sufficiency",
                "progress_tracking", "rank"}
    assert all(required <= set(r) and r["evidence"] and r["calculation"] for r in recs)
    dining = next(r for r in recs if r["title"].startswith("Bring dining"))
    assert dining["monthly_impact_cents"] == 10000 and dining["annual_impact_cents"] == 120000
    assert not any("utilities" in t for t in titles if t.startswith("Bring"))     # essential: never suggested
    # tier 1 first (goal shortfall 554,167 > budget overrun 5,000), then tier 2 by impact
    assert [r["tier"] for r in recs] == sorted(r["tier"] for r in recs)
    assert titles[0].startswith("Goal 'Car'") and recs[0]["monthly_impact_cents"] == 666667 - 112500
    assert titles[1] == "dining: over budget in 2026-06" and recs[1]["monthly_impact_cents"] == 5000
    t2 = [r["monthly_impact_cents"] for r in recs if r["tier"] == 2]
    assert t2 == sorted(t2, reverse=True)
    assert [r["rank"] for r in recs] == list(range(1, len(recs) + 1))


def test_no_recommendation_without_evidence():
    rows = [{"transaction_id": "X1", "account_id": "B", "transaction_type": "debit", "amount": "10.00",
             "currency": "USD", "merchant_category": "dining", "transaction_timestamp": "2026-01-05 10:00:00",
             "status": "completed"}]
    c = validate_transactions(pl.DataFrame(rows)).clean
    s = build_summaries(c)
    assert R.generate(c, s, build_context(c, s, "B", "USD")) == []
