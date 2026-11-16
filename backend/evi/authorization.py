"""Spending gates (2026-11-16). Configured provider keys are NOT budget approval.

A paid experiment run requires BOTH:
  1. environment flag EVI_ALLOW_PAID_RUNS=1 for that process, and
  2. a human-written approval file artifacts/approvals/<exp_id>.approval.json that names the exact manifest SHA-256 and
     explicit caps (SERV calls, Reppo evaluations, Reppo credits), with approver name/date and the approval text.
Without both, `python -m evi.experiment run|run-branch` refuses before any provider call. `--dry-run` prints the plan.

  python -m evi.authorization template <exp_id>   # prints an UNSIGNED template to stdout; never writes an approval
  python -m evi.authorization check <exp_id>      # validates an existing approval file against the manifest
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from .config import ROOT

APPROVALS = ROOT / "artifacts" / "approvals"
REPPO_CREDITS_PER_TEXT_EVAL = 440  # agents.md, read 2026-11-16; verify again before requesting approval


class NotAuthorized(Exception):
    pass


def manifest_sha(exp_dir: Path) -> str:
    return hashlib.sha256((exp_dir / "manifest.json").read_bytes()).hexdigest()


def planned_calls(m: dict, done: int = 0) -> dict:
    caps = m.get("caps", {})
    evals = int(caps.get("reppo_evals", 0))
    return {"serv_calls_max": int(caps.get("serv_calls", 0)), "reppo_evaluations_max": evals,
            "reppo_credits_max_at_documented_price": evals * REPPO_CREDITS_PER_TEXT_EVAL,
            "serv_usd": "unknown (no per-call price source)", "already_recorded_branches": done}


def require_approval(exp_id: str, exp_dir: Path, m: dict) -> dict:
    if os.environ.get("EVI_ALLOW_PAID_RUNS") != "1":
        raise NotAuthorized("EVI_ALLOW_PAID_RUNS=1 is not set for this process; no provider call was made.")
    path = APPROVALS / f"{exp_id}.approval.json"
    if not path.exists():
        raise NotAuthorized(f"No approval file {path}; no provider call was made.")
    a = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    if a.get("experiment_id") != exp_id:
        problems.append("approval names a different experiment")
    if a.get("manifest_sha256") != manifest_sha(exp_dir):
        problems.append("approval is bound to a different manifest hash")
    for k in ("approved_by", "approved_at", "approval_text"):
        if not a.get(k) or "FILL IN" in str(a.get(k)):
            problems.append(f"approval field {k} is missing or unfilled")
    plan = planned_calls(m)
    for cap, need in (("max_serv_calls", plan["serv_calls_max"]), ("max_reppo_evaluations", plan["reppo_evaluations_max"]),
                      ("max_reppo_credits", plan["reppo_credits_max_at_documented_price"])):
        if not isinstance(a.get(cap), int) or a[cap] < need:
            problems.append(f"{cap} must be an integer >= the manifest plan ({need})")
    if problems:
        raise NotAuthorized("Approval rejected: " + "; ".join(problems))
    return a


def template(exp_id: str, exp_dir: Path) -> dict:
    m = json.loads((exp_dir / "manifest.json").read_text(encoding="utf-8"))
    plan = planned_calls(m)
    return {"experiment_id": exp_id, "manifest_sha256": manifest_sha(exp_dir),
            "max_serv_calls": plan["serv_calls_max"], "max_reppo_evaluations": plan["reppo_evaluations_max"],
            "max_reppo_credits": plan["reppo_credits_max_at_documented_price"],
            "approved_by": "FILL IN (person authorizing spend)", "approved_at": "FILL IN (YYYY-MM-DD)",
            "approval_text": "FILL IN (e.g. 'I approve up to N Reppo evaluations / N credits and N SERV calls for this manifest')",
            "note": "Credits and USD are different units. SERV USD cost is unknown. This template is unsigned."}


if __name__ == "__main__":
    from .experiment import PROOF
    cmd, exp = sys.argv[1], sys.argv[2]
    d = PROOF / exp
    if not d.exists():
        d = ROOT / "artifacts" / "holdout" / exp
    if cmd == "template":
        print(json.dumps(template(exp, d), indent=1))
    elif cmd == "check":
        try:
            print(json.dumps(require_approval(exp, d, json.loads((d / "manifest.json").read_text(encoding="utf-8"))), indent=1))
        except NotAuthorized as e:
            print("NOT AUTHORIZED:", e)
            sys.exit(1)
