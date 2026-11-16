"""reppo-packet-v2 (dry run; never submitted)."""
import json
from pathlib import Path

import pytest

from evi import evaluation
from evi.replay import connect_ro

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "runs" / "evi.sqlite3"
pytestmark = pytest.mark.skipif(not DB.exists(), reason="real database not present")
WRONG_ROW_VERSION = "ver_63c7ce8b5e69_1"   # AT&T 2Q t1: candidate used 'Attributable to Common Stock'


def test_wrong_row_case_has_the_correct_alternative_row():
    pk = json.loads(evaluation.build_input_v2(connect_ro(DB), WRONG_ROW_VERSION))
    labels = [c["text"] for t in pk["full_statement_tables"] for r in t["rows"] for c in r["cells"] if c["col"][0] == 0]
    assert "Net Income Attributable to AT&T" in labels and "Net Income Attributable to Common Stock" in labels
    assert pk["packet_version"] == "reppo-packet-v2" and "not only the cells the candidate cites" in pk["task"]
    assert pk["candidate_response"]["version_id"] == WRONG_ROW_VERSION and len(pk["requested_targets"]) == 12


def test_over_limit_packet_fails_instead_of_truncating():
    with pytest.raises(evaluation.PacketTooLarge, match="not truncated"):
        evaluation.build_input_v2(connect_ro(DB), WRONG_ROW_VERSION, max_bytes=1000)


def test_packet_v1_unchanged_for_history():
    v1 = json.loads(evaluation.build_input(connect_ro(DB), WRONG_ROW_VERSION))
    assert "full_statement_tables" not in v1 and "cited_evidence" in v1
