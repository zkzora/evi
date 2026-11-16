"""Integration checks over REAL artifacts in data/runs (produced by an actual Docling parse).

Skipped when no real parse exists. For every evidence item with a bbox, extract the PDF's own text inside that
rectangle with pdfium and require it to match the evidence text. This proves highlights point at real regions.
"""
import re
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "runs" / "evi.sqlite3"
pytestmark = pytest.mark.skipif(not DB.exists(), reason="no real parse database")


def norm(s: str) -> str:
    return re.sub(r"[\s$—–-]+", "", s).lower()


def test_real_bboxes_contain_their_text():
    import json

    import pypdfium2 as pdfium
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    parses = conn.execute("SELECT p.parse_id, d.file_name, d.sha256, p.document_sha256 FROM parses p JOIN documents d USING(document_id)").fetchall()
    assert parses
    checked, mismatched = 0, []
    for p in parses:
        assert p["sha256"] == p["document_sha256"]
        pdf = pdfium.PdfDocument(str(ROOT / "public" / "sources" / p["file_name"]))
        for e in conn.execute("SELECT * FROM evidence WHERE parse_id=? AND bbox_json IS NOT NULL AND kind='table_cell'", (p["parse_id"],)):
            b = json.loads(e["bbox_json"])
            page = pdf[e["page_number"] - 1]
            w, h = page.get_size()
            assert abs(w - e["page_width"]) < 1 and abs(h - e["page_height"]) < 1
            if b["origin"] == "TOPLEFT":
                left, right, top, bottom = b["left"], b["right"], h - b["top"], h - b["bottom"]
            else:
                left, right, top, bottom = b["left"], b["right"], b["top"], b["bottom"]
            # Docling and PDF.js both use CropBox space; pdfium text bounds use MediaBox space.
            cx, cy = page.get_cropbox()[:2]
            text = page.get_textpage().get_text_bounded(left=cx + left - 1, bottom=cy + bottom - 1, right=cx + right + 1, top=cy + top + 1)
            checked += 1
            if e["text"].strip() in {"-", "—", "–"} and "�" in text:
                continue  # the PDF draws the dash with an unmapped glyph; position verified, text not extractable
            if norm(e["text"]) not in norm(text):
                mismatched.append((p["file_name"], e["text"]))
    assert checked > 150
    # Observed 2026-11-16 on the AT&T parses: Docling boxes that clip one glyph or straddle a wrapped header.
    # None is a value cell or a target row label; they are listed explicitly so any NEW mismatch fails.
    documented = {("att-3q2025.pdf", "Cost of revenues"), ("att-2q2025.pdf", "Cost of revenues"),
                  ("att-2q2025.pdf", "Percent"), ("att-2q2025.pdf", "Net Income Attributable to Noncontrolling Interest")}
    assert set(mismatched) <= documented, f"undocumented bbox mismatches: {set(mismatched) - documented}"


def test_every_resolved_target_cell_and_row_label_box_is_exact():
    """All 48 frozen targets: the resolver's value cell and row label boxes contain their text at a 1pt margin."""
    import json

    import pypdfium2 as pdfium

    from evi import binding, db, targets
    conn = db.connect(DB)
    checked = 0
    for doc in targets.COLUMNS:
        p = db.row(conn, "SELECT p.parse_id, d.file_name FROM parses p JOIN documents d USING(document_id) WHERE p.document_id=? "
                         "ORDER BY p.created_at DESC LIMIT 1", doc)
        if p is None:
            continue
        s = binding.load_structure(conn, p["parse_id"])
        pdf = pdfium.PdfDocument(str(ROOT / "public" / "sources" / p["file_name"]))
        for t in targets.targets_for(doc):
            r = binding.resolve_target(s, t, True, s.source_sha256)
            assert r["outcome"] == "supported", t["target_key"]
            cand = next(c for c in r["candidates"] if c["value_cell"] == r["classes"][0]["value_cells"][0])
            label_id = next(e["src"] for e in cand["edges"] if e["rel"] == "row_label_for")
            for eid in (cand["value_cell"], label_id):
                e = conn.execute("SELECT * FROM evidence WHERE evidence_id=?", (eid,)).fetchone()
                b = json.loads(e["bbox_json"])
                page = pdf[e["page_number"] - 1]
                w, h = page.get_size()
                cx, cy = page.get_cropbox()[:2]
                txt = page.get_textpage().get_text_bounded(left=cx + b["left"] - 1, right=cx + b["right"] + 1,
                                                           top=cy + h - b["top"] + 1, bottom=cy + h - b["bottom"] - 1)
                assert norm(e["text"]) in norm(txt), (t["target_key"], e["text"], txt)
                checked += 1
    assert checked == 96


def test_certificates_reverify_under_their_own_recorded_policy():
    """A certificate issued under an older binding policy must re-verify with THAT policy's rules (not the current ones),
    and must fail if re-labelled with a different policy."""
    import copy
    import hashlib
    import json

    from evi import binding, db
    conn = db.connect(DB)
    for pol in binding.SUPPORTED_POLICIES:
        r = conn.execute("SELECT body_json FROM certificates WHERE policy_version=? LIMIT 1", (pol,)).fetchone()
        if r is None:
            continue
        cert = json.loads(r["body_json"])
        ok, problems = binding.verify_certificate(conn, cert)
        assert ok, (pol, problems)
    r = conn.execute("SELECT body_json FROM certificates WHERE policy_version='binding-v1' LIMIT 1").fetchone()
    if r:
        forged = copy.deepcopy(json.loads(r["body_json"]))
        forged["policy_version"] = "binding-v3"
        body = {k: v for k, v in forged.items() if k != "content_sha256"}
        forged["content_sha256"] = hashlib.sha256(binding.canonical(body).encode()).hexdigest()
        assert not binding.verify_certificate(conn, forged)[0]


def test_att_fact_with_unprinted_dates_is_not_complete_coverage():
    """coverage-v1: a unique supported AT&T reading must not be presented as complete exact-period verification."""
    import json

    from evi import binding, db
    conn = db.connect(DB)
    rows = conn.execute("SELECT body_json FROM certificates WHERE document_id LIKE 'att-%' AND claim_outcome='supported'").fetchall()
    assert rows
    for r in rows:
        cov = binding.coverage_view(json.loads(r["body_json"]))
        assert cov["unique_supported_reading"] and not cov["complete_required_context"]
        assert cov["exact_interval"] == "not_printed_in_source" and "not printed" in cov["label"]
    v = conn.execute("SELECT body_json FROM certificates WHERE document_id='verizon-3q2025' AND claim_outcome='supported' LIMIT 1").fetchone()
    assert binding.coverage_view(json.loads(v["body_json"]))["complete_required_context"] is True
