"""Judge PDF upload (2026-11-16): one session-owned PDF, one selected physical page per run.

- Bytes are stored on the persistent volume under data_dir/uploads/<server id>.pdf (never public/, git or snapshots).
- Validation: %PDF- signature, bounded size, pdfium page count, encrypted PDFs rejected. Upload calls no provider.
- Ownership: an uploaded document and EVERY derivative (parses, runs, versions, evidence, certificates, evaluations)
  is visible only to the uploading browser session; other sessions get 404 as if it did not exist.
- Targets: columns (interval months, fiscal-year label) are derived deterministically from the parsed page with the
  binding policy's own header reader (no model, no user input); targets-v1 selection rules (two most recent years per
  interval) apply. No derivable column = unsupported layout, stopped before SERV.
- Retention: expires after EVI_UPLOAD_RETENTION_HOURS (default 24). Cleanup deletes only rows/files owned by expired
  uploads, by explicit path, and skips uploads with queued/running jobs.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import db
from .config import settings

SOURCE_KIND = "user_upload"
UPLOAD_PREFIX = "upl_"
TARGET_DERIVATION = "upload-columns-v1"


class UploadRejected(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def is_upload_id(document_id: str | None) -> bool:
    return bool(document_id) and document_id.startswith(UPLOAD_PREFIX)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(d: datetime) -> str:
    return d.isoformat(timespec="milliseconds")


def expired(doc) -> bool:
    return bool(doc["expires_at"]) and datetime.fromisoformat(doc["expires_at"]) <= _now()


# ---------------------------------------------------------------- ownership

def owner_ok(doc, session_id: str) -> bool:
    """True for registered public documents; for uploads only for the owning session and only before expiry."""
    if doc is None:
        return False
    try:
        kind = doc["source_kind"]
    except (IndexError, KeyError):
        kind = "registered"
    if kind != SOURCE_KIND:
        return True
    return doc["owner_session"] == session_id and not expired(doc)


def doc_visible(conn, document_id: str | None, session_id: str) -> bool:
    if not document_id:
        return False
    if not is_upload_id(document_id):
        return db.row(conn, "SELECT 1 FROM documents WHERE document_id=?", document_id) is not None
    return owner_ok(db.row(conn, "SELECT * FROM documents WHERE document_id=?", document_id), session_id)


def version_document(conn, version_id: str) -> str | None:
    r = db.row(conn, "SELECT r.document_id FROM versions v JOIN runs r ON r.run_id=v.run_id WHERE v.version_id=?", version_id)
    return r["document_id"] if r else None


# ---------------------------------------------------------------- validation and storage

def _clean_name(name: str) -> str:
    base = re.split(r"[\\/]", name or "")[-1]
    base = re.sub(r"[^\w .,()&+-]", "_", base).strip()[:120]
    return base or "upload.pdf"


def inspect_pdf(path: Path) -> int:
    """Physical page count via pdfium. Raises UploadRejected for unreadable or encrypted PDFs."""
    import pypdfium2 as pdfium
    from pypdfium2 import raw as pdfium_c
    try:
        pdf = pdfium.PdfDocument(str(path))
    except pdfium.PdfiumError as e:
        msg = str(e).lower()
        if "password" in msg:
            raise UploadRejected(422, "encrypted_pdf", "This PDF is password-protected or encrypted. Upload an unencrypted copy.")
        raise UploadRejected(422, "unreadable_pdf", "This file could not be read as a PDF.")
    try:
        # Owner-password-only encryption opens without a password; it is still rejected in this release.
        if pdfium_c.FPDF_GetSecurityHandlerRevision(pdf.raw) != -1:
            raise UploadRejected(422, "encrypted_pdf", "This PDF is encrypted. Upload an unencrypted copy.")
        n = len(pdf)
    finally:
        pdf.close()
    if n < 1:
        raise UploadRejected(422, "unreadable_pdf", "This PDF has no pages.")
    if n > settings.upload_max_pages:
        raise UploadRejected(413, "too_many_pages", f"This PDF has {n} pages; the limit is {settings.upload_max_pages}.")
    return n


def check_quotas(conn, session_id: str, incoming: int) -> None:
    now = _iso(_now())
    active = db.row(conn, "SELECT COUNT(*) n FROM documents WHERE source_kind=? AND owner_session=? AND expires_at>?",
                    SOURCE_KIND, session_id, now)["n"]
    if active >= settings.upload_per_session_active:
        raise UploadRejected(429, "upload_limit", f"This browser session already has {active} active uploads "
                             f"(limit {settings.upload_per_session_active}). They expire {settings.upload_retention_hours} h after upload.")
    hour = _iso(_now() - timedelta(hours=1))
    recent = db.row(conn, "SELECT COUNT(*) n FROM documents WHERE source_kind=? AND owner_session=? AND registered_at>=?",
                    SOURCE_KIND, session_id, hour)["n"]
    if recent >= settings.upload_per_session_per_hour:
        raise UploadRejected(429, "upload_rate_limited", f"This browser session uploaded {recent} PDFs in the last hour "
                             f"(limit {settings.upload_per_session_per_hour}).")
    import shutil
    free = shutil.disk_usage(settings.uploads_dir).free
    if free - incoming < settings.upload_min_free_bytes:   # never let uploads fill the volume the database lives on
        raise UploadRejected(507, "upload_storage_full", "Upload storage on this server is full right now. "
                             "Uploads expire automatically; try again later. Registered reports remain available.")
    tot = db.row(conn, "SELECT COUNT(*) n, COALESCE(SUM(byte_size),0) b FROM documents WHERE source_kind=?", SOURCE_KIND)
    if tot["n"] >= settings.upload_global_files or tot["b"] + incoming > settings.upload_global_bytes:
        raise UploadRejected(507, "upload_storage_full", "Upload storage on this server is full right now. "
                             "Uploads expire automatically; try again later. Registered reports remain available.")


def store(conn, *, data: bytes, original_name: str, session_id: str, label: str | None) -> dict:
    """Validate and register an uploaded PDF. Calls no provider and enqueues nothing."""
    if len(data) > settings.upload_max_bytes:
        raise UploadRejected(413, "payload_too_large", f"The PDF is larger than {settings.upload_max_bytes // (1024 * 1024)} MiB.")
    if not data.startswith(b"%PDF-"):
        raise UploadRejected(415, "not_a_pdf", "The file is not a PDF (missing the %PDF- signature).")
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    document_id = UPLOAD_PREFIX + secrets.token_hex(10)
    file_name = f"{document_id}.pdf"
    path = settings.uploads_dir / file_name
    tmp = path.with_suffix(".part")
    tmp.write_bytes(data)
    try:
        pages = inspect_pdf(tmp)
        with db.tx(conn):
            check_quotas(conn, session_id, len(data))
            tmp.replace(path)
            now = _now()
            title = _clean_name(original_name)
            conn.execute(
                "INSERT INTO documents (document_id, issuer_name, title, source_url, sha256, page_count, source_page, period_label, "
                "currency, file_name, byte_size, source_version, parse_pages, registered_at, source_kind, owner_session, expires_at, "
                "original_name) VALUES (?,?,?,?,?,?,?,?,?,?,?,1,?,?,?,?,?,?)",
                (document_id, (label or "").strip()[:80] or "Your uploaded PDF", title, "", hashlib.sha256(data).hexdigest(),
                 pages, 1, None, "not asserted", file_name, len(data), "[]", _iso(now), SOURCE_KIND, session_id,
                 _iso(now + timedelta(hours=settings.upload_retention_hours)), title))
    finally:
        if tmp.exists():
            tmp.unlink()
    return db.row(conn, "SELECT * FROM documents WHERE document_id=?", document_id)


# ---------------------------------------------------------------- targets from the parsed page

def derive_columns(conn, document_id: str, parse_id: str) -> tuple[list[tuple[int, int]], dict]:
    """(months, fiscal year) column identities read by the binding policy from metric-row value cells of this parse."""
    from . import binding
    from .corpus import sha256_file, source_path
    doc = db.row(conn, "SELECT * FROM documents WHERE document_id=?", document_id)
    src = source_path(doc)
    source_ok = src.exists() and sha256_file(src) == doc["sha256"]
    s = binding.load_structure(conn, parse_id)
    seen: dict[tuple[int, int], int] = {}
    metric_rows = 0
    for t in s.tables:
        fdr = binding.first_data_row(t)
        for c in t.cells:
            if c.r0 < fdr or c.c0 == 0:
                continue
            lbl = binding.row_label(t, c.r0)
            if not lbl:
                continue
            for metric, rx in binding.METRIC_ROWS.items():
                if not rx.search(lbl.text):
                    continue
                metric_rows += 1
                tp = binding.evaluate_cell(s, c.id, metric, source_ok, doc["sha256"])["tuple"]
                if tp.get("duration_months") in (3, 6, 9, 12) and isinstance(tp.get("fiscal_year"), int):
                    k = (tp["duration_months"], tp["fiscal_year"])
                    seen[k] = seen.get(k, 0) + 1
    cols: list[tuple[int, int]] = []
    for months in sorted({m for m, _ in seen}):
        years = sorted({y for m, y in seen if m == months}, reverse=True)[:2]   # targets-v1: current + prior year
        cols += [(months, y) for y in years]
    return cols, {"derivation": TARGET_DERIVATION, "tables": len(s.tables), "metric_row_cells": metric_rows,
                  "column_observations": {f"{m}M:{y}": n for (m, y), n in sorted(seen.items())}}


def save_targets(conn, document_id: str, parse_id: str, cols: list[tuple[int, int]], derivation: dict) -> None:
    conn.execute("INSERT OR REPLACE INTO upload_targets VALUES (?,?,?,?,?)",
                 (document_id, parse_id, json.dumps(cols), json.dumps(derivation), db.now()))


def columns_for(document_id: str, parse_id: str | None = None) -> list[tuple[int, int]]:
    c = db.connect()
    try:
        if parse_id:
            rows = db.rows(c, "SELECT columns_json FROM upload_targets WHERE document_id=? AND parse_id=?", document_id, parse_id)
        else:   # union over processed pages: key lookups for stored versions of any processed page
            rows = db.rows(c, "SELECT columns_json FROM upload_targets WHERE document_id=? ORDER BY created_at", document_id)
    except Exception:  # noqa: BLE001 - table absent in a database that predates uploads
        return []
    finally:
        c.close()
    out: list[tuple[int, int]] = []
    for r in rows:
        for m, y in json.loads(r["columns_json"]):
            if (m, y) not in out:
                out.append((m, y))
    return out


# ---------------------------------------------------------------- retention

def cleanup(conn, now: datetime | None = None, limit: int = 20) -> list[str]:
    """Delete expired uploads and only their own derivatives. Bounded per call; skips uploads with active jobs.
    Never touches registered sources, frozen experiments or files outside uploads/ and the upload's own parse/cert files."""
    now = now or _now()
    removed = []
    for d in db.rows(conn, "SELECT * FROM documents WHERE source_kind=? AND expires_at<=? ORDER BY expires_at LIMIT ?",
                     SOURCE_KIND, _iso(now), limit):
        did = d["document_id"]
        if not is_upload_id(did):
            continue
        busy = db.row(conn, "SELECT 1 FROM jobs WHERE status IN ('queued','running') AND json_extract(payload_json,'$.document_id')=?", did)
        run_busy = db.row(conn, "SELECT 1 FROM jobs j JOIN runs r ON r.run_id=json_extract(j.payload_json,'$.run_id') "
                                "WHERE j.status IN ('queued','running') AND r.document_id=?", did)
        if busy or run_busy:
            continue
        files: list[Path] = [settings.uploads_dir / d["file_name"]]
        with db.tx(conn):
            parses = db.rows(conn, "SELECT parse_id, artifact_path FROM parses WHERE document_id=?", did)
            runs = [r["run_id"] for r in db.rows(conn, "SELECT run_id FROM runs WHERE document_id=?", did)]
            versions = [v["version_id"] for r in runs for v in db.rows(conn, "SELECT version_id FROM versions WHERE run_id=?", r)]
            from .certify import CERT_DIR
            for cid in db.rows(conn, "SELECT certificate_id FROM certificates WHERE document_id=?", did):
                files.append(CERT_DIR / f"{cid['certificate_id']}.json")
            conn.execute("DELETE FROM certificates WHERE document_id=?", (did,))
            for v in versions:
                conn.execute("DELETE FROM check_runs WHERE version_id=?", (v,))
                conn.execute("DELETE FROM evaluations WHERE version_id=?", (v,))
                conn.execute("DELETE FROM revision_receipts WHERE child_version_id=? OR parent_version_id=?", (v, v))
                conn.execute("DELETE FROM versions WHERE version_id=?", (v,))
            for r in runs:
                conn.execute("DELETE FROM runs WHERE run_id=?", (r,))
            for p in parses:
                conn.execute("DELETE FROM evidence WHERE parse_id=?", (p["parse_id"],))
                files.append(Path(p["artifact_path"]))
            conn.execute("DELETE FROM parses WHERE document_id=?", (did,))
            conn.execute("DELETE FROM upload_targets WHERE document_id=?", (did,))
            conn.execute("DELETE FROM documents WHERE document_id=? AND source_kind=?", (did, SOURCE_KIND))
        allowed = {settings.uploads_dir.resolve(), (settings.artifacts_dir / "parses").resolve()}
        from .certify import CERT_DIR
        allowed.add(CERT_DIR.resolve())
        for f in files:
            f = f.resolve()
            if f.parent in allowed and f.is_file() and (did in f.name or f.parent != settings.uploads_dir.resolve()):
                f.unlink()
        removed.append(did)
    return removed

