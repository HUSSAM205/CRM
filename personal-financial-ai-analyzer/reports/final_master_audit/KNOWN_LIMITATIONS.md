# Known Limitations (summary)

Full list with evidence: [`docs/KNOWN_LIMITATIONS.md`](../../docs/KNOWN_LIMITATIONS.md).

1. **Synthetic data.**
   * There is no temporal signal: lag-1 autocorrelation is −0.044.
   * Hours and categories are near-uniform.
   * Currencies are only labels.
   * Timestamps are independent of the ledger order.

   Results do not transfer to real users.
2. **Forecasting ML is NOT EFFECTIVE** on this data (GBR REJECTED). The product shows a deterministic outlook; its interval is calibrated on the benchmark only.
3. **Unusual-transaction ranking is weak:** F1@k ≤ 0.041 at about 1% FPR. These are review recommendations, never fraud.
4. **The app knows only the uploaded file:**
   * no balances, other accounts or obligations;
   * inflows are not known to be income;
   * transfers are assumed internal.

   The Advisor states each unknown, and affordability is never confirmed without a balance.
5. **The Advisor uses rules, not personal financial planning.**
   * No investment, credit, tax or legal advice.
   * Category classes (discretionary or essential) are configurable assumptions.
6. **Assistant:** English patterns only; 13 intents.
7. **Not measured on the target hardware:** all timings are from the cloud container (HW1 P5 PARTIAL).
8. **Windows: NOT TESTED** (scripts provided, dependency resolution verified).
9. **No human-participant usability study:** browser tasks are scripted.
10. **Licence:** CC BY-NC 4.0. Commercial use of the data or trained models is **BLOCKED** pending legal review.
11. **No authentication:** local single-user only.
