"""SQLite persistence (WAL). Every artifact row is insert-only except job/evaluation state machines."""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
  document_id TEXT PRIMARY KEY, issuer_name TEXT NOT NULL, title TEXT NOT NULL, source_url TEXT NOT NULL,
  sha256 TEXT NOT NULL, page_count INTEGER NOT NULL, source_page INTEGER NOT NULL, period_label TEXT,
  currency TEXT NOT NULL, file_name TEXT NOT NULL, byte_size INTEGER NOT NULL, source_version INTEGER NOT NULL DEFAULT 1,
  parse_pages TEXT NOT NULL, registered_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS parses (
  parse_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, document_sha256 TEXT NOT NULL, cache_key TEXT NOT NULL UNIQUE,
  parser TEXT NOT NULL, parser_version TEXT NOT NULL, config_json TEXT NOT NULL, pages_json TEXT NOT NULL,
  coverage_note TEXT NOT NULL, artifact_path TEXT NOT NULL, table_count INTEGER NOT NULL, evidence_count INTEGER NOT NULL,
  duration_ms INTEGER NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS evidence (
  evidence_id TEXT PRIMARY KEY, parse_id TEXT NOT NULL, document_id TEXT NOT NULL, document_sha256 TEXT NOT NULL,
  kind TEXT NOT NULL, page_number INTEGER NOT NULL, text TEXT NOT NULL, table_index INTEGER, row_index INTEGER,
  col_index INTEGER, row_span INTEGER, col_span INTEGER, is_column_header INTEGER, is_row_header INTEGER,
  bbox_json TEXT, page_width REAL, page_height REAL, label TEXT);
CREATE INDEX IF NOT EXISTS evidence_parse ON evidence(parse_id);
CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY, kind TEXT NOT NULL, status TEXT NOT NULL, session_id TEXT, payload_json TEXT NOT NULL,
  idempotency_key TEXT UNIQUE, message TEXT, error_json TEXT, result_json TEXT, attempts INTEGER NOT NULL DEFAULT 0,
  lease_until TEXT, not_before TEXT, next_job_id TEXT, parent_job_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status);
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, parse_id TEXT NOT NULL, status TEXT NOT NULL, mode TEXT NOT NULL,
  policy_version TEXT NOT NULL, model TEXT NOT NULL, budget_json TEXT NOT NULL, session_id TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS provider_calls (
  call_id TEXT PRIMARY KEY, provider TEXT NOT NULL, purpose TEXT NOT NULL, run_id TEXT, job_id TEXT, request_sha256 TEXT,
  http_status INTEGER, outcome TEXT NOT NULL, upstream_id TEXT, finish_reason TEXT, usage_json TEXT, latency_ms INTEGER,
  response_path TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS versions (
  version_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, parent_version_id TEXT, evaluation_id TEXT, origin TEXT NOT NULL,
  seq INTEGER NOT NULL, content_sha256 TEXT NOT NULL, body_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS evaluations (
  evaluation_id TEXT PRIMARY KEY, version_id TEXT NOT NULL, mode TEXT NOT NULL, status TEXT NOT NULL, eval_id TEXT,
  provider_status TEXT, payload_sha256 TEXT, payload_bytes INTEGER, result_json TEXT, credits_charged INTEGER,
  raw_path TEXT, session_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS budget_ledger (
  entry_id TEXT PRIMARY KEY, scope TEXT NOT NULL, key TEXT NOT NULL, units INTEGER NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS worker_heartbeats (worker_id TEXT PRIMARY KEY, seen_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS allowance_reservations (
  reservation_id TEXT PRIMARY KEY, allowance_id TEXT NOT NULL, provider TEXT NOT NULL, purpose TEXT NOT NULL,
  job_id TEXT, units INTEGER NOT NULL, status TEXT NOT NULL, call_id TEXT, created_at TEXT NOT NULL, settled_at TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS allowance_reservations_call ON allowance_reservations(allowance_id, call_id) WHERE call_id IS NOT NULL;
CREATE TABLE IF NOT EXISTS allowance_backfills (allowance_id TEXT PRIMARY KEY, backfilled_calls INTEGER NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS certificates (
  certificate_id TEXT PRIMARY KEY, version_id TEXT, fact_id TEXT, fact_sha256 TEXT, document_id TEXT NOT NULL,
  parse_id TEXT NOT NULL, target_key TEXT NOT NULL, policy_version TEXT NOT NULL, claim_outcome TEXT NOT NULL,
  resolution_outcome TEXT NOT NULL, content_sha256 TEXT NOT NULL, body_json TEXT NOT NULL, check_run_id TEXT,
  created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS certificates_version ON certificates(version_id);
CREATE TABLE IF NOT EXISTS check_runs (
  check_run_id TEXT PRIMARY KEY, version_id TEXT NOT NULL, version_content_sha256 TEXT NOT NULL, policy_version TEXT NOT NULL,
  original_checks_sha256 TEXT NOT NULL, summary_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS revision_receipts (
  receipt_id TEXT PRIMARY KEY, parent_version_id TEXT NOT NULL, child_version_id TEXT, arm TEXT NOT NULL,
  evaluation_id TEXT, idempotency_key TEXT UNIQUE, body_json TEXT NOT NULL, content_sha256 TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS benchmarks (benchmark_id TEXT PRIMARY KEY, body_json TEXT NOT NULL, created_at TEXT NOT NULL);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:20]}"


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or settings.db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


@contextmanager
def tx(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def row(conn: sqlite3.Connection, sql: str, *args: Any) -> sqlite3.Row | None:
    return conn.execute(sql, args).fetchone()


def rows(conn: sqlite3.Connection, sql: str, *args: Any) -> list[sqlite3.Row]:
    return conn.execute(sql, args).fetchall()


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
