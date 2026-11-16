# 20 — Ablation, independent expectations, and reproducible proof

Status: normative experiment specification. No unexecuted measurement below is a claimed result. Used with documents 08 and 19 and the technical-depth prompt.

## 1. Hypotheses and falsification

State hypotheses before outcomes:

- **H1 — Context binding:** validated source-applicability relationships prevent period/unit misbinding while retaining supported ordinary facts, compared with competent initial extraction alone.
- **H2 — External feedback:** real Reppo critique improves final source-faithful outcomes over checks plus a comparable SERV revision without Reppo.
- **H3 — Controlled revision:** the revision gate prevents unsupported changes and reveals legitimate uncertainty without silently changing targets or concealing regressions.
- **H4 — Durable inspection:** a completed result and its source/revision lineage survive restart; an uncertain external submission is not duplicated automatically.

Each may fail. A good baseline can leave little room for improvement. A reviewer can become stricter while task accuracy/coverage worsens. A richer feedback arm can be more expensive and slower. Preserve those outcomes.

No interview/revenue/customer-loss evidence is established by these technical experiments. Do not convert a working mechanism into a claim of proven demand or a likely award.

## 2. Three separate evidence families

| Family | Input | Purpose | Permitted headline |
| --- | --- | --- | --- |
| Natural PDF extraction | Untouched registered issuer reports, frozen targets/reference | Measure actual extraction and revision | Small-corpus extraction results with counts, split, coverage, cost and limits |
| Controlled mechanism tests | Explicit candidate mutations or marked derivative documents | Isolate binding/revision behavior against independent expectations | Controlled test outcomes only |
| Operational fault tests | Isolated temporary state and bounded provider test doubles | Check durability, ownership, budgets and unknown outcomes | Tested operational behaviors; not live provider or extraction accuracy |

Real provider smoke tests and full browser workflow read-back add execution evidence. Their success does not replace a benchmark. Source snapshots and landing examples are a fourth, distinct public-data surface, not evaluation predictions.

## 3. Corpus and target freeze

Use 4–6 actual public USD reports from the telecom/connectivity sector. Include annual and interim statements with meaningful period/header/scale coverage. Acquire missing sources from issuer/regulator origins and register original bytes and URLs.

Prefer an issuer/template-separated development/holdout split. Do not put near-identical yearly layouts in both splits just to improve scores. Reports already inspected for tuning, including prominently featured examples, are not fresh unseen holdout evidence. Disclose developer exposure.

Freeze before model inference on the holdout:

```text
ExperimentManifest {
  experiment_id, schema_version, created_at,
  source_ids_and_sha256[], physical_page_coverage[],
  development_ids[], holdout_ids[], exposure_notes[],
  target_keys_and_eligibility[], reference_hash_and_provenance,
  parser_version_config_hash, candidate_policy_hash,
  prompt_hashes, model_identifier_and_observed_revision,
  adapter_versions, scorer_hash, precision_policy,
  arms, trial_plan, retrieval_and_call_caps,
  provider_spend_caps, timeouts, stopping_rules,
  failure_handling, environment_and_code_revision
}
```

No model/evaluator input may contain reference answers, hidden correctness flags, expected scale/date values, or gold-informed evidence selection. The source evidence itself may naturally contain dates and unit statements; those are legitimate input.

SEC facts can corroborate context outside a PDF evaluation, but do not inject their amounts/intervals as answers into the primary PDF experiment. If using a structured-data-assisted arm later, label it separately and disclose its information advantage.

Predefine current/comparative/3-/9-month target columns and eligibility. Targets without an explicitly available required metric are handled by an eligibility policy frozen before outcomes; do not remove failures after inference.

## 4. Reference provenance and adjudication

References come from original rendered source pages with independently determined expected fields and support regions. Record exact source amount, interpretation, metric/scope, interval/calendar basis, currency/scale, and rationale.

- Identify who/what annotated and who/what reviewed them.
- Builder-reviewed labels are not independently annotated labels.
- Agent-drafted labels are provisional, not human gold labels.
- A second model's confidence is not independent verification.
- SEC values with another accounting basis are not automatically equivalent labels.

If the human-reference review required by document 08 is unavailable, prepare a concrete annotated packet and proceed with other engineering. Any provisional scoring must name its reference provenance and remain separate from the required verified benchmark. Never silently promote draft annotations to independent gold.

Separate the scoring process/label directory from inference tools. Test that extraction, retrieval, evaluator packet building, and revision cannot access reference files or derived target correctness. Freeze versions and retain an audit of when labels/outcomes became visible.

## 5. Four-arm comparison

For each document/trial obtain one competent initial prediction A, then branch from that exact immutable artifact.

| Arm | Mechanism | Semantic changes allowed | Main comparison |
| --- | --- | --- | --- |
| A | Docling evidence + one competent SERV extraction | Initial prediction only | Actual extraction baseline |
| B | Same saved A + deterministic checks | No semantic repair; exact normalization under the same source-supported policy may be reported separately | Whether diagnostics detect issues; accuracy need not change |
| C | Same A + checks + bounded SERV revision, no Reppo critique | Source-supported revision under document 19 | Practical no-Reppo alternative |
| D | Same A + checks + actual Reppo critique + bounded SERV revision | Same acceptance policy as C | Incremental outcome of the feedback treatment |

All arms have the same target set/source bytes/initial parse. Baseline prompts include the applicable headings and unit notes; do not starve A of context to make D win. A manual correction or intentionally corrupted baseline is not a natural baseline.

### C versus D fairness

- Same initial prediction, model configuration, source evidence, target set, deterministic diagnostics and revision policy.
- Same maximum SERV revision calls and retrieval opportunity. A clear first policy is one revision proposal per branch with a fixed evidence packet.
- Reppo feedback is the intended additional input to D. Do not call the arms equal-information because the treatment supplies feedback.
- Account for the external evaluation's additional compute/credits and waiting time. Matching SERV budgets does not make total treatment cost identical.
- If extra context is retrieved, either provide the same retrieved source content to C under a predeclared protocol or report a separate expanded-context experiment. Do not silently attribute an information advantage to critique quality.
- No cross-arm reuse of successful child outputs or critiques in C.
- Define model parameters in advance; set seeds only if actually supported, and do not promise deterministic provider output.
- Balance/randomize execution order using a recorded local schedule where feasible; preserve timing/provider-version drift limitations.

If claiming external feedback itself adds value, C versus D is mandatory. A versus D alone is a pipeline comparison confounded by added checks, calls and feedback.

## 6. Repeats, budgets, and stopping

Use a bounded configured trial plan. A useful small stability target is three trials per document/arm branching from three separately recorded initial extractions, **only within configured authorized call/spend limits**. Shared A/B/C/D baseline identity must hold within each trial.

Before starting, estimate the maximum initial/revision/evaluator calls and recorded context/token budgets. Reserve room for the actual end-to-end verification. Provider credit balance and cost are measured from available account/response data; absent price/usage data remains unknown.

If only one trial can be afforded, execute it honestly and label repeatability unverified. Never fabricate repeats, reuse one cached provider reply as independent trials, or silently expand a paid budget.

Stop for predeclared limits or technical failures, not when a desired uplift/significance appears. Keep attempts, retries, refusals, timeouts, failed submissions, unknown outcomes and settlements in the execution ledger.

Targets and repeats within a document are correlated. Repeating the same four reports does not create dozens of independent reports. Treat small-corpus summaries as descriptive; show document-level effects and range/variation across trials. Do not compute a narrow fact-level confidence interval that pretends every cell is independent. Any uncertainty method must use a justified unit of independence and disclose that 4–6 documents cannot support broad population claims.

## 7. Outcome ledger and scorer

For every planned/attempted document/trial/arm/target, save:

- Stable experiment, source, target and trial keys.
- Initial artifact hash and actual output/certificate/revision/evaluation identities.
- Exact predicted fields and per-field reference matches.
- Required source-support obligation outcomes and evidence-correctness review.
- Complete/missing/unresolved/malformed/refused/provider-failed state.
- Whether the arm actually executed; reason when it did not.
- Calls, token/credit data, retries, compute/runtime, evaluation queue/wait time, and total elapsed time.
- Reference/scorer/policy versions and provenance level.

Scorer rules:

- Primary strict correctness requires all frozen required fields and supporting context to match.
- Every eligible target remains in the denominator for an executed task; missing/unknown/invalid/unsupported predictions are incorrect for strict task correctness.
- Report coverage separately so an always-abstaining system cannot win by refusing every hard case.
- A provider error in an attempted workflow is an execution failure/missing prediction under the frozen failure policy, not a target exclusion.
- An entire arm never run because credentials/approval are absent is **unexecuted**, not a fabricated 0% measured arm. Do not issue a completed paired comparison when required arms did not execute.
- Define upstream-baseline failure handling before runs; retain failed attempts and inability to branch. Do not cherry-pick only successful baseline trials to claim pipeline reliability.
- Unresolved/abstention may be more faithful than an unsupported guess while reducing strict correctness/coverage. Show both dimensions.
- Use exact Decimal equality when appropriate; freeze any source-precision tolerance before outputs. Display-unit formatting is not a change in source scale.

### Paired changes and regressions

For each relevant pair, count:

| Parent outcome | Child outcome | Classification |
| --- | --- | --- |
| Incorrect | Correct | Improvement |
| Correct | Incorrect | Regression |
| Correct | Correct | Preserved correct |
| Incorrect | Incorrect | Unchanged incorrect; include abstention transition separately |

Report A→C, A→D, and C versus D on the same targets/trials. For diagnostic arm B, report detected violations, missed violations and false alarms against independent expected context labels; do not invent an accuracy uplift when it only annotates A.

Show per-document/per-metric/period/unit breakdowns, coverage, false passes, false failures, unresolved cases, and actual denominator. Never call a Reppo verdict score extraction accuracy. Preserve null/missing provider scores and their scales instead of inventing zeros or a standard 100-point interpretation.

## 8. Controlled semantic and revision suite

Expected outcomes must be specified independently before checking the implementation. Use actual rendered source context where possible. Mark controlled corruptions and synthetic/derived test inputs explicitly; they must never populate production live results or natural accuracy totals.

| Case | Expected behavior |
| --- | --- |
| Supported annual/current and interim/comparative facts | Pass without invented corrections |
| Nine months labeled twelve | Reject candidate/request mismatch; preserve actual interval |
| Three-/nine-month groups with same end date | Bind through the correct duration and year spans |
| Correct source ID from the wrong year/column | Fail applicability despite valid ownership |
| Million versus billion mismatch | Reject wrong scale; exact supported normalization passes |
| Nearby unrelated unit/currency caption | Ignore inapplicable context, not inherit it |
| EPS under “except per-share” caption | Do not apply monetary-total scale to it |
| Supported zero versus dash versus missing | Keep distinct under the source convention |
| Unsupported fiscal calendar/start date | Unknown; no approximate coercion |
| Two equally applicable incompatible contexts | Unresolved conflict; no arbitrary tie break |
| Critique requests annualization/FX/source changes | Reject unsupported operation |
| Critique invents evidence or cites another parse | Reject or mark unverifiable; no support certificate |
| Patch removes a hard target/evidence/check to gain passes | Preserve target/obligation universe and record rejection/coverage loss |
| New valid source evidence defeats an old interpretation | Explicit correction or honest unresolved transition with receipt |
| Source-supported baseline with no error | Preserve it; no forced “improvement” |
| Altered certificate value/edge/date | Re-verifier fails against trusted source/parse |

Include positive controls alongside refusals. The test is not successful if the engine marks everything unknown.

## 9. Metamorphic and sensitivity checks

Use a small bounded set that targets the binding mechanism:

- Reorder serialized evidence nodes without changing relations: supported interpretation remains the same.
- Add unrelated neighboring text/year/scale: a valid binding does not inherit it.
- Rename an evidence identifier consistently within an isolated parse while preserving ownership/relations: semantics remain equivalent, identities/certificate hashes appropriately change.
- Change the governing duration or move the selected value to a different valid column: old interpretation/certificate no longer verifies.
- Apply a legitimate local unit exception: the applicable unit changes only in its scope.
- If creating a layout-derived PDF, label it a derivative, assign new source/parse hashes, reparse it, and independently confirm preserved/changed semantics. Do not assume arbitrary geometric transformations leave Docling extraction unchanged.

Record whether a failure belongs to parsing, relationship construction, semantic proposal, resolver, revision gate, or reference ambiguity. A parser failure is not evidence that the downstream verifier passed.

## 10. Operational fault matrix

Test with temporary databases/artifacts and bounded provider fakes; preserve actual provider smoke results separately. Exercise at least these consequential boundaries:

| Fault | Required observable invariant |
| --- | --- |
| Duplicate processing click | One logical request/idempotent response; no uncontrolled paid duplicate |
| Two workers claim one job | Durable lease/claim rules prevent simultaneous accepted execution |
| Worker dies before/after source artifact persistence | No successful row points to missing/incomplete bytes; recovery reconciles orphan state |
| Model result arrives around a restart | Persist request/attempt/outcome lineage; do not silently count duplicate attempts as one call |
| Reppo submit times out after possible acceptance | Unknown outcome retained; reconcile or require bounded operator action before resubmission |
| Pending evaluation survives restart | Same provider ID is polled; no invented fresh evaluation |
| Child version transaction is retried | One logical immutable child/decision receipt under defined idempotency scope |
| Budget reservation has uncertain external usage | No false refund/free-call claim; retain uncertainty and limits |
| Foreign session reads/writes private job state | Server ownership policy enforced independently of the browser |
| Wrong source/parse is passed to a revision | Request rejected before creating an accepted child |

Use transactional intent/result records or equivalent existing patterns where they solve these boundaries. External exactly-once semantics require provider support; local deduplication alone is not proof of it.

## 11. Proof bundle and replay commands

Choose paths that fit the existing repository. A suitable artifact organization is:

```text
artifacts/technical-proof/<experiment_id>/
  manifest.json
  source-and-parse-manifest.json
  references.provenance.json
  inputs-and-policy-hashes.json
  outcomes.jsonl
  certificates/
  revisions/
  provider-receipts-redacted/
  failure-tests.json
  summary.json
  report.md
```

Keep raw secrets and private labels out of public bundles. A hash of a private reference can be included without publishing its contents; inference must still not access it.

Expose actual commands, not merely illustrative commands in a README:

- Verify a real source/certificate/revision receipt without a fresh provider call.
- Execute the bounded real pipeline on a registered source with configured credentials.
- Run controlled/fault tests in isolated storage.
- Execute the frozen trial plan and score saved predictions in a separate scoring step.
- Reproduce report counts from the saved outcome ledger.

A replay is labeled replay and references its original live timestamps/provider IDs. It never impersonates a new paid run.

## 12. Judge path and claim ledger

Use the existing UI to show:

1. One real number and the concrete period/unit failure it could suffer.
2. Its original source page and applicable context paths.
3. An actual validity/contradiction/unknown outcome.
4. Actual critique, proposed field changes, accepted/rejected decisions, and parent/child identity where executed.
5. A reproducible artifact and the small-corpus comparison with coverage/regressions/cost.

Keep the source-data row count separate from processed-PDF count, benchmark targets, and throughput. Do not claim a named issuer made an error because it validly reports both quarterly and year-to-date revenue.

In `docs/PROOF-REPORT.md`, include a ledger:

| Claim | Implementation location | Execution artifact | Independent/reference basis | Limitation | Status |
| --- | --- | --- | --- | --- | --- |
| Applicable period/unit binding | Actual code path | Real certificate/check trace | Original source review | Supported-layout/calendar boundary | implemented/executed/etc. |
| External critique adds value | Actual C/D harness | Paired measured outcomes | Frozen reference provenance | Small corpus; added evaluator cost | measured or unverified |
| Revision cannot gain passes by removing obligations | Acceptance logic | Controlled positive/negative receipts | Predefined target/obligation cases | Tested policy/version only | tested or unverified |
| Restart and unknown submission behavior | Worker/storage adapter | Fault receipts and real read-back where available | Explicit fault schedule | Provider semantics boundary | tested or unverified |

Use actual links/IDs in the completed report; placeholders in this specification are not deliverable evidence. Include first-run results, negative/null outcomes and residual failure cases. The report must support the claims it makes rather than fit a predetermined winning narrative.
