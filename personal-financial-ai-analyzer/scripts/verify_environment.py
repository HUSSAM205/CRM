"""Environment & dependency verification. Writes reports/verification/environment.json.

Checks: interpreter/venv, every direct dependency importable with its version, `pip check`
(dependency consistency), system resources, and installed tools. Exits non-zero on failure.
"""
from __future__ import annotations

import importlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.resource_monitor import system_snapshot  # noqa: E402

# import name -> distribution name
DIRECT = {"polars": "polars", "pyarrow": "pyarrow", "pandas": "pandas", "numpy": "numpy",
          "sklearn": "scikit-learn", "statsmodels": "statsmodels", "streamlit": "streamlit",
          "plotly": "plotly", "yaml": "PyYAML", "joblib": "joblib", "psutil": "psutil",
          "pytest": "pytest", "matplotlib": "matplotlib", "requests": "requests"}


def main() -> int:
    from importlib.metadata import version
    res = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
           "python": sys.version, "executable": sys.executable,
           "in_project_venv": Path(sys.prefix).resolve() == (ROOT / ".venv").resolve(),
           "platform": platform.platform(), "machine": platform.machine(),
           "imports": {}, "failures": []}
    for mod, dist in DIRECT.items():
        try:
            importlib.import_module(mod)
            res["imports"][dist] = version(dist)
        except Exception as exc:
            res["failures"].append(f"{dist}: {exc!r}")
    pc = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True)
    if pc.returncode != 0 and "No module named pip" in pc.stderr:
        pc = subprocess.run(["uv", "pip", "check", "--python", sys.executable], capture_output=True, text=True)
    res["pip_check"] = {"returncode": pc.returncode, "output": (pc.stdout + pc.stderr).strip()}
    if pc.returncode != 0:
        res["failures"].append("dependency check failed")
    res["tools"] = {t: shutil.which(t) for t in ["git", "uv", "curl", "sha256sum"]}
    res["system"] = system_snapshot()
    res["status"] = "PASS" if not res["failures"] and res["in_project_venv"] else "FAIL"
    out = ROOT / "reports/verification/environment.json"
    out.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
