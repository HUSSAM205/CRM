"""Create .venv (Python 3.12), install pinned dependencies and verify imports. Cross-platform.

    py -3.12 scripts/setup_environment.py        (Windows)
    python3.12 scripts/setup_environment.py      (macOS/Linux)
"""
from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
if sys.version_info[:2] != (3, 12):
    print(f"WARNING: running on Python {sys.version.split()[0]}; the project is verified on 3.12.")
if not VENV.exists():
    print("creating .venv ...")
    venv.EnvBuilder(with_pip=True).create(VENV)
py = VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
subprocess.check_call([str(py), "-m", "pip", "install", "--upgrade", "pip"])
subprocess.check_call([str(py), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])
subprocess.check_call([str(py), str(ROOT / "scripts/verify_environment.py")])
print("Environment ready. Next: run.bat (Windows) or `python scripts/run_application.py`.")
