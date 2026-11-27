"""Launch the dashboard locally at http://localhost:8501 (Windows: START_HERE.bat or run.bat). Data stays here.

Before starting, the launcher checks the project files and saved models, then the port:
  * this app already running (recorded in .run/app.json and still alive) -> print its URL, open it, start nothing;
  * port free -> start Streamlit bound to 127.0.0.1 only (not reachable from other computers), wait for the
    health check, print the URL, open the browser;
  * port used by another program -> use the next free port (8502..8510) and say so; --port N with
    --strict-port reports the conflict instead.
The running instance is recorded in .run/app.json (pid, port, url) so that STOP.bat can stop exactly this app.
Options: --port N   --strict-port   --no-browser   (anything else is passed to `streamlit run`).
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
# PFA_RUN_STATE lets the tests use their own record, so they never touch a dashboard the user is running.
STATE = Path(os.environ.get("PFA_RUN_STATE") or ROOT / ".run/app.json")
REQUIRED = ["app/main.py", "configs/app.yaml", "artifacts/metadata/model_registry.json", ".streamlit/config.toml"]
FALLBACK_PORTS = range(8502, 8511)


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((HOST, port)) == 0


def is_streamlit(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{HOST}:{port}/_stcore/health", timeout=3) as r:
            return r.status == 200 and r.read().strip() == b"ok"
    except (OSError, http.client.HTTPException):     # refused, reset, timeout, not HTTP
        return False


def is_our_process(pid: int) -> bool:
    """True if `pid` is alive and is a Streamlit server running THIS project's app/main.py."""
    try:
        import psutil
        cmd = " ".join(psutil.Process(pid).cmdline()).replace("\\", "/").lower()
    except Exception:                                 # noqa: BLE001 - no such process / access denied
        return False
    return "streamlit" in cmd and str(ROOT / "app/main.py").replace("\\", "/").lower() in cmd


def running_instance() -> dict | None:
    """The instance recorded in .run/app.json, if it is alive, ours and answering; stale records are removed."""
    try:
        st = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if is_our_process(int(st.get("pid", -1))) and is_streamlit(int(st.get("port", -1))):
        return st
    STATE.unlink(missing_ok=True)
    return None


def preflight() -> list[str]:
    problems = [f"missing project file: {p}" for p in REQUIRED if not (ROOT / p).exists()]
    if sys.version_info[:2] != (3, 12):
        print(f"WARNING: Python {sys.version.split()[0]}; the project is verified on 3.12.")
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        print("WARNING: not running from the project's .venv (run setup.bat, then run.bat).")
    for mod in ("streamlit", "polars", "sklearn", "plotly", "psutil"):
        try:
            __import__(mod)
        except ImportError:
            problems.append(f"Python package '{mod}' is not installed: run setup.bat first")
    return problems


def choose_port(requested: int, strict: bool) -> int | None:
    if not port_in_use(requested):
        return requested
    if strict:
        return None
    return next((p for p in FALLBACK_PORTS if p != requested and not port_in_use(p)), None)


def _interrupt(signum, frame):
    raise KeyboardInterrupt


def install_signal_handlers() -> None:
    """Termination requests (SIGTERM, SIGHUP; SIGBREAK = Ctrl+Break on Windows) take the same clean path as
    Ctrl+C: the Streamlit child is stopped and .run/app.json removed, so no orphaned server is left (MA4-04)."""
    for name in ("SIGTERM", "SIGHUP", "SIGBREAK"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), _interrupt)


def stop_child(proc: subprocess.Popen) -> None:
    """Stop the server: politely, then forcefully after 10 s (Streamlit's own shutdown can hang)."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)


def main() -> int:
    install_signal_handlers()
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--port", type=int, default=8501)
    ap.add_argument("--strict-port", action="store_true", help="fail instead of using another free port")
    ap.add_argument("--no-browser", action="store_true")
    args, extra = ap.parse_known_args()
    problems = preflight()
    if problems:
        print("Cannot start:\n  - " + "\n  - ".join(problems))
        return 2
    inst = running_instance()
    if inst:
        print(f"The dashboard is already running: {inst['url']}  (no second server started)")
        if not args.no_browser:
            webbrowser.open(inst["url"])
        return 0
    port = choose_port(args.port, args.strict_port)
    if port is None:
        print(f"Port {args.port} is used by another program. Close it, or start on another port:\n"
              f"  run.bat --port {args.port + 1}")
        return 3
    if port != args.port:
        print(f"Port {args.port} is used by another program; using free port {port} instead.")
    url = f"http://localhost:{port}"
    print("Saved models: found (artifacts/metadata/model_registry.json). The dashboard does not need the 1.6 GB "
          "dataset; it is only used by train.bat and audit.bat.")
    print(f"Starting the dashboard on {url} (local only; press Ctrl+C or run STOP.bat to stop) ...")
    env = {**os.environ, "PYTHONUTF8": "1"}            # UTF-8 text I/O on Windows too
    proc = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(ROOT / "app/main.py"),
                             "--server.address", HOST, "--server.port", str(port),
                             "--server.headless", "true", "--browser.gatherUsageStats", "false", *extra],
                            cwd=ROOT, env=env)
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps({"pid": proc.pid, "port": port, "url": url, "started": time.time()}),
                     encoding="utf-8")
    try:
        for _ in range(240):                       # up to 120 s for the first start (imports, model loading)
            if proc.poll() is not None:
                print(f"The dashboard stopped during startup (exit code {proc.returncode}). See the messages above.")
                return proc.returncode or 1
            if is_streamlit(port):
                print(f"\n  Dashboard ready: {url}\n  Keep this window open while you use the app.\n")
                if not args.no_browser:
                    webbrowser.open(url)
                break
            time.sleep(0.5)
        else:
            print("The dashboard did not answer within 120 s; it may still be starting. Try opening " + url)
        return proc.wait()
    except KeyboardInterrupt:
        stop_child(proc)
        print("Dashboard stopped.")
        return 0
    finally:
        try:
            if json.loads(STATE.read_text(encoding="utf-8")).get("pid") == proc.pid:
                STATE.unlink(missing_ok=True)
        except (OSError, ValueError):
            pass


if __name__ == "__main__":
    raise SystemExit(main())
