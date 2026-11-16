"""Source-applicability binding, field obligations, resolution and support certificates (docs/19).

The model may *propose* a value cell and evidence; this module decides, from the parsed table structure and
explicit source language, which row label, column headers, duration heading, unit statement and statement scope
actually APPLY to that value cell. A valid evidence ID that does not apply to the value is not support.

Everything here is deterministic and re-executable by `verify_certificate`, which recomputes a certificate from the
registered source bytes + Docling artifact and compares it with the stored one.
"""
from __future__ import annotations

import calendar
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from . import db
from .checks import PER_SHARE, parse_amount
from .corpus import sha256_file, source_path

SUPPORTED_POLICIES = ("binding-v1", "binding-v2", "binding-v3")
POLICY_VERSION = "binding-v3"  # v2: start_date application-derived. v3: section scope reaches the row_section heading above the first data row
OBLIGATIONS = ["S1", "S2", "M1", "M2", "P1", "P2", "P3", "U1", "U2", "N1", "N2", "C1"]
# Obligations that must PASS for a supported fact. P3 (exact dates) is required only when the source states an end
# date for the column; otherwise it is `unknown` with reason end_date_not_stated and the fact carries null dates.
REQUIRED = ["S1", "S2", "M1", "M2", "P1", "P2", "U1", "U2", "N1", "N2", "C1"]
MAX_CANDIDATES = 12

MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})
WORD_MONTHS = {"three": 3, "six": 6, "nine": 9, "twelve": 12, "3": 3, "6": 6, "9": 9, "12": 12}
QUARTER = re.compile(r"\b(first|second|third|fourth)\s+quarter\b", re.I)
DUR_MONTHS = re.compile(r"\b(three|six|nine|twelve|3|6|9|12)[\s-]*(?:months?|mos\.?)(?:\s+(?:ended|period))?\b", re.I)
DUR_PERIOD = re.compile(r"\b(three|six|nine|twelve)-month\s+period\b", re.I)
DUR_YEAR = re.compile(r"\b(?:fiscal\s+)?years?\s+ended\b", re.I)
WEEKS = re.compile(r"\bweeks?\b", re.I)
NUM_DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})\b")
NAMED_DATE = re.compile(r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\.?\s+(\d{1,2})\b", re.I)
YEAR = re.compile(r"\b((?:19|20)\d{2})\b")
UNIT = re.compile(r"\b(?:(dollars|usd)\s+)?in\s+(thousands|millions|billions)\b", re.I)
SCALES = {"thousands": Decimal(1000), "millions": Decimal(10) ** 6, "billions": Decimal(10) ** 9}
PERCENT_COL = re.compile(r"percent|%|\bchange\b", re.I)
STATEMENT_TITLE = re.compile(r"statements?\s+of\s+(?:consolidated\s+)?(?:comprehensive\s+)?(income|operations|earnings)", re.I)

METRIC_ROWS = {
    "revenue": re.compile(r"^total\s+(?:operating\s+)?revenues?$", re.I),
    "operating_profit": re.compile(r"^(?:operating\s+income(?:\s+\(loss\))?|operating\s+profit|income\s+from\s+operations)$", re.I),
    # Policy: owners of the parent = the line attributable to the parent company, BEFORE preferred dividends.
    # 'Attributable to common stock/shareholders' and 'noncontrolling' are different scopes.
    "profit_attributable_to_owners": re.compile(
        r"^net\s+income(?:\s+\(loss\))?\s+attributable\s+to\s+(?!non-?controlling|common|preferred)[\w&.,\- ]+$", re.I),
}


def clean(text: str) -> str:
    return re.sub(r"\(\d\)$", "", re.sub(r"\s+", " ", text or "")).strip()


# ---------------------------------------------------------------- structure

@dataclass
class Cell:
    id: str
    table: int
    r0: int
    r1: int
    c0: int
    c1: int
    text: str
    column_header: bool
    row_header: bool
    row_section: bool

    def covers_col(self, c: int) -> bool:
        return self.c0 <= c < self.c1


@dataclass
class Text:
    id: str
    label: str
    text: str
    page: int
    top: float      # TOPLEFT page coordinates
    bottom: float


@dataclass
class Table:
    index: int
    page: int
    nrows: int
    ncols: int
    top: float      # TOPLEFT
    bottom: float
    cells: list[Cell]

    def row(self, r: int) -> list[Cell]:
        return sorted((c for c in self.cells if c.r0 == r), key=lambda c: c.c0)


@dataclass
class Structure:
    document_id: str
    source_sha256: str
    parse_id: str
    parse_cache_key: str
    artifact_sha256: str
    pages: dict[int, dict]
    tables: list[Table]
    texts: list[Text]
    cell_by_id: dict[str, Cell] = field(default_factory=dict)
    text_by_id: dict[str, Text] = field(default_factory=dict)


def _ev_id(key: str, *parts: Any) -> str:  # same derivation as parsing._evidence_id
    return "ev_" + hashlib.sha256((key + "|" + "|".join(map(str, parts))).encode()).hexdigest()[:20]


def load_structure(conn: sqlite3.Connection, parse_id: str) -> Structure:
    p = db.row(conn, "SELECT * FROM parses WHERE parse_id=?", parse_id)
    if p is None:
        raise KeyError(parse_id)
    art = Path(p["artifact_path"])
    raw = art.read_bytes()
    d = json.loads(raw)
    pages = {int(k): {"width": v["size"]["width"], "height": v["size"]["height"]} for k, v in d["pages"].items()}
    tables: list[Table] = []
    for ti, t in enumerate(d["tables"]):
        if not t.get("prov"):
            continue
        pv = t["prov"][0]
        h = pages[pv["page_no"]]["height"]
        top, bottom = _tl(pv["bbox"], h)
        cells = [Cell(_ev_id(p["cache_key"], "cell", ti, c["start_row_offset_idx"], c["start_col_offset_idx"]), ti,
                      c["start_row_offset_idx"], c["end_row_offset_idx"], c["start_col_offset_idx"], c["end_col_offset_idx"],
                      clean(c["text"]), bool(c.get("column_header")), bool(c.get("row_header")), bool(c.get("row_section")))
                 for c in t["data"]["table_cells"]]
        tables.append(Table(ti, pv["page_no"], t["data"]["num_rows"], t["data"]["num_cols"], top, bottom, cells))
    texts = []
    for xi, x in enumerate(d["texts"]):
        if not x.get("prov") or not (x.get("text") or "").strip():
            continue
        pv = x["prov"][0]
        top, bottom = _tl(pv["bbox"], pages[pv["page_no"]]["height"])
        texts.append(Text(_ev_id(p["cache_key"], "text", xi), x.get("label", ""), clean(x["text"]), pv["page_no"], top, bottom))
    s = Structure(p["document_id"], p["document_sha256"], parse_id, p["cache_key"], hashlib.sha256(raw).hexdigest(),
                  pages, tables, texts)
    s.cell_by_id = {c.id: c for t in tables for c in t.cells}
    s.text_by_id = {x.id: x for x in texts}
    return s


def _tl(b: dict, page_h: float) -> tuple[float, float]:
    if "BOTTOM" in str(b.get("coord_origin", "")).upper():
        return page_h - b["t"], page_h - b["b"]
    return b["t"], b["b"]


# ---------------------------------------------------------------- relations

@dataclass
class Edge:
    rel: str
    src: str          # node id (evidence id)
    dst: str          # value cell id
    rule: str
    note: str = ""

    def as_dict(self) -> dict:
        return {"rel": self.rel, "src": self.src, "dst": self.dst, "rule": self.rule, "note": self.note}


def first_data_row(t: Table) -> int:
    for r in range(t.nrows):
        if any(c.c0 > 0 and parse_amount(c.text).kind == "number" and not c.column_header and not YEAR.fullmatch(c.text)
               for c in t.row(r)):
            return r
    return t.nrows


def header_cells(t: Table) -> list[Cell]:
    fdr = first_data_row(t)
    return [c for c in t.cells if c.r0 < fdr]


def row_label(t: Table, r: int) -> Cell | None:
    cells = [c for c in t.row(r) if c.c0 == 0 and c.text]
    return cells[0] if cells else None


def section_label(t: Table, r: int, policy: str = POLICY_VERSION) -> Cell | None:
    """Nearest preceding label-only row inside the data region (e.g. 'Operating Revenues', 'Basic Earnings Per
    Common Share'). Multi-line labels that wrap onto a value row are not section rows."""
    fdr = first_data_row(t)
    if policy in ("binding-v1", "binding-v2"):   # historical rule: search only inside the data region
        for rr in range(r - 1, fdr - 1, -1):
            cells = [c for c in t.row(rr) if c.text]
            if cells and all(c.c0 == 0 for c in cells):
                return cells[0]
        return None
    for rr in range(r - 1, -1, -1):
        cells = [c for c in t.row(rr) if c.text]
        if any(c.column_header for c in cells):
            return None                       # reached the column-header block
        if cells and all(c.c0 == 0 for c in cells) and (rr >= fdr or cells[0].row_section):
            return cells[0]
    return None


@dataclass
class PeriodRead:
    duration: int | None = None
    duration_ids: list[str] = field(default_factory=list)
    duration_rule: str = ""
    year: int | None = None
    year_ids: list[str] = field(default_factory=list)
    end: str | None = None
    end_ids: list[str] = field(default_factory=list)
    weeks: bool = False
    conflicts: list[str] = field(default_factory=list)


def _durations(text: str) -> set[int]:
    out = set()
    for m in DUR_MONTHS.finditer(text):
        out.add(WORD_MONTHS[m.group(1).lower()])
    for m in DUR_PERIOD.finditer(text):
        out.add(WORD_MONTHS[m.group(1).lower()])
    if DUR_YEAR.search(text):
        out.add(12)
    if QUARTER.search(text):
        out.add(3)
    return out


def _dates(text: str) -> list[tuple[int, int, int | None]]:
    out = [(int(m.group(1)), int(m.group(2)), int(m.group(3)) % 100 + 2000 if len(m.group(3)) == 2 else int(m.group(3)))
           for m in NUM_DATE.finditer(text)]
    if not out:
        out = [(MONTHS[m.group(1).lower().rstrip(".")], int(m.group(2)), None) for m in NAMED_DATE.finditer(text)]
    return out


def read_column_period(t: Table, col: int, edges: list[Edge], value_id: str) -> PeriodRead:
    """Most specific applicable header wins: headers whose span covers `col` (smallest span first); a duration stated
    in a header-row label cell (column 0) applies table-wide only when no covering header states a duration."""
    pr = PeriodRead()
    covering = sorted((c for c in header_cells(t) if c.covers_col(col) and c.c0 > 0 or (c.c0 == 0 and c.c1 > col and c.c1 - c.c0 > 1)),
                      key=lambda c: (c.c1 - c.c0, -c.r0))
    covering = [c for c in covering if c.text]
    for c in covering:
        edges.append(Edge("column_header_for", c.id, value_id, "R-HDR-SPAN", f"span [{c.c0},{c.c1}) covers column {col}"))
    # duration: the most specific (smallest-span) covering header that states a duration
    with_dur = [(c.c1 - c.c0, c, _durations(c.text)) for c in covering if _durations(c.text)]
    for c in covering:
        if WEEKS.search(c.text):
            pr.weeks = True
    if with_dur:
        span = min(w[0] for w in with_dur)
        tight = [w for w in with_dur if w[0] == span]
        stated = set().union(*(w[2] for w in tight))
        if len(stated) > 1:
            pr.conflicts.append(f"Equally specific headers covering column {col} state more than one duration: {sorted(stated)} months.")
        else:
            pr.duration, pr.duration_rule = stated.pop(), "R-DUR-COLUMN"
            for _, c, _ in tight:
                pr.duration_ids.append(c.id)
                edges.append(Edge("duration_heading_for", c.id, value_id, "R-DUR-COLUMN", c.text))
    if pr.duration is None:
        table_wide = [c for c in header_cells(t) if c.c0 == 0 and c.c1 == 1 and _durations(c.text)]
        if len(table_wide) == 1:
            ds = _durations(table_wide[0].text)
            if len(ds) == 1:
                pr.duration, pr.duration_rule = next(iter(ds)), "R-DUR-TABLE-ROWLABEL"
                pr.duration_ids.append(table_wide[0].id)
                edges.append(Edge("duration_heading_for", table_wide[0].id, value_id, "R-DUR-TABLE-ROWLABEL",
                                  f"header-row label states the table interval: {table_wide[0].text}"))
                if WEEKS.search(table_wide[0].text):
                    pr.weeks = True
        elif len(table_wide) > 1:
            pr.conflicts.append("More than one header-row label states a table-wide duration.")
    # year: the most specific covering header that names exactly one year (4-digit year or m/d/yy date)
    for c in covering:
        yrs = {int(y) for y in YEAR.findall(c.text)} | {d[2] for d in _dates(c.text) if d[2]}
        if len(yrs) == 1:
            pr.year = yrs.pop()
            pr.year_ids.append(c.id)
            edges.append(Edge("year_header_for", c.id, value_id, "R-YEAR-SPECIFIC", c.text))
            break
        if len(yrs) > 1:
            continue  # a parent header naming several years is disambiguated by its child
    # end date: an explicit date in an applicable duration heading or year header
    for cid in pr.duration_ids + pr.year_ids:
        c = next(x for x in t.cells if x.id == cid)
        for m, dday, yy in _dates(c.text):
            y = yy or pr.year
            if y is None:
                continue
            try:
                end = f"{y:04d}-{m:02d}-{dday:02d}"
                calendar.monthrange(y, m)
                if dday > calendar.monthrange(y, m)[1]:
                    raise ValueError
            except ValueError:
                pr.conflicts.append(f"Invalid calendar date in '{c.text}'.")
                continue
            if pr.end and pr.end != end:
                pr.conflicts.append(f"Applicable headings state different end dates ({pr.end}, {end}).")
            pr.end = end
            if c.id not in pr.end_ids:
                pr.end_ids.append(c.id)
    if pr.year and pr.end and int(pr.end[:4]) != pr.year:
        pr.conflicts.append(f"Year header {pr.year} disagrees with the stated end date {pr.end}.")
    return pr


def derive_start(end: str, months: int, weeks: bool) -> tuple[str | None, str]:
    """R-CAL-MONTHEND: a stated N-month interval ending on the last day of a month starts on the first day of the
    month N-1 months earlier. Not applied to week-based (52/53-week) language or non-month-end dates."""
    if weeks:
        return None, "week_based_calendar_not_supported"
    y, m, d = (int(x) for x in end.split("-"))
    if calendar.monthrange(y, m)[1] != d:
        return None, "end_not_month_end"
    m0, y0 = m - months + 1, y
    while m0 <= 0:
        m0 += 12
        y0 -= 1
    return f"{y0:04d}-{m0:02d}-01", "R-CAL-MONTHEND"


@dataclass
class UnitRead:
    currency: str | None = None
    scale: Decimal | None = None
    ids: list[str] = field(default_factory=list)
    rule: str = ""
    per_share_exception: bool = False
    conflicts: list[str] = field(default_factory=list)


def read_unit(s: Structure, t: Table, col: int, edges: list[Edge], value_id: str) -> UnitRead:
    """Specificity order: (1) header cell in this table covering the column; (2) header cell in this table
    spanning the whole value area or a header-row label; (3) page text between the statement title and the table
    top, with no other table in between (geometric association + explicit unit language)."""
    u = UnitRead()
    levels: list[tuple[str, list[tuple[str, str]]]] = []
    hdr = header_cells(t)
    lvl1 = [(c.id, c.text) for c in hdr if c.covers_col(col) and c.c0 > 0 and UNIT.search(c.text)
            and (c.c1 - c.c0) < max(t.ncols - 1, 1)]
    lvl2 = [(c.id, c.text) for c in hdr if UNIT.search(c.text) and (c.c0 == 0 or (c.c1 - c.c0) >= max(t.ncols - 1, 1))]
    above = [x for x in s.texts if x.page == t.page and x.bottom <= t.top + 2]
    other_tables_between = lambda x: any(o.page == t.page and o.index != t.index and x.bottom <= o.top and o.bottom <= t.top
                                         for o in s.tables)
    lvl3 = [(x.id, x.text) for x in above if UNIT.search(x.text) and not other_tables_between(x)]
    for name, lv in (("R-UNIT-COLUMN", lvl1), ("R-UNIT-TABLE", lvl2), ("R-UNIT-CAPTION", lvl3)):
        if lv:
            levels.append((name, lv))
    if not levels:
        return u
    rule, chosen = levels[0]
    scales = {SCALES[UNIT.search(text).group(2).lower()] for _, text in chosen}
    if len(scales) > 1:
        u.conflicts.append(f"Equally specific unit statements disagree ({rule}).")
        return u
    u.scale, u.rule = scales.pop(), rule
    for nid, text in chosen:
        u.ids.append(nid)
        edges.append(Edge("unit_applies_to", nid, value_id, rule, text))
        if re.search(r"\bdollars\b|\busd\b|\$", text, re.I):
            u.currency = "USD"
        if re.search(r"except\s+per\s+share", text, re.I):
            u.per_share_exception = True
        if re.search(r"rupiah|\beur\b|euro|£|€|\bidr\b", text, re.I):
            u.conflicts.append("The governing unit statement names a non-USD currency.")
    return u


def statement_scope(s: Structure, t: Table, edges: list[Edge], value_id: str) -> tuple[str | None, list[str]]:
    titles = [x for x in s.texts if x.page == t.page and x.bottom <= t.top + 2 and STATEMENT_TITLE.search(x.text)]
    titles += [type("T", (), {"id": c.id, "text": c.text})() for c in header_cells(t) if STATEMENT_TITLE.search(c.text)]
    if not titles:
        return None, []
    ids = [x.id for x in titles]
    for x in titles:
        edges.append(Edge("section_scope_for", x.id, value_id, "R-SCOPE-TITLE", x.text))
    text = " ".join(x.text for x in titles).lower()
    if "segment" in text:
        return "segment", ids
    return ("consolidated" if "consolidated" in text else None), ids


# ---------------------------------------------------------------- candidate evaluation

@dataclass
class Ob:
    id: str
    status: str
    reason: str
    evidence: list[str] = field(default_factory=list)

    def as_dict(self):
        return {"id": self.id, "status": self.status, "reason": self.reason, "evidence": self.evidence}


def evaluate_cell(s: Structure, value_id: str, metric: str, source_ok: bool, registered_sha: str, policy: str = POLICY_VERSION) -> dict:
    """Derive the full semantic tuple and obligations for one value cell under the policy (no claim needed)."""
    cell = s.cell_by_id.get(value_id)
    edges: list[Edge] = []
    obs: dict[str, Ob] = {}
    if cell is None:
        return {"value_cell": value_id, "tuple": None, "edges": [], "obligations": [Ob("S1", "fail", "value_cell_not_in_parse").as_dict()]}
    t = next(tt for tt in s.tables if tt.index == cell.table)
    edges += [Edge("in_table", value_id, f"table:{t.index}", "R-STRUCT"), Edge("on_page", value_id, f"page:{t.page}", "R-STRUCT")]
    obs["S1"] = Ob("S1", "pass" if source_ok and s.source_sha256 == registered_sha else "fail",
                   "source_hash_and_parse_ownership" if source_ok else "source_bytes_do_not_match_registration")
    amt = parse_amount(cell.text)
    obs["S2"] = Ob("S2", "pass" if amt.kind == "number" else ("unknown" if amt.kind in ("dash", "empty") else "fail"),
                   {"number": "value_cell_amount_readable", "dash": "dash_printed_not_zero", "empty": "empty_cell",
                    "invalid": "unreadable_or_footnoted_amount"}[amt.kind], [value_id])
    obs["N1"] = Ob("N1", "pass" if amt.kind == "number" else obs["S2"].status,
                   "en_US_separators_parentheses_negative" if amt.kind == "number" else obs["S2"].reason, [value_id])
    # metric row / section
    lbl = row_label(t, cell.r0)
    sec = section_label(t, cell.r0, policy)
    pattern = METRIC_ROWS[metric]
    if lbl:
        edges.append(Edge("row_label_for", lbl.id, value_id, "R-ROW-LEFTMOST", lbl.text))
    if sec:
        edges.append(Edge("section_scope_for", sec.id, value_id, "R-SECTION-PRECEDING", sec.text))
    if lbl is None:
        obs["M1"] = Ob("M1", "unknown", "no_row_label")
    elif pattern.search(lbl.text):
        obs["M1"] = Ob("M1", "pass", "row_label_matches_metric_definition", [lbl.id])
    else:
        obs["M1"] = Ob("M1", "fail", "row_label_is_not_requested_metric", [lbl.id])
    scope, scope_ids = statement_scope(s, t, edges, value_id)
    per_share_section = bool(sec and PER_SHARE.search(sec.text)) or bool(lbl and PER_SHARE.search(lbl.text))
    if scope == "segment":
        obs["M2"] = Ob("M2", "fail", "segment_statement", scope_ids)
    elif scope != "consolidated":
        obs["M2"] = Ob("M2", "unknown", "consolidated_statement_title_not_associated", scope_ids)
    elif per_share_section:
        obs["M2"] = Ob("M2", "fail", "per_share_section_not_monetary_total", scope_ids + ([sec.id] if sec else []))
    else:
        obs["M2"] = Ob("M2", "pass", "consolidated_statement" + ("_parent_attribution" if metric == "profit_attributable_to_owners" else ""),
                       scope_ids + ([lbl.id] if lbl else []))
    # period
    pr = read_column_period(t, cell.c0, edges, value_id)
    pct_col = [c for c in header_cells(t) if c.covers_col(cell.c0) and c.c0 > 0 and PERCENT_COL.search(c.text)
               and not _durations(c.text)]
    obs["P1"] = Ob("P1", "pass" if pr.year else "unknown", "year_header_covers_column" if pr.year else "no_single_year_header",
                   pr.year_ids)
    obs["P2"] = Ob("P2", "pass" if pr.duration else "unknown",
                   pr.duration_rule if pr.duration else "no_applicable_duration_heading", pr.duration_ids)
    start, start_rule = (None, "end_date_not_stated")
    if pr.end and pr.duration:
        start, start_rule = derive_start(pr.end, pr.duration, pr.weeks)
    if pr.end and start:
        obs["P3"] = Ob("P3", "pass", f"stated_end_date+{start_rule}", pr.end_ids)
    else:
        obs["P3"] = Ob("P3", "unknown", start_rule if pr.end else "end_date_not_stated", pr.end_ids)
    # unit
    u = read_unit(s, t, cell.c0, edges, value_id)
    obs["U1"] = Ob("U1", "pass" if u.currency == "USD" and not u.conflicts else "unknown",
                   "usd_stated_in_governing_unit_statement" if u.currency == "USD" else "currency_not_stated", u.ids)
    if pct_col:
        obs["U2"] = Ob("U2", "fail", "percent_change_column_not_monetary", [c.id for c in pct_col])
    elif u.per_share_exception and per_share_section:
        obs["U2"] = Ob("U2", "fail", "per_share_exception_excludes_scale", u.ids + ([sec.id] if sec else []))
    elif u.scale is None:
        obs["U2"] = Ob("U2", "unknown", "no_applicable_scale_statement" if not u.conflicts else "conflicting_scale_statements", u.ids)
    else:
        obs["U2"] = Ob("U2", "pass", u.rule, u.ids)
    normalized = None
    if obs["S2"].status == "pass" and obs["U2"].status == "pass":
        normalized = _fmt(amt.value * u.scale)
        obs["N2"] = Ob("N2", "pass", "decimal_multiplication_no_fx_no_annualization", [value_id] + u.ids)
    else:
        obs["N2"] = Ob("N2", "unknown", "operands_not_supported")
    conflicts = pr.conflicts + u.conflicts
    obs["C1"] = Ob("C1", "fail" if conflicts else "pass", "; ".join(conflicts) if conflicts else "no_incompatible_applicable_evidence")
    tup = {"metric": metric, "scope": scope if scope else None, "amount_text": cell.text,
           "amount": _fmt(amt.value) if amt.kind == "number" else None, "currency": u.currency,
           "unit_scale": _fmt(u.scale) if u.scale else None, "normalized_value": normalized,
           "duration_months": pr.duration, "fiscal_year": pr.year, "end_date": pr.end if obs["P3"].status == "pass" else None,
           "start_date": start if obs["P3"].status == "pass" else None}
    return {"value_cell": value_id, "row_label": lbl.text if lbl else None, "table": t.index, "page": t.page,
            "row": cell.r0, "col": cell.c0, "tuple": tup, "edges": [e.as_dict() for e in edges],
            "obligations": [obs[k].as_dict() for k in OBLIGATIONS]}


def _fmt(v: Decimal) -> str:
    v = Decimal(v)
    return format(v.quantize(Decimal(1)) if v == v.to_integral_value() else v.normalize(), "f")


def supported(cand: dict | None) -> bool:
    """All required obligations pass; P3 passes, or is unknown only because the source states no end date.
    An end date that is stated but cannot be turned into an interval under a supported calendar rule is unresolved."""
    if not cand:
        return False
    st = {o["id"]: o for o in cand["obligations"]}
    if any(st.get(k, {}).get("status") != "pass" for k in REQUIRED):
        return False
    p3 = st.get("P3", {})
    return p3.get("status") == "pass" or (p3.get("status") == "unknown" and p3.get("reason") == "end_date_not_stated")


SEMANTIC_KEYS = ["metric", "scope", "amount", "currency", "unit_scale", "duration_months", "fiscal_year", "end_date", "start_date"]


def resolve_target(s: Structure, target: dict, source_ok: bool, registered_sha: str, policy: str = POLICY_VERSION) -> dict:
    """Enumerate value cells whose row matches the metric and whose derived column identity equals the target;
    evaluate obligations; group feasible candidates by full semantic tuple."""
    metric, dur, year = target["metric"], target["duration_months"], target["fiscal_year"]
    cands, coverage = [], []
    for t in s.tables:
        fdr = first_data_row(t)
        for c in t.cells:
            if c.r0 < fdr or c.c0 == 0:
                continue
            lbl = row_label(t, c.r0)
            if not lbl or not METRIC_ROWS[metric].search(lbl.text):
                continue
            ev = evaluate_cell(s, c.id, metric, source_ok, registered_sha, policy)
            tp = ev["tuple"]
            if tp["duration_months"] == dur and tp["fiscal_year"] == year:
                cands.append(ev)
    if len(cands) > MAX_CANDIDATES:
        coverage.append(f"candidate cap {MAX_CANDIDATES} exceeded ({len(cands)}); unresolved")
        return {"target_key": target["target_key"], "outcome": "unresolved", "reason": "candidate_cap_exceeded",
                "classes": [], "candidates": cands[:MAX_CANDIDATES], "coverage": coverage}
    feasible = [c for c in cands if supported(c)]
    classes: dict[str, dict] = {}
    for c in feasible:
        key = json.dumps({k: c["tuple"][k] for k in SEMANTIC_KEYS}, sort_keys=True)
        classes.setdefault(key, {"tuple": c["tuple"], "value_cells": []})["value_cells"].append(c["value_cell"])
    if len(classes) == 1:
        outcome, reason = "supported", "unique_supported_semantic_class"
    elif len(classes) > 1:
        outcome, reason = "unresolved", "ambiguous_context"
    elif cands:
        outcome, reason = "unresolved", "no_candidate_satisfies_required_obligations"
    else:
        outcome, reason = "unresolved", "no_candidate_for_target_column"
    return {"target_key": target["target_key"], "outcome": outcome, "reason": reason,
            "classes": list(classes.values()), "candidates": cands, "coverage": coverage}


# ---------------------------------------------------------------- claims, certificates, verification

CLAIM_FIELDS = ["metric", "value_cell", "amount", "currency", "unit_scale", "duration_months", "fiscal_year", "end_date", "start_date"]


def claim_from_fact(fact: dict) -> dict:
    p = fact.get("period") or {}
    end = p.get("end_date")
    return {"metric": fact["metric"], "value_cell": (fact["evidence"]["value_ids"] or [None])[0],
            "amount": fact.get("reported_value"), "currency": fact.get("currency"), "unit_scale": fact.get("unit_scale"),
            "duration_months": p.get("duration_months"),
            "fiscal_year": fact.get("fiscal_year") or (int(end[:4]) if end else None),
            "end_date": end, "start_date": p.get("start_date"),
            "cited": {k: list(v) for k, v in fact["evidence"].items()}}


def field_verdicts(claim: dict, ev: dict, policy: str = POLICY_VERSION) -> list[dict]:
    """Compare a claimed fact with the policy-derived reading of ITS OWN value cell, including whether the cited
    period/unit/metric evidence is on an applicable path to that cell."""
    tp = ev["tuple"] or {}
    applicable = {e["src"] for e in ev["edges"]}
    out = []

    def add(fld, ok, reason, unknown=False):
        out.append({"field": fld, "status": "unknown" if unknown else ("pass" if ok else "fail"), "reason": reason})

    if tp.get("amount") is None or claim["amount"] is None:
        add("amount", False, "amount_not_supported_or_missing", unknown=claim["amount"] is None)
    else:
        add("amount", Decimal(claim["amount"]) == Decimal(tp["amount"]), "claimed_amount_vs_value_cell")
    for fld in ("currency", "unit_scale", "duration_months", "fiscal_year"):
        want = tp.get(fld)
        if want is None:
            add(fld, False, f"{fld}_not_supported_by_applicable_context", unknown=True)
        else:
            got = claim.get(fld)
            ok = got is not None and (Decimal(str(got)) == Decimal(str(want)) if fld == "unit_scale" else str(got) == str(want))
            add(fld, ok, f"claimed_{fld}_vs_applicable_context")
    want, got = tp.get("start_date"), claim.get("start_date")
    if policy == "binding-v1":   # historical rule (end date verdict first, omitted derivable start date = unknown)
        for fld in ("end_date", "start_date"):
            want, got = tp.get(fld), claim.get(fld)
            if want is None:
                add(fld, got is None, f"{fld}_not_stated_claim_must_be_null" if got else f"{fld}_not_stated", unknown=got is None)
            else:
                add(fld, got == want, f"claimed_{fld}_vs_derived" if got else f"{fld}_omitted", unknown=got is None)
    elif got is None:
        add("start_date", True, "derived_by_application" if want else "start_date_not_stated", unknown=want is None)
    elif want is None:
        add("start_date", False, "start_date_claimed_but_not_supported")
    else:
        add("start_date", got == want, "claimed_start_date_vs_derived")
    for fld in (("end_date",) if policy != "binding-v1" else ()):
        want, got = tp.get(fld), claim.get(fld)
        if want is None:
            add(fld, got is None, f"{fld}_not_stated_claim_must_be_null" if got else f"{fld}_not_stated", unknown=got is None)
        else:
            add(fld, got == want, f"claimed_{fld}_vs_derived" if got else f"{fld}_omitted", unknown=got is None)
    for grp, fld in (("period_ids", "period_evidence"), ("unit_ids", "unit_evidence"), ("metric_ids", "metric_evidence")):
        cited = claim["cited"].get(grp, [])
        if not cited:
            add(fld, False, "none_cited", unknown=True)
        else:
            stray = [i for i in cited if i not in applicable]
            add(fld, not stray, "cited_ids_apply_to_value_cell" if not stray else f"cited_ids_do_not_apply:{','.join(stray)}")
    return out


def canonical(obj: Any) -> str:
    def default(o):
        if isinstance(o, Decimal):
            if not o.is_finite():
                raise ValueError("non-finite decimal")
            return format(o, "f")
        raise TypeError(type(o))
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=default)


def build_certificate(conn, *, document_id: str, parse_id: str, target: dict, fact: dict | None,
                      fact_ref: dict | None = None, policy: str = POLICY_VERSION) -> dict:
    if policy not in SUPPORTED_POLICIES:
        raise ValueError(f"unsupported binding policy {policy}")
    doc = db.row(conn, "SELECT * FROM documents WHERE document_id=?", document_id)
    src = source_path(doc)
    source_ok = src.exists() and sha256_file(src) == doc["sha256"]
    s = load_structure(conn, parse_id)
    if s.document_id != document_id:
        raise ValueError("parse belongs to another document")
    resolution = resolve_target(s, target, source_ok, doc["sha256"], policy)
    claim = claim_from_fact(fact) if fact else None
    claim_eval = None
    verdicts: list[dict] = []
    if claim:
        foreign = [i for ids in claim["cited"].values() for i in ids if i not in s.cell_by_id and i not in s.text_by_id]
        if claim["value_cell"] and claim["value_cell"] in s.cell_by_id:
            claim_eval = evaluate_cell(s, claim["value_cell"], claim["metric"], source_ok, doc["sha256"], policy)
            verdicts = field_verdicts(claim, claim_eval, policy)
        else:
            verdicts = [{"field": "value_cell", "status": "fail" if claim["value_cell"] else "unknown",
                         "reason": "value_cell_not_in_this_parse" if claim["value_cell"] else "no_value_cell"}]
        if foreign:
            verdicts.append({"field": "evidence_ownership", "status": "fail", "reason": f"foreign_or_invented_ids:{','.join(foreign)}"})
    resolved_cells = {c for cl in resolution["classes"] for c in cl["value_cells"]}
    if claim is None or (fact and fact.get("reported_value") is None):
        claim_outcome = "unresolved_claim"
    elif any(v["status"] == "fail" for v in verdicts):
        claim_outcome = "contradicted"
    elif resolution["outcome"] == "supported" and claim["value_cell"] in resolved_cells and \
            all(v["status"] == "pass" or (v["status"] == "unknown" and v["reason"] in ("end_date_not_stated", "start_date_not_stated"))
                for v in verdicts) and supported(claim_eval):
        claim_outcome = "supported"
    elif resolution["outcome"] == "supported" and claim["value_cell"] not in resolved_cells:
        claim_outcome = "contradicted" if claim_eval else "unsupported"
    else:
        claim_outcome = "unsupported"
    body = {
        "schema": "evi.support-certificate/1", "policy_version": policy,
        "source": {"document_id": document_id, "sha256": doc["sha256"], "source_url": doc["source_url"], "bytes_verified": source_ok},
        "parse": {"parse_id": parse_id, "cache_key": s.parse_cache_key, "docling_artifact_sha256": s.artifact_sha256,
                  "physical_pages": sorted(s.pages), "page_numbering": "docling page_no == physical 1-based page (validated)"},
        "target": target, "fact_ref": fact_ref,
        "claim": claim, "claim_outcome": claim_outcome, "field_verdicts": verdicts,
        "claim_cell_reading": claim_eval, "resolution": resolution,
        "boundary": "Certifies satisfaction of documented applicability rules over the registered source; "
                    "not issuer accounting truth, not a signature.",
    }
    body["content_sha256"] = hashlib.sha256(canonical(body).encode()).hexdigest()
    return body


def verify_certificate(conn, cert: dict) -> tuple[bool, list[str]]:
    """Recompute from trusted inputs (registered source bytes + Docling artifact) and compare. Checking the stored
    hash alone is NOT sufficient: any edited value/date/unit/edge/evidence ID changes the recomputation."""
    problems = []
    stored = dict(cert)
    claimed_hash = stored.pop("content_sha256", None)
    if hashlib.sha256(canonical(stored).encode()).hexdigest() != claimed_hash:
        problems.append("content hash does not match certificate content (edited after issue)")
    fact = None
    if cert.get("claim"):
        c = cert["claim"]
        fact = {"metric": c["metric"], "reported_value": c["amount"], "currency": c["currency"], "unit_scale": c["unit_scale"],
                "fiscal_year": c.get("fiscal_year"),
                "period": {"duration_months": c["duration_months"], "end_date": c["end_date"], "start_date": c["start_date"]},
                "evidence": c["cited"]}
    try:
        fresh = build_certificate(conn, document_id=cert["source"]["document_id"], parse_id=cert["parse"]["parse_id"],
                                  target=cert["target"], fact=fact, fact_ref=cert.get("fact_ref"),
                                  policy=cert.get("policy_version", POLICY_VERSION))
    except Exception as e:  # noqa: BLE001
        return False, problems + [f"recomputation failed: {type(e).__name__}: {e}"]
    for k in ("source", "parse", "claim_outcome", "field_verdicts", "claim_cell_reading", "resolution"):
        if canonical(fresh[k]) != canonical(cert.get(k)):
            problems.append(f"{k} differs from recomputation over the registered source")
    if not fresh["source"]["bytes_verified"]:
        problems.append("registered source bytes no longer match their SHA-256")
    return (not problems), problems


COVERAGE_VERSION = "coverage-v1"


def coverage_view(cert: dict) -> dict:
    """Additive presentation metadata derived from a stored certificate (never stored inside it, never hashed).
    Separates: a unique supported reading of the available source fields; complete period/unit context for every
    required field; and unknown required context (e.g. an exact interval the source does not print)."""
    reading = cert.get("claim_cell_reading") or {}
    obs = {o["id"]: o for o in reading.get("obligations", [])}
    p3 = obs.get("P3", {})
    unknown_fields = [v["field"] for v in cert.get("field_verdicts", []) if v["status"] == "unknown"]
    unknown_obligations = [k for k, o in obs.items() if o["status"] == "unknown"]
    supported_reading = cert.get("claim_outcome") == "supported"
    interval = ("known" if p3.get("status") == "pass" else
                "not_printed_in_source" if p3.get("reason") == "end_date_not_stated" else "unknown")
    complete = supported_reading and interval == "known" and not unknown_fields and not unknown_obligations
    if complete:
        label = "Supported: complete period and unit context"
    elif supported_reading and interval == "not_printed_in_source":
        label = "Supported reading; exact interval dates are not printed in the source"
    elif supported_reading:
        label = "Supported reading; some required context is unknown"
    else:
        label = {"contradicted": "Contradicted by applicable source context", "unsupported": "Not supported by applicable source context"}.get(
            cert.get("claim_outcome"), "Unresolved")
    tup = reading.get("tuple") or {}
    derived = ({"start_date": tup.get("start_date"), "end_date": tup.get("end_date"), "start_basis": "application-derived (R-CAL-MONTHEND)"}
               if supported_reading and interval == "known" else None)
    return {"coverage_version": COVERAGE_VERSION, "unique_supported_reading": supported_reading, "source_interval": derived,
            "complete_required_context": complete, "exact_interval": interval,
            "unknown_fields": unknown_fields, "unknown_obligations": unknown_obligations, "label": label}
