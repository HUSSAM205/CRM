# AI financial assistant

Deterministic, with **no language model** (HW1 S8, HW2 5.7). The pipeline:

1. question (truncated to 500 characters);
2. intent recognition (regular expressions);
3. out-of-scope check (fraud, stocks, investment, crypto, loan, mortgage, credit score, tax all get the fixed reply);
4. parameter extraction (months, category, amount, percent);
5. scope validation (records filtered to the selected account **and** currency, on a copy);
6. a deterministic calculation in `src/analytics`, `src/advisor`, `src/budget` or `src/models`;
7. a fixed template, rendered as plain text (`st.text`, so no Markdown or HTML).

| Intent | Source of the numbers |
|---|---|
| total spending, category spending, month comparison, budget status (HW2) | `Summaries` (identical to the dashboard) |
| forecast | the product outlook (`inference.outlook_next`) |
| income (recorded inflows), cash flow | `insights.cash_flow` |
| spending trend | `insights.spending_statistics`, `behaviour_changes` |
| unusual transactions | `anomaly_scoring.review_candidates` |
| savings goals, recommendations, what-if, affordability | `src/advisor/*` |

**Read-only:** the assistant cannot change budgets, goals or data. A test checks that they are unchanged after any question. Input that looks like code or SQL is only pattern-matched, never executed.

**Isolation:** a test with two accounts in the same currency checks that each answer uses only its own account's records.

**Limitations:** English keywords and month formats only; one account and currency at a time.

Tests: `tests/unit/test_assistant.py` and `test_assistant_advisor_intents.py`. Browser tasks 10, 11 and 21.
