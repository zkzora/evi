"""Fresh holdout: freeze BEFORE any candidate source is opened, then gated preparation (2026-11-16).

  python -m evi.holdout freeze <holdout_id>      # hashes code/config/prompts, records rules + candidates; opens no source
  python -m evi.holdout preflight <holdout_id>   # policy drift + every gate (sources, targets, references, approval)
  python -m evi.holdout stage-run <holdout_id>   # writes artifacts/technical-proof/<id>/manifest.json once gates pass
Running the staged experiment still requires `python -m evi.authorization` approval + EVI_ALLOW_PAID_RUNS=1.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from .config import ROOT, settings

HOLDOUT = ROOT / "artifacts" / "holdout"
CODE_DIR = Path(__file__).parent
FROZEN_FILES = sorted(p.name for p in CODE_DIR.glob("*.py"))
SELECTION_RULE = {
    "sector": "telecom/connectivity, USD-reporting US issuers",
    "excluded_issuers": ["Verizon", "AT&T"],
    "candidates": [
        {"issuer": "T-Mobile US", "report": "most recent quarterly (10-Q or IR quarterly financial statements PDF)", "kind": "interim"},
        {"issuer": "Comcast", "report": "most recent annual report on Form 10-K PDF", "kind": "annual"},
        {"issuer": "Charter Communications", "report": "most recent quarterly statements PDF", "kind": "interim"},
        {"issuer": "Lumen Technologies", "report": "most recent annual report on Form 10-K PDF", "kind": "annual"},
    ],
    "backups_in_order": ["Altice USA (annual)", "Cogent Communications (interim)"],
    "rule": ("Take the latest report of the stated kind published on the issuer's own investor-relations host as of the acquisition "
             "date. Use it only if it is a PDF whose consolidated statement of income/operations is in USD; otherwise move to the next backup. "
             "Do not choose or skip a report because of its layout."),
    "statement_page": "The physical page holding the consolidated statement of income/operations (plus an adjacent page only if that table continues).",
    "targets": "targets-v1: annual -> current + prior fiscal year; interim -> current + prior year of the quarter and of the YTD group; 3 metrics.",
    "eligibility": "All targets are eligible. A metric the page does not explicitly report is kept and scored unresolved; nothing is excluded after inference.",
}


def _hash_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def code_hashes() -> dict:
    h = {f"backend/evi/{n}": _hash_file(CODE_DIR / n) for n in FROZEN_FILES}
    h["backend/requirements.lock"] = _hash_file(ROOT / "backend" / "requirements.lock")
    return h


def freeze(hid: str) -> dict:
    d = HOLDOUT / hid
    if (d / "freeze.json").exists():
        raise SystemExit("already frozen; a changed policy needs a new holdout id")
    from importlib.metadata import version

    from .binding import POLICY_VERSION as BIND
    from .evaluation import PACKET_V2
    from .extraction import POLICY_V2, SYSTEM_EXTRACT_V2
    from .parsing import PARSER_CONFIG
    from .revision import REVISION_POLICY, SYSTEM_REVISE_V2
    fr = {"holdout_id": hid, "frozen_at": datetime.now(timezone.utc).isoformat(),
          "status": "frozen; no candidate source acquired or opened",
          "policies": {"extraction": POLICY_V2, "binding": BIND, "revision": REVISION_POLICY, "targets": "targets-v1",
                       "analysis": "analysis-v2", "replay": "replay-v2", "coverage": "coverage-v1",
                       "reppo_packet": PACKET_V2, "parser": {"docling": version("docling"), "config": PARSER_CONFIG},
                       "model": settings.serv_model},
          "prompt_sha256": {"extract_v2": hashlib.sha256(SYSTEM_EXTRACT_V2.encode()).hexdigest(),
                            "revise_v2": hashlib.sha256(SYSTEM_REVISE_V2.encode()).hexdigest()},
          "code_sha256": code_hashes(), "selection": SELECTION_RULE,
          "exposure": {
              "claim": "These report layouts and results were not used to tune the frozen Evi policy. This is NOT a claim that "
                       "the public reports are absent from any model's pretraining data.",
              "registration": "If no one outside the build loop is available, the builder/agent will acquire and register sources; "
                              "this will be disclosed. Registration must not involve viewing model outputs.",
              "references": "Labels must come from a person outside the implementation loop who has not seen model outputs; "
                            "otherwise provenance is reported as builder/agent-drafted and the result as provisional.",
              "on_unsupported_layout": "Report failure/unknown. Any code change creates a new policy; the affected report becomes "
                                       "development material and a different untouched report is needed for a fresh-test claim."},
          }
    d.mkdir(parents=True, exist_ok=True)
    (d / "freeze.json").write_text(json.dumps(fr, indent=1), encoding="utf-8")
    plan = {"holdout_id": hid, "kind": "dry-run plan (not executable until stage-run)", "freeze_sha256": _hash_file(d / "freeze.json"),
            "documents": "4 per selection rule (to be registered)", "trials": 2,
            "arms": {"A": "Docling + one SERV v2 extraction", "B": "A + binding-v3 certificates",
                     "C": "A + diagnostics + one revision-v3 call (no feedback)",
                     "D": "A + diagnostics + one real Reppo evaluation (reppo-packet-v2) + one revision-v3 call"},
            "caps": {"serv_calls": 4 * 2 * 3 + 2, "reppo_evals": 4 * 2, "reppo_credits_at_440": 4 * 2 * 440},
            "gates": ["no policy drift since freeze", "4 sources registered with URL/hash/page via EVI_SOURCE_REGISTRY",
                      "target columns registered via EVI_TARGET_REGISTRY", "Docling parses exist",
                      "reference file hashed with non-builder provenance (or disclosed)", "approval file bound to the staged manifest",
                      "EVI_ALLOW_PAID_RUNS=1"],
            "stopping": "caps, auth/credit failures, unknown Reppo submissions; never on observed results",
            "failure_handling": "as exp-2026-11-16-a (failed A leaves C/D unexecuted and recorded; provider failure = execution failure)",
            "reporting": "analysis-v2 metrics per document; replay-v2 must be VERIFIED before any result is reported; not pooled with "
                         "the historical five-report experiments"}
    (d / "manifest-dryrun.json").write_text(json.dumps(plan, indent=1), encoding="utf-8")
    return fr


def preflight(hid: str) -> dict:
    import os
    d = HOLDOUT / hid
    fr = json.loads((d / "freeze.json").read_text(encoding="utf-8"))
    now = code_hashes()
    drift = sorted(k for k in set(now) | set(fr["code_sha256"]) if now.get(k) != fr["code_sha256"].get(k))
    gates = {"policy_unchanged_since_freeze": not drift,
             "source_registry": bool(os.environ.get("EVI_SOURCE_REGISTRY")),
             "target_registry": bool(os.environ.get("EVI_TARGET_REGISTRY")),
             "references_registered": (d / "references.json").exists(),
             "staged_manifest": (ROOT / "artifacts" / "technical-proof" / hid / "manifest.json").exists(),
             "approval_file": (ROOT / "artifacts" / "approvals" / f"{hid}.approval.json").exists(),
             "paid_runs_flag": os.environ.get("EVI_ALLOW_PAID_RUNS") == "1"}
    return {"holdout_id": hid, "drifted_files": drift, "gates": gates, "runnable": all(gates.values())}


def stage_run(hid: str, seed: int = 20261116) -> dict:
    from . import db, targets
    pf = preflight(hid)
    if pf["drifted_files"]:
        raise SystemExit(f"REFUSED: policy changed since freeze: {pf['drifted_files']}")
    for g in ("source_registry", "target_registry", "references_registered"):
        if not pf["gates"][g]:
            raise SystemExit(f"REFUSED: gate {g} not satisfied")
    d = HOLDOUT / hid
    refs_meta = json.loads((d / "references.json").read_text(encoding="utf-8"))   # {path, sha256, provenance}
    reg = json.loads(Path(__import__("os").environ["EVI_SOURCE_REGISTRY"]).read_text(encoding="utf-8"))
    docs = [r["document_id"] for r in reg]
    conn = db.connect()
    sources, parses = [], []
    for doc in docs:
        r = db.row(conn, "SELECT * FROM documents WHERE document_id=?", doc)
        p = db.row(conn, "SELECT * FROM parses WHERE document_id=? ORDER BY created_at DESC LIMIT 1", doc)
        if r is None or p is None:
            raise SystemExit(f"REFUSED: {doc} not registered/parsed")
        sources.append({"document_id": doc, "sha256": r["sha256"], "source_url": r["source_url"], "physical_pages": json.loads(r["parse_pages"])})
        parses.append({"document_id": doc, "parse_id": p["parse_id"], "cache_key": p["cache_key"], "parser_version": p["parser_version"],
                       "docling_artifact_sha256": _hash_file(Path(p["artifact_path"])), "coverage": p["coverage_note"]})
    rnd = random.Random(seed)
    schedule = []
    for t in (1, 2):
        order = docs[:]
        rnd.shuffle(order)
        for doc in order:
            arms = ["C", "D"]
            rnd.shuffle(arms)
            schedule.append({"trial": t, "document_id": doc, "revision_order": arms})
    fr = json.loads((d / "freeze.json").read_text(encoding="utf-8"))
    m = {"experiment_id": hid, "schema_version": "evi.experiment-manifest/1", "created_at": datetime.now(timezone.utc).isoformat(),
         "holdout_freeze_sha256": _hash_file(d / "freeze.json"), "sources": sources, "parses": parses,
         "split": {"development": [], "holdout": docs}, "exposure_notes": [fr["exposure"]["claim"]],
         "targets": [t for doc in docs for t in targets.targets_for(doc)], "reference": refs_meta,
         "policies": {k: fr["policies"][k] for k in ("extraction", "binding", "revision", "targets")},
         "reppo_packet": fr["policies"]["reppo_packet"], "prompt_sha256": fr["prompt_sha256"], "code_sha256": fr["code_sha256"],
         "model": {"serv_model": settings.serv_model}, "trial_plan": {"trials": 2, "seed": seed, "schedule": schedule},
         "caps": {"serv_calls": len(docs) * 2 * 3 + 2, "reppo_evals": len(docs) * 2}}
    out = ROOT / "artifacts" / "technical-proof" / hid
    if (out / "manifest.json").exists():
        raise SystemExit("staged manifest exists; refusing to overwrite")
    out.mkdir(parents=True)
    (out / "manifest.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
    return {"staged": str(out / "manifest.json"), "documents": docs}


if __name__ == "__main__":
    cmd, hid = sys.argv[1], sys.argv[2]
    fn = {"freeze": freeze, "preflight": preflight, "stage-run": stage_run}[cmd]
    res = fn(hid)
    print(json.dumps(res if cmd != "freeze" else {"frozen": hid, "frozen_at": res["frozen_at"], "status": res["status"]}, indent=1))
