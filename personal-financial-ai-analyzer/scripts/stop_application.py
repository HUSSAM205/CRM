"""Stop the dashboard started by run.bat / START_HERE.bat (Windows: STOP.bat). Only THIS project's app is stopped.

The launcher records the running server in .run/app.json. This script checks that the recorded process is
alive and really is this project's Streamlit app (command line contains streamlit and this app/main.py), then
stops it and its child processes: politely first, forcefully after 10 s. Without a record, it looks for this
project's Streamlit process listening on 127.0.0.1 (ports 8501..8510). Nothing else is ever terminated.
Exit code 0 = stopped or nothing was running; 1 = could not stop. Option --no-scan: use the record only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_application import STATE, is_our_process


def candidates(scan: bool = True) -> list[int]:
    pids = []
    try:
        pids.append(int(json.loads(STATE.read_text(encoding="utf-8"))["pid"]))
    except (OSError, ValueError, KeyError):
        pass
    if not pids and scan:                          # no record: find our app among local listeners
        try:
            conns = psutil.net_connections(kind="inet")
        except (psutil.AccessDenied, OSError):
            conns = []
        for c in conns:
            if c.status == psutil.CONN_LISTEN and c.laddr and 8501 <= c.laddr.port <= 8510 and c.pid:
                pids.append(c.pid)
        if not conns:                              # restricted platforms: scan process command lines
            pids += [p.pid for p in psutil.process_iter(["cmdline"]) if is_our_process(p.pid)]
    return [p for p in dict.fromkeys(pids) if is_our_process(p)]


def stop(pid: int) -> bool:
    try:
        proc = psutil.Process(pid)
        tree = proc.children(recursive=True) + [proc]
    except psutil.NoSuchProcess:
        return True
    for p in tree:
        try:
            p.terminate()
        except psutil.NoSuchProcess:
            pass
    _, alive = psutil.wait_procs(tree, timeout=10)
    for p in alive:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass
    _, alive = psutil.wait_procs(alive, timeout=5)
    return not alive


def main() -> int:
    pids = candidates(scan="--no-scan" not in sys.argv[1:])
    if not pids:
        STATE.unlink(missing_ok=True)
        print("The dashboard is not running (nothing to stop).")
        return 0
    ok = all(stop(p) for p in pids)
    if ok:
        STATE.unlink(missing_ok=True)
        print(f"Dashboard stopped (process {', '.join(map(str, pids))}).")
        return 0
    print("Could not stop the dashboard; close its window instead.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
