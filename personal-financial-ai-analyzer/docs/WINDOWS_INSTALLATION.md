# Windows installation and use

**Status:** the scripts below have **never run on Windows**, because no Windows machine was available to this project. What was done instead:
* the Python logic they call was executed and tested on Linux, including a fresh install and a start/stop cycle;
* the `.bat` files were checked statically by tests (line endings, parentheses, labels, entry points);
* every pinned package was confirmed to have a Windows wheel for Python 3.12 (`reports/master_audit_4/requirements-windows-resolved.txt`).

To verify it yourself, follow `docs/WINDOWS_LAPTOP_VERIFICATION.md`.

## What you need

* **Windows 10 or 11**, 64-bit.
* **Python 3.12, 64-bit**, from https://www.python.org/downloads/. During installation, tick **"Add python.exe to PATH"**. Python 3.13 is not supported: the pinned packages are verified on 3.12.
* An internet connection **once**, for the first setup (about 300 MB of packages). After that the app works offline.
* About 1.5 GB of free disk space. The 1.6 GB dataset is **not** needed to use the app.

## Everyday use (no terminal needed)

| Action | What to do |
|---|---|
| **Start** | Double-click **`START_HERE.bat`**. The first time, it installs everything (a few minutes) and then starts the app. Afterwards it starts the app directly. Chrome (your default browser) opens at **http://localhost:8501** |
| Keep it running | Leave the black window open while you use the app. It shows the status and any errors |
| **Stop** | Close the black window, press Ctrl+C in it, or double-click **`STOP.bat`** |
| Start again | Double-click `START_HERE.bat` again. If the app is still running, it just opens the browser and starts no second copy |
| After updating the project files | Run `STOP.bat` first, then `START_HERE.bat`, so that the new code is loaded |

**What `START_HERE.bat` does:**
1. It checks whether `.venv` exists and has the required packages.
2. If not, it runs `setup.bat`. Setup reuses an existing `.venv`; it never deletes or overwrites it.
3. It runs `run.bat`, which:
   * starts the server on **127.0.0.1** only (other computers cannot connect);
   * waits until it answers;
   * prints `Dashboard ready: http://localhost:8501`;
   * opens the browser.

**If port 8501 is used by another program,** the next free port (8502–8510) is used and its URL is printed.

## Other scripts

| Script | Purpose |
|---|---|
| `setup.bat` | Setup only: finds Python 3.12 (`py -3.12` or `python`), creates or reuses `.venv`, installs the pinned packages, verifies the imports |
| `run.bat` | Start only. Options: `--port 8502`, `--strict-port`, `--no-browser` |
| `STOP.bat` | Stops this project's dashboard (it checks the recorded process before stopping it) |
| `test.bat` | Runs the automated tests. Without the dataset, 4 data-dependent tests are skipped, each with a reason |
| `benchmark.bat` | Measures speed and memory **on your laptop**. Writes `reports\laptop_benchmark.json` (HW1 P5) |
| `train.bat`, `audit.bat` | Optional: download the 1.6 GB dataset, retrain and re-verify. Not needed to use the app |

Every script runs from its own folder, sets UTF-8 mode (`PYTHONUTF8=1`) and pauses at the end so that you can read any error. `.ps1` versions exist for PowerShell users.

## Troubleshooting

| Message | Fix |
|---|---|
| `Python 3.12 was not found` | Install Python 3.12 64-bit with "Add python.exe to PATH", then run `START_HERE.bat` again |
| `the existing .venv was built with Python X` | Rename the `.venv` folder (for example to `.venv_old`) and run `START_HERE.bat` again. Nothing is deleted automatically |
| Setup fails while downloading packages | Check the internet connection or proxy, then run `START_HERE.bat` again (it resumes) |
| The browser did not open | Open http://localhost:8501 yourself (or the URL printed in the window) |
| Windows Defender / SmartScreen asks about the `.bat` file | Choose "More info" → "Run anyway" (the scripts only call the project's Python files) |
| `Port 8501 is used by another program` with `--strict-port` | Run `run.bat --port 8502` |

Cloud-container reference measurements (not laptop numbers) are in `reports/master_audit_3/benchmark_container.json`.
