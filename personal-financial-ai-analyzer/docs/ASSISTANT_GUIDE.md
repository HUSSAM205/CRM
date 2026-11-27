# Assistant guide (for users)

The **Financial assistant** answers questions about the selected account and currency only. It uses the same calculations as the dashboard:
* no language model and no internet;
* no API key;
* it cannot change anything.

Every answer shows its account, currency, period and intent. Technical details: `AI_ASSISTANT.md`.

## Questions you can ask

| Topic | Examples |
|---|---|
| Spending | "How much did I spend this month?", "How much did I spend on groceries in March?", "Compare this month with last month", "Compare January and February" |
| Rankings | "What is my largest spending category?", "Which months had the highest spending?" |
| Budget | "Am I exceeding my budget?", "How much budget remains?" |
| Inflows and cash flow | "What was my cash flow last month?", "Has my income changed?" |
| Patterns | "What payments appear to recur?", "Is my spending increasing?", "Show unusual transactions", "Why was this transaction flagged?" |
| Planning | "How much can I save?", "Any recommendations?", "What if I reduce dining by 10%?", "Can I afford 450?", "Am I on track with my goals?" |
| Estimates and indicators | "What is my expected spending next month?", "Is the prediction reliable?", "Explain the savings rate", "Explain this financial indicator" |

## What it will not do

* **Guess.** A one-word question ("spending") or an unknown category gets a clarifying question.
* **Answer about another account.** Select it in the sidebar instead.
* **Give investment, credit, tax or legal advice, or judge fraud.** You get a fixed reply.
* **Invent a number.** If the data or a fact is missing, it says what is missing.
