"""Failure-boundary tests for deterministic period/unit/anchor checks (no providers involved)."""
from decimal import Decimal

from evi.checks import Ev, normalize, parse_amount, read_period, read_unit, run_checks

DOC, SHA = "doc-a", "a" * 64


def ev(eid, text, kind="table_cell", table=0, row=None, col=None, span=1, header=False, doc=DOC, sha=SHA):
    return Ev(eid, doc, sha, kind, 1, text, table, row, col, span, header)


def base_evidence(duration_heading="Years Ended December 31,"):
    return {e.evidence_id: e for e in [
        ev("unit", "(dollars in millions, except per share amounts)", kind="text", table=None),
        ev("head", duration_heading, row=0, col=1, span=2, header=True),
        ev("y25", "2025", row=1, col=1, header=True),
        ev("y24", "2024", row=1, col=2, header=True),
        ev("lbl", "Total Operating Revenues", row=2, col=0),
        ev("v25", "$ 138,186", row=2, col=1),
        ev("v24", "134,788", row=2, col=2),
        ev("eps", "Basic Earnings Per Common Share", row=3, col=0),
        ev("epsv", "4.12", row=3, col=1),
    ]}


def fact(**over):
    f = {"fact_id": "f1", "metric": "revenue", "reported_value": "138186", "currency": "USD", "unit_scale": "1000000",
         "period": {"start_date": "2025-01-01", "end_date": "2025-12-31", "duration_months": 12, "kind": "full_year", "label": "FY2025"},
         "evidence": {"value_ids": ["v25"], "metric_ids": ["lbl"], "period_ids": ["head", "y25"], "unit_ids": ["unit"]},
         "notes": []}
    f.update(over)
    return f


def status(results, t):
    return [c.status for c in results if c.check_type == t]


def test_correct_annual_fact_passes_and_normalizes_exactly():
    r = run_checks(fact(), base_evidence(), DOC, SHA, requested_period_months=12)
    assert all(c.status == "pass" for c in r), [(c.check_type, c.message) for c in r if c.status != "pass"]
    assert normalize("138186", "1000000") == "138186000000"


def test_nine_month_source_requested_as_annual_fails_and_correct_request_passes():
    e = base_evidence("Nine Months Ended September 30,")
    claimed_annual = fact(period={"start_date": None, "end_date": "2025-09-30", "duration_months": 12, "kind": "full_year", "label": "FY"})
    r = run_checks(claimed_annual, e, DOC, SHA, requested_period_months=12)
    assert status(r, "period") == ["fail"]
    assert status(r, "requested_period") == ["fail"]
    correct = fact(period={"start_date": "2025-01-01", "end_date": "2025-09-30", "duration_months": 9, "kind": "year_to_date", "label": "9M"})
    r2 = run_checks(correct, e, DOC, SHA, requested_period_months=9)
    assert status(r2, "period") == ["pass"] and status(r2, "requested_period") == ["pass"]


def test_three_and_nine_month_columns_sharing_end_date_stay_distinct():
    e = base_evidence()
    e["q"] = ev("q", "Three Months Ended September 30,", row=0, col=1, header=True)
    e["ytd"] = ev("ytd", "Nine Months Ended September 30,", row=0, col=2, header=True)
    f = fact(evidence={"value_ids": ["v25"], "metric_ids": ["lbl"], "period_ids": ["q", "ytd", "y25"], "unit_ids": ["unit"]},
             period={"start_date": None, "end_date": "2025-09-30", "duration_months": 9, "kind": "year_to_date", "label": "9M"})
    r = run_checks(f, e, DOC, SHA)
    assert status(r, "period") == ["fail"]          # two durations cited -> conflict, not a silent pick
    assert status(r, "period_column") == ["fail"]   # the nine-month header does not span column 1


def test_comparative_year_column_is_not_accepted_for_current_year():
    f = fact(evidence={"value_ids": ["v24"], "metric_ids": ["lbl"], "period_ids": ["head", "y25"], "unit_ids": ["unit"]},
             reported_value="134788")
    r = run_checks(f, base_evidence(), DOC, SHA)
    assert status(r, "period_column") == ["fail"]


def test_year_not_inferred_without_period_evidence():
    f = fact(evidence={"value_ids": ["v25"], "metric_ids": ["lbl"], "period_ids": ["head"], "unit_ids": ["unit"]})
    r = run_checks(f, base_evidence(), DOC, SHA)
    assert status(r, "period") == ["unknown"]


def test_missing_scale_is_unknown_and_wrong_scale_fails():
    e = base_evidence()
    e["cur"] = ev("cur", "Amounts in U.S. dollars", kind="text", table=None)
    r = run_checks(fact(evidence={**fact()["evidence"], "unit_ids": ["cur"]}), e, DOC, SHA)
    assert status(r, "unit") == ["unknown"] and status(r, "normalization") == ["unknown"]
    r2 = run_checks(fact(unit_scale="1000000000"), base_evidence(), DOC, SHA)
    assert status(r2, "unit") == ["fail"]


def test_billions_and_conflicting_scale():
    assert read_unit(["(dollars in billions)"]).scale == Decimal(10) ** 9
    assert read_unit(["in millions", "in thousands"]).conflicts


def test_per_share_row_is_rejected():
    f = fact(metric="profit_attributable_to_owners", reported_value="4.12",
             evidence={"value_ids": ["epsv"], "metric_ids": ["eps"], "period_ids": ["head", "y25"], "unit_ids": ["unit"]})
    r = run_checks(f, base_evidence(), DOC, SHA)
    assert "fail" in status(r, "metric_scope") and status(r, "unit") == ["fail"]


def test_noncontrolling_scope_rejected():
    e = base_evidence()
    e["nci"] = ev("nci", "Net income attributable to noncontrolling interests", row=2, col=0)
    f = fact(metric="profit_attributable_to_owners",
             evidence={"value_ids": ["v25"], "metric_ids": ["nci"], "period_ids": ["head", "y25"], "unit_ids": ["unit"]})
    assert status(run_checks(f, e, DOC, SHA), "metric_scope") == ["fail"]


def test_large_and_negative_amounts_keep_precision():
    assert parse_amount("(12,345,678,901,234.56)").value == Decimal("-12345678901234.56")
    assert normalize("-12345678901234.56", "1000000") == "-12345678901234560000"


def test_missing_zero_dash_are_distinct():
    assert parse_amount("").kind == "empty"
    assert parse_amount("—").kind == "dash"
    assert parse_amount("0").kind == "number" and parse_amount("0").value == 0
    assert parse_amount("1,234(a)").kind == "invalid"


def test_unresolved_fact_is_unknown_not_pass():
    f = fact(reported_value=None, evidence={"value_ids": [], "metric_ids": [], "period_ids": [], "unit_ids": []}, notes=["absent"])
    r = run_checks(f, base_evidence(), DOC, SHA)
    assert r and all(c.status == "unknown" for c in r)


def test_foreign_and_hash_mismatched_anchors_rejected():
    e = base_evidence()
    e["other"] = ev("other", "138,186", doc="doc-b", row=2, col=1)
    e["badsha"] = ev("badsha", "138,186", sha="b" * 64, row=2, col=1)
    for bad in ("other", "badsha", "invented-id"):
        f = fact(evidence={**fact()["evidence"], "value_ids": [bad]})
        assert status(run_checks(f, e, DOC, SHA), "evidence_anchor") == ["fail"]


def test_value_mismatch_fails():
    assert status(run_checks(fact(reported_value="138187"), base_evidence(), DOC, SHA), "value_cell") == ["fail"]


def test_fiscal_year_end_read_from_heading_only():
    r = read_period(["Fiscal Years Ended June 30,", "2025"])
    assert (r.duration_months, r.end_month, r.end_day, r.year) == (12, 6, 30, 2025)


def real_layout():
    """Cell layout observed in the real Docling parse of Verizon FY2025 p.52 (parse_1adbf9bc185db4c476c1)."""
    return {e.evidence_id: e for e in [
        ev("unit", "(dollars in millions, except per share amounts)", row=0, col=1, span=3, header=True),
        ev("yrs", "Years Ended December 31,", row=1, col=0),
        ev("y25", "2025", row=1, col=1, header=True),
        ev("lbl", "Total Operating Revenues", row=5, col=0),
        ev("v25", "138,191", row=5, col=1),
        ev("sec", "Basic Earnings Per Common Share", row=30, col=0),
        ev("own", "Net income attributable to Verizon", row=31, col=0),
        ev("eps", "$ 4.06", row=31, col=1),
    ]}


def test_real_layout_row_header_period_and_unit_note_pass():
    f = fact(reported_value="138191", evidence={"value_ids": ["v25"], "metric_ids": ["lbl"], "period_ids": ["yrs", "y25"], "unit_ids": ["unit"]})
    r = run_checks(f, real_layout(), DOC, SHA, 12)
    assert all(c.status == "pass" for c in r), [(c.check_type, c.message) for c in r if c.status != "pass"]


def test_real_layout_eps_row_under_per_share_heading_is_rejected():
    f = fact(metric="profit_attributable_to_owners", reported_value="4.06",
             evidence={"value_ids": ["eps"], "metric_ids": ["own"], "period_ids": ["yrs", "y25"], "unit_ids": ["unit"]})
    assert status(run_checks(f, real_layout(), DOC, SHA, 12), "unit") == ["fail"]


def test_fact_omitting_stated_end_date_is_unknown_not_pass():
    f = fact(period={"start_date": None, "end_date": None, "duration_months": 12, "kind": "full_year", "label": "FY2025"})
    assert status(run_checks(f, base_evidence(), DOC, SHA), "period") == ["unknown"]
