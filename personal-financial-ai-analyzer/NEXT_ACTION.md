# Next Action

The implementation and the independent final audit are complete (`reports/final_audit/`). Remaining steps for the student:

1. **Windows verification (NOT TESTED by the agent).** On the laptop, follow the steps in `reports/final_audit/FINAL_DELIVERY_CHECKLIST.md` § "Windows verification":
   1. run `setup.bat`;
   2. run `python -m pytest` (expect 121 passed and 4 skipped without the dataset);
   3. run `run.bat`;
   4. load the demo data.

   Record the outcome. This also closes HW1 P5 (responsiveness on the final hardware).
2. Write the final report from `reports/final_evidence/results_tables.md`, `docs/final_results.md` and `docs/limitations.md`. Keep implementation completeness separate from scientific validity, and discuss F-1..F-4 explicitly.
3. Optional future work: add a zero or median baseline and an intermittent-demand metric to the forecasting protocol; use real (de-identified) data if permitted.
