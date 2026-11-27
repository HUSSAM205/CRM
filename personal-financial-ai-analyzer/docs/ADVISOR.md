# Advisor: what you could reasonably do next

The Advisor is a set of deterministic rules (`src/advisor/`, settings in `configs/advisor.yaml`) on top of the Analyzer. It covers budgeting, cash flow, savings and affordability. It does **not** give investment, credit, tax or legal advice. No language model computes or phrases any number.

## Inputs

* **Calculated** (`context.build_context`):
  * average monthly inflows, expenses and surplus over the last 6 calendar months;
  * per-category averages for the last 3 months and for the 9 months before;
  * the monthly total of recurring payment candidates.
* **User-provided** (optional, session only): current balance, current savings, monthly income, and monthly obligations not in the file.
* **Unknown:** anything not supplied. It is listed explicitly (`FinancialContext.unknowns()`) and never assumed.

## Features

| Feature | Rule |
|---|---|
| Budgets | HW2 method unchanged: suggested budget = median of the last 3 completed months; warnings at 80% and 100% (`src/budget/`) |
| Savings goals (`savings.plan`) | required monthly = ⌈(target − saved) / months to target⌉; completion month at a planned contribution; alternatives at 0.5×, 1.5× and 2×; feasibility compared with the average monthly surplus. No interest is assumed |
| Emergency fund | 3 × average monthly expenses (configurable) |
| What-if (`scenarios.simulate`) | category cut (% of the last-3-month average), extra monthly saving, income change (%), new recurring expense, horizon. Baseline, scenario and difference are shown as cumulative paths. Labelled "Simulation, not a prediction" |
| Affordability (`affordability.assess`) | asks for the amount if it is missing. Without a known balance **and** known obligations the verdict is always "cannot confirm"; the measurable effect is still shown (months of surplus, budget impact, goal delay). With both known: "within known means" if at least 1 month of average expenses remains, otherwise "tight"; a monthly cost above the surplus is "not supported" |
| Recommendations (`recommendations.generate`) | 5 evidence-gated rules: discretionary category above its own earlier average (at least 15% and 10.00 above); budget exceeded; 3 months of negative cash flow; recurring payments to review; a goal needing more than the surplus. Essential categories (groceries, healthcare, insurance, utilities, education, transport) are **never** suggested for cuts |

## Each recommendation carries

title · issue · evidence · action · monthly and annual impact · calculation · assumptions · horizon · drawbacks · alternatives · evidence sufficiency (high ≥ 12 months, medium ≥ 6, low) · progress tracking.

**Ranking** (fixed rule, no AI score):
1. urgency tier: problems now before opportunities;
2. estimated monthly impact;
3. evidence sufficiency.

## Labels

The page separates:
* user-provided facts (the "Facts only you know" form);
* calculated metrics;
* simulations (what-if);
* recommendations.

Model predictions appear only on the AI predictions page.

Tests: `tests/unit/test_advisor.py` (known answers: required monthly 666.67, scenario differences, affordability verdicts, ranking order, no recommendation without evidence) and `test_dashboard.py` (Advisor page and goal flow). Browser tasks 18–20.

## Additions in master audit 2

* **Financial profile.** Monthly averages split into essential, non-essential (discretionary) and unclassified expenses (other categories plus fees), recurring payment candidates, and the monthly surplus or deficit. Calculated from transactions, so it is not a verified bank balance. The three classes add up exactly to average expenses (tested).
* **Emergency fund** (`savings.emergency_fund_plan`). The **user chooses** the coverage in months and the basis: essential expenses by default, or all expenses. It shows current emergency savings, the remaining amount, progress, and months to completion at a given contribution. No universal target is assumed.
* **Goals.**
  * Status: reached, on track, behind, partially planned or no plan.
  * **Editing:** saved amount, target, contribution and date.
  * Milestones at 25, 50, 75 and 100%.
* **Scenarios.**
  * A change in all expenses (%) and a one-off unexpected expense.
  * Income increase or decrease.
  * **Goal impact:** months to fund a goal under the baseline vs the scenario, assuming the whole monthly net is saved (a stated assumption).
* **Recommendations.** Every recommendation also lists its *missing information*, *reason* and *next action*.
* **Affordability.** Shows the remaining monthly surplus or deficit.
