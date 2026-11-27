# Installation Guide (Windows 10/11, 64-bit)

1. Install **Python 3.12** (64-bit) from python.org, with "Add python.exe to PATH" ticked. Check it with `py -3.12 --version`.
2. Open the project folder `personal-financial-ai-analyzer` in VS Code, then open a terminal there.
3. Run **`setup.bat`**, or `.\setup.ps1` in PowerShell. This creates `.venv`, installs the pinned `requirements.txt` and runs `scripts/verify_environment.py`.
4. Run **`run.bat`** to start the dashboard at http://localhost:8501. The trained models are already in `artifacts/`, so the app works without the 1.6 GB dataset. Use **Transactions → Load demo data**, or upload your own CSV.

Optional: reproduce everything from the raw data with **`train.bat`** (resumable). It downloads and verifies the dataset (about 1.6 GB, plus about 1.3 GB of derived tables), audits it, preprocesses, trains, evaluates and tests. Each heavy worker is capped at 4 GB RAM. If PowerShell blocks scripts, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Status: the dependency set was verified to **resolve** for Windows x64 / CPython 3.12 with binary wheels only. An install on the target laptop has **not** been executed by the developer agent.
