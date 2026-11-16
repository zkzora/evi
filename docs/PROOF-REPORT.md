# Evi — proof report (2026-11-16)

Status labels: **implemented** · **executed** (ran on real sources and real providers) · **measured** (scored against frozen references) · **unverified**.
Reference provenance for every measured number: **builder-drafted, source-reviewed, provisional — not independent human gold** (`data/references/references-v1.json`, sha256 `cb02c74f…41942`).

## 1. Corpus (executed)

| Document | Source (issuer host) | SHA-256 (prefix) | Statement page | Docling parse | Split |
|---|---|---|---|---|---|
| verizon-fy2025 | verizon.com 2025 10-K | c804f30d… | p52 | parse_1adbf9bc185db4c476c1 | development |
| verizon-fy2024 | verizon.com 2024 10-K | 05ad83ec… | p54 | parse_c8ca25aa4dd29fc48c2c | development |
| verizon-3q2025 | verizon.com 3Q25 Financial Statements | 8b4249c1… | p1 | parse_5f7328dc81b0f5122762 | development |
| att-3q2025 | investors.att.com 3Q25 Schedules | 064b25a8… | p2 | parse_d771e78cd7eed0b9750d | holdout (issuer-separated) |
| att-2q2025 | investors.att.com 2Q25 Schedules | 0065aa98… | p2 | parse_3ce51ca5af220a046506 | holdout (issuer-separated) |

There are 48 frozen targets (`backend/evi/targets.py`, targets-v1): 3 metrics × (2 annual columns, or 4 interim columns: current and prior year of the quarter and of the year-to-date group). No target was excluded.

**Exposure:** the builder read every statement page, including AT&T, while designing rules and transcribing references. The holdout was not seen by the model-tuning loop, but it is **not unseen by the builder**.

## 2. Mechanism results (implemented + executed)

| Claim | Evidence | Status |
|---|---|---|
| All 48 targets resolve to one supported semantic class from structure | `binding.resolve_target` over the 5 real parses; for owner-attributable profit on Verizon the two EPS rows (also labelled "Net income attributable to Verizon") are rejected by the per-share section rule | executed |
| AT&T statements print no end date → dates stay null, never inferred | P3 = `unknown/end_date_not_stated` on all 24 AT&T targets | executed |
| Target value cells and row labels have exact boxes | 96/96 at a 1 pt margin (`tests/test_integration_real.py`); 4 non-target AT&T box exceptions listed by name | executed |
| Certificates re-verify from the PDF bytes and Docling artifact | **618/618** stored certificates (18 binding-v1, 312 v2, 288 v3) re-verify under their own recorded policy; a relabelled policy fails | executed |
| Tampering is detected after the hash is recomputed | Altered amount, end date or scale, a forged edge and an invented ID all fail (`binding.verify_certificate`) | executed |
| Controlled §9 cases | `tests/test_binding.py` (19): shared end date + 3/9-month groups, wrong-column ID, nine months labelled twelve, a caption spanning years, an unrelated scale note, a column-specific unit, per-share, dash ≠ zero, 52/53-week → unresolved, conflicting scales → unresolved, duplicate rows → ambiguous, percent column, segment scope, hash mismatch, plus 4 metamorphic tests | tested (controlled) |
| Revision gate | `tests/test_revision_gate.py` (9) on a copy of the real DB: legitimate wrong-column correction accepted; annualization, FX, invented or foreign IDs, forbidden fields, evidence-free patches, abstaining on a supported target and dropping evidence are all rejected; all targets preserved | tested (controlled) |
| Operational faults | `tests/test_faults.py` (6) + `test_pipeline.py`: concurrent claim (1 of 4 wins), pending eval polled by the same provider ID after restart, same-key retry → one child and one receipt, wrong-parent/sandbox feedback rejected before a child exists, provider 503 recorded without a receipt, timeout → `submission_unknown` and no resubmission | tested (fakes) |

## 3. Experiment `exp-2026-11-16-a` — frozen four-arm run (measured)

Manifest sha256 `9e1b4511…d2d6`. 2 trials × 5 documents, arms A/B/C/D, `binding-v2`, `revision-v2`, model `gpt-5.4-mini` (observed revision `gpt-5.4-mini-2026-03-17`). All 40 branches executed; no provider failures.

| Arm | Strict correct / 96 | Semantic correct | Covered |
|---|---|---|---|
| A — Docling + SERV | 56 | 60 | 96 |
| B — A + certificates | 56 | 60 | 96 |
| C — + SERV revision, no feedback | 56 | 60 | 96 |
| D — + real Reppo + SERV revision | 56 | 60 | 96 |

Paired outcomes (same trial and target):

| Comparison | Improvements | Regressions | Preserved correct | Unchanged incorrect |
|---|---|---|---|---|
| A→C | 0 | 0 | 56 | 40 |
| A→D | 0 | 0 | 56 | 40 |
| C→D | 0 | 0 | 56 | 40 |

Arm B certificates against the reference: 36 true detections, **0 missed errors**, 4 false alarms.

The 40 natural errors in A (all on unmodified issuer PDFs):

| Trial / document | Targets | Error |
|---|---|---|
| t1 AT&T 2Q | 4 | Wrong attribution row: "Net Income Attributable to **Common Stock**" ($4,464M, …) instead of "…to AT&T" ($4,500M, …). The certificate says contradicted. |
| t1 AT&T 3Q, t2 Verizon 3Q | 24 | Currency emitted as "$" instead of "USD" |
| t1 Verizon FY2024 | 6 | End dates the page prints were omitted |
| t1 AT&T 2Q, t2 Verizon FY2025 | 6 | False alarms: SERV cited the "Operating Revenues" section heading, which binding-v2 did not count as applicable. Fixed in binding-v3. |

**Reppo** (10 real evaluations, all `COMPLETED`, 440 credits each = **4,400 credits**, wait 36–137 s): score **100/100, accept, high confidence, route ship on every one**, including the 5 baselines that held errors (the AT&T common-stock row among them). Rubric dimensions returned: safety, completeness, factual_accuracy, instruction_adherence, with empty critiques. Eval IDs: `cmwif743f000308ifl20mgif8`, `cmwif9pp2000408ify1gumwm7`, `cmwifcu73000508ifyq7poasg`, `cmwiff4re000608ifru1paguu`, `cmwifhh7w000708if3k6rawyb`, `cmwifjwde000808if3zkk4nre`, `cmwifn0wh000908ifddbe69h8`, `cmwifq348000b08ifln9fs8s1`, `cmwifsv0p000008jp1itv8l53`, `cmwiftze8000c08ifs2t52jt0`.

**What the revision arms did:** the gate rejected every proposal that was proposed. That included re-asserting the wrong common-stock amounts, citing the literal string `"redacted"` as an evidence ID (arm D), and abstaining on targets that have a unique supported reading. No proposal fixed an error. Diagnosis: revision-v2 diagnostics named failing fields without the source-derived value.

Costs: 30 SERV calls, 255,312 tokens (USD unknown; the provider returns no per-call price); 4,400 Reppo credits.

## 4. Experiment `exp-2026-11-16-b` — post-hoc policy branch (measured, development only)

Designed **after** inspecting run a, so it is not holdout evidence. It branches from the **same 10 saved A versions** and the **same 10 completed Reppo evaluations**; there were no new evaluations. Changes: `binding-v3` (the section scope reaches the `row_section` heading) and `revision-v3` (diagnostics carry the resolver's source-derived reading — never references). Manifest sha256 `6f048c68…7d78`.

| Arm | Strict correct / 96 |
|---|---|
| A | 62 |
| B | 62 |
| C | 74 |
| D | 74 |

Paired: A→C **+12 improvements, 0 regressions**; A→D +12, 0 regressions; **C→D 0 / 0**. B: 34 true detections, 0 missed, **0 false alarms**. All 12 improvements are Verizon 3Q t2 ("$"→USD, plus the derived start date), accepted identically in C and D. Unchanged incorrect (22): AT&T 3Q t1 "$" (SERV proposed no patch), Verizon FY2024 t1 missing end dates (no patch), AT&T 2Q t1 common-stock row (proposals rejected). Costs: 20 SERV calls, 166,431 tokens, 0 Reppo credits.

## 5. Claim ledger

| Claim | Implementation | Execution artifact | Basis | Limitation | Status |
|---|---|---|---|---|---|
| Period/unit binding prevents misbinding while keeping ordinary facts (H1) | `binding.py` | 48/48 targets resolved; certificates detect 36/36 (a) and 34/34 (b) A errors with 0 misses | Provisional references | 5 statements, 2 issuers, single-table layouts | executed, measured (provisional) |
| External feedback adds value over checks + revision (H2) | `revision.py` arms C/D, `experiment.py` | C→D: 0 improvements, 0 regressions in both runs | Same frozen references | 10 evaluations; Reppo scored every version 100 | **not supported** (null result) |
| The revision gate blocks unsupported changes and can't game passes (H3) | `revision.gate` | 0 regressions across 40 natural revision branches; controlled suite | Predefined cases | Tested policy versions only | tested + executed |
| Restart and unknown-submission safety (H4) | `jobs.py`, `worker.py` | Fault tests | Fault schedule | Reppo offers no idempotency key; no exactly-once claim | tested (fakes) |
| Checks + revision improves strict correctness | revision-v3 | A→C +12/0 in run b | Provisional references | Post-hoc, development-only; all from one branch | measured (post-hoc) |

## 6. Reproduce (no provider calls)

```
cd backend
.venv\Scripts\python -m evi.replay exp-2026-11-16-a      # sources, artifacts, 288 certs, receipts, re-score → VERIFIED
.venv\Scripts\python -m evi.replay exp-2026-11-16-b      # 96 certs, receipts, re-score → VERIFIED
.venv\Scripts\python -m evi.certify --verify cert_4aa69a9e922ecd410cee
.venv\Scripts\python -m pytest -q tests                   # 79 tests (controlled, fakes, real artifacts)
```

Live paths (they spend provider credits): `python -m evi.experiment freeze <id> --trials N`, `run <id>`, then `python -m evi.scoring <id>`.

## 7. Post-freeze corrections, disclosed

1. `store_certificates` ID collision: identical certificate content across versions dropped rows. Fixed, and 21 versions backfilled with `evi.certify` under binding-v2 before scoring (`artifacts/technical-proof/exp-2026-11-16-a/certificate-backfill.json`). No prediction changed.
2. Scorer: the cost query matched no runs, then over-counted; it now attributes exact call IDs. The start date is taken from the experiment's own checker policy (2 targets in run b). Strict counts for run a were unchanged by both fixes.
3. Verifier: it now replays the certificate's recorded policy (it previously used the current rules).

## 8. Not established

- No independent human reference review. All accuracy figures are provisional.
- No population-level accuracy: 5 statements from 2 issuers; targets and trials are correlated.
- No evidence that Reppo adds value. In this corpus it gave 100/100 to versions containing wrong-row and currency errors.
- No public deployment; local only.

---

## 9. Addendum — proof-integrity repair (2026-11-16, later the same day)

Sections 1–8 above are kept as originally written. The following statements in them are **corrected** (details in [PROOF-INTEGRITY-REVIEW.md](PROOF-INTEGRITY-REVIEW.md)):

- §3 "The 40 natural errors in A": **34** are model-output errors; 6 are checker false alarms (binding-v2 section rule). Arm B against the reference, computed without circularity (analysis-v2): **TP 34 / FP 6 / FN 0**, not 36/4/0. The saved scoring-v1 numbers remain in `summary.json`; the corrected analysis is in `analysis-v2/`.
- §3 "semantic correct 60": analysis-v2 reference match is **62**. The difference is two Verizon FY2025 t2 targets whose start date scoring-v1 derived only when the checker approved them.
- §4 "A 62": the change from 56 is a checker-policy change (v2 → v3), not model output. C/D 74 is a real model-output change (one branch). C = D throughout.
- §6 "replay … VERIFIED" for exp-b: replay-v1 checked binding-v2 certificates for a binding-v3 experiment. replay-v2 verifies the required **288/288 binding-v3** certificates (exp-a: 288/288 binding-v2) and no longer rewrites summaries.
- §3 Reppo: the stored packets contained only the candidate's own cited cells and no other rows. For the wrong-row case the correct row was absent from the packet. See [REPPO-PAYLOAD-AUDIT.md](REPPO-PAYLOAD-AUDIT.md). The uniform 100/100 is a measured fact about this payload design and corpus, not a general statement about Reppo.
- AT&T facts with unprinted dates are a *unique supported reading with incomplete exact-interval context*, not complete period verification (coverage-v1).

Unchanged: no prediction, reference, provider result or manifest changed; **the null Reppo result (C = D) stands**.
