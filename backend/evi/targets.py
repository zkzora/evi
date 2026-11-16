"""Frozen target definitions (targets-v1, 2026-11-16). Column identity = (duration in months, fiscal-year label of the
column). Decided from source layouts before any v2 inference; never changed to fit a model output.

Annual reports: current and immediately prior fiscal year (older comparative columns are not targets).
Interim reports: current and prior-year columns of the quarter and of the year-to-date group.
All 3 metrics x all columns are eligible. A target the source cannot support stays in the denominator.
"""
from __future__ import annotations

import hashlib
import json

TARGET_POLICY_VERSION = "targets-v1"
METRICS = ["revenue", "operating_profit", "profit_attributable_to_owners"]
COLUMNS = {
    "verizon-fy2025": [(12, 2025), (12, 2024)],
    "verizon-fy2024": [(12, 2024), (12, 2023)],
    "verizon-3q2025": [(3, 2025), (3, 2024), (9, 2025), (9, 2024)],
    "att-3q2025": [(3, 2025), (3, 2024), (9, 2025), (9, 2024)],
    "att-2q2025": [(3, 2025), (3, 2024), (6, 2025), (6, 2024)],
}
SPLIT = {"development": ["verizon-fy2025", "verizon-fy2024", "verizon-3q2025"], "holdout": ["att-3q2025", "att-2q2025"]}


def _extra_columns() -> dict:
    """Optional DATA registry (EVI_TARGET_REGISTRY=path to JSON {document_id: [[months, year], ...]}) for documents
    registered after a freeze. The same targets-v1 rules apply; historical COLUMNS cannot be overridden."""
    import os
    path = os.environ.get("EVI_TARGET_REGISTRY")
    if not path:
        return {}
    extra = {k: [tuple(c) for c in v] for k, v in json.loads(open(path, encoding="utf-8").read()).items()}
    if set(extra) & set(COLUMNS):
        raise ValueError("target registry may not redefine frozen historical documents")
    for cols in extra.values():
        if not all(m in (3, 6, 9, 12) and isinstance(y, int) for m, y in cols):
            raise ValueError("target registry columns must be (months in 3/6/9/12, integer year)")
    return extra


def key(document_id: str, metric: str, months: int, year: int) -> str:
    return f"{document_id}:{metric}:{months}M:{year}"


def targets_for(document_id: str) -> list[dict]:
    return [{"target_key": key(document_id, m, d, y), "document_id": document_id, "metric": m,
             "duration_months": d, "fiscal_year": y, "policy": TARGET_POLICY_VERSION}
            for (d, y) in {**COLUMNS, **_extra_columns()}.get(document_id, []) for m in METRICS]


def all_targets() -> list[dict]:
    return [t for d in COLUMNS for t in targets_for(d)]


def manifest_hash() -> str:
    return hashlib.sha256(json.dumps({"columns": COLUMNS, "split": SPLIT, "metrics": METRICS}, sort_keys=True).encode()).hexdigest()


def target_for_fact(document_id: str, fact: dict) -> dict | None:
    """Map a stored fact to its frozen target by claimed duration + fiscal year (used for re-checking old versions)."""
    p = fact.get("period") or {}
    year = fact.get("fiscal_year") or (int(p["end_date"][:4]) if p.get("end_date") else None)
    if fact.get("target_key"):
        return next((t for t in targets_for(document_id) if t["target_key"] == fact["target_key"]), None)
    return next((t for t in targets_for(document_id) if t["metric"] == fact["metric"]
                 and t["duration_months"] == p.get("duration_months") and t["fiscal_year"] == year), None)
