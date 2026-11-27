"""Gate 10: verify every registered artifact loads in a FRESH process and produces predictions.

For each entry in artifacts/metadata/model_registry.json: metadata.json present; if a model.joblib
exists, load it in a new interpreter, check its feature count against feature_schema.json, predict
on real rows (forecasting: primary panel; anomaly: anomaly history features), and confirm the
feature schema excludes balance_after and account_id.
Without the derived data (a fresh clone has no dataset) - or with ARTIFACT_VERIFY_INPUT=demo - the inputs come
from the committed demo sample instead (master audit M-06), so model loading is verifiable in every checkout.
Output: reports/verification/artifact_verification.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHILD = r"""
import json, os, sys, joblib, numpy as np, polars as pl
sys.path.insert(0, '.')
path, kind = sys.argv[1], sys.argv[2]
DERIVED = os.path.exists('data/processed/splits/panel_primary.parquet') and os.environ.get('ARTIFACT_VERIFY_INPUT') != 'demo'
if not DERIVED:
    from src.data.ingestion import ingest
    from src.analytics.aggregation import build_summaries
    demo = ingest(open('data/samples/demo_transactions.csv', 'rb').read())[0].clean
m = joblib.load(f'{path}/model.joblib')
schema = json.load(open(f'{path}/feature_schema.json'))
feats = schema['features']
assert m.n_features_in_ == len(feats), (m.n_features_in_, feats)
assert not set(schema.get('excluded', [])) & set(feats)
if kind == 'forecasting':
    from src.experiments import forecasting_experiment as fe
    from src.features.temporal_features import features_at
    if DERIVED:
        _, Y = fe.load_panel('data/processed/splits/panel_primary.parquet')
    else:   # demo sample: every account-currency series over the 31 dataset months, zero-filled
        from src.experiments.data_splitting import ALL_MONTHS
        mon = build_summaries(demo).monthly
        Y = np.array([[r.get(m, 0) / 100 for m in ALL_MONTHS] for r in
                      [dict(zip(g['month'], g['expenses_cents'])) for _, g in mon.group_by(['account_id', 'currency'])]])
    if 'lag1_r' in feats:    # E2-B scale-free model: continuous series from the PersonaLedger demo sample
        from src.data.ingestion import ingest as _ing
        from src.analytics.aggregation import build_summaries as _bs
        from src.models.forecasting import scale_free
        from src.models.forecasting.inference import series_from_monthly, next_month
        _s = _bs(_ing(open('data/samples/demo_personaledger.csv', 'rb').read())[0].clean)
        X = np.vstack([scale_free.features(y, next_month(ms[-1]))[0] for ms, y, _ in
                       [series_from_monthly(g) for _, g in _s.monthly.group_by(['account_id', 'currency'])]])
    else:
        X = features_at(Y[:500], 30, fe.CAL[30], 'lag_12' in feats)
    p = m.predict(X)
else:
    from src.experiments.anomaly_experiment import prepare
    from src.features.account_features import build_features
    tx = pl.read_parquet('data/processed/splits/anomaly_transactions.parquet') if DERIVED else demo
    hist, scored, acc, cat, _ = prepare(tx.filter(pl.col('account_id').is_in(tx['account_id'].unique().sort().head(50).implode())))
    p = -m.score_samples(build_features(scored, acc, cat).select(feats).to_numpy())
assert np.isfinite(p).all()
print(json.dumps({'n_pred': int(len(p)), 'mean': float(np.mean(p)), 'type': type(m).__name__,
                  'input': 'demo_personaledger sample' if 'lag1_r' in feats else ('derived data' if DERIVED else 'demo sample')}))
"""


def main() -> None:
    reg = json.loads((ROOT / "artifacts/metadata/model_registry.json").read_text())
    results, ok_all = [], True
    for kind, models in reg.items():
        for name, entry in models.items():
            d = ROOT / entry["current"]
            rec = {"kind": kind, "model": name, "path": entry["current"], "role": entry["role"],
                   "versions": len(entry["history"]), "metadata": (d / "metadata.json").exists()}
            if (d / "model.joblib").exists():
                r = subprocess.run([sys.executable, "-c", CHILD, str(d), kind], cwd=ROOT, capture_output=True, text=True)
                rec["fresh_process_load"] = r.returncode == 0
                rec["detail"] = json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else r.stderr[-800:]
            else:
                rec["fresh_process_load"] = "n/a (no trainable artifact by design)"
            rec["status"] = "PASS" if rec["metadata"] and rec["fresh_process_load"] in (True, "n/a (no trainable artifact by design)") else "FAIL"
            ok_all &= rec["status"] == "PASS"
            results.append(rec)
            print(rec["status"], kind, name, rec.get("detail", ""))
    out = {"overall": "PASS" if ok_all else "FAIL", "artifacts": results}
    import os
    target = Path(os.environ.get("ARTIFACT_VERIFY_OUT", ROOT / "reports/verification/artifact_verification.json"))
    target.write_text(json.dumps(out, indent=2))
    raise SystemExit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
