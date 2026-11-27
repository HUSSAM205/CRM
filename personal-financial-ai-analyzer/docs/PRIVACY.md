# Privacy

| Question | Answer |
|---|---|
| Where is my file processed? | In the memory of your browser session on the computer running the app. It is never written to disk |
| Is it sent anywhere? | No. There is no external service, LLM or telemetry, and the app works offline after setup |
| Is it used for training? | Never. The models were trained offline on public synthetic data |
| How long is it kept? | You choose: 15 minutes, 1 hour (the default) or until the tab closes. **Delete my data now** in the sidebar and **Delete all my data** in Settings remove it immediately: transactions, budgets, goals, entered facts and questions |
| Can other users see it? | No. Each browser session is isolated, and the server is reachable only from this computer |
| What do the logs contain? | Counts and events only. Amounts and IDs are masked |

Details and tests: `SECURITY_AND_PRIVACY.md`.
