# Phase 8: Local Assistant Audit

Status: **COMPLETE**. Details: `docs/AI_ASSISTANT.md` and `ASSISTANT_VALIDATION.md`.

* **No external API.** No LLM, key or network call exists (`test_no_network_or_shell_calls_in_application_code`; grep finds 0 AI-provider references in `app/` and `src/`).
* **Intents:** the 5 HW2 intents (unchanged) plus 15 more: 13 question types (income, cash flow, trend, unusual transactions, goals, recommendations, what-if, affordability, recurring, remaining budget, forecast reliability, largest category, highest months) and 2 safety intents (unknown category, other account). "This month" and "last month" work across intents. All are deterministic and computed by the engine.
* **Safety:**
  * out-of-scope topics get the fixed reply;
  * an unknown category gets a clarification request (M-15);
  * another account gets a refusal;
  * missing parameters get a clarification request;
  * a month name without a year is answered with the year it was interpreted as;
  * the assistant is read-only (tested), and code- or SQL-like input is inert (tested).
* **Equality with the engine and dashboard:** `test_assistant_*`, `test_personaledger_demo_shows_accepted_model_and_assistant_agrees`; browser 10, 21, 24.
* **Context shown with each answer:** account, currency, period and intent.
