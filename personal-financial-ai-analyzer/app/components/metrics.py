"""KPI row: income, expenses, net cash flow (deterministic totals; HW1 F3)."""
from __future__ import annotations

import streamlit as st

from app.utils.formatting import money


def kpi_row(t: dict, currency: str) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Income (inflows)", money(t["income_cents"], currency),
              help="Completed credits, deposits and interest. Never assumed to be salary.")
    c2.metric("Expenses", money(t["expenses_cents"], currency),
              help="Completed debits, withdrawals and fees, minus completed refunds.")
    c3.metric("Net cash flow", money(t["net_cash_flow_cents"], currency))
    c4.metric("Transfers (excluded)", money(t["transfer_cents"], currency),
              help="Transfers are shown separately and not counted as income or expenses.")
