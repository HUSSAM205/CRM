# Known Limitations (summary)

Full list with evidence: [`docs/KNOWN_LIMITATIONS.md`](../../docs/KNOWN_LIMITATIONS.md).

1. **Synthetic data.**
   * There is no temporal signal: lag-1 autocorrelation is −0.044.
   * Hours and categories are near-uniform.
   * Currencies are only labels.
   * Timestamps are independent of the ledger order.

   Results do not transfer to real users.
2. **Forecasting.**
   * On Dataset A, ML is NOT EFFECTIVE (GBR REJECTED).
   * On Dataset B, a scale-free GBR is ACCEPTED, but with a small gain (−5% test MAE). Its 80% range covered 77.7% of test months.
   * The model is used only for continuous series; otherwise the app shows the deterministic outlook.
   * Both datasets are synthetic, so real-world accuracy is unknown.
3. **Unusual-transaction ranking is weak.**
   * Dataset A: F1@k ≤ 0.041.
   * Dataset B identity theft (E3-B): chance level, so identity-theft-like spending is **not detectable**.
   * Rule hits (new category, unusual hour, large amount) are surfaced.
   * Results are review recommendations, never fraud.
4. **The app knows only the uploaded file:**
   * no balances, other accounts or obligations;
   * inflows are not known to be income;
   * transfers are assumed internal.

   The Advisor states each unknown, and affordability is never confirmed without a balance.
5. **The Advisor uses rules, not personal financial planning.**
   * No investment, credit, tax or legal advice.
   * Category classes (discretionary or essential) are configurable assumptions.
6. **Assistant:** English patterns only; 20 intents.
7. **Not measured on the target hardware:** all timings are from the cloud container (HW1 P5 PARTIAL).
8. **Windows: NOT TESTED** (scripts provided, dependency resolution verified).
9. **No human-participant usability study:** browser tasks are scripted.
10. **Licence:** CC BY-NC 4.0. Commercial use of the data or trained models is **BLOCKED** pending legal review.
11. **No authentication:** local single-user only.
