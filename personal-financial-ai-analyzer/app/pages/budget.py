"""5. Budget: suggested budgets (median of last 3 completed months), editable, progress, 80%/100% alerts."""
from __future__ import annotations

import polars as pl
import streamlit as st

from app.components import alerts
from app.utils import session
from app.utils.formatting import md_escape, money
from src.budget.budget_alerts import budget_status
from src.budget.budget_calculator import suggest_budgets


def render() -> None:
    st.header("Budget")
    if alerts.need_data():
        return
    s = session.get_data()["summaries"]
    acc, cur = st.session_state["account"], st.session_state["currency"]
    months = s.months(acc, cur)
    current = st.selectbox("Budget month", months[::-1], index=0, key="bud_month",
                           help="Spending in this month is compared with the budgets.")
    sug = suggest_budgets(s.category, acc, cur, current)
    if sug.is_empty():
        st.info("No category spending for this account and currency.")
        return
    key = f"{acc}|{cur}|{current}"
    saved = st.session_state["budgets"].get(key)
    table = sug.select("merchant_category").with_columns(
        pl.Series("budget", [saved.get(c, v) / 100 if saved else v / 100
                             for c, v in zip(sug["merchant_category"], sug["suggested_cents"])]),
        (sug["suggested_cents"] / 100).alias("suggested"), sug["explanation"])
    st.caption("Suggestion = median net spending of the three months before the budget month. "
               "It is a historical rule of thumb, not a prediction or financial advice. Edit any value.")
    edited = st.data_editor(table.to_pandas(), disabled=["merchant_category", "suggested", "explanation"],
                            hide_index=True, width="stretch", key=f"editor_{key}",
                            column_config={"budget": st.column_config.NumberColumn(f"budget ({cur})", min_value=0.0,
                                                                                   step=0.01, format="%.2f"),
                                           "suggested": st.column_config.NumberColumn(f"suggested ({cur})",
                                                                                      format="%.2f")})
    budgets = {r["merchant_category"]: int(round(float(r["budget"]) * 100)) for _, r in edited.iterrows()}
    st.session_state["budgets"][key] = budgets
    st.session_state["budgets"][f"active|{acc}|{cur}"] = budgets   # assistant reads budgets for THIS account/currency
    st.subheader(f"Progress in {current}")
    shown = 0
    for row in sug.iter_rows(named=True):
        b = budgets[row["merchant_category"]]
        if b <= 0 and row["spent_current_cents"] == 0:
            continue                                   # nothing budgeted and nothing spent: no row
        shown += 1
        stt = budget_status(row["spent_current_cents"], b)
        c1, c2 = st.columns([1, 3])
        c1.markdown(f"**{md_escape(row['merchant_category'])}**")
        c2.progress(min(max(stt["ratio"] or 0.0, 0.0), 1.0),
                    text=f"{money(row['spent_current_cents'], cur)} of "
                         + (money(b, cur) if b > 0 else "no budget set"))
        if stt["level"] in ("warning", "exceeded"):
            alerts.budget_alert(stt["level"], f"{md_escape(row['merchant_category'])}: {stt['message']}")
    if not shown:
        st.caption("No category spending and no budgets for this month.")
