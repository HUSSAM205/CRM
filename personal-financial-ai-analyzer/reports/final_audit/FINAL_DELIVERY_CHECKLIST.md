# Final Delivery Checklist

| Item | Status | Where |
|---|---|---|
| Source code (src, app, scripts, tests) tracked and pushed | DONE | branch `claude/hopeful-noether-t6vfi7` |
| Fresh clone installs, tests pass, app runs (Linux) | DONE | `reports/audit/fresh_install_audit.md` |
| Dataset identity documented; dataset not committed | DONE | `docs/dataset_provenance.md` |
| Trained artifacts and registry committed (1.6 MB) | DONE | `artifacts/` |
| Results tables (HW2 Tables 9.1 and 9.2) | DONE | `reports/final_evidence/results_tables.md` |
| Results discussion, with unfavorable findings | DONE | `docs/final_results.md`, `docs/limitations.md` |
| Requirements traceability (69 rows) | DONE (1 PARTIAL, 1 N/A) | `docs/requirements_traceability.md` |
| Independent audit package | DONE | `reports/audit/`, `reports/final_audit/` |
| Screenshots of the 6 pages and 15 tasks | DONE | `reports/screenshots/` |
| Installation and user guides | DONE | `docs/installation_guide.md`, `docs/user_guide.md`, `README.md` |
| **Windows install on the student's laptop** | **NOT TESTED**: student action | below |
| **Responsiveness on the final hardware (HW1 P5)** | **PARTIAL**: student action | below |
| Final written report and presentation | Student action | Use the files above |

## Windows verification (exact steps; not executed by the agent)

1. Install Python 3.12 (64-bit) from python.org and tick "Add to PATH".
2. Run these commands:
   ```bat
   git clone <repo URL>
   cd CRM\personal-financial-ai-analyzer
   git checkout claude/hopeful-noether-t6vfi7
   setup.bat
   ```
   Expect the final line "Environment ready".
3. Run the tests:
   ```bat
   .venv\Scripts\python -m pytest
   ```
   Expect **121 passed, 4 skipped** (no dataset). See the note below.
4. Run `run.bat` and open http://localhost:8501.
5. On Transactions, click "Load demo data".
6. Visit all 6 pages and ask "How much did I spend in 2026-07?".
7. Note the time each page takes to appear. This closes HW1 P5.
8. Optional full pipeline (1.6 GB download, then preprocessing and training; duration not measured on a laptop): run `train.bat`.
9. Record the results in `reports/final_audit/KNOWN_ISSUES.md` (Open items).

Note on step 3: 121 passed and 4 skipped is the result measured on Linux in fresh clone 4 of `ed4d45c`.
