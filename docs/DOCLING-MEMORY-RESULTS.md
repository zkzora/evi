# Docling memory results (2026-11-16)

**Result: no deployable improvement. The unchanged Docling models do not fit the current 1 GB Railway container; uploaded-PDF processing remains unavailable on this host.** Nothing was deployed from this task. No SERV or Reppo calls were made.

## Method

- Fresh parse in a new process for every measurement (isolated temporary data dir, uploaded copy → cache miss). Page: physical page 54 of a copy of the registered development report `verizon-fy2024.pdf` (SHA-256 `05ad83ec…`), the page whose hosted parse restarted the Railway container.
- Docling 2.150.1, torch 2.15.0, Python 3.12, TableFormer ACCURATE, cell matching on, OCR off, float32. Local machine: Windows 11, 16 logical CPUs. Peak = OS-tracked peak working set of the parse process (`psutil … peak_wset`), plus a 20 ms RSS sampler.
- **Not tested:** a Linux container with a 1 GB cgroup limit (Docker is not available on this machine). Windows working set is evidence, not proof of Linux behaviour.
- Scripts: `scripts/docling_memory_probe.py`, `scripts/docling_memory_stages.py`. Raw outputs: `artifacts/docling-memory/`.

## Measurements

| Profile | Threads / batch / queue | Parse time | Process peak | RSS after parse | Tables / evidence | Derived columns |
|---|---|---|---|---|---|---|
| default (production) | 4 / 4 / 100 | 144.4 s | **1,001 MB** | 878 MB | 1 / 106 | 12M 2024, 12M 2023 |
| lowmem-v1 (candidate) | 1 / 1 / 1 | 132.1 s | **1,080 MB** | 952 MB | 1 / 106 | 12M 2024, 12M 2023 |

Equivalence (`local-equivalence-default-vs-lowmem.json`): identical cell keys (101), identical cell text and spans, maximum bounding-box difference 0.0 pt, identical text items and derived columns. The candidate is output-equivalent but **does not reduce memory** (the difference is within run-to-run variation).

Stage breakdown, default profile (`local-stages-default.json`):

| Stage | RSS | Peak so far |
|---|---|---|
| Python + torch + Docling imports | 259 MB | 259 MB |
| Models loaded (layout + TableFormer ACCURATE) | 853 MB | **1,056 MB** |
| One page converted | 985 MB | 1,056 MB |

The peak is set by **loading the model weights**, before any page is processed. Thread count, batch size and queue size cannot change that, and a child parser process would hit the same peak inside the same container (alongside the API process, roughly 100–150 MB). This matches the Railway metric peak of 1,023.99 MB of 1,024 MB recorded in `docs/DOCLING-HOST-FIX.md`.

## Decision

- `lowmem-v1` was implemented only in a temporary experimental build for these measurements and then reverted; production parsing code and the holdout freeze `holdout-2026-11-16-f` are unchanged.
- Not attempted (excluded by scope, would change quality): FAST TableFormer, quantisation, lower image resolution, a different PDF reader.
- **Smallest justified resource increase:** measured parse-process floor ≈ 1.06 GB + API/worker ≈ 0.15 GB ≈ 1.2 GB with no headroom. Recommend a **2 GB** memory limit for the existing service (one replica, one active job) to stay near the ~80% headroom target. This is a plan/resource decision for the owner; nothing was changed.
- Until then, uploaded-page processing is not available on the public host; upload, preview, ownership and all stored/registered results keep working, and a job that repeatedly stops the worker fails with that reason instead of looping.
