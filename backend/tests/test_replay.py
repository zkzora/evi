"""replay-v2 regression tests on ISOLATED COPIES of the real database and proof artifacts (originals untouched).
Each mutation below would have been reported VERIFIED by replay-v1 (policy hard-coded to binding-v2, coverage taken
from whatever the query returned, and summary files rewritten before comparison)."""
import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from evi import replay as R

ROOT = Path(__file__).resolve().parents[2]
REAL_DB = ROOT / "data" / "runs" / "evi.sqlite3"
REAL_PROOF = ROOT / "artifacts" / "technical-proof"
EXP_A, EXP_B = "exp-2026-11-16-a", "exp-2026-11-16-b"
pytestmark = pytest.mark.skipif(not (REAL_DB.exists() and (REAL_PROOF / EXP_B / "manifest.json").exists()),
                                reason="real experiment artifacts not present")


@pytest.fixture()
def iso(tmp_path):
    db_copy = tmp_path / "copy.sqlite3"
    src = sqlite3.connect(f"file:{REAL_DB.as_posix()}?mode=ro", uri=True)
    src.backup(sqlite3.connect(db_copy))
    proof = tmp_path / "proof"
    for e in (EXP_A, EXP_B):
        shutil.copytree(REAL_PROOF / e, proof / e)
    rw = sqlite3.connect(db_copy)
    rw.row_factory = sqlite3.Row
    return {"db": db_copy, "proof": proof, "rw": rw}


def run(iso, exp, verify=False):
    iso["rw"].commit()
    return R.replay(exp, conn=R.connect_ro(iso["db"]), proof_dir=iso["proof"], verify_certificates=verify)


def b_versions(iso):
    led = [json.loads(l) for l in (iso["proof"] / EXP_B / "ledger.jsonl").read_text().splitlines()]
    return sorted({r["version_id"] for r in led if r.get("version_id")})


def test_unmodified_copies_verify(iso):
    for e in (EXP_A, EXP_B):
        rep = run(iso, e, verify=True)
        assert rep["result"] == "VERIFIED", rep["problems"][:5]
        assert rep["certificates"]["expected"] == rep["certificates"]["verified"] > 0


def test_removed_v3_certificate_fails(iso):
    vid = b_versions(iso)[0]
    tk = iso["rw"].execute("SELECT target_key FROM certificates WHERE version_id=? AND policy_version='binding-v3' LIMIT 1", (vid,)).fetchone()[0]
    iso["rw"].execute("DELETE FROM certificates WHERE version_id=? AND target_key=? AND policy_version='binding-v3'", (vid, tk))
    rep = run(iso, EXP_B)
    assert rep["result"] == "FAILED" and rep["certificates"]["missing"] == 1


def test_only_historical_v2_certificates_do_not_satisfy_v3(iso):
    for vid in b_versions(iso):
        iso["rw"].execute("DELETE FROM certificates WHERE version_id=? AND policy_version='binding-v3'", (vid,))
    rep = run(iso, EXP_B)
    assert rep["result"] == "FAILED"
    assert rep["certificates"]["found"] == 0 and rep["certificates"]["wrong_policy_only"] > 0


def test_wrong_policy_label_fails(iso):
    vid = b_versions(iso)[0]
    cid = iso["rw"].execute("SELECT certificate_id FROM certificates WHERE version_id=? AND policy_version='binding-v3' LIMIT 1", (vid,)).fetchone()[0]
    iso["rw"].execute("UPDATE certificates SET policy_version='binding-v2' WHERE certificate_id=?", (cid,))
    rep = run(iso, EXP_B)
    assert rep["result"] == "FAILED" and rep["certificates"]["missing"] >= 1


def test_unknown_policy_row_fails(iso):
    vid = b_versions(iso)[0]
    row = iso["rw"].execute("SELECT * FROM certificates WHERE version_id=? AND policy_version='binding-v3' LIMIT 1", (vid,)).fetchone()
    iso["rw"].execute("INSERT INTO certificates VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      ("cert_unknownpolicy", *[row[k] for k in ("version_id", "fact_id", "fact_sha256", "document_id", "parse_id", "target_key")],
                       "binding-v9", *[row[k] for k in ("claim_outcome", "resolution_outcome", "content_sha256", "body_json", "check_run_id", "created_at")]))
    rep = run(iso, EXP_B)
    assert rep["result"] == "FAILED" and rep["certificates"]["unknown_policy_rows"] == 1


def test_duplicate_conflicting_certificate_fails(iso):
    vid = b_versions(iso)[0]
    row = iso["rw"].execute("SELECT * FROM certificates WHERE version_id=? AND policy_version='binding-v3' LIMIT 1", (vid,)).fetchone()
    body = json.loads(row["body_json"])
    body["claim_outcome"] = "contradicted" if body["claim_outcome"] != "contradicted" else "supported"
    iso["rw"].execute("INSERT INTO certificates VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      ("cert_conflict", row["version_id"], row["fact_id"], row["fact_sha256"], row["document_id"], row["parse_id"],
                       row["target_key"], "binding-v3", body["claim_outcome"], row["resolution_outcome"], "x", json.dumps(body), None, row["created_at"]))
    rep = run(iso, EXP_B)
    assert rep["result"] == "FAILED" and rep["certificates"]["conflicting"] == 1


def test_missing_ledger_branch_fails(iso):
    lp = iso["proof"] / EXP_B / "ledger.jsonl"
    lines = lp.read_text().splitlines()
    lp.write_text("\n".join(l for l in lines if not ('"arm": "D"' in l and '"trial": 1' in l and "att-3q2025" in l)) + "\n")
    rep = run(iso, EXP_B)
    assert rep["result"] == "FAILED" and rep["branches"]["missing_branches"] == 1


def test_executed_target_missing_from_version_fails(iso):
    vid = b_versions(iso)[0]
    v = iso["rw"].execute("SELECT body_json FROM versions WHERE version_id=?", (vid,)).fetchone()
    body = json.loads(v[0])
    body["facts"] = body["facts"][1:]
    iso["rw"].execute("UPDATE versions SET body_json=? WHERE version_id=?", (json.dumps(body), vid))
    rep = run(iso, EXP_B)
    assert rep["result"] == "FAILED"
    assert any("content hash" in p for p in rep["problems"]) and any("target set" in p for p in rep["problems"])


def test_changed_expected_summary_fails_and_is_not_overwritten(iso):
    sp = iso["proof"] / EXP_A / "summary.json"
    s = json.loads(sp.read_text())
    s["by_arm"]["D"]["strict_correct"] += 1
    sp.write_text(json.dumps(s, indent=1))
    before = sp.read_bytes()
    rep = run(iso, EXP_A)
    assert rep["result"] == "FAILED" and rep["score"]["summary_identical"] is False
    assert sp.read_bytes() == before        # replay never rewrites expected artifacts


def test_unknown_manifest_policy_fails(iso):
    mp = iso["proof"] / EXP_B / "manifest.json"
    m = json.loads(mp.read_text())
    m["policies"]["binding"] = "binding-v9"
    mp.write_text(json.dumps(m))
    rep = run(iso, EXP_B)
    assert rep["result"] == "FAILED" and any("unknown binding policy" in p for p in rep["problems"])


def test_replay_is_read_only(iso):
    with pytest.raises(sqlite3.OperationalError):
        R.connect_ro(iso["db"]).execute("DELETE FROM certificates")
