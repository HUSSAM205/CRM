# Assistant Validation (Gate H)

Design: [`docs/AI_ASSISTANT.md`](../../docs/AI_ASSISTANT.md).

| Check | Evidence | Status |
|---|---|---|
| 13 intents (5 HW2 unchanged + 8 new) answer from deterministic calculations | `tests/unit/test_assistant.py`, `test_assistant_advisor_intents.py` (income 2,500.00; June cash flow 2,500.00 / 1,500.00 / 1,000.00; scenario savings 2,400.00; goal 666.67 per month) | PASS |
| Answers equal the dashboard | `test_assistant_answer_matches_dashboard`; browser tasks 10 and 21 | PASS |
| Forecast answer equals the AI page | both use `outlook_next` | PASS |
| Unsupported or out-of-scope questions do not hallucinate | fixed reply for fraud, stocks, loans, tax and unknown text; `assistant_probe.txt` | PASS |
| Account isolation | two-account test: B's answers are exactly 10× A's; scope filtered on a copy | PASS |
| No arbitrary execution; read-only | code- and SQL-like questions give the unsupported reply; goals, budgets and data unchanged afterwards | PASS |
| No external LLM; no data transmission | `test_no_network_or_shell_calls_in_application_code` | PASS |
| Output rendering | `st.text`; Markdown and HTML shown literally | PASS |

**Limitation:** English keywords only. Paraphrases outside the patterns get the unsupported reply.
