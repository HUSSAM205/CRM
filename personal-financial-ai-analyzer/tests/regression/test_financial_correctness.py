"""End-to-end financial correctness: CSV bytes -> ingest -> summaries -> dashboard totals & assistant
answers, all equal to the independent hand-calculated expectations."""
from __future__ import annotations

import json
from pathlib import Path

from src.analytics.aggregation import build_summaries, period_totals
from src.assistant.response_generator import answer
from src.data.ingestion import ingest

FIX = Path(__file__).resolve().parents[1] / "fixtures"
EXP = {(r["account_id"], r["currency"], r["month"]): r
       for r in json.loads((FIX / "expected_financial_results.json").read_text())["monthly_summary"]}


def test_upload_path_reproduces_hand_calculations():
    res, _ = ingest((FIX / "sample_transactions.csv").read_bytes())
    assert res.rejected.is_empty()
    s = build_summaries(res.clean)
    for (acc, cur, month), e in EXP.items():
        t = period_totals(s, acc, cur, [month])
        for k in ("income_cents", "expenses_cents", "net_cash_flow_cents", "transfer_cents", "fee_cents",
                  "refund_cents", "completed_records", "excluded_status_records"):
            assert t[k] == e[k], (acc, cur, month, k)
        text, r = answer(f"How much did I spend in {month}?", s, acc, cur)
        assert r["expenses_cents"] == e["expenses_cents"]
        assert f"{e['expenses_cents'] / 100:,.2f} {cur}" in text


def test_currencies_reported_separately_for_mixed_file():
    res, _ = ingest((FIX / "sample_transactions.csv").read_bytes())
    s = build_summaries(res.clean)
    usd = period_totals(s, "A1", "USD")
    eur = period_totals(s, "A1", "EUR")
    assert usd["expenses_cents"] == 13275 + 20031 and eur["expenses_cents"] == 7000
