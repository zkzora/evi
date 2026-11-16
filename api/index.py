"""Vercel read-only adapter (archive mode). Serves the EXISTING stored results of the Evi FastAPI app.

Vercel cannot run the Docling worker, so this deployment never processes: EVI_EXECUTION_ENABLED is forced off, no
provider keys are configured, and POST routes return 503 'execution_disabled'. The stored database comes from
data/release-snapshot (verified backup; local session ids scrubbed). This file lives outside backend/evi so the frozen
policy code is untouched.
"""
import ntpath
import os
import shutil
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "release-snapshot"
TMP = Path(os.environ.get("EVI_ARCHIVE_TMP", "/tmp/evi"))

os.environ["EVI_EXECUTION_ENABLED"] = "false"          # forced: archive mode
os.environ["SERV_API_KEY"] = ""
os.environ["REPPO_API_KEY"] = ""
os.environ["EVI_DATA_DIR"] = str(TMP)
os.environ["EVI_SOURCES_DIR"] = str(ROOT / "public" / "sources")
os.environ["EVI_PUBLIC_EVIDENCE"] = str(ROOT / "public" / "evidence" / "experiments.v1.json")
os.environ.setdefault("EVI_ALLOWED_ORIGINS", ",".join(filter(None, [
    f"https://{os.environ['VERCEL_URL']}" if os.environ.get("VERCEL_URL") else "",
    f"https://{os.environ['VERCEL_PROJECT_PRODUCTION_URL']}" if os.environ.get("VERCEL_PROJECT_PRODUCTION_URL") else ""])))

if not (TMP / "evi.sqlite3").exists():
    TMP.mkdir(parents=True, exist_ok=True)
    (TMP / "artifacts").mkdir(exist_ok=True)
    shutil.copy2(SNAP / "evi.sqlite3", TMP / "evi.sqlite3")
    with closing(sqlite3.connect(TMP / "evi.sqlite3")) as c:
        for pid, path in c.execute("SELECT parse_id, artifact_path FROM parses").fetchall():
            name = ntpath.basename(path)            # stored paths may be Windows paths
            c.execute("UPDATE parses SET artifact_path=? WHERE parse_id=?", (str(SNAP / "artifacts" / "parses" / name), pid))
        c.commit()

sys.path.insert(0, str(ROOT / "backend"))
from fastapi.routing import APIRoute  # noqa: E402

from evi import api as evi_api  # noqa: E402

app = evi_api.app


def health():
    h = evi_api.health()
    h["components"].update(docling="not installed (Vercel read-only archive deployment)", worker="not deployed",
                           deployment="vercel-archive")
    h["mode"] = "archive: stored results only; new processing disabled"
    why = ("This public deployment is a read-only archive: it has no Docling worker and no provider keys, "
           "so new extraction and evaluation cannot run here.")
    caps = h.get("capabilities") or {}
    caps["mode"] = "archive"
    for k in ("extraction", "evaluation"):
        if k in caps:
            caps[k].update(state="unavailable", reason=why)
    return h


def documents():
    out = evi_api.documents()
    for d in out["items"]:
        if (ROOT / "public" / "sources" / f"{d['document_id']}.pdf").exists():
            d["source_path"] = f"/sources/{d['document_id']}.pdf"   # static copy, hash-identical to the registered source
    return out


# Override the two read-only views by putting archive-mode routes first.
for path, fn in (("/api/v1/health", health), ("/api/v1/documents", documents)):
    app.router.routes.insert(0, APIRoute(path, fn, methods=["GET"]))
