# 19 — Semantic binding, support certificates, and bounded revision

Status: normative implementation specification, not a claim that these mechanisms are already complete. Applies with the technical-depth prompt and current project decisions. Preserve the existing frontend/API and implement additive domain structures where practical.

## 1. Boundary and invariant

Evi checks fidelity between an extracted fact and its registered source context. It does not certify accounting truth, fraud, investment value, or universal semantic understanding.

For each target, the supported interpretation must bind:

`value cell + metric row/scope + applicable column/period + applicable monetary unit/scale + original source identity`.

Citing four real evidence IDs is insufficient when their contexts do not apply to the selected cell. The principal invariant is **field support through valid applicability relationships**, not the number of matching strings or passed checks.

## 2. Immutable source representation

Represent nodes using typed Python objects/Pydantic models and the existing artifact/database infrastructure. No graph database is required.

### Required node information

| Node type | Required information |
| --- | --- |
| Source | Registered document ID, original-byte SHA-256, issuer/source URL, verified source metadata |
| Parse | Source identity, parser/version/config, requested/actual page coverage, artifact hash, completion/limitation status |
| Page | Physical 1-based page number, dimensions, rotation/crop convention, printed page label separately |
| Table | Source/parse/page ownership, local table ID, original bounds, row/column dimensions and structure quality |
| Cell | Stable ID within the parse, original text, row/column start/end offsets, header/row-label flags, real bbox or explicit absence |
| Text/context | Original text, original item ID/type, page/geometry, anchored table/section applicability or unresolved association |
| Target | Immutable requested metric/column identity, requested scope, corpus/target-manifest version |

Use half-open row/column spans `[start, end)` internally and test them against the installed Docling semantics. Never treat a merged header as covering only its first column. Preserve empty cells/structure when necessary to determine alignment even if no text evidence is emitted for them.

Record the physical-page mapping actually returned by page-limited parsing. Do not guess whether a parser renumbers the first requested page as 1 or preserves the original page number. Validate using an original rendered page and a known source text anchor.

Stable identity is scoped to source hash + parser/config/coverage + original item location. A changed parse/config is a new parse identity. Do not silently reuse old evidence IDs for changed text/coordinates.

### Parse quality and coverage

A parse must record expected versus recovered tables/pages, structural warnings, missing cells, and unsupported layouts. A cached incomplete parse is not a complete successful parse. Include coverage in the cache key and completion gate.

If the statement title or governing heading lies outside a selected page range, expand to a bounded associated evidence window or return missing context. Do not invent a full-document default from a filename.

## 3. Explicit applicability relations

Represent relations with endpoints, relation type, derivation rule/version, and the source/structural facts supporting that relation.

Minimum relation types:

- `belongs_to_source`, `belongs_to_parse`, `on_page`, `in_table`.
- `row_label_for`, including supported multi-row labels and subtotal scope.
- `column_header_for`, including merged span coverage and parent-header paths.
- `duration_heading_for` and `year_header_for`.
- `unit_applies_to`, with source scope and applicable exceptions.
- `section_scope_for` and `continuation_of`, only with actual supporting context.
- `exception_to`, such as per-share/nonmonetary rows excluded from a monetary table default.

A derivation may use table structure, explicit language, and validated geometric association together. Euclidean proximity alone does not establish that a note applies to a table. A model-proposed relationship without sufficient structural/textual support stays a proposed/uncertain edge and cannot certify a field.

Cross-page inheritance requires supported table/section continuation. Cross-table inheritance requires an explicitly applicable section/document convention. Proximity to an unrelated balance sheet, segment table, tax note, or another currency caption is not enough.

## 4. Targets and candidate tuples

Target definitions must support explicit annual/interim and current/comparative columns. Remove an annual-only global target assumption where it prevents this task. Do not change a frozen target because the model finds a different column easier.

For a target, form bounded candidate tuples:

```text
Candidate {
  target_key,
  source_id, source_sha256, parse_id,
  value_cell_id,
  metric_path_ids[], scope_path_ids[],
  period_path_ids[], unit_path_ids[],
  amount_text, numeric_locale,
  proposed_metric, proposed_scope,
  proposed_interval, proposed_currency, proposed_scale,
  derivations[], unresolved_obligations[]
}
```

Candidate generation can use a small alias set, table structure, deterministic text parsing, and SERV proposals. Alias matches alone never prove consolidated/owner-attributable scope.

Do not compute absent operating profit from revenue/costs, replace it with EBITDA, or equate total net income with owner-attributable income when noncontrolling interests are present.

Cap candidate count and context expansion through a versioned policy. Record truncation/coverage limits as unresolved; do not silently drop difficult candidates and then assert uniqueness.

## 5. Mandatory field obligations

Each obligation yields `pass`, `fail`, `unknown`, or genuinely `not_applicable`, with an evidence path and machine-readable reason code. Applicability is decided by the target/policy, not by deleting candidate fields.

| ID | Obligation |
| --- | --- |
| S1 | Source bytes match the registered hash and all evidence belongs to the same permitted source/parse |
| S2 | Value text matches the selected cell; amount and references/footnotes are separable under a supported convention |
| M1 | Selected row and enclosing scope support the exact requested metric |
| M2 | Consolidated versus segment and parent-owner versus total/noncontrolling scope are supported |
| P1 | Year/header spans cover this value column and select its actual comparative/current identity |
| P2 | Duration/period-kind heading applies to that column, including nested three-/nine-month groups |
| P3 | Exact start/end dates and fiscal-calendar derivations are supported and internally consistent |
| U1 | Currency identity is supported by applicable source context or a verified cited source convention |
| U2 | Scale applies to the value and is not excluded by a cell/row/column exception |
| N1 | Amount uses an explicit locale/sign/dash convention; null/missing/zero are distinguished |
| N2 | Normalized amount equals the supported Decimal operands without annualization or FX |
| C1 | Mutually relevant evidence paths do not assert incompatible semantics |

The original PDF cannot normally make every semantic relationship mechanically indisputable. Record the policy's supported inference boundary and return unknown outside it. A certificate reports this boundary, not a general formal proof of source truth.

### Tri-state interpretation

- `fail`: a candidate/intended interpretation contradicts supported applicable evidence or violates an integrity constraint.
- `unknown`: support is absent, layout association is uncertain, or applicable evidence is unresolved/conflicting.
- `pass`: the stated obligation is supported under a named rule and its prerequisites.
- `not_applicable`: allowed only when the frozen obligation policy says it is irrelevant; it cannot substitute for an unresolved required field.

A candidate can fail without alleging an issuer error. “Nine-month observation does not satisfy an annual request” is a candidate/request mismatch.

## 6. Resolution algorithm

Implement and unit-test the policy as executable code. Suggested sequence:

```text
assert source_and_parse_integrity()
structure = build_source_nodes_and_supported_edges(parse)
candidates, coverage = enumerate_candidates(target, structure, fixed_policy_limits)
for candidate in candidates:
    evaluate_field_obligations(candidate, structure, policy)
feasible = candidates with supported required fields and no applicable contradiction
classes = group feasible candidates by the full semantic tuple, preserving support paths
if coverage is insufficient:
    return unresolved(coverage_reason, candidate_diagnostics)
if exactly one supported semantic class remains:
    return supported_fact(class, certificate)
if multiple incompatible supported semantic classes remain:
    return unresolved(ambiguous_context, all_relevant_candidates)
return failed_or_unresolved_based_on_actual_reasons(candidates)
```

Grouping equivalent paths to the same interpretation is allowed. Do not claim ambiguity merely because two different evidence paths support the same complete semantic tuple. Conversely, identical printed amounts with different periods/scopes are not equivalent.

Candidate rejection must not discard applicable contrary evidence to manufacture uniqueness. Keep unresolved associations distinct from real contradictions and preserve diagnostics.

### Header binding

For a value at column `c`, collect header paths whose validated spans cover `c`, retaining nested period and year levels. A heading containing both 2025 and 2024 can be disambiguated by the selected child year cell. Do not merge every year appearing on the page into a single period reading.

For 3-month and 9-month groups sharing September 30, both duration and year-header paths must apply. The shared end date cannot decide the duration. A balance-sheet date supplies no income-statement duration.

### Calendar handling

Prefer explicitly printed boundaries. Derive an interval from a supported duration/end date only under a documented calendar rule whose premises are evidenced. An annual fiscal period is not universally January–December. Do not infer 52-/53-week starts using approximate month subtraction. Validate actual calendar dates and leap years. Label unsupported fiscal calendars as unresolved rather than coercing them into the browser's broad day bands.

### Unit scope

Use a partial ordering of applicable specificity: explicit cell/column exceptions, governing table caption/header, supported section convention, and verified document convention. More specific context wins only when its association is established. A dollar symbol alone does not globally establish USD.

Do not silently resolve equally applicable conflicting scales. A per-share exception prevents a general “dollars in millions” statement from scaling EPS as a monetary total. Number-of-shares, percent, and ratio rows are different types.

### Amount handling

Preserve original amount text and canonical Decimal value. The normalizer must not decide metric, interval, or currency. It only multiplies validated operands. A dash is not automatically zero. Reject malformed separators or retain an explicit ambiguity. No binary floating-point canonical money.

## 7. Source-support certificate and local verifier

Persist an immutable certificate with:

- Source/parse/target/version/policy identifiers and hashes.
- Complete selected semantic tuple and original amount text.
- Value/metric/period/unit/scope node IDs and validated relation paths.
- Field obligations with status, reason code, evidence paths, and derivation prerequisites.
- Normalization operands and exact result.
- Candidate-resolution outcome, relevant rejected/ambiguous candidates, and coverage limits.
- Creation time and public artifact references, with secrets/private reasoning excluded.

Define a canonical serialization, explicit Decimal string convention, and content hash. Reject non-finite numbers. A hash establishes content identity relative to trusted inputs; it is not an independent signature or a guarantee against an attacker replacing both data and manifest.

The verifier re-loads source/parse artifacts, recomputes ownership and rule-derived relations/obligations, and checks the certificate's claimed result. It must fail if a monetary value, date, unit, evidence identity, or support edge is changed in an isolated test. Checking only the certificate's own hash or copying its pass flags is insufficient.

Keep certificate schema versioned. Add an API/detail/export reference without breaking existing fact/evidence responses. Show concise source paths and outcomes in the current Workspace, not a new generic graph-dashboard product.

## 8. Revision contract

A revision request identifies the parent content hash, target set/policy, actual completed evaluation record, original source/parse, and permitted field patches. No provider may edit those identities.

For each changed field require old value, proposed value, specific supporting node/edge paths, and an observable rationale category. Store the actual proposal separately from the accepted child.

Immutable target key, requested metric set/column selection, source identity, baseline, hidden labels, scorer, and budget policy cannot change through a model patch. A metric interpretation can become unresolved, but that does not rename/remove its requested target.

### Acceptance sequence

1. Verify exact evaluated parent, source/parse/version, real eligible provider status, and remaining budget.
2. Validate allowlisted patch shape and reject foreign/invented anchors.
3. Build the proposed candidate and rerun binding/normalization/obligations against original source evidence.
4. Evaluate each changed field's required support and every affected downstream obligation.
5. Preserve unaffected supported fields unless new explicit source evidence shows a conflict.
6. Reject an unsupported replacement; retain parent prediction plus the new diagnostic.
7. Permit an honest unresolved/conflict result when actual contrary evidence defeats the old support. Record loss of coverage; never call that a successful numeric correction.
8. Save immutable child result and a decision receipt even if all patches were rejected or unchanged.

Compare named obligations, semantic field states, and source coverage. A higher pass count cannot compensate for losing a required target, evidence group, period, or amount. The selected obligation universe must remain stable. A model cannot improve its verdict by making a check disappear.

A child with fewer accepted numeric facts can be epistemically more honest while scoring worse on strict task correctness. Keep source-fidelity outcome, coverage change, and benchmark result separate. True correctness still comes from the reference protocol, not the checker declaring itself correct.

### Rechecking an existing immutable version

Current real baseline versions include original check snapshots, including an earlier checker with known bugs. A new resolver/check policy may re-evaluate a saved fact, but it must create a new check-run/certificate artifact that names the unchanged fact content hash, source/parse identity, checker/policy version, and original versus new outcomes. Do not overwrite historical stored checks or rewrite the parent version in place.

A checker fix that changes pass/fail without changing the fact is a validation-policy change, not a Reppo correction or model accuracy improvement. Freeze one scoring/check policy across experimental arms and report historical policy differences separately. Preserve the existing per-share and missing-end-date regression cases.

### Revision receipt

Record parent/child hashes, actual evaluation ID/raw-result hash, model/policy/provider versions, proposed/accepted/rejected/unresolved field changes, old/new evidence paths, obligation transitions, newly retrieved evidence, conflicts, cost/usage, and timestamps. Never fabricate a correction when the baseline is already correct.

## 9. Required proof examples

Demonstrate with actual rendered-source expectations or explicitly labeled controlled derivatives:

- Supported annual and interim facts pass unchanged.
- A valid evidence ID from the wrong column fails applicability.
- A shared end date with 3-/9-month groups selects the correct interval.
- A caption spanning several year columns binds through the selected year child.
- A nearby unrelated scale note does not override the governing table.
- A local per-share exception is respected.
- An unsupported fiscal-calendar inference stays unresolved.
- A legitimate revision gets new support and an immutable receipt.
- A malicious or simply mistaken critique cannot annualize, convert FX, mutate sources, drop target keys, or delete obligations to gain passes.
- Altering a support certificate's semantics/edge fails re-verification.

Document unsupported cases and the exact original versus controlled evidence used. These tests demonstrate the bounded mechanism, not population-wide extraction accuracy.
