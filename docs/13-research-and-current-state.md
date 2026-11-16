# 13 — Research ledger and actual workspace state

Last inspected: November 4, 2026. This is a dated handoff snapshot, not a live status feed.

## What actually exists

Workspace at handoff:

```text
C:\Users\Pongo\Documents\ChatGPT\openserv hk 2
```

Existing preparation:

- A `.venv` created with Python 3.12 and system-site-packages enabled.
- Dependencies installed during preparation, including Docling and pytest.
- Empty application-oriented directories such as evidencegrid, tests, scripts, and web.
- Two downloaded publisher PDF files under data/sources.
- This Markdown documentation package.

There is no implemented frontend, backend, parser adapter, semantic engine, API wrapper, corpus manifest, gold dataset, extraction result, real SERV call, real Reppo verdict, benchmark report, or deployment. The workspace was not a Git repository when inspected. Do not assume any README command already works.

The dependency installation finished before the documentation handoff. No application server or extraction worker was started. Preserve the prepared files; do not delete them merely to restart setup.

## Installed package snapshot

These versions were reported by the local environment metadata, not verified as a portable build lock:

| Package | Version |
| --- | --- |
| Docling | 2.146.0 |
| docling-core | 2.105.0 |
| torch | 2.15.0 |
| pytest | 9.2.0 |

No actual Docling conversion or model-weight download was verified. The venv inherited system packages, so inspect imports and produce a clean reproducible lock/setup during implementation.

## Downloaded source 1

- ID: `telkom-9m2025`.
- Local file: `data/sources/telkom-9m2025.pdf`.
- Publisher URL: [Telkom Q3 2025 English financial statements](https://www.telkom.co.id/minio/show/data/lampiran/1761831900844_original_FS-Telkom-Triwulan-III-2025-Eng-release.pdf).
- File size: 2,483,091 bytes.
- Physical pages: 114.
- SHA-256: `5b9f0f7f2d4a870ecd35cfa80515e1b4ce622a02a09f9423212646c4f762e19f`.
- Verified: original download completed; PDF magic was present; pypdf could read page count; hash computed.
- Not verified: specific target metric rows, physical income-statement page positions, rendered headings, Docling output, semantic labels.

Search-indexed source text indicated nine-month reporting and billions of Rupiah. That is a candidate-selection observation, not a gold label or a completed parse.

## Downloaded source 2

- ID: `xl-q12025`.
- Local file: `data/sources/xl-q12025.pdf`.
- Publisher URL: [XL Axiata reviewed March 2025 financial statements](https://staticxl.ext.xlaxiata.co.id/s3fs-public/media/documents/Reviewed%20FS%20XL%20Axiata%2031%20March%202025.pdf).
- File size: 2,728,687 bytes.
- Physical pages: 132.
- SHA-256: `abd83d733e76f343064ad8e12a8b70089be588d6c5261454b1b7797b6b474d42`.
- Verified: original download completed; PDF magic was present; pypdf could read page count; hash computed.
- Not verified: exact requested metric availability, source page regions, rendered headings, Docling output, gold labels.

Search-indexed text indicated three-month reporting and millions of Rupiah. Treat this only as a reason to inspect the report.

## Candidate additional sources — not downloaded or frozen

| Candidate | Location | Required next step |
| --- | --- | --- |
| Telkom FY2024 annual report | [Publisher PDF](https://www.telkom.co.id/minio/show/data/lampiran/1745244391951_original_Annual%20Report%20Telkom%202024%20%281%29.pdf) | Download, verify bytes, locate financial statement pages, verify metric definitions |
| XL Axiata FY2024 integrated annual report | [Publisher PDF](https://staticxl.ext.xlaxiata.co.id/s3fs-public/media/documents/IR_XLAxiata_2024_EN_03032025_1930.pdf) | Download, distinguish financial-review summaries from the actual statement, select appropriate evidence |

Suggested initial 4-document corpus: these two annual reports plus the two existing interim reports. This is provisional until source/metric validation. Telkom can be development and XL holdout, keeping issuer templates separated. No source or label split has yet been frozen.

Two Indosat candidate PDFs found by search returned HTTP 404 during direct download attempts. They were not obtained and are not available corpus sources. A source appearing in search results does not guarantee the original URL is downloadable. Do not silently include those reports in claimed coverage.

## Credentials

At inspection, `SERV_API_KEY` and `REPPO_API_KEY` were absent from the process environment. No local .env file had been created. Do not request that the user paste keys into a chat or commit them. Configure secrets locally for the future build and expose only safe readiness booleans.

## Official source ledger

### Hackathon

- [Edition 02 event page](https://www.openserv.ai/hackathon-2): SERV requirement, Reppo track description, dates, judging dimensions, existing-project policy, submission requirements.
- [Edition 01 results](https://www.openserv.ai/hackathon): organizer confirms ASSAY as Best Overall and Open Track winner, plus separate track awards and honorable mention.

Do not transfer Edition 01-only rules or infer why a judge awarded a project without published reasoning.

### Docling

- [Quickstart](https://docling-project.github.io/docling/getting_started/quickstart/): Python DocumentConverter entry point and document export.
- [Docling repository](https://github.com/docling-project/docling): implementation, package/version/license verification.
- [Document model reference](https://docling-project.github.io/docling/reference/docling_document/): table/provenance model to check against the installed version.

Docling is deliberately reused for parsing. EvidenceGrid's original mechanism belongs above the parser.

### SERV

- [Documentation index](https://docs.openserv.ai/llms.txt).
- [Chat completions](https://docs.openserv.ai/serv-reasoning/api/chat-completions).
- [Day One guidance](https://docs.openserv.ai/serv-reasoning/day-one).
- [Models](https://docs.openserv.ai/serv-reasoning/models).

The inspected docs specify the inference-api.openserv.ai base URL and a system/developer instruction requirement. Recheck structured-output/model compatibility during implementation. Historical winner code can use different model names or flags and is not the current API contract.

### Reppo

- [Evaluation concept](https://docs.reppo.ai/concepts/evaluation-api).
- [Evaluation endpoints](https://docs.reppo.ai/api/eval/evaluations.md).
- [Live integration guide](https://eval.reppo.xyz/agents.md).

The Markdown endpoint and live guide were read through ordinary public HTTP requests after the web reader could not open some routes. No account, cookies, or private API data were accessed.

### Reppo discrepancies to preserve

At inspection the docs page and live guide disagreed about credit costs and attachment sizes. Both described required criteria, asynchronous API-key evaluation, and evalId-based read-back. The live guide additionally described a keyless lite sandbox that returns placeholders without running a judge.

Use current returned account/API behavior for actual credits, limits, and statuses. Avoid pricing claims in product copy until verified. Keep sandbox tests clearly separated from real evaluation evidence.

## Previous winner lesson and its limits

ASSAY's pre-deadline revision was inspected at commit `256aa19a79d420f96de492a3a885da65e57ccc68`. Its code re-fetches source chain evidence and distinguishes unavailable evidence from contradictory evidence. Its repository also discloses limitations, including project-controlled demonstration buyers and an unexercised solicited adjudication path.

Source: [ASSAY repository](https://github.com/OoJae/assay), especially its [verification code at that revision](https://github.com/OoJae/assay/blob/256aa19a79d420f96de492a3a885da65e57ccc68/src/verify/index.ts).

Transferable hypothesis: a concrete failure plus independently checkable source evidence can differentiate a build. This does not establish customer demand, causation of an award, or a probability of winning for EvidenceGrid.

## Open questions Claude Code must resolve through implementation

1. Can installed Docling retain the relevant merged headers, unit notes, and physical page coordinates?
2. Do all selected reports explicitly support the three requested metric definitions?
3. Does a competent one-shot baseline naturally make enough period/unit errors to justify the correction layer?
4. Does real Reppo feedback identify useful source-specific discrepancies?
5. Does the revision loop improve frozen holdout results without introducing regressions or disproportionate cost?
6. Can an analyst inspect and export a fact faster than their current manual workflow?

Only the first two require technical/source verification before a fair benchmark can be frozen. The others need measured results or real user observations; do not prefill the answers in the UI or write-up.
