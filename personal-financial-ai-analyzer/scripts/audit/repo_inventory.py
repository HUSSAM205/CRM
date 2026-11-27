"""Master audit: repository inventory and static health checks (Phase 0).

Writes reports/final_master_audit/repository_inventory.json. Read-only: imports every project module in a
child process, scans for hardcoded paths, compares declared dependencies with imports, and finds modules
that no other file imports (dead-code candidates, to be reviewed by hand, not deleted automatically).
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/final_master_audit/repository_inventory.json"
CATS = {"src": "source", "app": "application", "scripts": "scripts", "tests": "tests", "configs": "configuration",
        "docs": "documentation", "artifacts": "model artifacts", "reports": "reports", "data": "data (tracked samples)",
        "logs": "logs"}


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [l for l in out.splitlines() if l]


def main() -> None:
    files = tracked()
    by_cat = defaultdict(list)
    for f in files:
        top = f.split("/")[0]
        by_cat[CATS.get(top, "root/other")].append(f)
    py = [f for f in files if f.endswith(".py") and f.split("/")[0] in ("src", "app", "scripts", "tests")]

    # imports graph
    imported_modules, third_party = set(), set()
    for f in py:
        tree = ast.parse((ROOT / f).read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            names = []
            if isinstance(n, ast.Import):
                names = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                names = [n.module] + [f"{n.module}.{a.name}" for a in n.names]
            for m in names:
                if m.split(".")[0] in ("src", "app"):
                    imported_modules.add(m)
                else:
                    third_party.add(m.split(".")[0])
    mods = {f[:-3].replace("/", "."): f for f in py if f.split("/")[0] in ("src", "app") and not f.endswith("__init__.py")}
    pages = {m for m in mods if m.startswith("app.pages.")}
    not_imported = sorted(f for m, f in mods.items()
                          if m not in imported_modules and m not in pages and m != "app.main"
                          and not any(i.startswith(m + ".") for i in imported_modules))

    # declared deps
    req = [re.split(r"[=<>\[ ;]", l.strip())[0].lower() for l in (ROOT / "requirements.txt").read_text().splitlines()
           if l.strip() and not l.startswith("#")]
    import_name = {"scikit-learn": "sklearn", "pyyaml": "yaml", "python-dateutil": "dateutil"}
    std = set(sys.stdlib_module_names)
    used = {m.lower() for m in third_party if m not in std}
    unused_deps = [r for r in req if import_name.get(r, r).replace("-", "_") not in used]
    undeclared = sorted(m for m in used if m not in {import_name.get(r, r).replace("-", "_") for r in req}
                        and m not in ("pytest", "_pytest", "streamlit", "playwright"))

    # import every module (broken imports)
    code = ("import importlib,sys,json;bad={}\n"
            f"for m in {sorted(m for m in mods if not m.startswith('app.pages.'))!r}:\n"
            "    try: importlib.import_module(m)\n"
            "    except Exception as e: bad[m]=repr(e)\n"
            "print(json.dumps(bad))")
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    broken = json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else {"<runner>": r.stderr[-500:]}

    hard = []
    for f in files:
        if f.endswith((".py", ".yaml", ".bat", ".ps1", ".toml", ".mjs")):
            for i, line in enumerate((ROOT / f).read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if re.search(r"(/home/|/root/|/tmp/|[A-Za-z]:\\\\Users)", line) and "scratchpad" not in line:
                    hard.append(f"{f}:{i}")
    deprecated = []
    for f in py:
        t = (ROOT / f).read_text(encoding="utf-8")
        for pat in ("use_container_width", "st.experimental_", "datetime.utcnow(", "pd.np."):
            if pat in t:
                deprecated.append(f"{f}: {pat}")

    res = {"tracked_files": len(files), "by_category": {k: len(v) for k, v in sorted(by_cat.items())},
           "python_files": len(py), "app_pages": sorted(pages),
           "modules_not_imported_anywhere": not_imported, "broken_imports": broken,
           "declared_dependencies": req, "declared_but_not_imported": unused_deps,
           "imported_but_not_declared": undeclared, "hardcoded_paths": hard, "deprecated_api_uses": deprecated,
           "files": {k: sorted(v) for k, v in sorted(by_cat.items())}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "files"}, indent=1))


if __name__ == "__main__":
    main()
