"""Where does fresh-parse memory go? Peak working set after: imports, model load (initialize_pipeline), conversion.
python scripts/docling_memory_stages.py <pdf> <page> <out.json>   (no provider call; no database)"""
import json
import sys
import time
from pathlib import Path

import psutil

proc = psutil.Process()


def snap(label, t0):
    mi = proc.memory_info()
    peak = getattr(mi, "peak_wset", None)
    if peak is None:
        try:
            peak = next(int(l.split()[1]) * 1024 for l in open("/proc/self/status") if l.startswith("VmHWM"))
        except (OSError, StopIteration):
            peak = 0
    return {"stage": label, "rss_mb": round(mi.rss / 2**20, 1), "peak_mb": round(peak / 2**20, 1), "t": round(time.monotonic() - t0, 1)}


t0 = time.monotonic()
out = [snap("start", t0)]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from docling.datamodel.base_models import InputFormat  # noqa: E402

from evi.parsing import _converter  # noqa: E402

import torch  # noqa: E402,F401
out.append(snap("imports", t0))
conv = _converter()
conv.initialize_pipeline(InputFormat.PDF)
out.append(snap("models_loaded", t0))
page = int(sys.argv[2])
res = conv.convert(sys.argv[1], page_range=(page, page))
out.append(snap("converted", t0))
del res
import gc  # noqa: E402
gc.collect()
out.append(snap("after_gc", t0))
Path(sys.argv[3]).write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out))
