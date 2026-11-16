# Evi — Next Claude Code task: repair proof integrity

Open the existing project: `C:\Evidence\EvidenceGrid-Claude-Code-Handoff`.

Paste the instruction below into the same Claude Code session that implemented the technical extension.

---

Continue from the completed technical-depth work. Do not rebuild working components or start another experiment yet.

The existing evidence shows no incremental benefit from Reppo over the same revision without Reppo. Preserve that null result. This task is to make reproduction and reporting precise, independently inspectable, and ready for reference review.

## Boundaries

- Read AGENTS.md, the current code, docs/PROOF-REPORT.md, docs/TECHNICAL-DEPTH-IMPLEMENTATION.md, docs/DECISIONS.md, and both experiment manifests/summaries first.
- Preserve English UI, Evi branding, top navigation with Home first, USD presentation, and no-login access.
- Do not submit new SERV/Reppo calls, spend credits, deploy publicly, or change the extraction/revision policies during this task.
- Do not edit original predictions, provider responses, evaluation IDs, reference answers, or frozen manifests to obtain a better result.
- Snapshot hashes of the existing manifests, ledgers, outcomes, summaries, reports, and references before making changes. Preserve originals and record corrections in new versioned artifacts.
- The findings below describe the inspected snapshot. Check the current implementation first; if already fixed, verify the fix instead of repeating it.

## 1. Fix replay coverage and make verification non-destructive

Inspect backend/evi/replay.py. The inspected implementation filters certificates using policy_version='binding-v2' even for experiment b, whose manifest specifies binding-v3.

At the inspected checkpoint, experiment b's version set has 96 v2 certificates and 288 v3 certificates. Do not hard-code these counts as assertions of correctness; derive required coverage from the manifest, executed ledger branches, immutable target set, and actual versions.

Implement replay that:

1. Selects the binding policy recorded by the experiment manifest.
2. Computes the exact expected target/certificate coverage for each executed branch and each unique version. Explain sharing where A/B reuse one version; do not confuse branch count with unique-certificate count.
3. Requires the appropriate certificate for every expected target/version/policy. Missing certificates, missing branches, duplicate/conflicting certificates, wrong policies, unknown policies, changed sources/parses, and inconsistent identities must fail verification rather than return VERIFIED on an empty or incomplete query.
4. Verifies each certificate under its issued policy implementation, while checking that the experiment uses the policy its manifest requires. Historical v2 certificates do not substitute for required v3 certificates.
5. Checks source and Docling hashes, ledger/version identity and content, parent/child/receipt links, and saved reference provenance.
6. Computes a fresh score into an isolated output directory or in memory and compares it with the saved expected artifact. Do not overwrite the original summary/outcomes/report before discovering whether they differ. The existing scoring function writes those files; refactor or isolate that behavior.
7. Reports expected, found, verified, missing, conflicting and wrong-policy counts explicitly. Read-only replay must make no provider calls or budget reservations.

Add focused regression tests that would fail the old implementation: experiment b with its v3 certificate removed; only historical v2 certificates present; wrong policy; duplicate/conflicting target certificate; an executed target missing from the ledger or version; and a deliberately changed expected summary. Use isolated copies/temporary storage and preserve all original artifacts.

A separate all-history certificate audit may also verify the 618 stored certificates under their respective issued policies. Label this separately from experiment-specific replay; do not imply one proves the other.

## 2. Clarify metrics and remove checker/scorer circularity

Inspect backend/evi/scoring.py, including semantic_correct, strict_correct, start-date derivation, and detection_B.

The current experiment-a summary reports 60/96 semantic correct, 56/96 strict correct, 36 true detections and 4 false alarms. The proof report calls 40 cases natural errors even though four of those are semantically matching predictions rejected by the checker. Also inspect the six source-scope rejection cases in the report: start-date derivation depends on certificate outcome, which may move some cases between semantic mismatch and false alarm.

Do not simply rename counts without tracing target-level causes. Produce a reconciliation table linking every affected target/trial to its saved prediction, applicable derivation, reference comparison, checker result, and final metric.

Define and report separately:

- Raw model field match against the frozen reference, with missing output fields visible.
- Application-derived field match, where a declared deterministic transformation is part of the evaluated pipeline.
- Complete required-context coverage, including missing/unknown exact dates.
- Source-support/certificate outcome.
- Composite reference match plus source support, if retained as the old strict metric.
- Detector true/false positives/negatives against a reference comparison that is not made true or false by the detector's own pass/fail decision.

For application-derived start dates, derive according to the frozen source/calendar policy without making the independent reference comparison depend on whether this checker approved the whole candidate. Do not silently change historical experiment semantics. If this reveals a measurement-definition problem, preserve the original frozen result and publish a versioned corrected analysis, with exact differences, causes and unchanged predictions.

Keep target denominators stable. Do not treat missing reference dates as known dates. Explain whether correct abstention/null is counted as faithful source representation or complete interval recovery; these are different metrics.

Reconcile experiment a's 56/60 distinction and experiment b's 62 baseline under the changed policy. Clearly separate checker-policy changes, scorer corrections, and actual model-output changes. Do not present a policy/scorer correction as Reppo-driven improvement.

Preserve C versus D equality if the corrected results still show equality. Report any genuine change transparently without choosing the scoring variant that produces the best story.

## 3. Make partial context explicit without falsifying history

The AT&T pages omit exact end dates, so start/end remain null with P3 unknown. A unique candidate with known metric/amount/year/duration can still have an incomplete exact interval.

Audit API, certificate details, exports and Workspace wording. Distinguish:

- A unique supported reading of the available source fields.
- Complete period/unit support for every required field.
- Unknown exact interval or another required context field.

Use additive/versioned coverage metadata and accurate labels. Do not invent dates from filenames, silently change targets, overwrite old certificates, or rewrite historical check outcomes. A display change must not be reported as an extraction improvement.

Add a focused test and browser check showing that an AT&T fact with unknown dates cannot be mistaken for fully verified exact-period coverage. Preserve correct source highlights and the working deep links.

## 4. Audit the existing Reppo payloads offline

Inspect the stored actual submission packets and returned raw results. No new evaluation calls in this task.

Verify:

- The request includes a clear financial extraction task, the exact candidate response, applicable source evidence and instructions for assessing period/unit/scope fidelity.
- All three metrics and relevant current/comparative columns can actually be judged from the supplied evidence.
- Correct alternative row values, unit notes, duration/year headers, table membership and source relationships are available where needed; a list of self-selected citations alone may omit the evidence needed to discover a wrong-row answer.
- The packet is not truncated or misleadingly serialized.
- Provider status/source/mode, raw versus normalized scores, generic rubric fields, and empty critiques are represented faithfully.
- The recorded evaluations belong to the exact parent versions used in D.

Compare with current official provider documentation where necessary. Do not infer that JSON-embedded criteria are a supported provider-level custom-rubric setting unless documentation/actual interface establishes that.

Write docs/REPPO-PAYLOAD-AUDIT.md with concrete stored examples, confirmed observations, uncertainties, and plausible explanations for the uniform 100/100 results. Do not generalize the result to all Reppo tasks or declare a sponsor bug without evidence.

If a future calibration is justified, prepare a small predeclared positive/negative-control plan and an explicit maximum credit budget. Controlled faults must be labeled and kept separate from natural extraction accuracy. Do not execute that paid plan during this task.

## 5. Prepare human reference review and a genuinely new test plan

Do not change data/references/references-v1.json in this task.

Produce docs/REFERENCE-REVIEW-PACKET.md (or a browsable equivalent) that lets a reviewer inspect each of the 48 targets with:

- Original issuer URL, source hash, physical page, target identity and split/exposure.
- Printed metric/value, consolidation/attribution scope, unit/currency/scale, relevant year/duration heading and actual source regions.
- Draft reference fields and their evidence, explicitly identifying absent/derived dates and ambiguities.
- Review status, proposed corrections, reviewer identity/date, and rationale.

Drafted/transcribed references are not independently reviewed human labels. Keep draft/corrected reference versions and change logs distinct. Do not mark review complete yourself or pretend that machine re-verification supplies the missing independent human review.

Prepare a bounded future holdout plan with fresh reports/templates not used to tune these rules. Preserve the original AT&T exposure disclosure and experiment b's post-hoc development-only status. Do not download/process new paid experiment branches or label new outcomes during this repair task.

## 6. Verification and deliverables

Run meaningful regression tests, read-only experiment-a and experiment-b replay, frontend tests/build when affected, and a browser check for partial-context presentation.

Deliver:

1. Corrected replay and focused tests, with original proof artifacts unchanged.
2. Versioned metric reconciliation and, if necessary, corrected score artifacts linked to the original experiment—not a rewritten original result.
3. Explicit unknown-context coverage in relevant UI/API/export surfaces, without changing saved predictions.
4. docs/REPPO-PAYLOAD-AUDIT.md.
5. docs/REFERENCE-REVIEW-PACKET.md.
6. Updated proof/implementation/decision documentation that preserves chronological results and discloses corrections.
7. docs/PROOF-INTEGRITY-REVIEW.md summarizing exact fixes, original/current artifact hashes, expected versus verified certificate counts, metric differences, tests, and what remains unverified.

The final report must state whether any original prediction/reference/provider result changed (none should), whether any new provider calls occurred (none should), and whether the null Reppo result remains. Missing human review and public hosting remain real external dependencies; do not mark the entire project or independent accuracy validation complete.

Start with a short audit of the current code against these findings, then implement the concrete repairs. Do not stop at another plan.
