"""Registered public source allowlist. Only these files can be parsed or served; bytes must match the hash."""
from __future__ import annotations

import hashlib
import sqlite3

from . import db
from .config import settings

# Physical 1-based pages that are parsed. Coverage is recorded on every parse; it is a statement-page
# parse, not full-document coverage.
REGISTERED = [
    dict(document_id="verizon-fy2025", issuer_name="Verizon", title="Annual Report on Form 10-K — 2025",
         period_label="December 2025 · USD", currency="USD", file_name="verizon-fy2025.pdf", source_page=52,
         parse_pages=[52], page_count=329,
         source_url="https://www.verizon.com/about/sites/default/files/2025-Annual-Report-on-Form-10k.pdf",
         sha256="c804f30d5957b8b4d43d1714b6405c163510cab1e282a2a383b0205d129b1508"),
    dict(document_id="verizon-fy2024", issuer_name="Verizon", title="Annual Report on Form 10-K — 2024",
         period_label="December 2024 · USD", currency="USD", file_name="verizon-fy2024.pdf", source_page=54,
         parse_pages=[54], page_count=116,
         source_url="https://www.verizon.com/about/sites/default/files/2024-Annual-Report-on-Form-10k.pdf",
         sha256="05ad83ec2279c04683b50878f8aa8ff8c868aad481b205f52e316df63c403318"),
    # Added 2026-11-16 for the bounded interim/holdout corpus (downloaded from issuer investor-relations hosts).
    dict(document_id="verizon-3q2025", issuer_name="Verizon", title="3Q 2025 Financial Statements",
         period_label="September 2025 · USD", currency="USD", file_name="verizon-3q2025.pdf", source_page=1,
         parse_pages=[1], page_count=10,
         source_url="https://www.verizon.com/about/file/76633/download?token=P8wDXRsG",
         sha256="8b4249c1ca915374587570b79536c9dd9b46fc1b345a11285f51cbd8518697f4"),
    dict(document_id="att-3q2025", issuer_name="AT&T", title="3Q 2025 Financial and Operational Schedules",
         period_label="Third quarter 2025 · USD", currency="USD", file_name="att-3q2025.pdf", source_page=2,
         parse_pages=[2], page_count=20,
         source_url="https://investors.att.com/~/media/Files/A/ATT-IR-V2/financial-reports/quarterly-earnings/2025/3Q-2025/3Q25_ATT_Financial_and_Operational_Schedules_and_Non_GAAP_Reconciliations.pdf",
         sha256="064b25a85c218185f10509dec7838b3384351b80ce487b1b0e7c272a1ae8c2d0"),
    dict(document_id="att-2q2025", issuer_name="AT&T", title="2Q 2025 Financial and Operational Schedules",
         period_label="Second quarter 2025 · USD", currency="USD", file_name="att-2q2025.pdf", source_page=2,
         parse_pages=[2], page_count=20,
         source_url="https://investors.att.com/~/media/Files/A/ATT-IR-V2/financial-reports/quarterly-earnings/2025/2Q-2025/2Q25_ATT_Financial_and_Operational_Schedules_and_Non_GAAP_Reconciliations.pdf",
         sha256="0065aa98bd90d5f59d9b6c05c6921397c97e3fba5f49b3b53e1f6ae3a522450b"),
]


def _extra_registry() -> list[dict]:
    """Optional DATA registry (EVI_SOURCE_REGISTRY=path to JSON list) so new sources can be registered under frozen code."""
    import json
    import os
    path = os.environ.get("EVI_SOURCE_REGISTRY")
    if not path:
        return []
    items = json.loads(open(path, encoding="utf-8").read())
    known = {r["document_id"] for r in REGISTERED}
    need = {"document_id", "issuer_name", "title", "period_label", "currency", "file_name", "source_page", "parse_pages",
            "page_count", "source_url", "sha256"}
    for it in items:
        if not need <= set(it) or it["document_id"] in known or it["currency"] != "USD":
            raise ValueError(f"invalid registry entry {it.get('document_id')}")
    return items


class SourceIntegrityError(Exception):
    pass


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_path(doc: sqlite3.Row | dict):
    path = (settings.sources_dir / doc["file_name"]).resolve()
    if path.parent != settings.sources_dir.resolve():
        raise SourceIntegrityError("Source path escapes the registered source directory.")
    return path


def verify_bytes(doc) -> None:
    path = source_path(doc)
    if not path.exists():
        raise SourceIntegrityError(f"Registered source file is missing for {doc['document_id']}.")
    actual = sha256_file(path)
    if actual != doc["sha256"]:
        raise SourceIntegrityError(f"Source bytes for {doc['document_id']} do not match the registered SHA-256.")


def register_all(conn: sqlite3.Connection) -> None:
    for entry in REGISTERED + _extra_registry():
        path = source_path(entry)
        if not path.exists():
            continue
        existing = db.row(conn, "SELECT sha256 FROM documents WHERE document_id=?", entry["document_id"])
        if existing:
            if existing["sha256"] != entry["sha256"]:
                raise SourceIntegrityError("A registered document changed hash; register a new source version instead.")
            continue
        verify_bytes(entry)
        conn.execute(
            "INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?,1,?,?)",
            (entry["document_id"], entry["issuer_name"], entry["title"], entry["source_url"], entry["sha256"],
             entry["page_count"], entry["source_page"], entry["period_label"], entry["currency"], entry["file_name"],
             path.stat().st_size, db.dumps(entry["parse_pages"]), db.now()))
