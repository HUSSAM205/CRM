"""Local launcher (MA3-08, MA3-09): binds to 127.0.0.1 only, detects an already-running instance instead of
starting a duplicate, and reports a port used by another program. Runs the real scripts/run_application.py."""
from __future__ import annotations

import http.client
import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = [sys.executable, str(ROOT / "scripts/run_application.py"), "--no-browser"]
STOPPER = [sys.executable, str(ROOT / "scripts/stop_application.py"), "--no-scan"]


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Each test has its own launcher record, so a dashboard the user is running is never seen or stopped."""
    state = tmp_path / "app.json"
    monkeypatch.setenv("PFA_RUN_STATE", str(state))
    return state


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _healthy(host: str, port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/_stcore/health", timeout=2) as r:
            return r.read().strip() == b"ok"
    except (OSError, http.client.HTTPException):
        return False


def _lan_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        return None if ip.startswith("127.") else ip
    except OSError:
        return None


def test_launcher_is_local_only_and_never_starts_a_duplicate():
    port = _free_port()
    proc = subprocess.Popen([*LAUNCHER, "--port", str(port)], cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    try:
        for _ in range(120):
            if _healthy("127.0.0.1", port):
                break
            assert proc.poll() is None, proc.stdout.read()
            time.sleep(0.5)
        else:
            pytest.fail("dashboard did not start within 60 s")
        ip = _lan_ip()
        if ip:                                       # not reachable through the machine's network address
            with socket.socket() as s:
                s.settimeout(2)
                assert s.connect_ex((ip, port)) != 0, f"server reachable on {ip}:{port}"
        again = subprocess.run([*LAUNCHER, "--port", str(port)], cwd=ROOT, capture_output=True, text=True, timeout=60,
                               check=False)
        assert again.returncode == 0 and "already running" in again.stdout
    finally:
        proc.terminate()                 # handled like Ctrl+C: the server child is stopped too
        try:
            proc.wait(timeout=40)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_busy_port_falls_back_to_a_free_port_or_fails_when_strict():
    """MA4: a port used by another program -> the next free port is used (one-click start must not fail);
    with --strict-port the conflict is reported instead."""
    with socket.socket() as blocker:
        blocker.bind(("127.0.0.1", 0))
        blocker.listen(1)
        port = blocker.getsockname()[1]
        r = subprocess.run([*LAUNCHER, "--port", str(port), "--strict-port"], cwd=ROOT, capture_output=True,
                           text=True, timeout=60, check=False)
        assert r.returncode == 3 and "used by another program" in r.stdout and f"--port {port + 1}" in r.stdout
        sys.path.insert(0, str(ROOT / "scripts"))
        import run_application as RA
        free = RA.choose_port(port, strict=False)
        assert free is not None and free != port and 8502 <= free <= 8510 and not RA.port_in_use(free)


def test_stop_script_stops_only_this_app_and_clears_the_record(isolated_state):
    """STOP.bat logic: the recorded instance is verified as THIS project's Streamlit app, stopped with its
    children, and the record is removed; a second stop reports that nothing is running."""
    port = _free_port()
    state = isolated_state
    proc = subprocess.Popen([*LAUNCHER, "--port", str(port), "--strict-port"], cwd=ROOT,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(120):
            if _healthy("127.0.0.1", port) and state.exists():
                break
            time.sleep(0.5)
        else:
            pytest.fail("dashboard did not start")
        rec = json.loads(state.read_text(encoding="utf-8"))
        assert rec["port"] == port and rec["url"] == f"http://localhost:{port}"
        stop = subprocess.run(STOPPER, cwd=ROOT,
                              capture_output=True, text=True, timeout=60, check=False)
        assert stop.returncode == 0 and "Dashboard stopped" in stop.stdout, stop.stdout
        assert proc.wait(timeout=30) is not None and not _healthy("127.0.0.1", port)
        assert not state.exists()
        again = subprocess.run(STOPPER, cwd=ROOT,
                               capture_output=True, text=True, timeout=60, check=False)
        assert again.returncode == 0 and "not running" in again.stdout
    finally:
        if proc.poll() is None:
            proc.kill()


def test_terminating_the_launcher_leaves_no_orphaned_server(isolated_state):
    """MA4-04 regression: SIGTERM to the launcher used to kill only the launcher; its Streamlit child kept
    running (11 orphans were found during this audit) and blocked the next start as 'already running'."""
    port = _free_port()
    state = isolated_state
    proc = subprocess.Popen([*LAUNCHER, "--port", str(port), "--strict-port"], cwd=ROOT,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(120):
        if _healthy("127.0.0.1", port) and state.exists():
            break
        time.sleep(0.5)
    child = json.loads(state.read_text(encoding="utf-8"))["pid"]
    proc.terminate()
    proc.wait(timeout=40)
    import psutil
    assert not psutil.pid_exists(child) or psutil.Process(child).status() == psutil.STATUS_ZOMBIE
    assert not _healthy("127.0.0.1", port) and not state.exists()
