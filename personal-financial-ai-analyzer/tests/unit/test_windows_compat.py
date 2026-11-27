"""Windows compatibility guards (master audit 4). They run on any OS and fail if a Windows-only failure mode
is reintroduced: default-encoding text I/O (cp1252 on Windows), Unix-only modules, LF-only batch files."""
from __future__ import annotations

import ast
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text_io_without_encoding(path: Path) -> list[str]:
    out = []
    for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not isinstance(n, ast.Call) or any(k.arg == "encoding" for k in n.keywords):
            continue
        f = n.func
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
        if name in ("read_text", "write_text"):
            out.append(f"{path.relative_to(ROOT)}:{n.lineno}")
        elif name == "open" and not (isinstance(f, ast.Attribute) and getattr(f.value, "id", "") in ("webbrowser", "os")):
            idx = 0 if isinstance(f, ast.Attribute) else 1
            mode = n.args[idx] if len(n.args) > idx else next((k.value for k in n.keywords if k.arg == "mode"), None)
            if isinstance(mode, ast.Constant) and "b" in str(mode.value):
                continue
            if mode is not None and not isinstance(mode, ast.Constant):
                continue                        # variable mode (binary download): checked by its own test
            out.append(f"{path.relative_to(ROOT)}:{n.lineno}")
    return out


def test_all_text_io_states_utf8():
    """Without encoding=, Python on Windows reads and writes text as cp1252: JSON/YAML/Markdown with characters
    such as '—', '≥' or '×' then fail or are corrupted. Every text read/write must say encoding='utf-8'."""
    bad = [x for d in ("src", "app", "scripts", "tests") for p in (ROOT / d).rglob("*.py")
           if "__pycache__" not in p.parts for x in _text_io_without_encoding(p)]
    assert not bad, bad


def test_no_unix_only_modules_outside_the_guarded_helper():
    offenders = []
    for d in ("src", "app", "scripts"):
        for p in (ROOT / d).rglob("*.py"):
            if "__pycache__" in p.parts or p.name == "peak_memory.py":
                continue
            t = p.read_text(encoding="utf-8")
            if any(s in t for s in ("import resource", "import fcntl", "os.fork(", "signal.SIGKILL")):
                offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, offenders


def test_peak_memory_falls_back_to_psutil_without_resource(monkeypatch):
    from src.utils import peak_memory
    monkeypatch.setitem(sys.modules, "resource", None)              # import resource -> ImportError
    fake = types.SimpleNamespace(Process=lambda: types.SimpleNamespace(
        memory_info=lambda: types.SimpleNamespace(peak_wset=2_500_000_000)))
    monkeypatch.setitem(sys.modules, "psutil", fake)
    assert peak_memory.peak_rss_gb() == 2.5


def test_download_writes_binary_and_resumes(tmp_path, monkeypatch):
    """The resumable download opens its file in a VARIABLE binary mode ('wb' or 'ab'); adding an encoding there
    raises ValueError, which the retry loop would swallow until the download fails."""
    from src.data import download as D
    payload = b"\x00\x01PARQUET\xff" * 10
    calls = []

    class Resp:
        def __init__(self, status, body):
            self.status_code, self.body = status, body

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def iter_content(self, n):
            yield self.body

    def fake_get(url, headers=None, **kw):
        calls.append(headers)
        if not headers:
            return Resp(200, payload[:40])        # first attempt: partial body only
        start = int(headers["Range"].split("=")[1].rstrip("-"))
        return Resp(206, payload[start:])
    monkeypatch.setattr(D.requests, "get", fake_get)
    monkeypatch.setattr(D.time, "sleep", lambda s: None)
    dest = tmp_path / "file.parquet"
    D.download("http://example.invalid/x", dest, expected_size=len(payload))
    assert dest.read_bytes() == payload and calls[1] == {"Range": "bytes=40-"}


def test_windows_scripts_enable_utf8_mode_and_keep_errors_visible():
    for bat in ("setup.bat", "run.bat", "test.bat", "train.bat", "audit.bat", "benchmark.bat", "START_HERE.bat",
                "STOP.bat"):
        text = (ROOT / bat).read_text(encoding="utf-8")
        assert "PYTHONUTF8=1" in text, bat
    for bat in ("START_HERE.bat", "run.bat", "setup.bat"):
        assert "pause" in (ROOT / bat).read_text(encoding="utf-8").lower(), bat


def _unquoted(line: str) -> str:
    out, q = [], False
    for ch in line:
        if ch == '"':
            q = not q
        elif not q:
            out.append(ch)
    return "".join(out)


def test_batch_files_are_structurally_sound():
    """Static checks for cmd.exe (no Windows here): CRLF endings, run from their own folder, balanced
    parenthesised blocks, labels exist for every goto, and no one-line `(... & if ... & exit)` trap in which
    the exit becomes part of the inner if."""
    import re
    for bat in sorted(ROOT.glob("*.bat")):
        raw = bat.read_bytes()
        assert raw.count(b"\n") == raw.count(b"\r\n"), f"{bat.name}: LF-only line"
        text = raw.decode("utf-8")
        assert 'cd /d "%~dp0"' in text, bat.name
        depth = 0
        for ln in text.splitlines():
            if ln.strip().upper().startswith("REM"):
                continue
            u = _unquoted(ln)
            depth += u.count("(") - u.count(")")
            assert depth >= 0, (bat.name, ln)
            assert not re.search(r"\(.*&\s*if .*&\s*exit", u, re.IGNORECASE), (bat.name, ln)
        assert depth == 0, f"{bat.name}: unbalanced parentheses"
        for label in re.findall(r"goto\s+:?(\w+)", text, re.IGNORECASE):
            assert re.search(rf"^:{label}\b", text, re.MULTILINE | re.IGNORECASE), (bat.name, label)


def test_one_click_workflow_scripts_exist_and_chain_correctly():
    start = (ROOT / "START_HERE.bat").read_text(encoding="utf-8")
    assert "call setup.bat" in start and "call run.bat" in start
    assert "rmdir" not in start.lower() and "del " not in start.lower()          # never overwrites anything
    assert "scripts\\stop_application.py" in (ROOT / "STOP.bat").read_text(encoding="utf-8")
    cfg = (ROOT / ".streamlit/config.toml").read_text(encoding="utf-8")
    assert 'address = "127.0.0.1"' in cfg and "port = 8501" in cfg
