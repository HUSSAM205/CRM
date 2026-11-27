"""6. Financial advisor: ranked evidence-based recommendations, savings goals, what-if scenarios and an
affordability check (master audit phase 5 and 7). Every number is a deterministic calculation from the
validated transactions or a value the user typed in; facts, calculations, simulations and recommendations
are labelled separately. No investment, credit or legal advice."""
from __future__ import annotations

import datetime as dt

import polars as pl
import streamlit as st

from app.components import alerts
from app.utils import session
from app.utils.formatting import md_escape, money
from src.advisor import affordability as A
from src.advisor import recommendations as R
from src.advisor import savings as S
from src.advisor import scenarios as SC
from src.advisor.context import UserFacts, build_context

SCOPE = ("Budgeting, cash flow, savings and affordability education only. Not investment, credit, tax or legal "
         "advice. Figures come from your uploaded transactions and the values you enter.")


def _cents(x: float | None) -> int | None:
    return None if x is None else int(round(x * 100))


def facts_form(cur: str) -> UserFacts:
    f = st.session_state["user_facts"]
    with st.expander("Facts only you know (optional, kept in this session only)", expanded=not f):
        st.caption("Leave a box empty if you prefer not to say; the advisor then states that it is unknown.")
        c1, c2 = st.columns(2)
        bal = c1.number_input(f"Current balance ({cur})", value=f.get("bal"), min_value=0.0, step=10.0, key="uf_bal")
        sav = c2.number_input(f"Current savings ({cur})", value=f.get("sav"), min_value=0.0, step=10.0, key="uf_sav")
        inc = c1.number_input(f"Monthly income ({cur})", value=f.get("inc"), min_value=0.0, step=10.0, key="uf_inc")
        obl = c2.number_input(f"Monthly obligations not in this file ({cur})", value=f.get("obl"), min_value=0.0,
                              step=10.0, key="uf_obl", help="e.g. rent or loan payments from another account")
        st.session_state["user_facts"] = {"bal": bal, "sav": sav, "inc": inc, "obl": obl}
    return UserFacts(current_savings_cents=_cents(sav), current_balance_cents=_cents(bal),
                     monthly_income_cents=_cents(inc), monthly_obligations_cents=_cents(obl))


def render() -> None:
    st.header("Financial advisor")
    st.caption(SCOPE)
    if alerts.need_data():
        return
    d = session.get_data()
    s, clean = d["summaries"], d["clean"]
    acc, cur = st.session_state["account"], st.session_state["currency"]
    ctx = build_context(clean, s, acc, cur, facts_form(cur))
    if not ctx.window:
        st.info("No completed transactions for this account and currency.")
        return
    start = ctx.window[-1]
    surplus, basis = ctx.monthly_surplus_cents
    c1, c2, c3 = st.columns(3)
    c1.metric("Average monthly inflows", money(ctx.monthly_income_basis[0], cur), help=ctx.monthly_income_basis[1])
    c2.metric("Average monthly expenses", money(ctx.avg_expenses_cents, cur), help=f"{ctx.window[0]}..{ctx.window[-1]}")
    c3.metric("Average monthly surplus", money(surplus, cur), help=basis)
    st.caption("Calculated from your transactions (" + f"{ctx.window[0]}..{ctx.window[-1]}). Unknown to this app: "
               + "; ".join(ctx.unknowns()) + ".")
    goals = [S.Goal(**g) for g in st.session_state["goals"]]
    budgets = st.session_state.get("budgets", {}).get(f"active|{acc}|{cur}")
    tabs = st.tabs(["Recommendations", "Savings goals", "What-if scenarios", "Can I afford this?"])

    with tabs[0]:
        recs = R.generate(clean, s, ctx, budgets, goals, start)
        st.caption(R.RANKING_RULE)
        if not recs:
            st.success("No recommendation is supported by the evidence in your data right now.")
        for r in recs:
            with st.container(border=True):
                st.markdown(f"**{r['rank']}. {md_escape(r['title'])}**  ·  "
                            f"{'problem now' if r['tier'] == 1 else 'opportunity'}  ·  evidence: {r['evidence_sufficiency']}")
                st.text(f"Issue: {r['issue']}\nEvidence: {r['evidence']}\nAction: {r['action']}\n"
                        f"Expected impact: {money(r['monthly_impact_cents'], cur)} per month, "
                        f"{money(r['annual_impact_cents'], cur)} per year\nCalculation: {r['calculation']}\n"
                        f"Time horizon: {r['horizon']}\nDrawbacks: {r['drawbacks']}\n"
                        f"Alternatives: {'; '.join(r['alternatives'])}\nAssumptions: {'; '.join(r['assumptions'])}\n"
                        f"Track progress: {r['progress_tracking']}")

    with tabs[1]:
        ef = S.emergency_fund_target(ctx)
        st.caption(f"Suggested emergency fund: {money(ef['target_cents'], cur)} = {ef['calculation']}.")
        with st.form("goal_form", clear_on_submit=True):
            g1, g2 = st.columns(2)
            name = g1.text_input("Goal name", max_chars=40)
            kind = g2.selectbox("Type", ["savings", "emergency_fund", "expense_reduction"])
            target = g1.number_input(f"Target amount ({cur})", min_value=0.01, value=max(ef["target_cents"] / 100, 1.0))
            saved = g2.number_input(f"Already saved ({cur})", min_value=0.0, value=0.0)
            month = g1.text_input("Target month (YYYY-MM, optional)", max_chars=7)
            contrib = g2.number_input(f"Planned monthly contribution ({cur}, optional)", min_value=0.0, value=0.0)
            if st.form_submit_button("Add goal"):
                ok = bool(name.strip()) and (not month or (len(month) == 7 and month[4] == "-" and month[:4].isdigit()
                                                           and month[5:].isdigit() and 1 <= int(month[5:]) <= 12))
                if not ok:
                    st.error("Enter a goal name and a target month like 2027-06 (or leave the month empty).")
                else:
                    st.session_state["goals"].append({"name": name.strip(), "kind": kind, "target_cents": _cents(target),
                                                      "saved_cents": _cents(saved), "target_month": month or None,
                                                      "monthly_contribution_cents": _cents(contrib) or None})
                    st.rerun()
        for i, g in enumerate(goals):
            p = S.plan(g, start, ctx)
            with st.container(border=True):
                st.markdown(f"**{md_escape(g.name)}** ({g.kind.replace('_', ' ')}) · target {money(g.target_cents, cur)}")
                st.progress(min(p["progress"] or 0.0, 1.0), text=f"{(p['progress'] or 0):.0%} saved "
                                                                  f"({money(g.saved_cents, cur)} entered by you)")
                lines = [f"Remaining: {money(p['remaining_cents'], cur)}"]
                if p["required_monthly_cents"]:
                    lines.append(f"Required per month to reach it by {g.target_month}: "
                                 f"{money(p['required_monthly_cents'], cur)} ({p['months_left']} months from {start})")
                if p["completion_month"]:
                    lines.append(f"With {money(g.monthly_contribution_cents, cur)} per month: reached in "
                                 f"{p['completion_month']}")
                    lines += [f"  Alternative: {money(a['monthly_cents'], cur)}/month → {a['completion_month']}"
                              for a in p["alternatives"]]
                if p["feasibility"]:
                    lines.append(f"Feasibility: {p['feasibility']}")
                lines.append("Assumptions: " + "; ".join(p["assumptions"]))
                st.text("\n".join(lines))
                if st.button("Remove goal", key=f"rm_goal_{i}"):
                    st.session_state["goals"].pop(i)
                    st.rerun()

    with tabs[2]:
        st.caption("A simulation applies your changes to historical averages. It is **not a prediction**.")
        cats = sorted(k for k, v in ctx.category_avg_recent_cents.items() if v > 0)
        w1, w2 = st.columns(2)
        cut_cat = w1.selectbox("Reduce spending in", ["(none)"] + cats, key="wi_cat")
        cut_pct = w2.slider("by (%)", 0, 100, 10, key="wi_pct")
        extra = w1.number_input(f"Save extra each month ({cur})", min_value=0.0, value=0.0, key="wi_save")
        inc_chg = w2.slider("Change in monthly income (%)", -100, 100, 0, key="wi_inc")
        new_exp = w1.number_input(f"Add a recurring monthly expense ({cur})", min_value=0.0, value=0.0, key="wi_new")
        horizon = w2.slider("Horizon (months)", 1, 60, 12, key="wi_h")
        sc = SC.Scenario(horizon_months=horizon,
                         category_cuts_pct={cut_cat: cut_pct} if cut_cat != "(none)" and cut_pct else {},
                         extra_saving_cents=_cents(extra), income_change_pct=inc_chg,
                         new_recurring_expense_cents=_cents(new_exp),
                         starting_savings_cents=ctx.user.current_savings_cents or 0)
        r = SC.simulate(ctx, sc)
        m1, m2, m3 = st.columns(3)
        m1.metric("Baseline monthly net", money(r["baseline"]["monthly_net_cents"], cur))
        m2.metric("Scenario monthly net", money(r["scenario"]["monthly_net_cents"], cur),
                  delta=money(r["difference_monthly_cents"], cur))
        m3.metric(f"Difference over {horizon} months", money(r["difference_over_horizon_cents"], cur))
        path = pl.DataFrame(r["path"]).with_columns([(pl.col(c) / 100).alias(c.removesuffix("_cents"))
                                                     for c in ("baseline_cumulative_net_cents",
                                                               "scenario_cumulative_net_cents", "savings_pot_cents")])
        st.line_chart(path, x="month", y=["baseline_cumulative_net", "scenario_cumulative_net", "savings_pot"])
        st.text(f"{r['label']}. Assumptions: " + "; ".join(r["assumptions"]))

    with tabs[3]:
        a1, a2 = st.columns(2)
        amt = a1.number_input(f"Purchase amount ({cur})", min_value=0.0, value=0.0, key="af_amt")
        pay = a2.radio("Payment", ["one-off", "monthly"], horizontal=True, key="af_pay")
        cat = a1.selectbox("Category (optional)", ["(none)"] + cats, key="af_cat")
        goal_names = ["(none)"] + [g.name for g in goals]
        gsel = a2.selectbox("Would it come from a savings goal?", goal_names, key="af_goal")
        res = A.assess(_cents(amt) if amt else None, ctx, pay, None if cat == "(none)" else cat, budgets,
                       next((g for g in goals if g.name == gsel), None))
        if res["needs_input"]:
            st.info(res["message"])
        else:
            {"cannot_confirm": st.warning, "within_known_means": st.success, "tight": st.warning,
             "not_supported": st.error}[res["verdict"]](res["summary"])
            st.text("Known: " + "; ".join(f"{k}: {v}" for k, v in res["known_context"].items()) + "\n"
                    + "Effects: " + " ".join(res["effects"]) + "\n"
                    + "Missing information: " + "; ".join(res["missing_information"]) + "\n"
                    + "Assumptions: " + "; ".join(res["assumptions"])
                    + ("\nAlternatives: " + " ".join(res["alternatives"]) if res["alternatives"] else ""))
    st.caption(f"As of {dt.date.today().isoformat()} · data through {start}.")
