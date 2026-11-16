"""review-v1 importer. All sheets here are TEST sheets in temporary storage; the real sheet stays 0/48 pending."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest

from evi import review

ROOT = Path(__file__).resolve().parents[2]
REAL_SHEET = ROOT / "data" / "references" / "review" / "review-sheet-references-v1.json"
REFS = ROOT / "data" / "references" / "references-v1.json"
TODAY = dt.date(2026, 11, 16)


def base():
    return json.loads(REAL_SHEET.read_text())


def filled(relation="independent_human"):
    s = base()
    s["review_provenance"] = {"reviewer_name": "TEST REVIEWER (synthetic test fixture)", "reviewer_relation": relation,
                              "method": "TEST: inspected rendered issuer pages", "declaration": "TEST ONLY"}
    for i in s["items"]:
        i.update(review_status="confirmed", reviewer="TEST REVIEWER", reviewed_at="2026-11-16",
                 rationale=f"TEST: printed {i['draft']['printed_amount']} on row {i['draft']['row_label']}",
                 source_evidence=f"TEST: box {i['box_number']} {i['target_key']}")
    return s


def write(tmp_path, s, name="sheet.json"):
    p = tmp_path / name
    p.write_text(json.dumps(s))
    return p


def test_real_sheet_is_valid_and_pending():
    v = review.validate(base(), today=TODAY)
    assert v["errors"] == [] and v["counts"] == {"pending": 48} and v["complete"] is False and v["reviewed"] == 0


def test_complete_test_sheet_imports_new_version_and_preserves_v1(tmp_path):
    before = hashlib.sha256(REFS.read_bytes()).hexdigest()
    s = filled()
    s["items"][0].update(review_status="corrected", proposed_corrections={"amount": "138192", "printed_amount": "138,192"})
    out = review.import_sheet(write(tmp_path, s), out_dir=tmp_path / "out", today=TODAY)
    assert out["independent"] is True and out["version"].startswith("references-r1-")
    new = json.loads(Path(out["reference"]).read_text())
    assert new["items"][0]["amount"] == "138192" and new["items"][0]["normalized_value"] == "138192000000"
    assert new["derived_from"]["sha256"] == before and "not independently authenticated" in new["provenance"]
    assert hashlib.sha256(REFS.read_bytes()).hexdigest() == before
    with pytest.raises(SystemExit, match="refusing to overwrite"):
        review.import_sheet(write(tmp_path, s), out_dir=tmp_path / "out", today=TODAY)


@pytest.mark.parametrize("mutate,msg", [
    (lambda s: s["items"].pop(), "missing targets"),
    (lambda s: s["items"].append(copy.deepcopy(s["items"][0])), "duplicate targets"),
    (lambda s: s["items"][0].update(target_key="nope:revenue:3M:2025"), "unknown targets"),
    (lambda s: s.update(reference_sha256="0" * 64), "different reference file hash"),
    (lambda s: s["items"][0]["draft"].update(amount="1"), "changed reference identity"),
    (lambda s: s["items"][0].update(review_status="corrected", proposed_corrections={"amount": "12,3"}), "decimal"),
    (lambda s: s["items"][0].update(review_status="corrected", proposed_corrections={"end_date": "2025-02-30"}), "YYYY-MM-DD"),
    (lambda s: s["items"][0].update(review_status="corrected", proposed_corrections={"unit_scale": "1000000000000"}), "unit_scale"),
    (lambda s: s["items"][0].update(review_status="corrected", proposed_corrections={"currency": "$"}), "ISO 4217"),
    (lambda s: s["items"][0].update(review_status="corrected", proposed_corrections={}), "no field-level corrections"),
    (lambda s: s["items"][0].update(reviewed_at="2030-01-01"), "future"),
    (lambda s: s["items"][0].update(source_evidence=""), "source_evidence missing"),
    (lambda s: s["review_provenance"].update(reviewer_relation="friend"), "reviewer_relation"),
])
def test_invalid_sheets_rejected(tmp_path, mutate, msg):
    s = filled()
    mutate(s)
    v = review.validate(s, today=TODAY)
    assert any(msg in e for e in v["errors"]), v["errors"][:3]
    with pytest.raises(SystemExit):
        review.import_sheet(write(tmp_path, s), out_dir=tmp_path / "out", today=TODAY)


def test_blanket_synthetic_approval_rejected():
    s = filled()
    for i in s["items"]:
        i.update(rationale="Looks correct.", source_evidence="Checked the PDF.")
    assert any("blanket review" in e for e in review.validate(s, today=TODAY)["errors"])


def test_pending_entries_never_carry_a_reviewer_or_count_as_confirmed(tmp_path):
    s = base()
    s["items"][0].update(reviewer="Someone", reviewed_at="2026-11-16")
    assert any("pending entry carries" in e for e in review.validate(s, today=TODAY)["errors"])
    s = filled()
    s["items"][5].update(review_status="pending", reviewer=None, reviewed_at=None, rationale=None, source_evidence=None)
    with pytest.raises(SystemExit, match="incomplete"):
        review.import_sheet(write(tmp_path, s), out_dir=tmp_path / "out", today=TODAY)


def test_agent_or_builder_review_is_labelled_not_independent(tmp_path):
    for rel in ("agent", "builder"):
        v = review.validate(filled(rel), today=TODAY)
        assert v["errors"] == [] and v["independent"] is False and "NOT" in v["warnings"][0]
    out = review.import_sheet(write(tmp_path, filled("agent")), out_dir=tmp_path / "o", today=TODAY)
    assert out["independent"] is False
    assert json.loads(Path(out["reference"]).read_text())["independent_human_review"] is False


def test_ambiguity_preserved_and_adjudication_explicit(tmp_path):
    s = filled()
    s["items"][2].update(review_status="ambiguous", rationale="TEST: page omits it", source_evidence="TEST: box 3")
    out = review.import_sheet(write(tmp_path, s), out_dir=tmp_path / "a", today=TODAY)
    assert json.loads(Path(out["reference"]).read_text())["items"][2]["status"] == "ambiguous_unadjudicated"
    k = s["items"][2]["target_key"]
    adj = tmp_path / "adj.json"
    adj.write_text(json.dumps({k: {"decision": "unresolvable", "adjudicator": "TEST ADJUDICATOR", "adjudicated_at": "2026-11-16",
                                   "rationale": "TEST: source insufficient"}}))
    s["items"][3]["rationale"] = "TEST: distinct sheet"
    out2 = review.import_sheet(write(tmp_path, s, "s2.json"), adj, out_dir=tmp_path / "a", today=TODAY)
    assert json.loads(Path(out2["reference"]).read_text())["items"][2]["status"] == "ambiguous_unresolvable"
    adj.write_text(json.dumps({k: {"decision": "apply_correction"}}))
    s["items"][4]["rationale"] = "TEST: third sheet"
    with pytest.raises(SystemExit, match="adjudication"):
        review.import_sheet(write(tmp_path, s, "s3.json"), adj, out_dir=tmp_path / "a", today=TODAY)


def test_reviewed_reference_analysis_separates_reference_change_from_predictions(tmp_path):
    from evi import analysis
    from evi.replay import connect_ro
    s = filled()
    k0 = s["items"][0]["target_key"]
    s["items"][0].update(review_status="corrected", proposed_corrections={"amount": "1"})
    s["items"][1].update(review_status="ambiguous", rationale="TEST: ambiguous", source_evidence="TEST: box 2")
    out = review.import_sheet(write(tmp_path, s), out_dir=tmp_path / "r", today=TODAY)
    res = analysis.evaluate_reviewed("exp-2026-11-16-a", out["reference"], conn=connect_ro(ROOT / "data" / "runs" / "evi.sqlite3"),
                                     write_out=False)
    a = res["by_arm"]["A"]
    assert a["executed"] == 96 and a["reference_ambiguous"] == 2              # one ambiguous target x 2 trials
    assert a["targets_whose_reference_changed"] == 2                          # the corrected target x 2 trials
    assert a["reviewed_reference_match"] <= a["v1_reference_match"]
    assert "TEST" in res["reference_provenance"] or res["independent_human_review"] is True
