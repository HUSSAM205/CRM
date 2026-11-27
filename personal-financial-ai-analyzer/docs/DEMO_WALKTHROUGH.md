# Practical walkthrough (synthetic personal demo)

This walkthrough uses **two invented bank exports** (`data/samples/demo_personal_part1.csv` and
`demo_personal_part2.csv`, made by `scripts/prepare_personal_demo.py`, seed 20261127). They are **synthetic**: no
real person, not academic data, not used by any experiment. Every expected value below was computed by the app's
own engine (`scripts/ux/demo_walkthrough.py` → `reports/demo/demo_expected.json`) and the browser test checks the
screen against it. Your own CSV will of course give other numbers.

| # | Do this | You should see |
|---|---|---|
| 1 | Double-click **START_HERE.bat** | a window that says `Dashboard ready: http://localhost:8501`; Chrome opens the app |
| 2 | **Transactions** → *Load demo data* | the public-dataset demo (3 synthetic accounts) — a quick look around |
| 3 | Sidebar → **Delete my data now**, then **Transactions** → upload `demo_personal_part1.csv` | preview; mapping Date/Description/Category/Amount/Currency is filled in |
| 4 | Tick *All rows in this file are completed* → **Validate and load** | Valid rows **199**, Rejected 0 |
| 5 | Upload `demo_personal_part2.csv`, keep **Add to the loaded transactions**, tick *completed* → **Validate and load** | *Added 116 new transaction(s) … 31 were already loaded and skipped*; Valid rows **315** (the Nov–Dec 2025 overlap is not double-counted) |
| 6 | Upload any file again with **Replace the loaded transactions** | the button stays disabled until you tick the confirmation — only then is the data replaced (skip this to keep the demo data) |
| 7 | Sidebar: account **my-account**, currency **TRY** → **Overview** | inflows **828,000.00 TRY**, expenses **551,766.75 TRY**, net **276,233.25 TRY** for 2025-01..2026-06; *Download monthly report (CSV)* |
| 8 | **Analytics** | spending by day / week / month; categories; inflows and cash flow (not a bank balance); recurring candidates (rent, subscriptions, bills); dining rising in the last 3 months; indicators with formulas |
| 9 | **Financial advisor** → *Savings goals*: name *Laptop*, target 60000, already saved 5000, target month 2026-12 → *Add goal* | required per month **9,166.67 TRY**, milestones, status; emergency fund (3 months, essential) target **23,225.40 TRY** |
| 10 | **Financial assistant** — ask the questions below | the answers below |
| 11 | **AI predictions** | *Type of result: Validated forecast (quality gate passed on synthetic Dataset B, E2-B)*; estimate for 2026-07 **29,225.59 TRY** (80% range 21,210.68 TRY – 43,381.87 TRY); evidence and limitations |
| 12 | **AI predictions** → *Unusual transactions* | first: 2026-05-20 03:12:00 retail 24,999.00 TRY — *Unusual amount: 33.3x your usual for this category; Rare category: not seen in your history before; Unusual timing: an hour of day you have not used before*; labelled "review recommended", never fraud |
| 13 | **Transactions** → *Download these transactions (CSV)*; **Overview** → *Download monthly report (CSV)* | CSV files of exactly what is shown |
| 14 | **Settings and privacy** → *Delete all my data*; finally **STOP.bat** | everything removed from the session; the server stops |

## Assistant questions and the engine's answers

* **Which months had the highest spending?**  
  Your highest-spending months: 2026-05 56,859.59 TRY; 2026-06 31,513.93 TRY; 2026-04 31,426.21 TRY.
* **Compare this month with last month**  
  Spending: 2026-05 56,859.59 TRY; 2026-06 31,513.93 TRY. 2026-06 was less than 2026-05 (25,345.66 TRY less). ('this month' = 2026-06, the latest month in your data)
* **How much can I save?**  
  On average you had 13,439.18 TRY per month left over in 2026-01..2026-06 (average recorded inflows (2026-01..2026-06) − average expenses). If that pattern continues, that is roughly the most you could set aside each month. This is transaction-derived, not a bank balance. Unknown: current bank balance; verified income (only recorded inflows are known); upcoming obligations (rent, loans, bills not in this file).
* **What payments appear to recur?**  
  Recurring payment candidates (not confirmed subscriptions): housing about 17,500.00 TRY monthly (every 31 days, 18×, high confidence); subscription about 750.00 TRY monthly (every 31 days, 18×, high confidence); utilities about 449.90 TRY monthly (every 31 days, 18×, high confidence); subscription about 229.99 TRY monthly (every 31 days, 18×, high confidence).
* **Is the prediction reliable?**  
  Validated forecast (quality gate passed on synthetic Dataset B, E2-B). The estimate for 2026-07 comes from gbr_personaledger (ACCEPTED (experiment E2-B, Dataset B)), using your history 2025-01..2026-06. Evidence: Dataset B test MAE 971.34 (MASE 0.781); validation MAE 929.71; best baseline (historical_median) test MAE 1022.66, 5.0% higher than the model. Limitations: Trained on synthetic PersonaLedger card spending (CC BY 4.0); not effective on the intermittent series of Dataset A; the 80% interval covered 77.7% of test months.
* **Explain the savings rate**  
  Net inflow ratio (savings-rate proxy): 0.334. Formula: (recorded inflows - expenses) / recorded inflows over the whole period. How to read it: not a verified savings rate: transfers are excluded and inflows are not known to be income.

## Your own CSV

Any bank export with a date, an amount and a currency works (comma/semicolon/tab, UTF-8 or Windows encoding,
any ISO currency such as TRY). Map the columns on the Transactions page; if there is no status column, confirm
that all rows are completed; if amounts are signed, negative = spending. Add further exports with *Add to the
loaded transactions* — transactions already loaded are skipped and counted.
