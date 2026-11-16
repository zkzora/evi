# Evi — Technical-depth continuation prompt

Use this prompt after or together with `CLAUDE-CODE-FULL-PROMPT.md`. Open `C:\Evidence\EvidenceGrid-Claude-Code-Handoff` in Claude Code. The two accompanying specifications are mandatory parts of this prompt:

- `docs/19-semantic-binding-and-revision-spec.md`
- `docs/20-ablation-and-proof-protocol.md`

This is an implementation instruction for technical depth and inspectable evidence. It does not promise an award and does not authorize unrelated product expansion.

---

Continue implementing **Evi** in the existing project. Deepen its actual period/unit verification and feedback-driven correction mechanism, then demonstrate what the implementation can and cannot establish. Do not substitute a longer architecture document, more screens, or a larger source count for the working mechanism.

## 1. Inspect the current state before acting

Read applicable AGENTS.md files, the latest sections of CLAUDE.md, brand.md, README.md, the full continuation prompt, and documents 18–20. Read docs/DECISIONS.md before relying on older provider/API assumptions. Inspect actual source, database schema, tests, artifacts, current processes, and uncommitted changes without printing secrets.

As of this prompt's preparation on November 16, 2026, a `backend/evi/` implementation and backend tests exist. They include parsing, extraction, deterministic checks, evaluation adapters, durable jobs, and a worker. The old handoff's claim that there is no backend is historical. **Inspect and extend the current implementation; do not recreate it.** File presence and an existing run in a browser do not establish that every stage has been independently verified.

### Latest execution baseline — November 16, 2026

The user supplied a completed-slice report, also recorded in `artifacts/backend-status.md`. Preserve this progress:

- Real Docling 2.150.1 statement-page parses exist for Verizon FY2025 physical page 52 and FY2024 page 54, with explicitly limited page coverage.
- Parse IDs in the status artifact: `parse_1adbf9bc185db4c476c1` (FY2025) and `parse_c8ca25aa4dd29fc48c2c` (FY2024).
- The source-box audit reports 202 table-cell boxes with explicitly documented dash-glyph exceptions and CropBox offset handling. Read the actual assertions/exceptions; do not omit those qualifications.
- Actual SERV `gpt-5.4-mini` outputs are stored as `ver_b9c64dad515d_1` and `ver_eb2ca88e293b_1`, with three metrics each and 24 passing checks per report under the corrected checker. The earlier `ver_b76bceac016e_1` remains unchanged under its historical checks.
- Known checker bugs already fixed: a per-share exception was applied to every row; a missing period end date passed instead of remaining unknown. Preserve their regression coverage.
- The reported completed browser path is no-login Process → actual parse/extraction → source-linked facts/highlights/deep links. Reported tests are 41 backend and 15 frontend, plus a successful production build. Verify current results as appropriate; these are prior execution records, not a new independent rerun by this prompt's author.
- Reppo has not run live and no real critique-driven revision has executed. At the recorded status no Reppo key was configured; recheck current ignored configuration without printing values.
- Only two of the required 4–6 USD PDF reports are registered for the evaluation, no benchmark is complete, and deployment remains local.
- SERV secrets were moved into ignored `backend/.env`; do not move them back into examples or frontend variables. Existing keys/values must not be printed.

Start after the working vertical slice. Reuse real source/parse/output artifacts for audit, certificates and replay. Do not waste paid calls regenerating a correct baseline solely to restate that the first slice works. Make fresh calls only for a defined changed mechanism, provider integration or frozen experiment within its budget.

A bbox containing its printed text is evidence of geometric alignment, not proof that the value has the correct governing period/unit. Twenty-four passing checks are current checker outcomes, not independent gold labels or evidence that Reppo improves anything. The technical extension must establish those separate claims.

Review these specific areas against the new specifications:

| Current area | What to inspect and establish |
| --- | --- |
| `backend/evi/parsing.py` | Table/cell spans, physical-page mapping, provenance fidelity, coverage, incomplete parse/cache behavior |
| `backend/evi/checks.py` | Whether correct-sounding text anywhere in a packet can be mistaken for the applicable column/table context |
| `backend/evi/extraction.py` | Annual-only target assumptions, candidate binding, supported uncertainty, immutable outputs, revision acceptance |
| `backend/evi/evaluation.py` and `providers.py` | Current provider contracts, explicit completion status, optional/missing scores, original evaluation/version identity |
| `backend/evi/jobs.py`, `worker.py`, `db.py` | Leases, duplicate submissions, restart recovery, durable provider outcomes and budgets |
| `backend/tests/` | What assertions use real source evidence versus mocks or controlled examples |
| `src/types.ts`, `src/api.ts`, `src/App.tsx` | Actual current wire schemas and process/readiness behavior; do not revert recent integration work |

These are audit targets, not blanket claims that every issue exists. Read the code and record evidence before declaring an implementation defective.

## 2. Preserve the product and distinguish the evidence layers

The user is a financial analyst comparing reported monetary figures. The failure is a correct amount assigned to the wrong reporting interval, monetary scale, or metric scope. The analyst bears the downstream comparison/rework risk; no measured dollar loss has been established.

The strongest alternatives include manual review, structured SEC/XBRL context, and a competent parser plus one-shot model. The differentiation to prove is supported context binding and controlled revision on **unstructured public PDFs**, not the existence of a table or a provider call.

Preserve:

- Evi name/logo, English UI, USD-only public presentation, original source currencies, no unrecorded FX conversion.
- Top navigation with Home first; existing six main entries; no sidebar or rejected organization/workspace selector card.
- Direct judge access without sign-in or provider keys.
- Three core metrics, one telecom/connectivity sector, 4–6 actual USD reports for the bounded PDF proof.
- Docling as the parser, SERV for semantic interpretation/revision, Reppo for real external feedback, deterministic code for arithmetic/constraints/scoring.
- Genuine source snapshots, live AI runs, controlled tests, reference annotations, and benchmark results as distinct provenance categories.
- Existing working UI, APIs, source downloads, provider artifacts, and original versions.

Do not build a graph database, blockchain attestation, new OCR system, training pipeline, general document chat, restatement engine, or extra sponsor integration. The evidence graph in document 19 is a compact typed domain representation backed by the existing storage/artifact system.

## 3. Implement the context-binding mechanism

Implement document 19's source nodes, applicability relations, candidate tuples, obligations, deterministic resolution, and machine-readable support certificates.

The critical distinction is:

`valid source ID` does not imply `evidence applies to this value`.

The resolver must establish the relationship from the value cell to its actual row label, column hierarchy, duration heading, currency/scale statement, and consolidation scope. A matching year or the word “millions” elsewhere on a page is insufficient.

Use SERV to propose interpretations and candidate evidence. Use deterministic typed constraints to validate allowed associations and explicit ambiguity. Do not ask the model to certify its own output through a confidence score.

Preserve all plausible candidates needed to explain a genuine ambiguity. If the supported candidates disagree materially, expose unresolved/conflict state; do not break ties by highest model confidence, first text match, or desired benchmark answer. Do not abstain from clearly supported ordinary cases.

Do not apply a fixed “annual / latest year” target to interim reports. Target selection must be explicit, source-backed, and part of the frozen manifest/policy, with current/comparative and 3-/9-month columns independently addressable.

Derive exact period boundaries only from applicable source statements and supported fiscal-calendar rules. Browser day-band labels are not the production date algorithm. Handle local unit exceptions, per-share rows, footnotes, monetary versus non-monetary rows, explicit negative values, missing versus zero, and ambiguous locale without silently inventing values.

## 4. Make revision acceptance field-aware and evidence-aware

Inspect the current acceptance gate, including any “no failing checks and at least as many passing checks” rule.

A count of passed checks is not a sufficient revision invariant. A revision could increase that count by dropping a target, erasing an amount/evidence, changing check applicability, or replacing a meaningful fact with an abstention. Prevent that route without forbidding a necessary honest unresolved result.

Implement document 19's allowed-field patch schema, immutable target keys, old/new support mapping, obligation-level comparison, conflict-aware abstention, and explicit accepted/rejected/unchanged/unresolved outcomes.

A Reppo critique is a hypothesis. It cannot authorize annualization, inferred FX, source mutation, changing metric scope, replacing parent identities, or hiding a regression. Validate its cited evidence, current provider completion state, exact evaluated version, and source version on the server.

Always retain the original automated baseline. Save a child receipt even when a bounded revision is unchanged or rejected. Do not silently repair the baseline or hide rejected proposals.

## 5. Produce a machine-checkable explanation, not hidden reasoning

For a selected fact, expose the actual supporting nodes, applicable scope relations, normalized operands, exact interval derivation, satisfied/failed/unknown obligations, policy version, and revision changes.

Save observable structured decisions and tool inputs/outputs. Do not require or expose a model's private chain of thought. A source-support certificate establishes satisfaction of documented application rules; it does not prove the issuer's accounting, universal semantic correctness, or tamper-proof publication.

Provide a local verifier CLI/function that can re-read the registered original source/parse/certificate and fail on altered values, foreign evidence, invalid relations, incorrect normalization, or unsupported period claims. Reuse the same domain semantics rather than a second incompatible verifier. Anchor its tests in independent expected outcomes from rendered sources and hand-derived cases.

Make the existing Workspace evidence view sufficient to inspect these artifacts. Add compact details where needed; do not turn this into a menu expansion.

## 6. Run a real ablation that can defeat the hypothesis

Implement document 20's pre-registered four-arm protocol. The no-Reppo revision arm is **required before claiming that Reppo itself adds value**:

- **A — Competent initial extraction:** Docling + SERV, with applicable context present.
- **B — Checks only:** the same saved prediction plus deterministic diagnostics; do not silently replace its semantic prediction.
- **C — Checks + SERV revision:** same initial prediction, no external evaluator feedback.
- **D — Checks + real Reppo + SERV revision:** same initial prediction, with the real critique as the treatment.

For C versus D, match the initial evidence, model configuration, revision-call cap, and retrieval opportunity. The evaluator call is an added treatment/cost and must be accounted for, not called “identical total compute.” If D receives additional source information, explicitly control or disclose that advantage.

Pre-freeze split, target eligibility, reference provenance, policy/prompt/model settings, scorer, seeds where supported, trial count, stopping rules, and budgets before holdout results are inspected. Use issuer/template-separated holdout where possible. Do not use public SEC snapshot values as hidden answers in the PDF inference path.

Report paired outcome counts, regressions, missing/unresolved coverage, source-support correctness, latency, retries, all model/evaluator usage, and actual or explicitly unknown cost. Keep repeated runs grouped by document; a few PDFs are not hundreds of independent samples.

A null or negative result is valid evidence. If C performs as well as D, report that. If the baseline is already correct, preserve the result rather than corrupting it to create an improvement story.

## 7. Separate natural extraction, controlled mechanism tests, and operational tests

Create the test/artifact families in document 20.

Natural extraction: untouched real reports, frozen targets/reference, complete original predictions, all target outcomes retained.

Controlled mechanism tests: a wrong period/scale/column, a nearby irrelevant heading, bad evidence, malicious critique, legitimate correction, and supported positive controls. Label mutations and derived documents explicitly; never include their success rate in natural accuracy.

Metamorphic checks: equivalent input ordering or irrelevant neighboring context should not change a supported binding; actual semantic changes must invalidate the old certificate. Reparse/rescope derived PDFs with new hashes where needed. Do not assume Docling itself is invariant to arbitrary layout changes.

Operational failure injection: duplicate click, concurrent job claim, expired lease, interruption around artifact/database persistence, provider submission timeout, pending evaluation across restart, and budget reservation uncertainty. Use isolated temporary data and bounded fake provider transports for these fault tests. Keep them distinct from real provider smoke tests.

Do not claim exactly-once external side effects unless the provider actually supplies the necessary idempotency/reconciliation semantics. Preserve unknown external outcomes and prevent unsafe automatic paid resubmissions.

## 8. Use the existing stack and current provider contracts

Fit the mechanism into the current Python/FastAPI/Pydantic/database/worker implementation and existing frontend contracts. Prefer additive versioned artifacts/fields and small migrations. Avoid an unnecessary rewrite.

Current local decision notes describe provider behavior that differs from older handoff examples. Verify authoritative docs and actual authenticated response shapes before implementing changes; do not copy historical endpoints, settlement names, model IDs, or score scales from stale documents. Do not revert a working new adapter merely to match an older prompt.

Missing evaluator scores are unknown/missing, not numeric zero; missing usage or credit data is unknown, not free. Do not fabricate a normalized score or call provider opinion measured accuracy. Version adapters and preserve raw redacted responses.

Keep all secrets server-side. Use available ignored configuration without printing values. Missing credentials do not block graph/binding/resolver/tests/evaluation harness/worker work. Ask only for indispensable missing configuration, after completing the independent work, and never request secret values in chat.

## 9. Work in milestones with observable gates

**Milestone 1 — Actual-state audit and first source binding**

Produce a concise gap table with file/function evidence. Reuse a verified existing Verizon parse and saved SERV version; add context nodes/relations, bind the three metric targets, and issue support certificates with actual PDF provenance. Demonstrate a legitimate supported fact and an explicitly controlled contradictory period interpretation without corrupting the stored real baseline. Reparse or re-extract only when an actual change requires it.

**Milestone 2 — Bounded revision**

Complete the remaining Reppo integration using its actual current API when a server key is available; do not repeat SERV setup or use simulated verdicts as live feedback. Validate one proposed change with its field support and obligation transition; preserve a rejection/no-change case honestly. Show original/child/read-back artifacts. Do not claim an improved natural prediction unless one actually improved.

**Milestone 3 — Independent proof and durability**

Execute source-anchor, ambiguity, controlled adversarial, metamorphic, and operational fault checks. Repair consequential failures. Produce a replay/verification command that another person can run without reading the whole codebase.

**Milestone 4 — Frozen experiment**

Run the bounded corpus protocol, matched C/D revision comparison, configured repeats, honest cost/latency accounting, and per-document reports. When credentials or annotation review prevent a required arm, mark it unexecuted and continue the other required work; do not substitute fake verdicts.

**Milestone 5 — Judge inspection**

Retain the current no-login flow. A reviewer should reach one real fact, inspect its source/context, see why a proposed interpretation is valid/invalid/unresolved, inspect feedback/revision lineage, and open the reproduction artifacts. Keep actual limitations visible at the point of use.

Do not stop after writing any of these milestone descriptions. Implement and verify them in the existing project.

## 10. Deliverables and completion criteria

Deliver implementation plus:

- `docs/TECHNICAL-DEPTH-IMPLEMENTATION.md`: implemented mechanisms, invariants, supported cases, unsupported cases, and real code/artifact links.
- `docs/PROOF-REPORT.md`: source facts, expected versus observed outcomes, artifact IDs/hashes, commands, actual provider execution, and limits.
- A frozen experiment manifest and machine-readable per-target/trial outcomes, with the four-arm report when executed.
- A field-level revision receipt and source-support certificates for real examples.
- A meaningful verification command and test results, including the actual real-PDF path.
- Current browser proof/screenshots without secrets or the rejected UI pattern.
- Updated run instructions and a concise claim/evidence ledger.

Mark each claim as **implemented**, **executed**, **source-reviewed**, **measured**, or **unverified** as appropriate. Do not collapse those labels into “done.” A test-double integration is not a real provider call. A provider call is not evidence of improvement. A support certificate is not independent accounting truth. Source-row count is not processing throughput or benchmark sample size.

If a required dependency prevents completion, provide the finished independent artifacts and name exactly what execution is missing. Do not expand scope or invent a winning result to compensate.

Start by inspecting the current code and returning a short gap table. Then implement the first supported source binding and its independently checkable result.
