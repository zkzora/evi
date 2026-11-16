"""Controlled revision-gate tests (docs/19 §8, docs/20 §8) over a COPY of the real database and the real Verizon 3Q25
parse. Parents marked 'controlled' are deliberately corrupted copies; they never enter natural results."""
import copy
import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from evi import binding, db
from evi.revision import Patch, Proposal, Unresolve, gate

REAL = Path(__file__).resolve().parents[2] / "data" / "runs" / "evi.sqlite3"
VID = "ver_02d96b0afcce_1"
pytestmark = pytest.mark.skipif(not REAL.exists(), reason="no real database")


@pytest.fixture()
def env(tmp_path):
    dst = tmp_path / "copy.sqlite3"
    src = sqlite3.connect(REAL)
    src.backup(sqlite3.connect(dst))
    conn = db.connect(dst)
    db.init(conn)
    v = db.row(conn, "SELECT * FROM versions WHERE version_id=?", VID)
    if v is None:
        pytest.skip("natural v2 version not present")
    body = json.loads(v["body_json"])
    run = db.row(conn, "SELECT * FROM runs WHERE run_id=?", v["run_id"])
    s = binding.load_structure(conn, run["parse_id"])
    return conn, body, run, s


def fact(body, key):
    return next(f for f in body["facts"] if f["target_key"] == key)


def find_cell(s, text):
    return next(c.id for c in s.cell_by_id.values() if c.text == text)


def run_gate(env, parent_facts, proposal):
    conn, body, run, s = env
    return gate(conn, document_id=run["document_id"], parse_id=run["parse_id"], parent_facts=parent_facts,
                proposal=proposal, child_prefix="test")


K3 = "verizon-3q2025:revenue:3M:2025"


def test_natural_parent_is_supported_and_no_patch_is_unchanged(env):
    child, dec = run_gate(env, env[1]["facts"], Proposal())
    assert all(d["decision"] == "unchanged" for d in dec) and len(child) == 12
    assert all(d["parent_claim_outcome"] == "supported" for d in dec)


def test_legitimate_correction_of_controlled_wrong_column_is_accepted(env):
    conn, body, run, s = env
    facts = copy.deepcopy(body["facts"])
    f = fact({"facts": facts}, K3)
    wrong = find_cell(s, "33,330")                     # CONTROLLED corruption: 2024 cell claimed as 2025
    f["evidence"]["value_ids"] = [wrong]; f["reported_text"] = "33,330"; f["reported_value"] = "33330"
    right = find_cell(s, "33,821")
    p = [Patch(target_key=K3, field="value_cell", new_value=right, evidence_ids=[right], rationale_category="wrong_column"),
         Patch(target_key=K3, field="amount_text", new_value="33,821", evidence_ids=[right], rationale_category="wrong_column")]
    child, dec = run_gate(env, facts, Proposal(patches=p))
    d = next(x for x in dec if x["target_key"] == K3)
    assert d["parent_claim_outcome"] == "contradicted" and d["decision"] == "accepted"
    assert fact({"facts": child}, K3)["reported_value"] == "33821"
    assert "amount" in d["field_transitions"] or "fiscal_year" in d["field_transitions"] or d["field_transitions"]


def test_critique_requesting_annualization_is_rejected(env):
    conn, body, run, s = env
    cell = fact(body, K3)["evidence"]["value_ids"][0]
    p = [Patch(target_key=K3, field="duration_months", new_value="12", evidence_ids=[cell], rationale_category="wrong_interval"),
         Patch(target_key=K3, field="amount_text", new_value="135,284", evidence_ids=[cell], rationale_category="other")]
    child, dec = run_gate(env, body["facts"], Proposal(patches=p))
    d = next(x for x in dec if x["target_key"] == K3)
    assert d["decision"] == "rejected" and fact({"facts": child}, K3)["reported_value"] == "33821"


def test_fx_conversion_is_rejected(env):
    conn, body, run, s = env
    cell = fact(body, K3)["evidence"]["value_ids"][0]
    p = [Patch(target_key=K3, field="currency", new_value="EUR", evidence_ids=[cell], rationale_category="wrong_currency")]
    _, dec = run_gate(env, body["facts"], Proposal(patches=p))
    assert next(x for x in dec if x["target_key"] == K3)["decision"] == "rejected"


def test_invented_or_foreign_evidence_is_rejected(env):
    conn, body, run, s = env
    att = db.row(conn, "SELECT evidence_id FROM evidence WHERE document_id='att-3q2025' LIMIT 1")["evidence_id"]
    for bad in ("ev_invented0000000000", att):
        p = [Patch(target_key=K3, field="value_cell", new_value=bad, evidence_ids=[bad], rationale_category="wrong_column")]
        _, dec = run_gate(env, body["facts"], Proposal(patches=p))
        assert next(x for x in dec if x["target_key"] == K3)["why"].startswith("foreign_or_invented_evidence")


def test_forbidden_field_and_patch_without_evidence_rejected(env):
    conn, body, run, s = env
    _, dec = run_gate(env, body["facts"], Proposal(patches=[Patch(target_key=K3, field="metric", new_value="operating_profit", evidence_ids=["x"])]))
    assert next(x for x in dec if x["target_key"] == K3)["decision"] == "rejected"
    _, dec = run_gate(env, body["facts"], Proposal(patches=[Patch(target_key=K3, field="unit_scale", new_value="1000000", evidence_ids=[])]))
    assert next(x for x in dec if x["target_key"] == K3)["why"] == "patch_without_supporting_evidence"


def test_abstaining_on_supported_target_to_avoid_checks_is_rejected(env):
    conn, body, run, s = env
    cell = fact(body, K3)["evidence"]["value_ids"][0]
    child, dec = run_gate(env, body["facts"], Proposal(mark_unresolved=[Unresolve(target_key=K3, reason="unsure", evidence_ids=[cell])]))
    assert next(x for x in dec if x["target_key"] == K3)["decision"] == "rejected"
    assert len(child) == 12 and fact({"facts": child}, K3)["reported_value"] == "33821"


def test_dropping_evidence_to_gain_passes_is_rejected(env):
    conn, body, run, s = env
    p = [Patch(target_key=K3, field="period_evidence_ids", new_value="", evidence_ids=[fact(body, K3)["evidence"]["value_ids"][0]])]
    _, dec = run_gate(env, body["facts"], Proposal(patches=p))
    d = next(x for x in dec if x["target_key"] == K3)
    assert d["decision"] == "rejected" and "period_evidence" in d["why"]


def test_target_universe_is_preserved(env):
    child, _ = run_gate(env, env[1]["facts"], Proposal())
    assert [f["target_key"] for f in child] == [f["target_key"] for f in env[1]["facts"]]
