"""Four-arm experiment harness (docs/20). Inference only — this module never reads reference labels.

  python -m evi.experiment freeze <exp_id> --trials N     # writes the frozen manifest (refuses to overwrite)
  python -m evi.experiment run <exp_id>                   # executes A, B, C, D per document/trial; append-only ledger
  python -m evi.scoring <exp_id>                          # separate scoring step (the only reader of references)
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

from . import db, targets
from .config import ROOT, settings
from .evaluation import build_input, map_result
from .extraction import POLICY_V2, SYSTEM_EXTRACT_V2, OutputRejected, run_extraction_v2
from .providers import ProviderError, reppo_get, reppo_submit
from .revision import REVISION_POLICY, SYSTEM_REVISE_V2, RevisionRefused, run_revision_v2

PROOF = ROOT / "artifacts" / "technical-proof"
REFERENCES = ROOT / "data" / "references" / "references-v1.json"   # hashed only; never opened for reading content here
CODE = ["binding.py", "revision.py", "extraction.py", "targets.py", "checks.py", "evaluation.py", "scoring.py"]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def freeze(exp_id: str, trials: int, seed: int = 20261116) -> dict:
    out = PROOF / exp_id
    if (out / "manifest.json").exists():
        raise SystemExit("manifest already frozen; create a new experiment id to change anything")
    conn = db.connect()
    docs = list(targets.COLUMNS)
    sources, parses = [], []
    for d in docs:
        r = db.row(conn, "SELECT * FROM documents WHERE document_id=?", d)
        p = db.row(conn, "SELECT * FROM parses WHERE document_id=? ORDER BY created_at DESC LIMIT 1", d)
        sources.append({"document_id": d, "sha256": r["sha256"], "source_url": r["source_url"], "physical_pages": json.loads(r["parse_pages"])})
        parses.append({"document_id": d, "parse_id": p["parse_id"], "cache_key": p["cache_key"], "parser_version": p["parser_version"],
                       "docling_artifact_sha256": _sha(Path(p["artifact_path"])), "coverage": p["coverage_note"]})
    rnd = random.Random(seed)
    schedule = []
    for t in range(1, trials + 1):
        order = docs[:]
        rnd.shuffle(order)
        for d in order:
            arms = ["C", "D"]
            rnd.shuffle(arms)
            schedule.append({"trial": t, "document_id": d, "revision_order": arms})
    m = {"experiment_id": exp_id, "schema_version": "evi.experiment-manifest/1", "created_at": db.now(),
         "sources": sources, "parses": parses, "split": targets.SPLIT,
         "exposure_notes": [
             "The builder read all five statement pages (including the AT&T holdout pages) while designing binding rules "
             "(e.g. undated 'Third Quarter' headers) and transcribing references. The holdout is issuer-separated but NOT unseen "
             "by the builder; it is unseen only by the model prompts/policy tuning loop, which used Verizon development runs.",
             "Verizon FY2025/FY2024 were featured in earlier demos; development only."],
         "targets": targets.all_targets(), "target_manifest_sha256": targets.manifest_hash(),
         "eligibility": "all 48 targets eligible; none excluded after inference",
         "reference": {"path": "data/references/references-v1.json", "sha256": _sha(REFERENCES),
                       "provenance": "builder-drafted, source-reviewed, provisional (not independent human gold)"},
         "policies": {"extraction": POLICY_V2, "binding": "binding-v2", "revision": REVISION_POLICY, "targets": targets.TARGET_POLICY_VERSION},
         "prompt_sha256": {"extract_v2": hashlib.sha256(SYSTEM_EXTRACT_V2.encode()).hexdigest(),
                           "revise_v2": hashlib.sha256(SYSTEM_REVISE_V2.encode()).hexdigest()},
         "code_sha256": {f: _sha(Path(__file__).parent / f) for f in CODE if (Path(__file__).parent / f).exists()},
         "model": {"serv_model": settings.serv_model, "observed_revision": "recorded per call in provider_calls"},
         "adapters": {"serv": "chat/completions json_schema strict", "reppo": "POST /api/v1/agents/evals taskType=response"},
         "arms": {"A": "Docling + one SERV v2 extraction", "B": "A + binding certificates (no semantic change)",
                  "C": "A + diagnostics + one SERV revision, no external feedback", "D": "A + diagnostics + real Reppo critique + one SERV revision"},
         "fairness": "C and D branch from the same A version, same model, same evidence packet, same prompt skeleton, one revision call each; "
                     "D additionally receives the Reppo result (the treatment) and costs one evaluation plus waiting time.",
         "trial_plan": {"trials": trials, "seed": seed, "schedule": schedule},
         "caps": {"serv_calls": trials * len(docs) * 3 + 2, "reppo_evals": trials * len(docs), "reppo_poll_timeout_s": 900,
                  "serv_timeout_s": settings.serv_timeout_s},
         "stopping_rules": "Stop only on caps, credential/auth failure, or provider unknown outcomes; never on observed results.",
         "failure_handling": "A failure of A leaves B/C/D for that branch unexecuted (recorded). Provider failure in C/D is an execution "
                             "failure: the parent prediction stands as that arm's output and the failure is reported. Unknown Reppo "
                             "submission outcomes are never resubmitted.",
         "scorer": {"module": "evi/scoring.py", "strict": "amount, currency, scale, duration, fiscal year, end date, start date (claimed or "
                    "application-derived) must equal the reference AND the support certificate must be 'supported'",
                    "precision": "exact Decimal equality", "denominator": "all eligible targets of every executed branch"}}
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
    return m


def _ledger(exp_id: str, rec: dict) -> None:
    rec["at"] = db.now()
    with open(PROOF / exp_id / "ledger.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _new_run(conn, doc: str, parse_id: str, tag: str) -> str:
    rid = db.new_id("run")
    conn.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (rid, doc, parse_id, "queued", "live", POLICY_V2, settings.serv_model, json.dumps({"experiment": tag}), f"experiment:{tag}", db.now()))
    return rid


def _reppo(conn, exp_id: str, version_id: str, timeout_s: int, packet: str = "reppo-packet-v1") -> tuple[str | None, dict]:
    eid = db.new_id("evl")
    conn.execute("INSERT INTO evaluations (evaluation_id, version_id, mode, status, session_id, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                 (eid, version_id, "reppo_live", "submitting", f"experiment:{exp_id}", db.now(), db.now()))
    started = time.monotonic()
    try:
        from .evaluation import build_input_v2
        text = build_input_v2(conn, version_id) if packet == "reppo-packet-v2" else build_input(conn, version_id)
        sub = reppo_submit(conn, input_text=text, job_id=None)
    except ProviderError as e:
        conn.execute("UPDATE evaluations SET status=?, updated_at=? WHERE evaluation_id=?",
                     ("submission_unknown" if e.outcome_unknown else "failed", db.now(), eid))
        return None, {"evaluation_id": eid, "error": str(e), "code": e.code}
    d = sub["data"]
    conn.execute("UPDATE evaluations SET status='pending', eval_id=?, provider_status=?, payload_sha256=?, payload_bytes=?, raw_path=?, updated_at=? "
                 "WHERE evaluation_id=?", (d["id"], d.get("status"), sub["payload_sha256"], sub["payload_bytes"], sub["raw_path"], db.now(), eid))
    status, last = "pending", d
    while time.monotonic() - started < timeout_s:
        time.sleep(10)
        try:
            got = reppo_get(conn, d["id"], job_id=None)
        except ProviderError:
            continue
        last = got["data"]
        status, result = map_result(last)
        conn.execute("UPDATE evaluations SET status=?, provider_status=?, result_json=?, credits_charged=?, raw_path=?, updated_at=? WHERE evaluation_id=?",
                     (status, last.get("status"), json.dumps(result) if result else None, last.get("creditsCharged"), got["raw_path"], db.now(), eid))
        if status != "pending":
            break
    meta = {"evaluation_id": eid, "eval_id": d["id"], "status": status, "provider_status": last.get("status"),
            "credits_charged": last.get("creditsCharged"), "payload_bytes": sub["payload_bytes"],
            "wait_s": round(time.monotonic() - started, 1), "score": (last.get("result") or {}).get("score") if isinstance(last.get("result"), dict) else None}
    return (eid if status == "completed" else None), meta


def _gate(exp_id: str, exp_dir: Path, m: dict, dry_run: bool) -> bool:
    """Spending gate: returns True if the caller may proceed with provider calls."""
    from .authorization import NotAuthorized, planned_calls, require_approval
    plan = planned_calls(m)
    if dry_run:
        print(json.dumps({"dry_run": True, "experiment_id": exp_id, "plan": plan}, indent=1))
        return False
    try:
        require_approval(exp_id, exp_dir, m)
    except NotAuthorized as e:
        raise SystemExit(f"REFUSED: {e}")
    return True


def run(exp_id: str, dry_run: bool = False) -> None:
    m = json.loads((PROOF / exp_id / "manifest.json").read_text(encoding="utf-8"))
    if not _gate(exp_id, PROOF / exp_id, m, dry_run):
        return
    conn = db.connect()
    db.init(conn)
    parse_of = {p["document_id"]: p["parse_id"] for p in m["parses"]}
    done = set()
    lp = PROOF / exp_id / "ledger.jsonl"
    if lp.exists():
        for line in lp.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done.add((r["trial"], r["document_id"], r["arm"]))
    serv_calls = sum(1 for k in done if k[2] in ("A", "C", "D"))
    reppo_evals = sum(1 for k in done if k[2] == "D")
    for item in m["trial_plan"]["schedule"]:
        t, doc = item["trial"], item["document_id"]
        if (t, doc, "A") in done:
            a_rec = next(json.loads(l) for l in lp.read_text(encoding="utf-8").splitlines()
                         if (json.loads(l)["trial"], json.loads(l)["document_id"], json.loads(l)["arm"]) == (t, doc, "A"))
            a_vid = a_rec.get("version_id")
        else:
            if serv_calls >= m["caps"]["serv_calls"]:
                _ledger(exp_id, {"trial": t, "document_id": doc, "arm": "A", "executed": False, "reason": "serv_call_cap"}); continue
            rid = _new_run(conn, doc, parse_of[doc], f"{exp_id}:t{t}")
            t0 = time.monotonic()
            try:
                a_vid = run_extraction_v2(conn, run_id=rid, job_id=None)
                rec = {"executed": True, "version_id": a_vid}
            except (ProviderError, OutputRejected) as e:
                a_vid, rec = None, {"executed": True, "failed": True, "error": str(e)}
            serv_calls += 1
            _ledger(exp_id, {"trial": t, "document_id": doc, "arm": "A", "run_id": rid, "latency_s": round(time.monotonic() - t0, 1), **rec})
            _ledger(exp_id, {"trial": t, "document_id": doc, "arm": "B", "executed": a_vid is not None, "version_id": a_vid,
                             "note": "B = A's prediction with its binding certificates (issued at extraction); no semantic change"})
        if not a_vid:
            for arm in ("C", "D"):
                if (t, doc, arm) not in done:
                    _ledger(exp_id, {"trial": t, "document_id": doc, "arm": arm, "executed": False, "reason": "baseline_A_failed"})
            continue
        for arm in item["revision_order"]:
            if (t, doc, arm) in done:
                continue
            t0 = time.monotonic()
            rec: dict = {"trial": t, "document_id": doc, "arm": arm, "parent_version_id": a_vid}
            evaluation_id = None
            if arm == "D":
                if reppo_evals >= m["caps"]["reppo_evals"]:
                    _ledger(exp_id, {**rec, "executed": False, "reason": "reppo_eval_cap"}); continue
                evaluation_id, meta = _reppo(conn, exp_id, a_vid, m["caps"].get("reppo_poll_timeout_s", 900),
                                             m.get("reppo_packet", "reppo-packet-v1"))
                meta["packet"] = m.get("reppo_packet", "reppo-packet-v1")
                reppo_evals += 1
                rec["reppo"] = meta
                if not evaluation_id:
                    _ledger(exp_id, {**rec, "executed": False, "reason": f"reppo_not_completed:{meta.get('status') or meta.get('code')}",
                                     "latency_s": round(time.monotonic() - t0, 1)}); continue
            if serv_calls >= m["caps"]["serv_calls"]:
                _ledger(exp_id, {**rec, "executed": False, "reason": "serv_call_cap"}); continue
            try:
                receipt = run_revision_v2(conn, version_id=a_vid, arm=arm, evaluation_id=evaluation_id, job_id=None,
                                          idempotency_key=f"{exp_id}:t{t}:{doc}:{arm}")
                rec.update(executed=True, version_id=receipt["child_version_id"], counts=receipt["counts"],
                           proposal_status=receipt["proposal_status"], serv_usage=receipt["serv"]["usage"],
                           receipt_sha256=receipt["content_sha256"])
            except (ProviderError, OutputRejected, RevisionRefused) as e:
                rec.update(executed=True, failed=True, error=str(e), version_id=a_vid,
                           note="execution failure: parent prediction stands as this arm's output")
            serv_calls += 1
            rec["latency_s"] = round(time.monotonic() - t0, 1)
            _ledger(exp_id, rec)
            print(json.dumps({k: rec.get(k) for k in ("trial", "document_id", "arm", "version_id", "counts", "latency_s")}), flush=True)


# ---------------------------------------------------------------- post-hoc policy branch (no new Reppo evaluations)

def freeze_branch(exp_id: str, base_id: str) -> dict:
    """Branch a new revision/checker policy from the SAME saved A versions and the SAME completed real Reppo
    evaluations of a finished experiment. Everything is development material by now; labelled post-hoc."""
    out = PROOF / exp_id
    if (out / "manifest.json").exists():
        raise SystemExit("manifest already frozen")
    from . import binding, revision
    base = json.loads((PROOF / base_id / "manifest.json").read_text(encoding="utf-8"))
    ledger = [json.loads(l) for l in (PROOF / base_id / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    branches = []
    for r in ledger:
        if r["arm"] == "A" and r.get("version_id"):
            d = next((x for x in ledger if x["arm"] == "D" and x["trial"] == r["trial"] and x["document_id"] == r["document_id"]), {})
            branches.append({"trial": r["trial"], "document_id": r["document_id"], "a_version_id": r["version_id"],
                             "evaluation_id": (d.get("reppo") or {}).get("evaluation_id"), "eval_id": (d.get("reppo") or {}).get("eval_id")})
    m = {**base, "experiment_id": exp_id, "created_at": db.now(), "base_experiment": base_id,
         "kind": "post-hoc policy branch (development only)",
         "exposure_notes": base["exposure_notes"] + [
             f"Designed after inspecting {base_id} outcomes (false alarms from section-scope rule; vague diagnostics). "
             "No split here is unseen; results are development evidence, not holdout generalization."],
         "policies": {**base["policies"], "binding": binding.POLICY_VERSION, "revision": revision.REVISION_POLICY},
         "prompt_sha256": {**base["prompt_sha256"], "revise_v2": hashlib.sha256(revision.SYSTEM_REVISE_V2.encode()).hexdigest()},
         "code_sha256": {f: _sha(Path(__file__).parent / f) for f in CODE if (Path(__file__).parent / f).exists()},
         "branches": branches,
         "arms": {**base["arms"], "B": "same A re-certified under the new checker",
                  "C": "same A + new diagnostics + one SERV revision, no feedback",
                  "D": "same A + new diagnostics + the SAME completed real Reppo evaluation of A + one SERV revision"},
         "caps": {"serv_calls": 2 * len(branches), "reppo_evals": 0}}
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
    return m


def run_branch(exp_id: str, dry_run: bool = False) -> None:
    from .certify import certify_version
    m = json.loads((PROOF / exp_id / "manifest.json").read_text(encoding="utf-8"))
    if not _gate(exp_id, PROOF / exp_id, m, dry_run):
        return
    conn = db.connect()
    lp = PROOF / exp_id / "ledger.jsonl"
    done = {(json.loads(l)["trial"], json.loads(l)["document_id"], json.loads(l)["arm"]) for l in lp.read_text(encoding="utf-8").splitlines()} if lp.exists() else set()
    for b in m["branches"]:
        t, doc, a_vid = b["trial"], b["document_id"], b["a_version_id"]
        if (t, doc, "A") not in done:
            _ledger(exp_id, {"trial": t, "document_id": doc, "arm": "A", "executed": True, "version_id": a_vid, "reused_from": m["base_experiment"]})
            out = certify_version(conn, a_vid)
            _ledger(exp_id, {"trial": t, "document_id": doc, "arm": "B", "executed": True, "version_id": a_vid, "check_run_id": out["check_run_id"]})
        for arm in ("C", "D"):
            if (t, doc, arm) in done:
                continue
            rec = {"trial": t, "document_id": doc, "arm": arm, "parent_version_id": a_vid}
            if arm == "D" and not b["evaluation_id"]:
                _ledger(exp_id, {**rec, "executed": False, "reason": "no completed base evaluation"}); continue
            t0 = time.monotonic()
            try:
                rc = run_revision_v2(conn, version_id=a_vid, arm=arm, evaluation_id=b["evaluation_id"] if arm == "D" else None,
                                     job_id=None, idempotency_key=f"{exp_id}:t{t}:{doc}:{arm}")
                rec.update(executed=True, version_id=rc["child_version_id"], counts=rc["counts"], proposal_status=rc["proposal_status"],
                           receipt_sha256=rc["content_sha256"], reused_reppo_eval_id=b["eval_id"] if arm == "D" else None)
            except (ProviderError, OutputRejected, RevisionRefused) as e:
                rec.update(executed=True, failed=True, error=str(e), version_id=a_vid)
            rec["latency_s"] = round(time.monotonic() - t0, 1)
            _ledger(exp_id, rec)
            print(json.dumps({k: rec.get(k) for k in ("trial", "document_id", "arm", "version_id", "counts", "latency_s")}), flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["freeze"]:
        n = int(a[a.index("--trials") + 1]) if "--trials" in a else 1
        print(json.dumps(freeze(a[1], n)["trial_plan"], indent=1))
    elif a[:1] == ["run"]:
        run(a[1], dry_run="--dry-run" in a)
    elif a[:1] == ["branch"]:
        print(json.dumps(freeze_branch(a[1], a[a.index("--from") + 1])["policies"]))
    elif a[:1] == ["run-branch"]:
        run_branch(a[1], dry_run="--dry-run" in a)
    else:
        print(__doc__)

