# Evi — Reduce Docling memory without removing features

Work in `C:\Evidence\EvidenceGrid-Claude-Code-Handoff`. Implement and measure a narrowly scoped memory optimization for the existing Docling upload pipeline. Do not stop at suggestions. Time is limited: test a small number of justified changes, preserve working behavior and report the actual result.

## Required outcome

Try to make a fresh, single-page uploaded-PDF parse work within the current Railway container limit without changing the model, removing source verification, weakening table extraction or raising hosting costs. Longer processing is an acceptable trade-off if job recovery and reasonable timeouts remain usable.

Do not promise that the existing 1 GB limit is sufficient. Success requires a measured fresh parse, equivalent evidence and a complete public path. If preserving the pipeline cannot fit safely, report the measured floor and the smallest justified resource increase. Do not silently downgrade quality to declare success.

## Inspect current state first

Read applicable AGENTS.md, CLAUDE.md, brand.md and the current files:

- `docs/DOCLING-HOST-FIX.md`, `docs/JUDGE-UPLOAD.md`, `docs/LIVE-DEPLOYMENT-STATUS.md` and the acceptance report.
- `backend/evi/parsing.py`, `worker.py`, `uploads.py`, `jobs.py`, `allowance.py`, the Dockerfile and deployment entrypoint.
- The installed Docling implementation/options, current tests, `artifacts/judge-upload/` and existing model caches.
- README.md and `docs/EVIDENCE-INDEX.json`, which have separate ongoing documentation changes. Preserve them and other agents' uncommitted work. Commit only changes belonging to this task.

Measured Railway evidence from November 16:

- Existing project `reasonable-benevolence`, service `evi`, production environment.
- Container memory limit approximately **1024 MB**; observed peak **1023.99 MB**.
- `/data` volume limit **500 MB**, current usage approximately **346 MB** in that snapshot.
- Model downloads previously filled the data volume. The required models are now baked into the image, outside `/data`.
- Upload/preview/ownership work; fresh hosted parsing restarts the container before SERV. Recorded registered-report extractions reused existing parses.

These facts strongly suggest memory exhaustion; an explicit kernel OOM record has not been obtained. Recheck current metrics before assuming the configuration is unchanged. Do not expose secrets in diagnostics.

## Preserve these invariants

- Same Docling version, layout model, **TableFormer ACCURATE**, cell matching and numerical precision. No FAST model, quantization, reduced image resolution or replacement PDF reader in this task.
- One selected physical page on the original PDF, one active processing job, one replica. These constraints already exist; do not present them as newly achieved savings.
- OCR remains off for the current supported text-native PDF scope. No changes to metric/period/unit definitions, null-date handling, certificates or revision acceptance rules.
- Keep original PDF coordinates, source hashes, private upload ownership, 24-hour retention and server-side spending safeguards.
- Do not remove API features, exports, Reppo integration, dashboard views or public source inspection.
- No Supabase migration, new cloud project/service, paid-plan change, infrastructure purchase, swap-file experiment or public processing on a judge's computer.
- No original experiment, reference, certificate, provider record or saved score may be rewritten.

## 1. Establish an honest baseline

Use isolated scratch state, a copy of a registered development PDF and the existing installed environment/models. Do not use planned unseen holdout documents. Do not trigger SERV or Reppo to measure parsing.

Measure a **fresh** baseline parse and a fresh candidate in separate process lifetimes; a cache hit is not a memory optimization. Record:

- OS/container, Python/Docling versions, CPU configuration, model identifiers or available weight hashes.
- Exact selected page, source hash, cache hit/miss and effective parser/runtime settings.
- Wall time, peak process-tree memory, idle memory and memory after parsing.
- On Linux, cgroup current/peak/limit and available OOM counters where accessible. Compare total container memory, including API/worker, to the actual host limit; child RSS alone is insufficient.
- Parsed tables, cells, text, headers, spans, page dimensions, bounding boxes and derived target columns.

Windows working set/commit is useful local evidence but does not prove that a Linux 1 GB container will succeed. If Docker is available, use an isolated container with the matching resource limit. If not, clearly label the untested container condition instead of simulating a pass. Do not repeatedly download large model weights.

## 2. Try execution changes before changing architecture

Start with one explicit low-memory execution profile:

1. **One inference thread:** `DOCLING_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, applied before numerical libraries initialize. Confirm effective settings, not merely the environment strings.
2. **Small batches and bounded queues:** where supported by the installed Docling API, set layout/table batch sizes to 1 and minimize inter-stage buffering. Check actual pipeline behavior and avoid queue deadlocks. Because only one page is already processed, these changes may save little; measure rather than claiming a gain.
3. **Avoid unnecessary retention:** verify optional generated image/export/enrichment settings are already off; preserve all table cells, text and coordinates required by Evi. Existing disabled defaults are not a new optimization. Consider a conservative Linux allocator setting only if profiling supports it; record the setting and measured effect.
4. **Parse-process lifetime, only if needed:** if model allocations remain resident in the long-lived worker, use a narrowly scoped child parser process that exits after persisting a complete artifact. Keep the parent worker/job heartbeat, lease, timeout, cancellation and error handling intact. Handle child death without corrupting state or blindly retrying a crash loop.

A subprocess releases memory after its exit; it does NOT automatically reduce the first-parse peak or escape the container's shared memory limit. Do not add it unless the measurement justifies it. Keep process IPC small: write artifacts atomically and pass identifiers/paths rather than duplicating a large document object between processes. Do not start more parser workers.

Model weights and framework imports impose a memory floor. If the first candidate does not meaningfully reduce the measured peak, identify where the remaining memory goes before trying more knobs. Avoid a broad optimization grid or unrelated dependency upgrades.

## 3. Prove that the evidence still agrees

Compare fresh baseline and optimized output, initially on one representative page. If the candidate improves memory, validate representative annual and interim layouts, including the offset FY2024 page and AT&T's unprinted exact dates.

Compare semantic content rather than generated IDs/timestamps:

- Table count, metric-row cells, printed amounts, relevant header text, row/column spans, year/duration groups and applicable unit notes.
- Physical pages and page dimensions; bounding boxes must remain suitable for original-PDF highlights. Explain any coordinate differences. Do not widen tolerances to hide a regression.
- Derived targets, source readings, obligation outcomes and support/partial-context results under the same checker policy. Do not repair outputs manually for the comparison.

Do not claim bit-for-bit equivalence merely because the model name is unchanged. Preserve model semantics and test observed results. A meaningful extraction or context regression rejects the candidate.

Record all effective parse/execution settings. If configuration changes can alter output, use a new explicit parse-profile/cache identity so old cached parses cannot masquerade as optimized fresh results. Preserve legacy cache/evidence IDs and verification of old certificates. Do not relabel or backfill original artifacts.

## 4. Integrate and verify only the justified candidate

Add focused tests for effective runtime options, profile-aware caching/legacy compatibility and any changed child-process lifecycle. Test timeout/crash handling and partial-artifact cleanup on isolated state. Use the existing upload/source/revision tests to detect regressions. Run the relevant backend suite and production build; run frontend tests if UI/job behavior changes.

Only deploy a candidate to the existing authorized Vercel/Railway projects after measurement and equivalence checks support it. Keep SQLite, one local volume and one replica. Preserve the working registered-report path and rollback state. Do not increase limits or spend on a different host without authorization.

Treat **approximately 800 MB total container peak** as a useful headroom target under the observed 1 GB ceiling, not an asserted property. A single run peaking immediately below the hard limit is not robust acceptance. If headroom remains insufficient, keep fresh-upload processing explicitly unavailable or accurately limited while stored/registered results remain usable; report the resource requirement instead of repeatedly crashing the public service.

For hosted acceptance, first verify the fresh Docling stage under the same quality configuration. A full upload smoke run may make at most **one new SERV call**, only when covered by the owner's existing explicit allowance and remaining quota. No automatic Reppo submission and no new experimental run. If a paid submission's outcome is unknown, reconcile it without retrying it blindly.

Confirm the same job after reload, correct original-PDF highlights, actual certificate states, fresh-versus-cached parse labels and post-run container memory. Do not claim success from upload/preview alone, an unsupported-page early exit, a saved parse or a mocked provider response.

## Deliverables and stopping rule

- Working, narrowly scoped implementation with a documented rollback/profile switch.
- `docs/DOCLING-MEMORY-RESULTS.md`: baseline/candidate comparison, effective settings, source/layout equivalence, latency, memory measurement method and total-container fit or failure.
- Sanitized raw measurements and comparison artifacts under `artifacts/docling-memory/`.
- Update upload instructions, acceptance/deployment status, README and evidence index only to the level actually established. Preserve their independent existing edits.
- If code changes invalidate a future holdout freeze, record that administratively without opening holdout sources or changing old experiment results.

Stop after one defensible optimization path and its necessary validation. If unchanged models cannot fit with adequate headroom, say so and provide the smallest measured hosting requirement. Do not pursue silent quality downgrades to meet 1 GB.

Final report: what changed; before/after total peak RAM and latency on the same page/environment; evidence equivalence; whether Linux/container and public upload completion were actually tested; exact SERV/Reppo usage; remaining limits; and whether the current host is sufficient. State plainly if the optimization saved RAM but did not solve the crash.
