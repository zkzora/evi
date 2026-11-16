"""Controlled mechanism tests for source-applicability binding (docs/19 §9, docs/20 §8-9).

Every table here is a CONTROLLED, hand-built structure; expected outcomes were written from the table design before
running the resolver. These are mechanism tests, not natural extraction accuracy.
"""
import copy
import random

from evi import binding as b

SHA = "f" * 64


def cell(i, r, c, text, c1=None, hdr=False, sec=False):
    return b.Cell(i, 0, r, r + 1, c, c1 if c1 is not None else c + 1, text, hdr, False, sec)


def structure(cells, texts=(), nrows=None, ncols=5, extra_tables=()):
    t = b.Table(0, 1, nrows or (max(c.r1 for c in cells)), ncols, 100.0, 400.0, list(cells))
    s = b.Structure("doc", SHA, "parse", "key", "art", {1: {"width": 600, "height": 800}}, [t, *extra_tables], list(texts))
    s.cell_by_id = {c.id: c for tt in s.tables for c in tt.cells}
    s.text_by_id = {x.id: x for x in s.texts}
    return s


TITLE = b.Text("title", "section_header", "Consolidated Statements of Income", 1, 60, 70)
UNIT_M = b.Text("unitm", "text", "(dollars in millions, except per share amounts)", 1, 80, 90)


def interim(d3="Three Months Ended September 30,", d9="Nine Months Ended September 30,"):
    return [
        cell("h3", 0, 1, d3, c1=3, hdr=True), cell("h9", 0, 3, d9, c1=5, hdr=True),
        cell("y1", 1, 1, "2025", hdr=True), cell("y2", 1, 2, "2024", hdr=True),
        cell("y3", 1, 3, "2025", hdr=True), cell("y4", 1, 4, "2024", hdr=True),
        cell("lr", 2, 0, "Total operating revenues"),
        cell("r1", 2, 1, "10,000"), cell("r2", 2, 2, "9,000"), cell("r3", 2, 3, "30,500"), cell("r4", 2, 4, "(27)"),
        cell("sec", 3, 0, "Basic Earnings Per Common Share", sec=True),
        cell("le", 4, 0, "Net income attributable to Parent Co"), cell("e1", 4, 1, "1.17"),
        cell("lo", 5, 0, "Net income attributable to Parent Co"), cell("o1", 5, 1, "—"),
    ]


def T(metric, d, y):
    return {"target_key": f"doc:{metric}:{d}M:{y}", "metric": metric, "duration_months": d, "fiscal_year": y}


def resolve(s, t):
    return b.resolve_target(s, t, True, SHA)


def obl(ev, oid):
    return next(o for o in ev["obligations"] if o["id"] == oid)


def claim(cell_id, amount, d, y, end=None, start=None, scale="1000000", cur="USD", period_ids=(), unit_ids=("unitm",), metric_ids=("lr",)):
    return {"metric": "revenue", "value_cell": cell_id, "amount": amount, "currency": cur, "unit_scale": scale,
            "duration_months": d, "fiscal_year": y, "end_date": end, "start_date": start,
            "cited": {"value_ids": [cell_id], "metric_ids": list(metric_ids), "period_ids": list(period_ids), "unit_ids": list(unit_ids)}}


def test_interim_columns_sharing_end_date_bind_by_duration_and_year():
    s = structure(interim(), [TITLE, UNIT_M])
    r3 = resolve(s, T("revenue", 3, 2025))
    r9 = resolve(s, T("revenue", 9, 2025))
    assert r3["outcome"] == r9["outcome"] == "supported"
    t3, t9 = r3["classes"][0]["tuple"], r9["classes"][0]["tuple"]
    assert (t3["amount"], t3["start_date"], t3["end_date"]) == ("10000", "2025-07-01", "2025-09-30")
    assert (t9["amount"], t9["start_date"], t9["end_date"]) == ("30500", "2025-01-01", "2025-09-30")
    assert t3["normalized_value"] == "10000000000"
    neg = resolve(s, T("revenue", 9, 2024))["classes"][0]["tuple"]
    assert neg["amount"] == "-27" and neg["normalized_value"] == "-27000000"


def test_valid_id_from_wrong_column_fails_applicability():
    s = structure(interim(), [TITLE, UNIT_M])
    ev = b.evaluate_cell(s, "r2", "revenue", True, SHA)          # 2024 column
    v = {x["field"]: x["status"] for x in b.field_verdicts(claim("r2", "9000", 3, 2025, period_ids=["h3", "y1"]), ev)}
    assert v["fiscal_year"] == "fail"                              # claims 2025 for a 2024 cell
    assert v["period_evidence"] == "fail"                          # cited 2025 header does not apply to this cell


def test_nine_months_labelled_twelve_fails():
    s = structure(interim(), [TITLE, UNIT_M])
    ev = b.evaluate_cell(s, "r3", "revenue", True, SHA)
    v = {x["field"]: x["status"] for x in b.field_verdicts(claim("r3", "30500", 12, 2025, period_ids=["h9", "y3"]), ev)}
    assert v["duration_months"] == "fail" and v["amount"] == "pass"


def test_caption_naming_several_years_binds_through_year_child():
    cells = [cell("cap", 0, 1, "Years Ended December 31, 2025 and 2024", c1=3, hdr=True),
             cell("y1", 1, 1, "2025", hdr=True), cell("y2", 1, 2, "2024", hdr=True),
             cell("lr", 2, 0, "Total revenues"), cell("a", 2, 1, "5"), cell("b", 2, 2, "4")]
    s = structure(cells, [TITLE, UNIT_M], ncols=3)
    r = resolve(s, T("revenue", 12, 2024))
    assert r["outcome"] == "supported" and r["classes"][0]["value_cells"] == ["b"]
    assert r["classes"][0]["tuple"]["end_date"] == "2024-12-31"


def test_unrelated_scale_note_above_another_table_is_not_inherited():
    other = b.Table(1, 1, 2, 2, 35.0, 50.0, [b.Cell("o", 1, 0, 1, 0, 1, "Segment data", False, False, False)])
    far_note = b.Text("thou", "text", "(in thousands)", 1, 20, 30)   # sits above the other table
    s = structure(interim(), [TITLE, far_note], extra_tables=[other])
    ev = b.evaluate_cell(s, "r1", "revenue", True, SHA)
    assert obl(ev, "U2")["status"] == "unknown"                      # no applicable scale -> not inherited
    s2 = structure(interim(), [TITLE, UNIT_M, far_note], extra_tables=[other])
    ev2 = b.evaluate_cell(s2, "r1", "revenue", True, SHA)
    assert obl(ev2, "U2")["status"] == "pass" and ev2["tuple"]["unit_scale"] == "1000000"


def test_column_specific_unit_overrides_table_caption():
    cells = interim() + [cell("cu", 0, 4, "(in thousands)", hdr=True)]
    cells = [c for c in cells if c.id != "h9"] + [cell("h9", 0, 3, "Nine Months Ended September 30,", c1=4, hdr=True)]
    s = structure(cells, [TITLE, UNIT_M])
    assert b.evaluate_cell(s, "r4", "revenue", True, SHA)["tuple"]["unit_scale"] == "1000"
    assert b.evaluate_cell(s, "r1", "revenue", True, SHA)["tuple"]["unit_scale"] == "1000000"


def test_per_share_row_excepted_from_monetary_scale():
    s = structure(interim(), [TITLE, UNIT_M])
    ev = b.evaluate_cell(s, "e1", "profit_attributable_to_owners", True, SHA)
    assert obl(ev, "U2")["status"] == "fail" and obl(ev, "M2")["status"] == "fail"


def test_dash_is_not_zero_and_not_supported():
    s = structure(interim(), [TITLE, UNIT_M])
    ev = b.evaluate_cell(s, "o1", "profit_attributable_to_owners", True, SHA)
    assert obl(ev, "S2")["reason"] == "dash_printed_not_zero" and ev["tuple"]["amount"] is None


def test_unsupported_week_based_calendar_stays_unresolved():
    s = structure(interim("13 Weeks Ended September 28, 2025", "39 Weeks Ended September 28, 2025"), [TITLE, UNIT_M])
    r = resolve(s, T("revenue", 3, 2025))
    assert r["outcome"] == "unresolved"


def test_equally_specific_conflicting_scales_are_unresolved_not_tie_broken():
    s = structure(interim(), [TITLE, UNIT_M, b.Text("u2", "text", "(dollars in billions)", 1, 92, 96)])
    r = resolve(s, T("revenue", 3, 2025))
    assert r["outcome"] == "unresolved"
    assert obl(r["candidates"][0], "U2")["reason"] == "conflicting_scale_statements"


def test_two_rows_same_metric_different_values_is_ambiguous():
    cells = [c for c in interim() if c.r0 <= 2] + [cell("lr2", 3, 0, "Total operating revenues"), cell("x1", 3, 1, "11,000")]
    s = structure(cells, [TITLE, UNIT_M])
    r = resolve(s, T("revenue", 3, 2025))
    assert r["outcome"] == "unresolved" and r["reason"] == "ambiguous_context" and len(r["classes"]) == 2


def test_percent_change_column_is_not_money():
    cells = [cell("h", 0, 1, "Years Ended December 31,", c1=4, hdr=True), cell("y1", 1, 1, "2025", hdr=True),
             cell("y2", 1, 2, "2024", hdr=True), cell("pc", 1, 3, "% Change", hdr=True),
             cell("lr", 2, 0, "Total revenues"), cell("a", 2, 1, "5"), cell("b", 2, 2, "4"), cell("c", 2, 3, "25.0")]
    s = structure(cells, [TITLE, UNIT_M], ncols=4)
    assert obl(b.evaluate_cell(s, "c", "revenue", True, SHA), "U2")["reason"] == "percent_change_column_not_monetary"


def test_segment_statement_fails_scope():
    s = structure(interim(), [b.Text("st", "section_header", "Segment Statements of Operations", 1, 60, 70), UNIT_M])
    assert obl(b.evaluate_cell(s, "r1", "revenue", True, SHA), "M2")["status"] == "fail"


def test_source_hash_mismatch_fails_s1():
    s = structure(interim(), [TITLE, UNIT_M])
    assert obl(b.evaluate_cell(s, "r1", "revenue", False, SHA), "S1")["status"] == "fail"


# ---------------- metamorphic

def test_reordering_nodes_does_not_change_resolution():
    cells, texts = interim(), [TITLE, UNIT_M]
    base = resolve(structure(cells, texts), T("revenue", 9, 2025))["classes"][0]["tuple"]
    rnd = random.Random(7)
    for _ in range(5):
        c2, t2 = cells[:], texts[:]
        rnd.shuffle(c2); rnd.shuffle(t2)
        assert resolve(structure(c2, t2), T("revenue", 9, 2025))["classes"][0]["tuple"] == base


def test_consistent_id_renaming_preserves_semantics():
    cells = [b.Cell("Z" + c.id, c.table, c.r0, c.r1, c.c0, c.c1, c.text, c.column_header, c.row_header, c.row_section) for c in interim()]
    r = resolve(structure(cells, [TITLE, UNIT_M]), T("revenue", 3, 2025))
    assert r["classes"][0]["tuple"] == resolve(structure(interim(), [TITLE, UNIT_M]), T("revenue", 3, 2025))["classes"][0]["tuple"]
    assert r["classes"][0]["value_cells"] == ["Zr1"]


def test_changing_governing_duration_invalidates_old_reading():
    old = b.evaluate_cell(structure(interim(), [TITLE, UNIT_M]), "r1", "revenue", True, SHA)
    new = b.evaluate_cell(structure(interim(d3="Six Months Ended September 30,"), [TITLE, UNIT_M]), "r1", "revenue", True, SHA)
    assert old["tuple"]["duration_months"] == 3 and new["tuple"]["duration_months"] == 6
    v = {x["field"]: x["status"] for x in b.field_verdicts(claim("r1", "10000", 3, 2025, end="2025-09-30", period_ids=["h3", "y1"]), new)}
    assert v["duration_months"] == "fail"


def test_irrelevant_neighbor_text_does_not_change_binding():
    noise = [b.Text("n1", "text", "Fiscal 2019 amounts in thousands are shown in Note 7", 1, 500, 510)]  # BELOW the table
    a = resolve(structure(interim(), [TITLE, UNIT_M]), T("revenue", 3, 2025))["classes"][0]["tuple"]
    bb = resolve(structure(interim(), [TITLE, UNIT_M] + noise), T("revenue", 3, 2025))["classes"][0]["tuple"]
    assert a == bb


def test_section_heading_directly_above_first_data_row_is_applicable_scope():
    """Regression (found in exp-2026-11-16-a on the real AT&T/Verizon layouts): 'Operating Revenues' row_section heading
    sits just above the first data row; citing it as metric context must count as an applicable path (binding-v3)."""
    cells = [cell("h", 0, 1, "Years Ended December 31,", c1=3, hdr=True), cell("y1", 1, 1, "2025", hdr=True), cell("y2", 1, 2, "2024", hdr=True),
             cell("sec", 2, 0, "Operating Revenues", sec=True),
             cell("l1", 3, 0, "Service"), cell("a1", 3, 1, "4"), cell("b1", 3, 2, "3"),
             cell("lr", 4, 0, "Total Operating Revenues"), cell("a", 4, 1, "5"), cell("b", 4, 2, "4")]
    s = structure(cells, [TITLE, UNIT_M], ncols=3)
    ev = b.evaluate_cell(s, "a", "revenue", True, SHA)
    assert any(e["rel"] == "section_scope_for" and e["src"] == "sec" for e in ev["edges"])
    v = {x["field"]: x["status"] for x in b.field_verdicts(
        claim("a", "5", 12, 2025, end="2025-12-31", period_ids=["h", "y1"], metric_ids=("lr", "sec")), ev)}
    assert v["metric_evidence"] == "pass"
