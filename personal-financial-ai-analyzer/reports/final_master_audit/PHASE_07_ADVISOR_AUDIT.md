# Phase 7: Advisor Audit

Status: **COMPLETE**. Details: `ADVISOR_VALIDATION.md` and `docs/ADVISOR.md`.

**Added in this phase:**
* financial profile (essential, non-essential and unclassified; the classes add up exactly to average expenses);
* user-defined emergency fund (coverage, current savings, progress, time to completion);
* goal status and goal editing (state change verified in AppTest);
* scenarios for expense change, one-off expense, income change and goal impact;
* recommendation fields for missing information, reason and next action;
* affordability shows the remaining surplus.

**Known answers:** `tests/unit/test_advisor.py` has 13 tests, with every figure hand-derived. Browser tasks 18–20 and 25.

**Protections:**
* essential categories are never suggested for cuts;
* affordability is never confirmed without a known balance and obligations;
* no recommendation is shown without evidence.
