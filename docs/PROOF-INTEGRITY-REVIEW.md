# Proof-integrity review (2026-11-16)

Scope: repair reproduction and reporting of exp-2026-11-16-a and exp-2026-11-16-b. No new SERV or Reppo calls (`provider_calls` count 162 before and after), no credits spent, no deployment, no policy change to extraction, binding or revision.

## 1. What was wrong and what changed

| # | Finding (verified in the code before fixing) | Fix | Where |
|---|---|---|---|
| 1 | Replay filtered `policy_version='binding-v2'` for **every** experiment. For exp-b (manifest: binding-v3) it verified 96 v2 certificates and called that VERIFIED; the 288 required v3 certificates were never checked. | **replay-v2:** the required policy comes from the manifest; coverage is derived from expected branches × frozen targets × actual versions; v2 never substitutes for v3. | `backend/evi/replay.py` |
| 2 | Coverage was whatever the query returned, so an empty or partial query could still VERIFY. | Explicit expected/found/verified/missing/conflicting/consistent-duplicate/wrong-policy/unknown-policy/identity-mismatch counts; any gap fails. | `replay.py` |
| 3 | Replay called `score()`, which **rewrote** summary/outcomes/report before comparing them. | `scoring.compute()` is pure; replay compares an in-memory result with the saved files; the database is opened read-only (`mode=ro`). | `scoring.py`, `replay.py` |
| 4 | scoring-v1 derived the start date from the certificate **only when the certificate was supported**, so "semantic correct" depended on the detector being judged. | **analysis-v2** (versioned, separate files): the start date is derived from the model's own claimed end date and duration by the frozen calendar rule; the metrics are reported separately. scoring-v1 files are preserved. | `backend/evi/analysis.py`, `artifacts/technical-proof/<exp>/analysis-v2/` |
| 5 | A unique supported AT&T reading with unprinted dates was shown as "Supported" (certificate badge) and "Unchecked" (fact table); exports had no coverage field. | **coverage-v1**, an additive view outside the hashed certificate: "Supported reading; exact interval dates are not printed in the source" in the API, Workspace and CSV export. The stored certificates are unchanged. | `binding.coverage_view`, `api.py`, `src/App.tsx`, `src/Certificate.tsx`, `src/export.ts` |

## 2. Certificate coverage (replay-v2, read-only)

| Experiment | Required policy | Expected branches | Executed | Unique versions | Expected certs | Found | Verified | Missing / conflicting / wrong-policy | Receipts | Score recomputation |
|---|---|---|---|---|---|---|---|---|---|---|
| exp-2026-11-16-a | binding-v2 | 40 | 40 | 30 | 288 | 288 | 288 | 0 / 0 / 0 | 20/20 | summary, outcomes and report identical |
| exp-2026-11-16-b | binding-v3 | 40 | 40 | 30 | 288 | 288 | 288 | 0 / 0 / 0 | 20/20 | identical |

Unique versions: per branch, A and B share one version (B = certificates over A); C and D are separate children. So 10 branches × 3 versions = 30, and each has 6 or 12 targets, for 288 (version, target) pairs. replay-v1 had reported "96/96" for exp-b because it checked the wrong policy.

Separate all-history audit (`python -m evi.replay --all-certificates`): 618/618 stored certificates re-verify under their own issued policy (18 binding-v1, 312 v2, 288 v3). This does **not** prove experiment-specific coverage; it is reported separately.

## 3. Metric reconciliation (analysis-v2, arm A; saved predictions, nothing re-run)

| Metric (of 96) | exp-a scoring-v1 (saved) | exp-a analysis-v2 | exp-b scoring-v1 (saved) | exp-b analysis-v2 |
|---|---|---|---|---|
| Semantic / reference match | 60 | **62** | 62 | 62 |
| Strict / composite (reference match + certificate supported) | 56 | 56 | 62 | 62 |
| Certificate supported | 56 | 56 | 62 | 62 |
| …of which exact dates unknown (AT&T, dates not printed) | — | 28 | — | 32 |
| Complete exact interval (of 48 targets whose interval is printed) | — | 42 | — | 42 |
| Detector TP / FP / FN | 36 / 4 / 0 | **34 / 6 / 0** | 34 / 0 / 0 | 34 / 0 / 0 |

Target-level causes (`analysis-v2/reconciliation.md`): of the 40 non-composite A targets in exp-a, **34 are model-output errors** (24 × "$" instead of "USD"; 6 × printed end date omitted; 4 × wrong attribution row) and **6 are checker false alarms** (the binding-v2 section-heading rule). Two of those six (Verizon FY2025 t2) were misclassified as errors by scoring-v1's circular start date. The proof report's "40 natural errors" was wrong; the correct figure is 34.

What moved and why:
- exp-a 60 → 62: **scorer correction**.
- exp-b A at 62 (versus 56 in exp-a): **checker-policy change** (binding-v2 → v3), not model output.
- exp-b C/D at 74: **actual model-output change** (one branch: "$" → USD), identical in C and D.

None of these is attributable to Reppo. **C = D in every metric in both experiments; the null Reppo result stands.**

Sensitivity, shown but not adopted: accepting "$" as USD would give A a reference match of 86/96 in both experiments.

## 4. Original versus current artifact hashes

Snapshot before repair: `artifacts/proof-integrity/snapshot-before-repair.json` (files) and `db-snapshot-before-repair.json` (56 versions, 11 evaluations, 42 receipts, 618 certificates, 162 raw provider files). After repair, every snapshotted **proof artifact and database record** is byte-identical. The only snapshotted files that changed are three documents (`PROOF-REPORT.md`, `TECHNICAL-DEPTH-IMPLEMENTATION.md`, `DECISIONS.md`), and only by appended addenda; the original text of each is an exact byte prefix of the current file (checked). The identical artifacts are: manifests (a `9e1b4511…`, b `6f048c68…`), ledgers, outcomes, summaries, reports, `references-v1.json` (`cb02c74f…`), version bodies, evaluation records, receipts, certificates and raw provider responses.

New artifacts (sha256 prefix): exp-a `analysis-v2/summary.json` 2cb3ea5a…, `reconciliation.md` 3e0c0416…; exp-b `analysis-v2/summary.json` 2b497e71…, `reconciliation.md` 2e1adbfc…; `artifacts/proof-integrity/reppo-payload-audit.json` f305ec64…; `data/references/review/review-sheet-references-v1.json` 61fb79ca….

## 5. Tests and checks run

- Backend: **95 passed**, including `tests/test_replay.py` (11, on isolated copies: removed v3 cert, v2-only, wrong policy label, unknown policy row, conflicting duplicate, missing ledger branch, target missing from a version, changed expected summary, unknown manifest policy, read-only connection, unmodified copies verify), `tests/test_analysis.py` (4) and the coverage test in `test_integration_real.py`.
- Frontend: 16 tests passed (adds an export test that keeps unprinted dates distinct from complete verification); production build OK.
- Browser (`scripts/e2e_partial_context.py`): AT&T 2Q shows "Supported · dates not printed" and "Supported · partial context", with "3 months · exact dates not printed in source"; Verizon 3Q shows "Checks passed" and "2025-07-01 → 2025-09-30 (start derived)"; no page errors. `scripts/e2e_browser.py`: top navigation, highlights and deep-link reload unchanged.

## 6. Still unverified

- **Independent human reference review**: not performed. 0 of 48 targets reviewed (`docs/REFERENCE-REVIEW-PACKET.md`). All accuracy figures remain provisional.
- **A fresh, unseen holdout**: none exists (`docs/FUTURE-HOLDOUT-PLAN.md`).
- **Reppo calibration**: plan only (`docs/REPPO-PAYLOAD-AUDIT.md` §5, max 5,280 credits); not executed.
- **Public hosting**: not done.
