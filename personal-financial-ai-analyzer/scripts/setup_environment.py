"""Create or reuse .venv (Python 3.12), install pinned dependencies and verify imports. Cross-platform.

    setup.bat  (Windows; finds Python 3.12 via `py -3.12` or `python`)
    python3.12 scripts/setup_environment.py      (macOS/Linux)

Safe to re-run: an existing .venv built with Python 3.12 is reused (only missing packages are installed).
Nothing is ever deleted: a .venv built with another Python version is reported and left untouched.
"""
from __future__ import annotations

import re
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
REQUIRED = ["requirements.txt", "app/main.py", "configs/app.yaml", "artifacts/metadata/model_registry.json",
            ".streamlit/config.toml", "data/samples/demo_transactions.csv"]


def venv_version() -> str | None:
    cfg = VENV / "pyvenv.cfg"
    if not cfg.exists():
        return None
    m = re.search(r"^version(?:_info)?\s*=\s*(\d+\.\d+)", cfg.read_text(encoding="utf-8"), re.MULTILINE)
    return m.group(1) if m else None


def main() -> int:
    if sys.version_info[:2] != (3, 12):
        print(f"ERROR: this is Python {sys.version.split()[0]}; the project requires Python 3.12.")
        return 1
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    if missing:
        print("ERROR: project files are missing (is the repository complete?):\n  - " + "\n  - ".join(missing))
        return 1
    if VENV.exists():
        v = venv_version()
        if v and v != "3.12":
            print(f"ERROR: the existing .venv was built with Python {v}. It was NOT deleted. Rename or remove the "
                  f".venv folder yourself, then run setup again.")
            return 1
        print(f"Reusing the existing .venv (Python {v or 'unknown'}).")
    else:
        print("Creating .venv ...")
        venv.EnvBuilder(with_pip=True).create(VENV)
    py = VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not py.exists():
        print(f"ERROR: {py} not found; the .venv folder looks incomplete. Rename it and run setup again.")
        return 1
    subprocess.check_call([str(py), "-m", "pip", "install", "--disable-pip-version-check", "-r",
                           str(ROOT / "requirements.txt")])
    subprocess.check_call([str(py), str(ROOT / "scripts/verify_environment.py")])
    raw = ROOT / "data/raw/transactions_50M.parquet"
    print("Saved models: present. Demo data: present.")
    print("Dataset A (1.6 GB, only needed for train.bat / audit.bat): " +
          ("present" if raw.exists() else "not downloaded (the dashboard works without it)"))
    print("Environment ready. Next: run.bat (Windows) or `python scripts/run_application.py`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
