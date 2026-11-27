"""Plotly charts. One neutral palette; income vs expenses colours are consistent on every page."""
from __future__ import annotations

import plotly.graph_objects as go
import polars as pl

INCOME, EXPENSE, NET, NEUTRAL = "#2E7D6B", "#C0504D", "#3B5998", "#8C8C8C"
LAYOUT = dict(margin=dict(l=10, r=10, t=40, b=10), height=360, legend=dict(orientation="h", y=-0.2),
              template="plotly_white")


def monthly_trend(m: pl.DataFrame, currency: str) -> go.Figure:
    m = m.sort("month")
    fig = go.Figure()
    fig.add_bar(x=m["month"], y=m["income_cents"] / 100, name="Income", marker_color=INCOME)
    fig.add_bar(x=m["month"], y=m["expenses_cents"] / 100, name="Expenses", marker_color=EXPENSE)
    fig.add_scatter(x=m["month"], y=m["net_cash_flow_cents"] / 100, name="Net cash flow", mode="lines+markers",
                    line=dict(color=NET))
    fig.update_layout(title=f"Monthly income and expenses ({currency})", barmode="group", **LAYOUT)
    return fig


def category_bar(c: pl.DataFrame, currency: str, title: str) -> go.Figure:
    c = c.sort("net_spending_cents")
    fig = go.Figure(go.Bar(x=c["net_spending_cents"] / 100, y=c["merchant_category"], orientation="h",
                           marker_color=EXPENSE))
    fig.update_layout(title=f"{title} ({currency})", **LAYOUT)
    return fig


def category_stacked(c: pl.DataFrame, currency: str) -> go.Figure:
    fig = go.Figure()
    for cat in sorted(c["merchant_category"].unique().to_list()):
        d = c.filter(pl.col("merchant_category") == cat).sort("month")
        fig.add_bar(x=d["month"], y=d["net_spending_cents"] / 100, name=cat)
    fig.update_layout(title=f"Monthly spending by category ({currency})", barmode="relative", **LAYOUT)
    return fig


def forecast_chart(months: list[str], actual, backtest: dict, target: str | None, forecast: float | None,
                   currency: str) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=months, y=actual, name="Actual expenses", mode="lines+markers", line=dict(color=EXPENSE))
    if backtest:
        fig.add_scatter(x=list(backtest), y=list(backtest.values()), name="Model's past one-month forecasts",
                        mode="markers", marker=dict(color=NET, symbol="x", size=10))
    if forecast is not None:
        fig.add_scatter(x=[target], y=[forecast], name="Forecast", mode="markers",
                        marker=dict(color=NET, size=14, symbol="diamond"))
    fig.update_layout(title=f"Spending history and forecast ({currency})", **LAYOUT)
    return fig
