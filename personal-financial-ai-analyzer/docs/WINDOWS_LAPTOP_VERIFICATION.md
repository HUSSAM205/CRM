# Verifying the app on your Windows laptop

Nothing in this project has been executed on Windows yet. This checklist turns your first run into recorded evidence. Fill in the right-hand column and keep the file. Each step takes a few minutes.

| # | Step | Expected | Your result |
|---|---|---|---|
| 1 | In a Command Prompt, run `py -3.12 --version` | `Python 3.12.x` | |
| 2 | Double-click `START_HERE.bat` (first time) | package installation, then `Environment ready.`, then `Dashboard ready: http://localhost:8501`; the browser opens | |
| 3 | In the browser: Transactions → *Load demo data*, then open all 8 pages from the left menu | every page shows data, no error box | |
| 4 | Follow `docs/DEMO_WALKTHROUGH.md` steps 3–14 | the values listed there (they were computed by the engine and checked in a browser on Linux) | |
| 5 | Double-click `START_HERE.bat` again while the app is running | `The dashboard is already running …`; no second server | |
| 6 | Double-click `STOP.bat` | `Dashboard stopped (process …)`; http://localhost:8501 no longer loads | |
| 7 | Double-click `test.bat` | `… passed, 4 skipped` and 0 failed. Note the counts | |
| 8 | Double-click `benchmark.bat` (after you write your P5 threshold into the report) | creates `reports\laptop_benchmark.json` | |
| 9 | From another device on the same Wi-Fi, try `http://<laptop-IP>:8501` | does **not** load (the app is local-only) | |

**If a step fails:**
* Keep the black window open and copy its text.
* Note the step number.
* Run `test.bat` and keep its log, which is saved in `logs\testing\`.

Those three items are enough to diagnose the problem.
