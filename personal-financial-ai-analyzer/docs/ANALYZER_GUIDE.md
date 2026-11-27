# Analyzer guide (for users)

The Analyzer shows **what actually happened** in your transactions: exact totals in integer cents, per account and per currency. It never mixes currencies. The technical definitions are in `ANALYZER.md`; the formulas are in `FINANCIAL_RULES.md`.

## 1. Load data (Transactions page)

1. Choose **Load demo data** or upload a CSV (up to 50 MB and 1,000,000 rows). Comma, semicolon, tab and pipe separators work, as do the UTF-8, UTF-8-BOM, cp1252 and latin-1 encodings.
2. Check the preview and the column mapping. Date, amount and currency are required.
   * **Without a status column**, confirm that all rows are completed.
   * **Without a type column**, negative amounts are spending and positive amounts are money received.
3. Press **Validate and load**. Every rejected row is listed with its reason. Nothing is dropped silently.
4. **A second file:** choose **Add to the loaded transactions** (the default).
   * Transactions that are already loaded are skipped and counted.
   * An identical file is refused.
   * **Replace the loaded transactions** works only after you tick the confirmation.

**Currencies:** any active ISO 4217 code is accepted, for example USD, EUR, GBP or TRY. Amounts are never converted.

## 2. Read the results

| Page | What you see |
|---|---|
| Overview | inflows, expenses, net cash flow and transfers (excluded) for the selected account, currency and period; a CSV report download |
| Transactions | the validated rows, date range, category, type and status filters, and the import summary |
| Analytics | spending by day, week or month; categories; month comparison; recorded inflows; cash flow; recurring payment candidates; behaviour changes; indicators, each with its formula |

## 3. What the numbers mean (and do not mean)

* **Expenses** = outflows + fees − refunds, completed transactions only.
* **Recorded inflows** are credits, deposits and interest. They are **not known to be salary**.
* **Cash flow** is derived from the transactions. It is **not a bank balance**: opening balances and other accounts are unknown.
* **Recurring payments** are *candidates* (similar amount at a regular interval), not confirmed subscriptions.
* **No combined "financial health score"** is computed.
