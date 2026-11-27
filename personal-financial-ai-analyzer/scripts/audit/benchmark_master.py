"""Master audit: performance benchmarks of the application paths (Phase L).

Each operation is timed separately: 'cold' = first call in a NEW Python process (imports and model loading
included, OS file cache state not controlled), 'warm' = median of 20 repeated calls in the same process.
CPU% = process CPU time / wall time over the warm repetitions (can exceed 100% with threads).
Peak RSS of the process tree is sampled every 20 ms. Writes reports/final_master_audit/performance_benchmarks.json
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/final_master_audit/performance_benchmarks.json"

SETUP = """
import sys, time; sys.path.insert(0, {root!r})
import polars as pl
from src.data.ingestion import ingest
from src.analytics.aggregation import build_summaries
DEMO = open({root!r} + '/data/samples/demo_transactions.csv', 'rb').read()
"""
OPS = {
    "csv_ingest_validate_demo_195_rows": ("", "res, _ = ingest(DEMO)"),
    "csv_ingest_validate_200k_rows": ("BIG = ('Date,Amount,Currency,Category\\n' + '\\n'.join(f'2026-0{1 + i % 6}-{1 + i % 28:02d} 10:00:00,-{1 + i % 997}.{i % 100:02d},USD,c{i % 14}' for i in range(200_000))).encode()",
                                      "res, _ = ingest(BIG, assume_completed=True)"),
    "build_summaries_demo": ("res, _ = ingest(DEMO)", "s = build_summaries(res.clean)"),
    "model_load_and_forecast_outlook": ("res, _ = ingest(DEMO); s = build_summaries(res.clean); a = s.accounts[0]\nfrom src.models.forecasting.inference import outlook_next",
                                        "outlook_next(s.monthly.filter((pl.col('account_id') == a) & (pl.col('currency') == 'USD')))"),
    "model_load_and_forecast_gbr_e2": ("res, _ = ingest(DEMO); s = build_summaries(res.clean); a = s.accounts[0]\nfrom src.models.forecasting.inference import forecast_next",
                                       "forecast_next(s.monthly.filter((pl.col('account_id') == a) & (pl.col('currency') == 'USD')))"),
    "model_load_and_anomaly_review": ("res, _ = ingest(DEMO); s = build_summaries(res.clean); a = s.accounts[0]\nfrom src.models.anomaly.anomaly_scoring import review_candidates",
                                      "review_candidates(res.clean, a, 'USD')"),
    "model_load_and_forecast_product_personaledger": (
        "resB, _ = ingest(open({root!r} + '/data/samples/demo_personaledger.csv', 'rb').read()); sB = build_summaries(resB.clean)\n"
        "from src.models.forecasting.inference import forecast_product",
        "forecast_product(sB.monthly.filter(pl.col('account_id') == sB.accounts[0]))"),
    "assistant_hw2_intent": ("res, _ = ingest(DEMO); s = build_summaries(res.clean); a = s.accounts[0]\nfrom src.assistant.response_generator import answer",
                             "answer('How much did I spend in 2026-07?', s, a, 'USD')"),
    "assistant_advisor_intent": ("res, _ = ingest(DEMO); s = build_summaries(res.clean); a = s.accounts[0]\nfrom src.assistant.response_generator import answer\nfrom src.assistant.advisor_intents import AssistantContext",
                                 "answer('Any recommendations?', s, a, 'USD', context=AssistantContext(clean=res.clean))"),
    "advisor_recommendations": ("res, _ = ingest(DEMO); s = build_summaries(res.clean); a = s.accounts[0]\nfrom src.advisor.context import build_context\nfrom src.advisor.recommendations import generate",
                                "generate(res.clean, s, build_context(res.clean, s, a, 'USD'))"),
    "analyzer_insights_all": ("res, _ = ingest(DEMO); s = build_summaries(res.clean); a = s.accounts[0]\nfrom src.analytics import insights as I",
                              "I.indicators(res.clean, s, a, 'USD'); I.behaviour_changes(res.clean, s, a, 'USD'); I.income_analysis(res.clean, s, a, 'USD')"),
    "dataset_metadata_inspection": ("import pyarrow.parquet as pq, os\nP = {root!r} + '/data/raw/transactions_50M.parquet'",
                                    "pq.ParquetFile(P).metadata if os.path.exists(P) else None"),
}
PAGE = """
import sys; sys.path.insert(0, {root!r})
from streamlit.testing.v1 import AppTest
from tests.integration.test_dashboard import page_app
from src.data.ingestion import ingest
from src.analytics.aggregation import build_summaries
res, m = ingest(open({root!r} + '/data/samples/demo_transactions.csv', 'rb').read())
st_ = {{'clean': res.clean, 'rejected': res.rejected, 'summaries': build_summaries(res.clean), 'source': 'demo', 'mapping': m, 'loaded_at': 1e18}}
import time, statistics, json
out = {{}}
for page in {pages!r}:
    ts = []
    for i in range(4):
        at = page_app(page); at.session_state['data'] = st_
        at.session_state['account'], at.session_state['currency'] = st_['summaries'].accounts[0], 'USD'
        t = time.perf_counter(); at.run(); ts.append(time.perf_counter() - t)
        assert not at.exception, page
    out[page] = {{'first_render_s': round(ts[0], 3), 'median_rerender_s': round(statistics.median(ts[1:]), 3)}}
print(json.dumps(out))
"""


def run_child(code: str) -> tuple[str, float, float]:
    t = time.perf_counter()
    p = psutil.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=ROOT)
    peak = 0
    while p.poll() is None:
        try:
            peak = max(peak, p.memory_info().rss)
        except psutil.Error:
            pass
        time.sleep(0.02)
    out, err = p.communicate()
    if p.returncode:
        raise RuntimeError(err[-800:])
    return out, time.perf_counter() - t, peak / 1e9


def cpu_model() -> str:
    """CPU model string on Windows, Linux and macOS (best effort; recorded, never guessed)."""
    if platform.system() == "Windows":
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            return winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        except OSError:
            return platform.processor()
    try:
        for line in open("/proc/cpuinfo", encoding="utf-8"):
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", default="cloud container, NOT the target Windows laptop (i7-1355U, 16 GB)",
                    help="describe the machine, e.g. 'student laptop'")
    ap.add_argument("--out", default=str(OUT), help="output JSON path")
    args = ap.parse_args()
    out_path = Path(args.out)
    res = {"environment": {"platform": platform.platform(), "python": platform.python_version(), "cpu_model": cpu_model(),
                           "cpu_logical": psutil.cpu_count(), "cpu_physical": psutil.cpu_count(logical=False),
                           "ram_gb": round(psutil.virtual_memory().total / 1e9, 2),
                           "dataset_mode": "full dataset present" if (ROOT / "data/raw/transactions_50M.parquet").exists()
                           else "demo mode (no 1.6 GB dataset)", "note": args.label,
                           "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
           "operations": {}}
    for name, (prep, op) in OPS.items():
        R = lambda x: x.replace("{root!r}", repr(str(ROOT)))  # noqa: E731
        code = SETUP.format(root=str(ROOT)) + R(prep) + f"""
import os, psutil, statistics, json
t0 = time.perf_counter(); {R(op)}; cold = time.perf_counter() - t0
pr = psutil.Process(); c0 = pr.cpu_times(); ws = []
for _ in range(20):
    t = time.perf_counter(); {R(op)}; ws.append(time.perf_counter() - t)
c1 = pr.cpu_times()
print(json.dumps({{'cold_first_call_ms': round(cold * 1000, 2), 'warm_median_ms': round(statistics.median(ws) * 1000, 2),
                  'warm_max_ms': round(max(ws) * 1000, 2),
                  'cpu_percent_warm': round(100 * ((c1.user + c1.system) - (c0.user + c0.system)) / sum(ws), 1)}}))
"""
        out, wall, peak = run_child(code)
        res["operations"][name] = {**json.loads(out.strip().splitlines()[-1]), "process_wall_s_incl_imports": round(wall, 2),
                                   "peak_rss_gb": round(peak, 3)}
        print(name, res["operations"][name], flush=True)
    pages = ["overview", "transactions", "analytics", "ai_predictions", "budget", "financial_advisor",
             "financial_assistant", "settings"]
    out, wall, peak = run_child(PAGE.format(root=str(ROOT), pages=pages))
    res["page_render_apptest"] = {"pages": json.loads(out.strip().splitlines()[-1]), "process_peak_rss_gb": round(peak, 3),
                                  "note": "server-side script execution per page (AppTest), demo data; excludes browser paint"}
    print(res["page_render_apptest"])
    import urllib.request
    starts = {}
    for label in ("cold", "warm"):
        t = time.perf_counter()
        p = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app/main.py", "--server.port", "8521",
                              "--server.headless", "true"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while True:
            try:
                if urllib.request.urlopen("http://localhost:8521/_stcore/health", timeout=1).read() == b"ok":
                    break
            except Exception:
                time.sleep(0.05)
        starts[label] = round(time.perf_counter() - t, 2)
        p.terminate()
        p.wait()
    res["app_server_start_s"] = starts
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(res, indent=1))
    print('written', out_path)
    print(starts)


if __name__ == "__main__":
    main()
