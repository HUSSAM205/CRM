"""3. Analytics: categories, spending over time, income and cash flow, recurring payments and behaviour,
transparent indicators (HW1 F3; master audit 6.2-6.7). Every figure comes from validated completed records of
the selected account and currency; nothing is inferred about salary, personality or lifestyle."""
from __future__ import annotations

import polars as pl
import streamlit as st

from app.components import alerts, charts, tables
from app.utils import session
from app.utils.formatting import md_escape, money
from src.analytics import insights as I
from src.analytics.category_analysis import category_distribution
from src.analytics.monthly_analysis import compare_months


def render() -> None:
    st.header("Analytics")
    if alerts.need_data():
        return
    d = session.get_data()
    s, clean = d["summaries"], d["clean"]
    acc, cur = st.session_state["account"], st.session_state["currency"]
    months = s.months(acc, cur)
    tabs = st.tabs(["Categories", "Spending over time", "Income and cash flow", "Recurring and behaviour",
                    "Indicators"])

    with tabs[0]:
        a, b = st.select_slider("Period", options=months, value=(months[max(0, len(months) - 6)], months[-1]),
                                key="an_period")
        c = s.category.filter((pl.col("account_id") == acc) & (pl.col("currency") == cur)
                              & pl.col("month").is_between(pl.lit(a), pl.lit(b)))
        tot = category_distribution(s.category, acc, cur, a, b)
        left, right = st.columns(2)
        left.plotly_chart(charts.category_bar(tot, cur, f"Spending by category, {a} to {b}"), width="stretch")
        right.plotly_chart(charts.category_stacked(c, cur), width="stretch")
        st.caption("Category spending = purchases minus refunds in that category. Fees are reported separately.")
        st.subheader("Compare two months")
        x1, x2 = st.columns(2)
        m1 = x1.selectbox("First month", months, index=max(0, len(months) - 2), key="cmp1")
        m2 = x2.selectbox("Second month", months, index=len(months) - 1, key="cmp2")
        piv = compare_months(s.category, acc, cur, m1, m2)
        if not piv.is_empty():
            tables.show(piv, height=300)

    with tabs[1]:
        freq = st.radio("Granularity", ["day", "week", "month"], index=2, horizontal=True, key="an_freq")
        ps = I.period_spending(clean, acc, cur, freq)
        if ps.is_empty():
            st.info("No completed spending records for this account and currency.")
        else:
            st.bar_chart(ps.with_columns((pl.col("spend_cents") / 100).alias(f"spending ({cur})"))
                           .select("period_start", f"spending ({cur})"), x="period_start", y=f"spending ({cur})")
            st.caption(f"{ps.height} {freq}(s) with spending records. Spending = outflows + fees − refunds; "
                       "periods without any record are not shown.")
        st_ = I.spending_statistics(s, acc, cur)
        if st_["months"]:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Average month", money(st_["mean_cents"], cur))
            c2.metric("Median month", money(st_["median_cents"], cur))
            c3.metric(f"Highest ({st_['highest_month']})", money(st_["highest_cents"], cur))
            c4.metric(f"Lowest ({st_['lowest_month']})", money(st_["lowest_cents"], cur))
            if st_["recent_change_pct"] is not None:
                st.caption(f"Change: {st_['recent_change_pct']:+.1f}% ({st_['recent_change_basis']}). "
                           f"Averages include months without spending ({st_['months']} months in range).")

    with tabs[2]:
        inc = I.income_analysis(clean, s, acc, cur)
        c1, c2, c3 = st.columns(3)
        c1.metric("Months with recorded inflows", f"{inc['months_with_inflows']} of {inc['months']}")
        c2.metric("Average monthly inflows", money(inc["mean_monthly_cents"], cur))
        cv = inc["coefficient_of_variation"]
        c3.metric("Inflow variability (CV)", "—" if cv is None else f"{cv:.2f}",
                  help="Standard deviation / mean of monthly inflows. Higher = less regular.")
        st.caption(inc["note"])
        if inc["by_type"].height:
            tables.show(inc["by_type"], height=150)
        if inc["recurring_candidates"].height:
            st.write("Inflows that repeat at a regular interval (candidates, not confirmed income sources):")
            tables.show(inc["recurring_candidates"], height=150)
        cf = I.cash_flow(s, acc, cur)
        if not cf.is_empty():
            st.subheader("Monthly cash flow")
            neg = cf.filter(pl.col("net_cents") < 0)
            st.caption(f"{neg.height} of {cf.height} months had more expenses than recorded inflows. This is "
                       "transaction-derived net flow, **not a bank balance**: opening balances, other accounts "
                       "and transfers are not included.")
            tables.show(cf.with_columns(pl.col("expense_to_income").round(3)), height=260)

    with tabs[3]:
        rec = I.recurring_candidates(I.scope(clean, acc, cur))
        st.subheader("Recurring payment candidates")
        if rec.is_empty():
            st.info("No payments repeat with a similar amount at a regular weekly or monthly interval.")
        else:
            st.caption("Same category, amount within ±5%, regular interval. A candidate is **not** a confirmed "
                       "subscription; check the supporting transactions.")
            tables.show(rec, height=220)
        b = I.behaviour_changes(clean, s, acc, cur)
        st.subheader("Changes in category spending")
        if b["basis"] is None:
            st.info("At least 6 months are needed to compare recent with earlier spending.")
        else:
            st.caption(f"Comparison: {b['basis']} (changes of at least 25% and {money(1000, cur)}).")
            for kind, lab in (("increasing", "Increasing"), ("declining", "Declining")):
                for x in b[kind]:
                    st.write(f"{lab}: **{md_escape(x['category'])}** {money(x['prior_cents'], cur)} → "
                             f"{money(x['recent_cents'], cur)} ({x['change_pct']:+.1f}%)")
            if not b["increasing"] and not b["declining"]:
                st.write("No category changed by that much.")
            if b["top_category_share"]:
                t = b["top_category_share"]
                st.write(f"Largest category in the recent months: **{md_escape(t['category'])}** "
                         f"({t['share']:.0%} of category spending).")
        if b.get("large_isolated"):
            st.write("Large single expenses (at least 5× your median payment):")
            tables.show(pl.DataFrame(b["large_isolated"]), height=180)
        if b.get("repeated_small"):
            st.write("Many small expenses in the last 3 months (each at most 20% of your median payment):")
            tables.show(pl.DataFrame(b["repeated_small"]), height=150)

    with tabs[4]:
        st.caption("Descriptive indicators with their formulas. There is deliberately no combined 'health score'.")
        budgets = st.session_state.get("budgets", {}).get(f"active|{acc}|{cur}")
        ind = I.indicators(clean, s, acc, cur, budgets)
        st.dataframe(pl.DataFrame(ind).with_columns(pl.col("value").cast(pl.String).fill_null("not available")),
                     hide_index=True, width="stretch")
