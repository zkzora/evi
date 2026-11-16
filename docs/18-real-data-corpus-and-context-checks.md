# 18 — Real source corpus and frontend context checker

## Actual dataset

Downloaded November 15, 2026 from the official SEC Company Facts API. The exact downloaded responses contain **128,748 observations** across all original units. Following the latest user instruction, the public interface includes **103,644 actual USD observations** from six telecom/connectivity issuers, of which **4,037 observations map to the three core metrics**. Non-USD observations are excluded from browser shards; no currency conversion is performed. Counts are computed from actual downloaded arrays, not target/marketing estimates.

| Company | CIK | Public USD observations |
| --- | --- | ---: |
| Verizon | 732712 | 25,685 |
| AT&T | 732717 | 27,885 |
| T-Mobile US | 1283699 | 26,598 |
| Comcast | 1166691 | 22,696 |
| Vodafone | 839923 | 28 |
| Telkom Indonesia | 1001807 | 752 |

Each official URL is in public/datasets/manifest.json. The [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) explains standard-taxonomy, entity-wide facts and differing reporting dates. The data is real published information, stored locally as an explicitly dated source snapshot. No provider key is required to inspect it.

Comparative observations repeated across filings are retained. They are not unique economic facts, unique financial statements, user records, or detected issuer errors. The corpus has not been scored for extraction accuracy. Do not replace the actual total with two million. Vodafone has limited USD disclosures and no observations in the three core-metric mappings; its view defaults to all available USD concepts instead. Original EUR figures are not converted.

A quarterly Financial Statement Data Sets ZIP was researched, but direct download returned HTTP 403. The accessible official Company Facts API was used instead; no third-party mirror silently replaced it.

## Rebuild and audit

```powershell
python scripts/download-companyfacts.py
python scripts/build-source-catalog.py
npm test
npm run build
```

The downloader reuses existing files. To refresh a snapshot, deliberately download a new version, record the new retrieval date, rebuild the manifest, and review changed counts/cases. The Verizon source was initially downloaded directly from its official URL. Its raw file is preserved just like the other five.

- data/raw/*-companyfacts.json: exact original responses retained locally.
- public/datasets/*-source.json: same original responses available to the reviewer.
- public/datasets/{company}.json: normalized, columnar browser shards.
- public/datasets/manifest.json: counts, source URLs, exact-file SHA-256 hashes, case records, cutoff, and definitions.
- src/data-manifest.json: small generated manifest used by the UI.
- Original array indices survive sorting/filtering. Exported JSON pointers escape special characters.
- Values remain decimal strings; display-scale formatting shifts text without floating-point conversion.
- Missing source labels use the actual taxonomy tag as a fallback; no missing financial values are filled.
- Browser loading verifies the normalized shard's SHA-256 and record count before showing results.
- Integrity tests validate every company shard, hash, total, and featured-case source pointer against original responses.

## Real cases

Verizon accession 0000732712-26-000052 reports revenue of USD 34,313,000,000 for July–September 2026 and USD 103,006,000,000 for January–September 2026. Both end September 30; their difference is USD 68,693,000,000. Both observations are valid disclosures. The source should not be accused of an error.

Comparable latest revenue pairs are stored for AT&T, T-Mobile US, and Comcast. The builder also counts 861 qualifying same-filing/concept/unit/end-date contexts with a 3-month observation and a longer 6-/9-month observation. This is a count of period contexts, not detected errors or an accuracy denominator.

Verizon's 2025 original Annual Report on Form 10-K states revenue of 138,191 in millions of dollars on physical page 52. The Company Facts record for 2025-01-01 through 2025-12-31 reports 138191000000 USD, accession 0000732712-26-000007. Multiplication by one million reconciles the two, without FX conversion. Home links to both the PDF and that exact annual observation.

## Frontend behavior

- `/` — public landing; actual source figures and period selector.
- `/data?company=verizon` — read-only source explorer; company, core/all metrics, search, year filter, 25-row pagination.
- Observation inspector: exact dates, original unit, scaled display, alternate interval from the same filing, original API, original JSON, filing link, source hash.
- Context checker: compares the selected observation with the user's intended interval and unit. A mismatch means it is unsuitable for that selection, not that the issuer filed incorrect data.
- Period labels classify inclusive day counts into documented bands: 3 months 60–120 days; 6 months 150–210; 9 months 240–310; 12 months 330–400. These are coarse labels. Exact start/end dates remain authoritative; unclassified durations return unknown.
- The USD-only interface compares intended source units (base USD, USD millions, USD billions). The original SEC amount is in base USD; display formatting does not change its stored unit. A scale mismatch is rejected. No FX conversion or annualization occurs.
- Export includes source provenance, the actual array pointer, and the user's metadata-check result only when they ran it.

This is working browser-side deterministic verification of published metadata. It is not a synthetic demo and does not impersonate a live Docling extraction, SERV reasoning call, Reppo score, revision, or frozen-label benchmark.

## PDF library

The public PDF catalog now starts with two original USD issuer reports: Verizon FY2025 (329 physical pages; income statement at page 52) and Verizon FY2024 (116 pages; income statement at page 54). Publisher URLs and SHA-256 hashes are in src/catalog.ts.

Four previously downloaded Indonesian PDFs remain preserved on disk and in archivedIndonesianReports, outside the default public catalog. Their original currencies are never relabeled as USD. Their presence does not mean Docling parsing or evaluation has run.

## Backend continuation

Keep document 16's live API contract for `/workspace`, `/documents`, `/feedback`, and `/benchmark`. The SEC source explorer is a separate public-data surface. It must not populate immutable live extraction versions or the benchmark with source snapshots. The newest user instruction requires an international USD presentation. Claude Code should finalize a 4–6-report USD corpus and freeze its labels/splits before tuning. The earlier Indonesian evaluation plan is historical; no benchmark has been executed or relabeled by this change.

Public deployment still requires backend hosting, secret configuration, public compute limits, SPA routing, and real end-to-end validation. No public URL or fresh AI/provider execution is claimed by this delivery.
