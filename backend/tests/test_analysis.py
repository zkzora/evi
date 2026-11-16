"""analysis-v2: reference comparison must not depend on the detector's verdict (read-only over real artifacts)."""
from pathlib import Path

import pytest

from evi import analysis
from evi.replay import connect_ro

ROOT = Path(__file__).resolve().parents[2]
RO = lambda: connect_ro(ROOT / "data" / "runs" / "evi.sqlite3")
pytestmark = pytest.mark.skipif(not (ROOT / "artifacts" / "technical-proof" / "exp-2026-11-16-a" / "ledger.jsonl").exists(),
                                reason="real experiment artifacts not present")


def test_start_date_derivation_uses_model_claims_not_certificate():
    fact = {"period": {"end_date": "2025-12-31", "duration_months": 12, "start_date": None}}
    assert analysis.derived_start(fact) == ("2025-01-01", "R-CAL-MONTHEND")
    assert analysis.derived_start({"period": {"end_date": None, "duration_months": 3}})[0] is None   # AT&T: nothing to derive


def test_checker_false_alarms_are_not_counted_as_model_errors():
    rows, s = analysis.evaluate("exp-2026-11-16-a", conn=RO())
    fa = [r for r in rows if r["arm"] == "A" and r["reference_match"] and r["certificate"] != "supported"]
    assert len(fa) == 6                                    # 4 AT&T 2Q t1 + 2 Verizon FY2025 t2 (binding-v2 section rule)
    assert s["detector_B"] == {"TP": 34, "FP": 6, "TN": 56}  # no FN: every reference mismatch was flagged
    assert s["by_arm"]["A"]["reference_match"] == 62 and s["by_arm"]["A"]["composite"] == 56


def test_denominators_stable_and_c_equals_d():
    for exp in ("exp-2026-11-16-a", "exp-2026-11-16-b"):
        _, s = analysis.evaluate(exp, conn=RO())
        assert {a["executed"] for a in s["by_arm"].values()} == {96}
        assert s["by_arm"]["C"] == s["by_arm"]["D"]
        assert s["paired"]["reference_match:C->D"].get("improvement", 0) == 0 == s["paired"]["reference_match:C->D"].get("regression", 0)


def test_null_dates_counted_as_faithful_not_complete_interval():
    rows, s = analysis.evaluate("exp-2026-11-16-a", conn=RO())
    att = [r for r in rows if r["arm"] == "A" and r["document_id"].startswith("att") and r["reference_match"]]
    assert att and not any(r["complete_interval"] for r in att)
    assert s["by_arm"]["A"]["complete_interval"] <= s["by_arm"]["A"]["reference_interval_known"] == 48
