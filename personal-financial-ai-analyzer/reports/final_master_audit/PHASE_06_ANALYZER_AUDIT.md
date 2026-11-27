# Phase 6: Analyzer Audit

Status: **COMPLETE**.

| Area | Evidence | Result |
|---|---|---|
| CSV ingestion: preview, mapping, encoding, delimiter, ISO currencies (M-12), overflow bounds | `test_ingestion.py`, `test_validation.py`, `test_csv_upload.py`; browser 1–4, 14 | PASS |
| Financial calculations | full-data reconciliation 9,488/9,488; Dataset C C1 14,320/14,320 (incl. TRY, refunds, transfers, pending) | PASS |
| Account, currency and date filters | AppTests; browser 6, 13 | PASS |
| Daily, weekly and monthly spending; statistics; income (recorded inflows); cash flow; recurring candidates; behaviour; indicators | `test_insights.py`, AppTests, browser 17; Dataset C C2 recurring P 0.986 / R 0.865 | PASS |
| Budget utilisation incl. remaining budget | `test_budget.py`, `test_assistant_shows_answer_context_and_budget_shows_remaining`; browser 7 | PASS |
| Data deletion | browser 12, 22; tests | PASS |

**Defects fixed in this phase:** M-12 (currencies).
