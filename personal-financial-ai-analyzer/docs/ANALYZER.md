# Analyzer: what actually happened

The Analyzer turns validated, **completed** transactions of one account and one currency into exact figures. It never combines currencies and never infers salary, personality or lifestyle.

| Feature | Module | Page | Definition |
|---|---|---|---|
| Income, expenses, net cash flow, transfers | `src/analytics/financial_metrics.py`, `aggregation.py` | Overview | expenses = outflow + fee − refund; net = inflows − expenses; transfers reported separately (`FINANCIAL_RULES.md`) |
| Month-over-month change, largest categories, recent activity, available period | `pages/overview.py` | Overview | from `Summaries` |
| Category distribution and month comparison | `category_analysis.py`, `monthly_analysis.py` | Analytics › Categories | category net = purchases − refunds |
| Daily, weekly and monthly spending | `insights.period_spending` | Analytics › Spending over time | same spending definition, bucketed by calendar period |
| Average, median, highest and lowest month; recent change | `insights.spending_statistics` | same | months without records count as 0 |
| Recorded inflows | `insights.income_analysis` | Analytics › Income and cash flow | credit + deposit + interest; frequency, CV, regular repeats. **Never labelled salary** |
| Cash flow | `insights.cash_flow` | same | monthly inflows, expenses, net, expense-to-income ratio (only where inflows > 0), negative months. **Not a bank balance** |
| Recurring payment candidates | `insights.recurring_candidates` | Analytics › Recurring and behaviour | same category; amount within ±5%; median interval 5–9 days (weekly) or 25–35 days (monthly); interval variation < 25%; ≥ 3 occurrences. Confidence is "high" at ≥ 4 occurrences and variation < 15%. Supporting transaction IDs are listed |
| Behaviour changes | `insights.behaviour_changes` | same | last 3 months vs the 3 before, per category, at least ±25% and 10.00; top-category share; repeated small expenses (≤ 20% of the median payment, ≥ 5 in 3 months); large single expenses (≥ 5× the median payment) |
| Indicators | `insights.indicators` | Analytics › Indicators | spending stability (CV), cash-flow consistency, net-inflow ratio (savings-rate proxy, labelled as such), recurring burden, budget adherence. **No combined health score**: each indicator shows its formula and how to read it |

Tests: `tests/unit/test_insights.py` (hand-built ledger, known answers) and `tests/integration/test_dashboard.py` (page values equal module values).

**What the Analyzer cannot know:** opening balances, other accounts, whether an inflow is income, and the purpose of a payment beyond its category.
