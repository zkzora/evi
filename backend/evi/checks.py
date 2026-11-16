"""Deterministic period / unit / scope / anchoring checks.

The model interprets context; this module decides whether that interpretation is supported by the
registered evidence. Missing context is `unknown`, contradictory context is `fail`; neither is a pass.
"""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

MONTH_NAMES = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
DURATION_WORDS = {"three": 3, "six": 6, "nine": 9, "twelve": 12, "3": 3, "6": 6, "9": 9, "12": 12}
SCALES = {"thousand": Decimal(1000), "thousands": Decimal(1000), "million": Decimal(10) ** 6,
          "millions": Decimal(10) ** 6, "billion": Decimal(10) ** 9, "billions": Decimal(10) ** 9}
DASHES = {"-", "—", "–", "‒", "―"}

METRIC_RULES: dict[str, dict[str, Any]] = {
    "revenue": {"require_any": [r"\b(total\s+)?operating\s+revenues?\b", r"\btotal\s+revenues?\b", r"^\s*revenues?\b"],
                "reject": [r"segment", r"\bper\s+(common\s+)?share\b", r"ebitda", r"cost\s+of"]},
    "operating_profit": {"require_any": [r"\boperating\s+income\b", r"\boperating\s+profit\b", r"\bincome\s+from\s+operations\b"],
                         "reject": [r"ebitda", r"\bper\s+(common\s+)?share\b", r"\bnon-?operating\b", r"before"]},
    "profit_attributable_to_owners": {
        "require_any": [r"attributable\s+to\s+(verizon|common|owners|the\s+parent|stockholders|shareholders|\w+\s+(inc|corporation))",
                        r"\bnet\s+income\s+attributable\s+to\s+(?!noncontrolling)"],
        "reject": [r"noncontrolling", r"non-controlling", r"\bper\s+(common\s+)?share\b", r"comprehensive"]},
}


@dataclass
class Ev:
    """The subset of an evidence record the checks depend on."""
    evidence_id: str
    document_id: str
    document_sha256: str
    kind: str
    page_number: int
    text: str
    table_index: int | None = None
    row_index: int | None = None
    col_index: int | None = None
    col_span: int | None = 1
    is_column_header: bool = False


@dataclass
class CheckResult:
    check_type: str
    status: str  # pass | fail | unknown | not_applicable
    message: str
    evidence_ids: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- numbers

@dataclass
class ParsedAmount:
    kind: str  # number | dash | empty | invalid
    value: Decimal | None = None
    note: str = ""


def parse_amount(text: str) -> ParsedAmount:
    """Explicit en-US locale: comma thousands separators, dot decimals, parentheses negative."""
    t = (text or "").strip().replace(" ", " ")
    if not t:
        return ParsedAmount("empty", note="Cell is empty.")
    t = t.replace("$", "").replace(" ", "")
    if t in DASHES:
        return ParsedAmount("dash", note="A dash is printed; it is not a numeric zero or a missing cell.")
    negative = t.startswith("(") and t.endswith(")")
    if negative:
        t = t[1:-1]
    if t.startswith("-") or t.startswith("−"):
        negative, t = True, t[1:]
    if not re.fullmatch(r"\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?", t):
        return ParsedAmount("invalid", note=f"'{text}' is not an en-US formatted amount (footnote or mixed text?).")
    try:
        value = Decimal(t.replace(",", ""))
    except InvalidOperation:
        return ParsedAmount("invalid", note=f"'{text}' could not be read as a decimal.")
    return ParsedAmount("number", -value if negative else value)


# ---------------------------------------------------------------- period

@dataclass
class PeriodReading:
    duration_months: int | None = None
    end_month: int | None = None
    end_day: int | None = None
    year: int | None = None
    kind: str | None = None  # duration | instant
    conflicts: list[str] = field(default_factory=list)


def read_period(texts: Iterable[str]) -> PeriodReading:
    r = PeriodReading()
    durations: set[int] = set()
    years: set[int] = set()
    for raw in texts:
        t = raw.lower()
        for m in re.finditer(r"\b(three|six|nine|twelve|3|6|9|12)[\s-]+months?\s+ended\b", t):
            durations.add(DURATION_WORDS[m.group(1)])
        if re.search(r"\b(fiscal\s+)?years?\s+ended\b|\bannual\b|\bfull[\s-]year\b", t):
            durations.add(12)
        if re.search(r"\bquarter\s+ended\b", t):
            durations.add(3)
        if re.search(r"\b(as\s+of|as\s+at|at)\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b", t):
            r.kind = r.kind or "instant"
        md = re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})\b", t)
        if md:
            r.end_month, r.end_day = MONTH_NAMES[md.group(1)], int(md.group(2))
        for y in re.findall(r"\b((?:19|20)\d{2})\b", t):
            years.add(int(y))
    if len(durations) > 1:
        r.conflicts.append(f"More than one duration is stated in the cited headings: {sorted(durations)} months.")
    if len(durations) == 1:
        r.duration_months = durations.pop()
        r.kind = "duration"
    if len(years) > 1:
        r.conflicts.append(f"More than one year is present in the cited period evidence: {sorted(years)}.")
    elif years:
        r.year = years.pop()
    return r


def end_date(r: PeriodReading) -> str | None:
    if r.year and r.end_month and r.end_day:
        return f"{r.year:04d}-{r.end_month:02d}-{r.end_day:02d}"
    return None


def start_date(end: str, months: int) -> str:
    y, m, d = (int(x) for x in end.split("-"))
    last_day_end = calendar.monthrange(y, m)[1] == d
    m0 = m - months + 1
    y0 = y
    while m0 <= 0:
        m0 += 12
        y0 -= 1
    if last_day_end:
        return f"{y0:04d}-{m0:02d}-01"
    # Non month-end interval (e.g. 52/53-week years) is not inferred.
    raise ValueError("Start date is only derived for month-end interval ends.")


# ---------------------------------------------------------------- unit

@dataclass
class UnitReading:
    currency: str | None = None
    scale: Decimal | None = None
    per_share_excepted: bool = False
    conflicts: list[str] = field(default_factory=list)


def read_unit(texts: Iterable[str]) -> UnitReading:
    u = UnitReading()
    scales: set[Decimal] = set()
    for raw in texts:
        t = raw.lower()
        for m in re.finditer(r"(?:dollars|\$|usd|u\.s\.\s*dollars)?\s*in\s+(thousands|millions|billions)", t):
            scales.add(SCALES[m.group(1)])
        if re.search(r"\bdollars\b|\$|\busd\b", t):
            u.currency = "USD"
        if re.search(r"\b(rupiah|idr|euro|eur|€|£|gbp)\b", t):
            u.conflicts.append("A non-USD currency is stated in the cited unit evidence.")
        if re.search(r"except\s+per\s+share", t):
            u.per_share_excepted = True
    if len(scales) > 1:
        u.conflicts.append("More than one monetary scale is stated in the cited unit evidence.")
    elif scales:
        u.scale = scales.pop()
    return u


# ---------------------------------------------------------------- fact-level checks

def run_checks(fact: dict, evidence: dict[str, Ev], document_id: str, document_sha256: str,
               requested_period_months: int | None = None) -> list[CheckResult]:
    """`fact` is the internal fact dict (see extraction.py). `evidence` maps every evidence ID of the parse."""
    out: list[CheckResult] = []
    groups = fact["evidence"]
    all_ids = [i for g in ("value_ids", "metric_ids", "period_ids", "unit_ids") for i in groups[g]]

    # 1. Source hash and evidence ownership
    bad = [i for i in all_ids if i not in evidence or evidence[i].document_id != document_id
           or evidence[i].document_sha256 != document_sha256]
    if fact.get("reported_value") is None and not all_ids:
        out.append(CheckResult("evidence_anchor", "unknown", "No evidence was cited; the target is unresolved."))
        return out + _unresolved_tail(fact)
    if bad:
        out.append(CheckResult("evidence_anchor", "fail",
                               "Cited evidence is missing, belongs to another document, or has a different source hash.", bad))
        return out
    out.append(CheckResult("evidence_anchor", "pass", "Every cited evidence ID belongs to this source and hash.", all_ids))

    value_ev = [evidence[i] for i in groups["value_ids"]]
    metric_ev = [evidence[i] for i in groups["metric_ids"]]
    period_ev = [evidence[i] for i in groups["period_ids"]]
    unit_ev = [evidence[i] for i in groups["unit_ids"]]

    # 2. Value cell
    value_cell = value_ev[0] if len(value_ev) == 1 and value_ev[0].kind == "table_cell" else None
    if not value_cell:
        out.append(CheckResult("value_cell", "fail" if value_ev else "unknown",
                               "Exactly one table value cell must be cited for the amount.", groups["value_ids"]))
        parsed = None
    else:
        parsed = parse_amount(value_cell.text)
        if parsed.kind != "number":
            out.append(CheckResult("value_cell", "fail" if parsed.kind == "invalid" else "unknown", parsed.note, [value_cell.evidence_id]))
        elif fact.get("reported_value") is None or Decimal(fact["reported_value"]) != parsed.value:
            out.append(CheckResult("value_cell", "fail",
                                   f"The cited cell reads {value_cell.text!r}, which does not equal the extracted amount.",
                                   [value_cell.evidence_id]))
        else:
            out.append(CheckResult("value_cell", "pass", f"The cited cell prints {value_cell.text!r}.", [value_cell.evidence_id]))

    # 3. Metric row and scope
    rules = METRIC_RULES[fact["metric"]]
    if not metric_ev:
        out.append(CheckResult("metric_row", "unknown", "No metric label evidence was cited."))
    else:
        label = " ".join(e.text for e in metric_ev).lower()
        same_row = value_cell is not None and all(
            e.table_index == value_cell.table_index and e.row_index == value_cell.row_index for e in metric_ev)
        if any(re.search(p, label) for p in rules["reject"]):
            out.append(CheckResult("metric_scope", "fail",
                                   f"The cited row label '{label}' is outside the requested metric scope.", groups["metric_ids"]))
        elif not any(re.search(p, label) for p in rules["require_any"]):
            out.append(CheckResult("metric_scope", "unknown",
                                   f"The cited row label '{label}' does not clearly name the requested metric.", groups["metric_ids"]))
        else:
            out.append(CheckResult("metric_scope", "pass", f"Row label '{label}' matches the requested metric scope.", groups["metric_ids"]))
        if value_cell is not None:
            out.append(CheckResult("metric_row", "pass" if same_row else "fail",
                                   "The metric label is on the same table row as the value." if same_row
                                   else "The metric label is not on the value cell's table row.", groups["metric_ids"]))

    # 4. Reporting interval
    if not period_ev:
        out.append(CheckResult("period", "unknown", "No period evidence was cited; the interval is unsupported."))
    else:
        if value_cell is not None:
            col_headers = [e for e in period_ev if e.kind == "table_cell" and e.is_column_header]
            off_column = [e.evidence_id for e in col_headers if e.table_index == value_cell.table_index and not
                          _covers_column(e, value_cell.col_index)]
            if off_column:
                out.append(CheckResult("period_column", "fail",
                                       "A cited period header does not span the value cell's column.", off_column))
        reading = read_period(e.text for e in period_ev)
        p = fact["period"]
        ids = groups["period_ids"]
        if reading.conflicts:
            out.append(CheckResult("period", "fail", " ".join(reading.conflicts), ids))
        elif reading.duration_months is None or reading.year is None:
            out.append(CheckResult("period", "unknown",
                                   "The cited evidence does not state both the interval length and the year.", ids))
        elif p.get("duration_months") != reading.duration_months:
            out.append(CheckResult("period", "fail",
                                   f"The source states a {reading.duration_months}-month interval but the fact claims "
                                   f"{p.get('duration_months')} months.", ids))
        elif end_date(reading) and not p.get("end_date"):
            out.append(CheckResult("period", "unknown",
                                   f"The source states an interval ending {end_date(reading)}, but the fact omits its end date.", ids))
        elif end_date(reading) and p["end_date"] != end_date(reading):
            out.append(CheckResult("period", "fail",
                                   f"The source interval ends {end_date(reading)} but the fact claims {p['end_date']}.", ids))
        elif not end_date(reading):
            out.append(CheckResult("period", "unknown", "The interval end month/day is not stated in the cited evidence.", ids))
        else:
            out.append(CheckResult("period", "pass",
                                   f"{reading.duration_months}-month interval ending {end_date(reading)} is stated in the cited headings.", ids))
        if requested_period_months is not None:
            ok = reading.duration_months == requested_period_months
            out.append(CheckResult("requested_period", "pass" if ok else ("unknown" if reading.duration_months is None else "fail"),
                                   f"Requested a {requested_period_months}-month interval; source states "
                                   f"{reading.duration_months or 'no'}-month.", ids))

    # 5. Currency and scale
    if not unit_ev:
        out.append(CheckResult("unit", "unknown", "No currency/unit evidence was cited; scale is unsupported."))
    else:
        u = read_unit(e.text for e in unit_ev)
        ids = groups["unit_ids"]
        claimed = Decimal(fact["unit_scale"]) if fact.get("unit_scale") else None
        metric_label = " ".join(e.text for e in metric_ev).lower()
        if u.conflicts:
            out.append(CheckResult("unit", "fail", " ".join(u.conflicts), ids))
        elif u.scale is None or u.currency is None:
            out.append(CheckResult("unit", "unknown", "The cited evidence does not state both currency and scale.", ids))
        elif u.per_share_excepted and (PER_SHARE.search(metric_label) or _in_per_share_section(value_cell, evidence)):
            out.append(CheckResult("unit", "fail", "Per-share amounts are excepted from the statement scale.", ids))
        elif fact.get("currency") != u.currency or claimed != u.scale:
            out.append(CheckResult("unit", "fail",
                                   f"The source states {u.currency} with scale {u.scale:,}; the fact claims "
                                   f"{fact.get('currency')} with scale {fact.get('unit_scale')}.", ids))
        else:
            out.append(CheckResult("unit", "pass", f"{u.currency} in units of {u.scale:,} is stated in the cited unit note.", ids))

    # 6. Normalization (application arithmetic only)
    passes = {c.check_type for c in out if c.status == "pass"}
    if {"value_cell", "unit"} <= passes:
        out.append(CheckResult("normalization", "pass",
                               f"{fact['reported_value']} × {Decimal(fact['unit_scale']):,} = {normalize(fact['reported_value'], fact['unit_scale'])}.",
                               groups["value_ids"] + groups["unit_ids"]))
    else:
        out.append(CheckResult("normalization", "unknown", "Normalization is withheld until the value and unit checks pass."))
    return out


PER_SHARE = re.compile(r"\bper\s+(common\s+)?share\b|\bweighted[\s-]+average\s+shares\b", re.I)


def _in_per_share_section(value_cell: Ev | None, evidence: dict[str, Ev]) -> bool:
    """A row labelled e.g. 'Net income attributable to X' under a 'Basic Earnings Per Common Share' heading
    is a per-share amount even though its own label does not say so."""
    if value_cell is None or value_cell.row_index is None:
        return False
    return any(e.table_index == value_cell.table_index and e.row_index is not None and e.row_index < value_cell.row_index
               and e.col_index == 0 and not re.search(r"except", e.text, re.I) and PER_SHARE.search(e.text)
               for e in evidence.values())


def _covers_column(header: Ev, col: int | None) -> bool:
    if col is None or header.col_index is None:
        return False
    return header.col_index <= col < header.col_index + (header.col_span or 1)


def _unresolved_tail(fact: dict) -> list[CheckResult]:
    reason = "; ".join(fact.get("notes") or []) or "No reason supplied."
    return [CheckResult("resolution", "unknown", f"Unresolved target: {reason}")]


def normalize(reported_value: str, unit_scale: str) -> str:
    v = Decimal(reported_value) * Decimal(unit_scale)
    return format(v.quantize(Decimal(1)) if v == v.to_integral_value() else v.normalize(), "f")
