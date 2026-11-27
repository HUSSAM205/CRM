# Advisor Validation (Gate G)

Design: [`docs/ADVISOR.md`](../../docs/ADVISOR.md). Code: `src/advisor/`. Settings: `configs/advisor.yaml`.

| Requirement (master audit) | Implementation | Verification | Status |
|---|---|---|---|
| 8.1 Use only validated or user-supplied inputs; state what is missing | `context.build_context`, `UserFacts`, `unknowns()` | `test_context_known_values_and_unknowns`, `test_user_supplied_income_and_obligations_override_recorded_inflows` | PASS |
| 8.2 Budgets: HW2 median-of-3 method preserved; editable; progress | `src/budget/` (unchanged method) | `test_budget.py`, AppTests, browser task 7 | PASS |
| 8.3 Warnings at 80% and 100% that update after edits | `budget_alerts.budget_status` | `test_saved_budget_changes_drive_alerts_and_assistant` | PASS |
| 8.4 Savings: required monthly, progress, completion, alternatives, feasibility | `savings.plan` | `test_savings_plan_known_answers` (ceil(400,000/6) = 66,667; completion 2027-02; alternatives 16/6/4 months; "Appears feasible … 59%") | PASS |
| 8.5 Reduction suggestions with evidence; essentials never called waste | `recommendations.generate` rule 1 | `test_recommendations_…_never_target_essentials` (dining +100.00/month → 1,200.00/year; utilities excluded) | PASS |
| 8.6 Affordability: asks for the amount; conservative without a balance | `affordability.assess` | `test_affordability_never_confirms_without_balance` (cannot_confirm / within_known_means / tight / not_supported); browser task 20 | PASS |
| 8.7 What-if scenarios, deterministic, labelled as simulation | `scenarios.simulate` | `test_scenario_is_deterministic_and_labelled_simulation`; browser task 19 | PASS |
| 8.8 Documented ranking, no AI score | `RANKING_RULE` | ranking-order assertions | PASS |
| 8.9 12 evidence fields; nothing shown without evidence | `_rec` fields | field-presence assertion; `test_no_recommendation_without_evidence` | PASS |
| 10 Goals, emergency fund, milestones, contribution plans, scenario comparison | `savings.plan` (milestones), `emergency_fund_target` | milestone known answers; `test_emergency_fund_target`; `test_advisor_page_goal_flow_and_values_equal_engine` | PASS |
| 10 Facts vs calculations vs predictions vs simulations vs recommendations labelled | page sections and captions | AppTest + screenshot `reports/screenshots/page_7_advisor.png` | PASS |
| Goals and facts deleted with the data | `session.purge` | `test_settings_delete_purges_goals_facts_and_data`; browser task 22 | PASS |

**Limitations:**
* Goals are session-only, with no persistence. That follows the privacy design.
* Feasibility uses historical averages, and inflows are not known to be income.
* Category lists are configurable assumptions.
* "Expense reduction" goals use the same savings arithmetic.
