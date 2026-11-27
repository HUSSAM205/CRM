# AI Assistant Audit (Gate K)

**Design:** a deterministic, rule-based assistant (HW1 S8, HW2 5.7), **no LLM**.
* `src/assistant/intent_detection.py` recognizes 5 intents: total spending, category spending, month comparison, budget status, forecast.
* `query_executor.py` answers only from validated `Summaries` and the forecasting inference module.
* `response_generator.py` uses fixed templates.
* Anything else gets the fixed reply "Sorry, I can't answer that question…".

| Check | Method | Result | Status |
|---|---|---|---|
| Answers equal the dashboard | `test_assistant_answer_matches_dashboard`; UX task 10 | Equal (e.g. 2026-07: 9.06 USD for both) | PASS |
| Forecast answer equals the AI page | `assistant_probe.txt` (called as the page calls it) | Same target month, value and model | PASS |
| Month not in data | Probe | "That month is not in your data (available: 2024-01 to 2026-07)." | PASS |
| Unsupported, adversarial and injection input | Probe: "Ignore previous instructions…", `<script>`, empty, 5,000 characters, "fraud?", "stocks?" | Fixed unsupported reply; nothing executed or echoed | PASS |
| Plain-text rendering | `st.text` (A-03) | Markdown and HTML shown literally | PASS |
| Account and currency isolation | Budgets keyed `active\|account\|currency` (K-17); UX task 13 | No cross-account data | PASS |
| Saved budget edits drive the answer | `test_saved_budget_changes_drive_alerts_and_assistant` | PASS | PASS |
| Latency | `inference_performance.json` | median 0.9 ms | PASS |

**Limitations:**
* English keywords and month formats only. An Arabic question gets the unsupported reply.
* Answers report the latest data month for budget status.
* The forecast answer inherits F-1: it often predicts 0.00.
