"""Docling parse of the registered statement pages -> immutable evidence records with real provenance."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sqlite3
import time
from typing import Any

from . import db
from .config import settings
from .corpus import source_path, verify_bytes

PARSER_CONFIG = {"do_ocr": False, "do_table_structure": True, "table_mode": "accurate", "do_cell_matching": True}


def parser_version() -> str:
    return importlib.metadata.version("docling")


def cache_key(sha256: str, pages: list[int], scope: str | None = None) -> str:
    m = {"sha": sha256, "parser": parser_version(), "config": PARSER_CONFIG, "pages": pages}
    if scope:   # added for uploads; registered keys are unchanged
        m["scope"] = scope
    material = json.dumps(m, sort_keys=True)
    return hashlib.sha256(material.encode()).hexdigest()


def _evidence_id(parse_key: str, *parts: Any) -> str:
    return "ev_" + hashlib.sha256((parse_key + "|" + "|".join(map(str, parts))).encode()).hexdigest()[:20]


def _bbox(b) -> dict | None:
    if b is None:
        return None
    origin = str(getattr(b.coord_origin, "value", b.coord_origin)).upper()
    origin = "BOTTOMLEFT" if "BOTTOM" in origin else "TOPLEFT"
    return {"left": float(b.l), "top": float(b.t), "right": float(b.r), "bottom": float(b.b), "origin": origin}


def doc_cache_key(doc, pages: list[int]) -> str:
    """Registered corpus: hash/parser/config/pages (shared public parse). Uploads additionally include the upload's own
    document_id, so identical bytes uploaded by another session never reuse (or reveal) its parse."""
    from .corpus import source_kind
    if source_kind(doc) == "user_upload":
        return cache_key(doc["sha256"], pages, scope=doc["document_id"])
    return cache_key(doc["sha256"], pages)


def parse_document(conn: sqlite3.Connection, document_id: str, pages: list[int] | None = None) -> str:
    """Return parse_id. Reuses a complete parse with the same hash/parser/config/page coverage (and, for uploads, owner).
    pages: explicit physical pages (uploads: exactly the selected page); default the registered statement pages."""
    doc = db.row(conn, "SELECT * FROM documents WHERE document_id=?", document_id)
    if doc is None:
        raise KeyError(document_id)
    pages = list(pages) if pages else json.loads(doc["parse_pages"])
    if not pages or any(not isinstance(p, int) or p < 1 or p > doc["page_count"] for p in pages):
        raise ValueError(f"invalid physical page selection {pages}")
    key = doc_cache_key(doc, pages)
    cached = db.row(conn, "SELECT parse_id FROM parses WHERE cache_key=?", key)
    if cached:
        return cached["parse_id"]
    verify_bytes(doc)

    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    from docling.document_converter import DocumentConverter, PdfFormatOption

    opts = PdfPipelineOptions(do_ocr=PARSER_CONFIG["do_ocr"], do_table_structure=True)
    opts.table_structure_options.mode = TableFormerMode.ACCURATE
    opts.table_structure_options.do_cell_matching = True
    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    started = time.monotonic()
    result = converter.convert(str(source_path(doc)), page_range=(min(pages), max(pages)))
    duration_ms = int((time.monotonic() - started) * 1000)
    ddoc = result.document

    parse_id = "parse_" + key[:20]
    sha = doc["sha256"]
    records: list[tuple] = []

    def page_dims(page_no: int) -> tuple[float | None, float | None]:
        p = ddoc.pages.get(page_no)
        return (float(p.size.width), float(p.size.height)) if p else (None, None)

    for ti, table in enumerate(ddoc.tables):
        if not table.prov:
            continue
        page_no = table.prov[0].page_no
        w, h = page_dims(page_no)
        for cell in table.data.table_cells:
            text = (cell.text or "").strip()
            if not text:
                continue
            records.append((
                _evidence_id(key, "cell", ti, cell.start_row_offset_idx, cell.start_col_offset_idx),
                parse_id, document_id, sha, "table_cell", page_no, text, ti, cell.start_row_offset_idx,
                cell.start_col_offset_idx, cell.end_row_offset_idx - cell.start_row_offset_idx,
                cell.end_col_offset_idx - cell.start_col_offset_idx, int(bool(cell.column_header)),
                int(bool(cell.row_header)), db.dumps(_bbox(cell.bbox)) if cell.bbox else None, w, h, None))
    for xi, item in enumerate(ddoc.texts):
        text = (item.text or "").strip()
        if not text or not item.prov:
            continue
        prov = item.prov[0]
        w, h = page_dims(prov.page_no)
        records.append((_evidence_id(key, "text", xi), parse_id, document_id, sha, "text", prov.page_no, text,
                        None, None, None, None, None, None, None, db.dumps(_bbox(prov.bbox)), w, h,
                        str(getattr(item.label, "value", item.label))))

    covered = sorted({r[5] for r in records})
    artifact = settings.artifacts_dir / "parses" / f"{parse_id}.docling.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps(ddoc.export_to_dict(), ensure_ascii=False), encoding="utf-8")
    note = (f"Statement-page parse of physical pages {pages} out of {doc['page_count']}; "
            f"evidence found on pages {covered}. Not full-document coverage.")
    with db.tx(conn):
        conn.execute("INSERT INTO parses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (parse_id, document_id, sha, key, "docling", parser_version(), db.dumps(PARSER_CONFIG),
                      db.dumps(pages), note, str(artifact), len(ddoc.tables), len(records), duration_ms, db.now()))
        conn.executemany("INSERT OR IGNORE INTO evidence VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", records)
    return parse_id
