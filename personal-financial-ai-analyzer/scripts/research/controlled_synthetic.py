"""Dataset C: controlled synthetic ledgers with known ground truth (explicitly synthetic; never presented as
real-world validation). Experiments C1-C4 test the PIPELINE, not real-world performance.

Generator (seeded; deterministic): 200 users x 36 months (2023-01..2025-12), one currency each (USD/EUR/TRY).
  * income: monthly deposit on day 25 (fixed amount per user, +/-1%)            -> recurring inflow ground truth
  * subscriptions: 1-3 per user, monthly (fixed day, fixed amount +/-1%) or weekly (+/-1%) -> recurring ground truth
  * groceries: weekly, amount varies +/-40% (regular timing, irregular amount: must NOT be a recurring candidate)
  * discretionary 'dining': users 0-99 "structured": monthly total follows AR(1) (phi 0.7) + December +40%;
    users 100-199 "unstructured": i.i.d. monthly totals. Split into 3-8 random-day payments.
  * refunds (dining, occasional), monthly savings transfer (neutral), small fees, pending and failed records,
    and 2 missing months (no records at all) for users divisible by 10.
  * anomalies injected in the last 3 months for users divisible by 4: amount x8 (groceries), unusual hour
    (03:xx, dining), rare category ('jewelry'); labelled in the ground truth.
Experiments:
  C1 financial correctness: Decimal recomputation from raw rows vs build_summaries (exact equality).
  C2 recurring detection: precision/recall of insights.recurring_candidates vs subscription ground truth.
  C3 forecasting positive control: HW2 features + GBR (E2 config) vs baselines on monthly dining spending,
     structured vs unstructured users; train targets months 6-23, validation 24-29, test 30-35.
  C4 unusual transactions: app review_candidates (top 5) detection rate per injected type.
Outputs: data/samples/controlled_synthetic.csv is NOT written (generated on demand); results in
reports/experiments/dataset_c/summary.json.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
MONTHS = [f"{2023 + i // 12}-{i % 12 + 1:02d}" for i in range(36)]


def generate(seed: int = 42, n_users: int = 200):
    rng = np.random.default_rng(seed)
    rows, truth = [], {"subscriptions": [], "income": [], "anomalies": [], "structured_users": list(range(n_users // 2))}
    tid = 0

    def add(u, cur, ts, typ, amt, cat, status="completed"):
        nonlocal tid
        tid += 1
        rows.append({"transaction_id": f"C{tid:08d}", "account_id": f"U{u:03d}", "transaction_type": typ,
                     "amount": f"{amt:.2f}", "currency": cur, "merchant_category": cat,
                     "transaction_timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"), "status": status})
        return f"C{tid:08d}"

    for u in range(n_users):
        cur = ["USD", "EUR", "TRY"][u % 3]
        scale = {"USD": 1.0, "EUR": 0.9, "TRY": 30.0}[cur]
        missing = set(rng.choice(range(3, 33), 2, replace=False)) if u % 10 == 0 else set()
        salary = round(float(rng.uniform(2000, 5000)) * scale, 2)
        subs = []
        for _ in range(int(rng.integers(1, 4))):
            subs.append({"period": str(rng.choice(["monthly", "weekly"])), "amount": round(float(rng.uniform(5, 60)) * scale, 2),
                         "day": int(rng.integers(1, 28)), "weekday": int(rng.integers(0, 7))})
        truth["subscriptions"] += [{"user": f"U{u:03d}", **s} for s in subs]
        truth["income"].append({"user": f"U{u:03d}", "amount": salary})
        level, ar = float(rng.uniform(150, 400)) * scale, 0.0
        for mi, m in enumerate(MONTHS):
            if mi in missing:
                continue
            y, mo = map(int, m.split("-"))
            start = datetime(y, mo, 1)
            ndays = ((datetime(y + (mo == 12), mo % 12 + 1, 1)) - start).days
            add(u, cur, start + timedelta(days=24, hours=9), "deposit", salary * float(rng.uniform(0.99, 1.01)), "income")
            for s in subs:
                if s["period"] == "monthly":
                    add(u, cur, start + timedelta(days=s["day"] - 1, hours=8), "debit", s["amount"] * float(rng.uniform(0.99, 1.01)), "subscription")
                else:
                    d0 = (s["weekday"] - start.weekday()) % 7
                    for d in range(d0, ndays, 7):
                        add(u, cur, start + timedelta(days=d, hours=7), "debit", s["amount"] * float(rng.uniform(0.99, 1.01)), "subscription")
            for d in range(int(rng.integers(0, 7)), ndays, 7):
                add(u, cur, start + timedelta(days=d, hours=18), "debit", float(rng.uniform(30, 90)) * scale * float(rng.uniform(0.6, 1.4)), "groceries")
            if u < n_users // 2:
                ar = 0.7 * ar + float(rng.normal(0, 0.25))
                total = level * float(np.exp(ar)) * (1.4 if mo == 12 else 1.0)
            else:
                total = level * float(rng.lognormal(0, 0.35))
            k = int(rng.integers(3, 9))
            parts = rng.dirichlet(np.ones(k)) * total
            for p in parts:
                add(u, cur, start + timedelta(days=int(rng.integers(0, ndays)), hours=int(rng.integers(11, 22))), "debit", max(p, 1.0), "dining")
            if rng.random() < 0.2:
                add(u, cur, start + timedelta(days=int(rng.integers(0, ndays)), hours=14), "refund", float(parts[0]) * 0.5, "dining")
            add(u, cur, start + timedelta(days=26, hours=10), "transfer", salary * 0.1, "savings")
            add(u, cur, start + timedelta(days=27, hours=10), "fee", 2.5 * scale, "bank fee")
            add(u, cur, start + timedelta(days=15, hours=13), "debit", 99.0 * scale, "retail", status=str(rng.choice(["pending", "failed"])))
            if u % 4 == 0 and mi >= 33:
                kind = ["amount", "hour", "category"][mi - 33]
                when = start + timedelta(days=10, hours=3 if kind == "hour" else 15)
                amt = (300.0 if kind == "amount" else 40.0) * scale * (8 if kind == "amount" else 1)
                cat = {"amount": "groceries", "hour": "dining", "category": "jewelry"}[kind]
                truth["anomalies"].append({"user": f"U{u:03d}", "type": kind, "transaction_id": add(u, cur, when, "debit", amt, cat)})
    return pl.DataFrame(rows), truth


def c1_financial(raw: pl.DataFrame, clean: pl.DataFrame, s) -> dict:
    exp: dict = {}
    sign = {"debit": "out", "withdrawal": "out", "fee": "fee", "refund": "ref", "deposit": "in", "credit": "in", "interest": "in"}
    for r in raw.iter_rows(named=True):
        if r["status"] != "completed" or r["transaction_type"] not in sign:
            continue
        k = (r["account_id"], r["currency"], r["transaction_timestamp"][:7])
        e = exp.setdefault(k, {"in": Decimal(0), "out": Decimal(0), "fee": Decimal(0), "ref": Decimal(0)})
        e[sign[r["transaction_type"]]] += Decimal(r["amount"])
    mism = 0
    for row in s.monthly.iter_rows(named=True):
        e = exp.get((row["account_id"], row["currency"], row["month"]))
        inc = int(e["in"] * 100) if e else 0
        ex = int((e["out"] + e["fee"] - e["ref"]) * 100) if e else 0
        mism += (row["income_cents"] != inc) + (row["expenses_cents"] != ex)
    return {"groups": s.monthly.height, "checks": 2 * s.monthly.height, "mismatches": int(mism),
            "raw_rows": raw.height, "clean_rows": clean.height,
            "excluded_status_rows": int(clean.filter(pl.col("status") != "completed").height)}


def c2_recurring(clean: pl.DataFrame, truth: dict) -> dict:
    from src.analytics import insights as I
    tp = fp = fn = 0
    for u in sorted(clean["account_id"].unique().to_list()):
        cur = clean.filter(pl.col("account_id") == u)["currency"][0]
        det = I.recurring_candidates(I.scope(clean, u, cur))
        det_subs = [r for r in det.iter_rows(named=True) if r["merchant_category"] == "subscription"]
        det_other = [r for r in det.iter_rows(named=True) if r["merchant_category"] != "subscription"]
        gt = [g for g in truth["subscriptions"] if g["user"] == u]
        matched = set()
        for g in gt:
            hit = next((i for i, d in enumerate(det_subs) if i not in matched and d["period"] == g["period"]
                        and abs(d["typical_amount_cents"] / 100 - g["amount"]) <= 0.02 * g["amount"]), None)
            if hit is None:
                fn += 1
            else:
                matched.add(hit)
                tp += 1
        fp += len(det_subs) - len(matched) + len(det_other)
    return {"true_positives": tp, "false_positives": fp, "false_negatives": fn,
            "precision": tp / (tp + fp) if tp + fp else None, "recall": tp / (tp + fn) if tp + fn else None,
            "ground_truth_subscriptions": len(truth["subscriptions"])}


def c3_forecast(s, truth: dict) -> dict:
    from src.evaluation.forecasting_metrics import evaluate, mase_scale
    from src.features.temporal_features import features_at
    from src.models.forecasting.baselines import BASELINES
    from src.models.forecasting.gradient_boosting import fit_gbr
    cat = s.category.filter(pl.col("merchant_category") == "dining")
    users = sorted(cat["account_id"].unique().to_list())
    Y = np.array([[dict(zip(g["month"], g["net_spending_cents"])).get(m, 0) / 100 for m in MONTHS]
                  for g in [cat.filter(pl.col("account_id") == u) for u in users]])
    cal = [int(m[5:7]) for m in MONTHS]
    struct = np.array([int(u[1:]) in truth["structured_users"] for u in users])
    params = {"learning_rate": 0.05, "max_iter": 100, "max_depth": 3, "loss": "absolute_error"}   # E2 config
    out = {}
    for name, msk in (("structured_AR1_seasonal", struct), ("unstructured_iid", ~struct)):
        Ys = Y[msk]
        scale = mase_scale(Ys[:, :24])
        val, test = list(range(24, 30)), list(range(30, 36))
        res = {"series": int(msk.sum())}
        for split, cols, tr in (("validation", val, list(range(12, 24))), ("test", test, list(range(12, 30)))):
            m = fit_gbr(Ys, tr, cal, params, seasonal=True)
            preds = {"gbr_seasonal_E2config": np.column_stack([m.predict(features_at(Ys, t, cal[t], True)) for t in cols]),
                     "zero": np.zeros((len(Ys), len(cols))),
                     "historical_median": np.column_stack([np.median(Ys[:, :t], axis=1) for t in cols]),
                     **{b: np.column_stack([BASELINES[b](Ys, t) for t in cols]) for b in BASELINES}}
            res[split] = {k: {mm: round(v_, 4) for mm, v_ in evaluate(Ys[:, cols], p, scale).items() if mm in ("MAE", "MASE")}
                          for k, p in preds.items()}
        best_base_val = min((k for k in res["validation"] if k != "gbr_seasonal_E2config"), key=lambda k: res["validation"][k]["MAE"])
        g = res["validation"]["gbr_seasonal_E2config"]
        res["gbr_beats_best_baseline_validation"] = (g["MAE"] < res["validation"][best_base_val]["MAE"] and
                                                     g["MASE"] < res["validation"][best_base_val]["MASE"])
        res["best_baseline_validation"] = best_base_val
        out[name] = res
    return out


def c4_anomaly(clean: pl.DataFrame, truth: dict) -> dict:
    from src.models.anomaly.anomaly_scoring import review_candidates
    by_type = {t: {"injected": 0, "in_top5": 0} for t in ("amount", "hour", "category")}
    flagged_normal = flagged_total = 0
    inj = {a["transaction_id"]: a["type"] for a in truth["anomalies"]}
    for u in sorted({a["user"] for a in truth["anomalies"]}):
        cur = clean.filter(pl.col("account_id") == u)["currency"][0]
        r = review_candidates(clean, u, cur)
        ids = set(r["candidates"]["transaction_id"].to_list()) if r["ok"] else set()
        for tid, t in inj.items():
            if tid in set(clean.filter(pl.col("account_id") == u)["transaction_id"].to_list()):
                by_type[t]["injected"] += 1
                by_type[t]["in_top5"] += tid in ids
        flagged_total += len(ids)
        flagged_normal += len([i for i in ids if i not in inj])
    for t in by_type.values():
        t["detection_rate"] = t["in_top5"] / t["injected"] if t["injected"] else None
    return {"by_type": by_type, "flagged": flagged_total, "flagged_not_injected": flagged_normal,
            "precision_of_flags": (flagged_total - flagged_normal) / flagged_total if flagged_total else None}


def main() -> None:
    from src.analytics.aggregation import build_summaries
    from src.data.validation import validate_transactions
    raw, truth = generate()
    v = validate_transactions(raw)
    s = build_summaries(v.clean)
    res = {"dataset_id": "C-CONTROLLED-SYNTHETIC-v1", "seed": 42, "users": 200, "rows": raw.height,
           "rejected_rows": v.rejected.height,
           "C1_financial": c1_financial(raw, v.clean, s), "C2_recurring": c2_recurring(v.clean, truth),
           "C3_forecasting_positive_control": c3_forecast(s, truth), "C4_unusual_transactions": c4_anomaly(v.clean, truth)}
    out = ROOT / "reports/experiments/dataset_c"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(json.dumps(res, indent=1, default=float)[:6000])


if __name__ == "__main__":
    main()
