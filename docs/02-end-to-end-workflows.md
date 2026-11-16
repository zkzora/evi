# 02 — End-to-end workflows

## Shared operating model

Every action is attached to a document version and immutable run version. The UI, CLI, and backend must use the same domain engine and statuses. A parsed document, an extracted fact, a passed source check, a favorable evaluator score, and a correct benchmark answer are different things.

## Flow A — Curate and freeze the corpus

1. Register 4 public issuer PDFs in a corpus manifest with stable ID, issuer, title, publisher URL, intended split, and download time.
2. Download each original PDF and verify file signature, size, readability, and SHA-256. An HTTP 200 containing HTML is a failed download.
3. Identify the financial statement pages plus their contextual headings. Record 1-based PDF page numbers separately from printed page labels.
4. Select relevant page ranges to keep Docling processing bounded. Preserve the full original PDF and identify omitted coverage.
5. Assign development and holdout splits by issuer where feasible. All reports from one issuer remain in the same split for the strongest small-corpus separation.
6. Create human labels from rendered source pages. Labels must not be inferred from agent output.
7. Freeze corpus manifest and labels with hashes before model/prompt tuning.

Completion: each eligible document has stable source identity, source regions, an assigned split, and labeled requested facts. Any unavailable source is listed explicitly rather than silently replaced.

## Flow B — Parse a real report

1. Analyst chooses a registered document and selects Parse.
2. Backend creates a durable parse job. UI returns immediately with a job ID.
3. Worker loads the original bytes, verifies the registered hash, and invokes Docling.
4. Save raw Docling JSON, parser version/configuration, page coverage, and parser warnings.
5. Build stable evidence cells and context windows containing row labels, column headers, caption, section heading, and unit statements.
6. Record page/bounding-box provenance for both value cells and supporting context. Do not attach a whole-page citation and pretend it identifies one column.
7. Publish `parsed`, `partial`, or `failed`. Missing context becomes a reviewable issue.

On interruption: resume/retry from a persisted job, reuse a complete cached parse with the same PDF hash and parser configuration, and never report an incomplete file as a completed parse.

## Flow C — Produce a fair initial extraction

1. Analyst chooses a parsed document and the three requested metrics.
2. Create an extraction run recording source hash, evidence-packet hash, model, prompt/policy versions, and configuration.
3. Send the same initial evidence packet used by the baseline protocol to SERV.
4. Validate the returned structure. Validate every referenced evidence ID against this document and extraction packet.
5. Store the raw provider response and the initial facts without modifying them.
6. Execute deterministic checks. Save each result with evidence and explanation.
7. Present an initial fact grid, including unresolved or missing values.

Errors: unavailable key -> `blocked_credentials`; provider timeout -> `failed` or outcome unknown as applicable; malformed response -> `invalid_output`. No hidden local-model substitution.

## Flow D — Inspect a fact

1. Analyst selects a grid row.
2. Open an evidence panel with original number, normalized value, currency, unit scale, interval, metric definition, and source citations.
3. Show the original PDF page with separate highlights for number, metric label, period heading, and unit statement.
4. Show check results individually. A byte/hash match is not presented as proof of financial truth.
5. If the value is uncertain, offer source inspection or manual review rather than a fabricated “verified” badge.

## Flow E — Evaluate with Reppo

1. Build a compact public evidence packet from this exact fact version and source excerpts.
2. Show whether the run is real API evaluation, recorded real evaluation, or sandbox contract test.
3. Check configured per-run evaluation budget and account-level in-flight constraints.
4. Persist the evaluation attempt before POST. On success, immediately save `evalId`.
5. Poll through durable scheduled jobs; never hold an HTTP request open for the full settlement window.
6. Store the returned response, criteria, critiques, status, and actual charged credits when provided.
7. Display pending, settled, failed, denied, or unknown states faithfully.

No Reppo result is substituted for the hidden-label benchmark. No sandbox placeholder counts as a real judge.

## Flow F — Revise from real feedback

1. Start only from a settled real evaluation for a known immutable fact version.
2. Send SERV the initial facts, relevant source evidence, deterministic diagnostics, and Reppo critiques.
3. SERV proposes bounded field edits and supporting source evidence. It may request an additional source context window within the configured budget.
4. Validate the proposal. Source bytes, evidence locations, labels, scoring configuration, and budget cannot be changed by the agent.
5. Re-run checks on the revised facts. A correction whose source support is absent stays unresolved.
6. Save a child run/version with before/after field differences and change reasons. Preserve the parent version.
7. Stop after the revision limit, on unavailable evidence, on budget exhaustion, or when further edits are unsupported.
8. Optionally request a second real Reppo evaluation within budget. It is a new evaluation, not an implied improvement.

If Reppo requests an unsupported annualization, the agent must retain the reported interim interval and explain why the proposed change lacks support.

## Flow G — Human correction

An analyst may create a manual fork and cite a source. Store editor attribution, time, original value, new value, and reason. Label the version `manual`. Exclude it from the primary autonomous benchmark. Do not let a manual edit retroactively alter an existing provider evaluation.

## Flow H — Compare facts

Permit direct comparisons only for compatible metric definitions, currency, reporting intervals, and consolidation scope. Normalize unit scale deterministically. Never annualize a nine-month fact to make a comparison fit. Display incompatible facts side by side with an explicit reason instead of calculating misleading growth.

## Flow I — Run the benchmark

1. Freeze baseline, revision policy, corpus, model, and scoring configuration.
2. Run initial and feedback-assisted extraction without access to gold labels.
3. Save immutable predictions and timing/usage artifacts.
4. Invoke the isolated scorer with frozen labels and predictions.
5. Report integer counts, percentages, abstentions, regressions, and per-document results.
6. If the holdout result is inspected, record the inspection. Subsequent tuning retires that holdout for claims about unseen evaluation.

## Flow J — Export and revisit

Export CSV for analysts, JSON for reproducibility, and a Markdown evidence summary. Each fact includes its source URL/hash, original page, metric, raw amount, normalized amount, currency, interval, status, and version. Reopening an export must identify the exact source/run version. Export provider status honestly; do not include secrets or private account identifiers.
