"""Launch the Streamlit dashboard locally (http://localhost:8501). Data stays on this computer."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
raise SystemExit(subprocess.call([sys.executable, "-m", "streamlit", "run", str(ROOT / "app/main.py"),
                                  "--browser.gatherUsageStats", "false", *sys.argv[1:]], cwd=ROOT))
