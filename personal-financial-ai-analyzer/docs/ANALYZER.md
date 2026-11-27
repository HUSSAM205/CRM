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

## Importing several files (master audit 3)

When data is already loaded, the Transactions page asks what to do with the next file.

**Add to the loaded transactions** (the default):
* Existing records, budgets, goals and facts are kept.
* A record whose account and transaction ID are already loaded is skipped and listed as `already_loaded`.
* An identical file (same bytes) is refused as a whole.
* The combined total range is re-checked.
* Module: `src/data/merge.py`.

**Replace the loaded transactions:**
* The button stays disabled until you tick a confirmation.
* The loaded transactions and their budgets are removed.

**IDs for files without an ID column** are generated from the row content plus an occurrence counter, never from the row position. So:
* the same purchase in two overlapping exports is recognised as one transaction;
* two identical purchases inside one file stay two.

Tests:
* `tests/unit/test_merge.py`;
* `tests/integration/test_csv_upload.py::test_append_keeps_existing_data_and_replace_needs_confirmation`;
* browser tasks 26 and 27.
