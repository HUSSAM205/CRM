"""Gate 10: verify every registered artifact loads in a FRESH process and produces predictions.

For each entry in artifacts/metadata/model_registry.json: metadata.json present; if a model.joblib
exists, load it in a new interpreter, check its feature count against feature_schema.json, predict
on real rows (forecasting: primary panel; anomaly: anomaly history features), and confirm the
feature schema excludes balance_after and account_id.
Output: reports/verification/artifact_verification.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHILD = r"""
import json, sys, joblib, numpy as np, polars as pl
sys.path.insert(0, '.')
path, kind = sys.argv[1], sys.argv[2]
m = joblib.load(f'{path}/model.joblib')
schema = json.load(open(f'{path}/feature_schema.json'))
feats = schema['features']
assert m.n_features_in_ == len(feats), (m.n_features_in_, feats)
assert not set(schema.get('excluded', [])) & set(feats)
if kind == 'forecasting':
    from src.experiments import forecasting_experiment as fe
    from src.features.temporal_features import features_at
    _, Y = fe.load_panel('data/processed/splits/panel_primary.parquet')
    X = features_at(Y[:500], 30, fe.CAL[30], 'lag_12' in feats)
    p = m.predict(X)
else:
    from src.experiments.anomaly_experiment import prepare
    from src.features.account_features import build_features
    tx = pl.read_parquet('data/processed/splits/anomaly_transactions.parquet')
    hist, scored, acc, cat, _ = prepare(tx.filter(pl.col('account_id').is_in(tx['account_id'].unique().sort().head(50).implode())))
    p = -m.score_samples(build_features(scored, acc, cat).select(feats).to_numpy())
assert np.isfinite(p).all()
print(json.dumps({'n_pred': int(len(p)), 'mean': float(np.mean(p)), 'type': type(m).__name__}))
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
    (ROOT / "reports/verification/artifact_verification.json").write_text(json.dumps(out, indent=2))
    raise SystemExit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
