# 10 — API and durable job contracts

## API conventions

Use `/api/v1`. Return JSON with stable IDs, explicit states, and structured errors. Long-running operations return HTTP 202 with a job reference. Use UTC timestamps in stored records; the dashboard may localize display with a visible timezone.

Source and run artifacts are immutable. Validate path/ID lookups through registered records rather than accepting arbitrary filesystem paths from the browser.

## Error format

```json
{
  "error": {
    "code": "provider_not_configured",
    "message": "SERV_API_KEY is not configured on the server.",
    "retryable": false,
    "job_id": null,
    "details": {"provider": "serv"}
  }
}
```

Never include credential values or a raw provider response that contains secrets. Preserve a sanitized transport error artifact for debugging.

## Readiness and settings

| Endpoint | Behavior |
| --- | --- |
| `GET /health` | Process/storage readiness; does not claim provider success |
| `GET /settings` | Safe public config and credential-presence booleans |
| `GET /providers/status` | Configured state plus last actually verified live call/evaluation |
| `GET /activity` | Bounded job/run events for Overview |

Do not implement a browser endpoint that returns environment variables wholesale. Settings changes are validated/versioned and affect only future runs.

## Documents and evidence

| Endpoint | Behavior |
| --- | --- |
| `GET /documents` | Corpus list with provenance, split, parse readiness |
| `GET /documents/{document_id}` | Registered source metadata and versions |
| `GET /documents/{document_id}/source` | Original PDF from a registered source |
| `POST /documents/{document_id}/parse` | Enqueue parse for source/config hash |
| `GET /documents/{document_id}/parses` | Parse history and coverage |
| `GET /documents/{document_id}/evidence` | Bounded evidence index |
| `GET /documents/{document_id}/pages/{page_number}` | Source-page metadata/render asset for physical page |
| `GET /evidence/{evidence_id}` | Original item plus source identity and coordinates |

Register/download sources through the curated corpus CLI/config first. Public arbitrary URL fetch/upload endpoints are out of scope. Source bytes must match the registered hash before parsing or preview.

## Runs and versions

| Endpoint | Behavior |
| --- | --- |
| `POST /runs` | Enqueue initial extraction for document/parse/policy |
| `GET /runs` | Filter by document, status, mode, date |
| `GET /runs/{run_id}` | Run metadata, lineage, version IDs, actual provider evidence |
| `GET /versions/{version_id}` | Immutable facts, checks, and origin |
| `GET /versions/{version_id}/checks` | Detailed check results |
| `GET /versions/{version_id}/diff?other={other_id}` | Validated related-version diff |
| `POST /versions/{version_id}/manual-revisions` | Create manual fork with reason and evidence |

Illustrative initial request:

```json
{
  "document_id": "telkom-9m2025",
  "parse_id": "<completed parse>",
  "policy_version": "period-unit-v1",
  "metrics": ["revenue", "operating_profit", "profit_attributable_to_owners"],
  "mode": "live"
}
```

Only live SERV calls generate `serv_initial` output. Offline contract fixtures have a distinct mode and are excluded from natural benchmark results.

## Evaluations and revisions

| Endpoint | Behavior |
| --- | --- |
| `POST /versions/{version_id}/evaluations` | Persist attempt, enqueue real Reppo submit within budget |
| `GET /evaluations` | Filter evaluation sessions |
| `GET /evaluations/{evaluation_id}` | Local record with external `eval_id`, status, result, mode |
| `POST /evaluations/{evaluation_id}/refresh` | Read/poll existing external evaluation; never create a new one |
| `POST /versions/{version_id}/revisions` | Enqueue SERV revision referencing settled real evaluation |
| `POST /provider-contract-tests/reppo` | Explicit sandbox test with synthetic/public payload |

Revision request includes `evaluation_id`, expected parent version/hash, and frozen budget/config version. Reject feedback for a different version. Reject the normal real-feedback revision action when the evaluation is sandbox/fixture or unsettled.

Return conflicts for duplicate local actions, account in-flight constraints, exhausted budget, stale parent version, and pending unknown submissions. A 409 is not a successful evaluation result.

## Review queue

`GET /review-items` returns flagged checks with filters and evidence pointers. A reviewed item can record an analyst disposition, but this does not rewrite the immutable fact or the gold label. A manual correction uses the manual-revision endpoint.

## Benchmarks

| Endpoint | Behavior |
| --- | --- |
| `GET /benchmarks` | Stored benchmark runs and freeze status |
| `GET /benchmarks/{benchmark_id}` | Counts, denominators, hashes, timing, per-document results |
| `POST /benchmarks` | Enqueue a predefined frozen evaluation configuration |
| `GET /benchmarks/{benchmark_id}/report` | Human-readable artifact |

The orchestrator runs inference without labels, freezes predictions, and then invokes the separate scorer. Never expose a gold-lookup endpoint as an agent tool. The dashboard may show target/prediction comparisons after a scored run; record holdout inspection.

## Exports

`POST /exports` accepts a known run/version and one format: `csv`, `json`, `markdown`. Return a job/artifact reference. `GET /exports` lists generated bundles. `GET /exports/{export_id}/download` serves a registered artifact with an appropriate filename. Do not accept arbitrary download paths.

## Job API

`GET /jobs/{job_id}` returns status, operation, progress message, timestamps, next poll/attempt time, and result/error references. A progress percentage is optional and only valid if the work has a real known denominator.

Canonical local states:

```text
queued -> running -> succeeded
                  -> waiting_external -> queued/polling -> succeeded
                  -> blocked
                  -> failed
                  -> outcome_unknown
                  -> cancelled
```

Normalized polling may use `running` with a polling operation rather than creating an undocumented extra job status. Provider statuses remain separately stored.

## Job kinds

`parse_document`, `extract_facts`, `submit_evaluation`, `poll_evaluation`, `revise_facts`, `run_benchmark`, `generate_export`.

Persist job payload, configuration hash, logical operation ID, attempt history, lease, heartbeat, retry deadline, and output artifact IDs.

## Retry and idempotency rules

- Parse: cache by PDF hash + parser version/settings + page coverage. A partial artifact is never a cache hit for a complete parse.
- Extraction: explicit new runs are allowed; retry attempts remain under their original run and are not cherry-picked using gold results.
- Reppo submit: local idempotency prevents duplicate clicks but cannot guarantee upstream exactly-once behavior. Timeout -> outcome unknown, no automatic resubmission.
- Reppo poll: safe bounded GET retries with backoff; persist the original external ID.
- Revision: validate parent hash and settled evaluation linkage; do not overwrite prior output.
- Export: deterministic content hash can reuse an identical export.

Do not claim cross-system exactly-once submission when the external API has not provided an idempotency contract.

## Cancellation and recovery

Cancel locally queued work when safe. An already submitted Reppo evaluation may continue upstream; cancellation must not imply a refund or cancellation at the provider. A cancelled local job can still retain an external evaluation record for later read-back.

On restart, recover expired local leases, resume pending polls, and expose unknown submissions. Prevent an account from immediately submitting another paid evaluation while its previous outcome is unresolved.

## Required contract tests

Validate normal responses and missing IDs, wrong source/version linkage, invalid model output, Reppo 401/402/409, failed/denied/unknown status, timeout after submission, worker restart during pending evaluation, missing artifact, and attempted path traversal. Include a real provider smoke test separately when credentials exist.
