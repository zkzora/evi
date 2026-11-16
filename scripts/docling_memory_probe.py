"""Fresh Docling parse memory/latency probe (one parse per process lifetime; no provider call).

  python scripts/docling_memory_probe.py <profile> <registered_document_id> <physical_page> <out.json>

profile: "default" (current production settings) or "lowmem-v1" (EVI_PARSE_PROFILE). Threading environment variables
for lowmem-v1 are set HERE, before torch/numpy are imported, as they would be by the container environment.
The PDF is uploaded as a copy into an ISOLATED temporary data dir, so the parse is always a cache miss.
Peak memory: Windows peak working set (exact, OS-tracked) or Linux VmHWM/cgroup where available; plus a 20 ms RSS sampler.
"""
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

PROFILE, DOC, PAGE, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), Path(sys.argv[4])
if PROFILE == "lowmem-v1":
    for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "DOCLING_NUM_THREADS"):
        os.environ[k] = "1"
os.environ["EVI_PARSE_PROFILE"] = PROFILE
os.environ["EVI_DATA_DIR"] = tempfile.mkdtemp(prefix="evi-memprobe-")
os.environ["EVI_EXECUTION_ENABLED"] = "false"
os.environ["SERV_API_KEY"] = ""
os.environ["REPPO_API_KEY"] = ""
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import psutil  # noqa: E402

proc = psutil.Process()
peak = {"rss": 0}
stop = threading.Event()


def sampler():
    while not stop.wait(0.02):
        try:
            r = sum(p.memory_info().rss for p in [proc] + proc.children(recursive=True))
            peak["rss"] = max(peak["rss"], r)
        except psutil.Error:
            pass


def mb(n):
    return round(n / 1024 / 1024, 1)


def os_peak():
    mi = proc.memory_info()
    if hasattr(mi, "peak_wset"):
        return {"kind": "windows_peak_working_set", "mb": mb(mi.peak_wset)}
    try:
        for line in open("/proc/self/status"):
            if line.startswith("VmHWM"):
                return {"kind": "linux_VmHWM", "mb": round(int(line.split()[1]) / 1024, 1)}
    except OSError:
        pass
    return None


threading.Thread(target=sampler, daemon=True).start()
t0 = time.monotonic()
from fastapi.testclient import TestClient  # noqa: E402

from evi import api, db, uploads  # noqa: E402
from evi.corpus import REGISTERED  # noqa: E402
from evi import parsing  # noqa: E402

entry = next(r for r in REGISTERED if r["document_id"] == DOC)
pdf = (ROOT / "public" / "sources" / entry["file_name"]).read_bytes()
with TestClient(api.app) as cl:
    did = cl.post("/api/v1/uploads", files={"file": ("probe.pdf", pdf, "application/pdf")},
                  headers={"Origin": "http://127.0.0.1:5173"}).json()["document_id"]
c = db.connect()
import torch  # noqa: E402

after_imports = proc.memory_info().rss
t1 = time.monotonic()
pid = parsing.parse_document(c, did, [PAGE])
t2 = time.monotonic()
after_parse = proc.memory_info().rss
stop.set()
p = db.row(c, "SELECT * FROM parses WHERE parse_id=?", pid)
cells = db.rows(c, "SELECT text, page_number, table_index, row_index, col_index, row_span, col_span, is_column_header, "
                   "bbox_json, page_width, page_height FROM evidence WHERE parse_id=? AND kind='table_cell' "
                   "ORDER BY table_index, row_index, col_index", pid)
texts = db.rows(c, "SELECT text, page_number, bbox_json FROM evidence WHERE parse_id=? AND kind='text' ORDER BY evidence_id", pid)
cols, derivation = uploads.derive_columns(c, did, pid)
out = {
    "profile": PROFILE, "document_copy_of": DOC, "physical_page": PAGE, "source_sha256": entry["sha256"],
    "cache_hit": False, "python": sys.version.split()[0], "platform": sys.platform, "cpu_count": os.cpu_count(),
    "torch": torch.__version__, "torch_threads": torch.get_num_threads(),
    "env": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "DOCLING_NUM_THREADS")},
    "effective_settings": json.loads(p["config_json"]),
    "parse_seconds": round(t2 - t1, 2), "process_seconds_total": round(t2 - t0, 2),
    "rss_after_imports_mb": mb(after_imports), "rss_after_parse_mb": mb(after_parse),
    "peak_rss_sampled_mb": mb(peak["rss"]), "peak_os": os_peak(),
    "tables": p["table_count"], "evidence_items": p["evidence_count"],
    "cells": [{k: x[k] for k in ("text", "page_number", "table_index", "row_index", "col_index", "row_span", "col_span",
                                 "is_column_header")} | {"bbox": json.loads(x["bbox_json"]) if x["bbox_json"] else None,
                                                         "page": [x["page_width"], x["page_height"]]} for x in cells],
    "texts": [{"text": x["text"], "page": x["page_number"], "bbox": json.loads(x["bbox_json"]) if x["bbox_json"] else None}
              for x in texts],
    "derived_columns": cols, "derivation": derivation,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps({k: out[k] for k in ("profile", "parse_seconds", "rss_after_imports_mb", "rss_after_parse_mb",
                                      "peak_rss_sampled_mb", "peak_os", "torch_threads", "tables", "evidence_items",
                                      "derived_columns")}))
