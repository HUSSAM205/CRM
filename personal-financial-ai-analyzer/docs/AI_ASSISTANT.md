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
| this month, last month (relative to the latest month in the data; the resolved month is stated) | `Summaries` |
| largest expense category, highest-spending months | `Summaries`, `insights.monthly_series` |
| recurring payments (candidates) | `insights.recurring_candidates` |
| remaining budget, categories over budget | `Summaries` + user budgets |
| "Is the prediction reliable?", "Which model?", "Why no forecast?" | `inference.forecast_product` (method, status, evidence, limitations) |
| inflow change; categories affecting cash flow | `insights.cash_flow` |
| expense or income what-ifs | `advisor.scenarios` |
| unusual transactions | `anomaly_scoring.review_candidates` |
| savings goals, recommendations, what-if, affordability | `src/advisor/*` |
| "Compare this month with last month" (master audit 3) | `Summaries`; relative months resolved against the latest data month, which is stated |
| "How much can I save?" | `advisor.context` surplus (recorded inflows or user income − average expenses − user obligations), with unknowns listed; not a bank balance |
| "Why was this transaction flagged?" | `anomaly_scoring.review_candidates`: date, amount, usual amount, rule explanation, how it was surfaced; "review recommended", never fraud |
| "Explain the savings rate / this indicator" | `insights.indicators`: value, formula, how to read it; no combined score |

**Read-only:** the assistant cannot change budgets, goals or data. A test checks that they are unchanged after any question. Input that looks like code or SQL is only pattern-matched, never executed.

**Isolation:** a test with two accounts in the same currency checks that each answer uses only its own account's records.

**Limitations:** English keywords and month formats only; one account and currency at a time.

Tests: `tests/unit/test_assistant.py` and `test_assistant_advisor_intents.py`. Browser tasks 10, 11 and 21.

## Clarification and refusal rules (master audit 2)

* **Unknown category** ("How much did I spend on unicorns?"): the assistant asks which category is meant and lists the account's categories. It never falls back to total spending (M-15).
* **Month name without a year:** it answers for the latest such month and **says so**, naming the other years present.
* **Other accounts:** mentioning another account's ID ("ACC-…", "PL-USER-…") or "another / someone else's account" gives a refusal. The assistant only answers for the account selected in the sidebar.
* **Missing parameters** (affordability without an amount, a what-if without a change): it asks with examples.
* **Out of scope** (fraud, stocks, investments, crypto, loans, mortgages, credit scores, tax): the fixed unsupported reply.
* **Context:** every answer in the UI shows the account, currency, period and intent it used.

No external API, key or LLM is used or configurable. The assistant is pattern matching plus deterministic calculations.
* **Ambiguous one-word questions** ("spending", "budget", "money"), added in master audit 3: it asks for a more specific question with examples, and never guesses.
* **Professional advice** (investment, credit, tax, legal): the fixed reply, which says so explicitly.

Tests for master audit 3: `tests/unit/test_assistant_ma3.py`; browser tasks 28 and 29.
