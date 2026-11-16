# 17 — Winner artifacts, public sources, and interface decisions

Checked November 15, 2026. This file records inspectable evidence and the limits of the comparison.

## Organizer-confirmed awards

The [Edition 01 results](https://www.openserv.ai/hackathon) identify ASSAY as Best Overall Build and Open Track winner, Shijima for Robinhood Mainnet & MCP, Payrun for Coinbase AgentKit, CapitalRail for IXS, and SERVPIT as an honorable mention. These are distinct award categories.

## Interfaces inspected

| Project | Primary artifacts checked | Observed lesson | Limit |
| --- | --- | --- | --- |
| ASSAY | [Live website](https://assay-steel.vercel.app/), [repository](https://github.com/OoJae/assay), landing hero and stage CSS | Top navigation; a specific multiplier and underlying reads in the first view; a path to a findings wall and reproducible evidence | Current website and main-branch source may include changes after judging. We did not rerun its onchain verification. The organizer result does not establish that design caused the award. |
| Payrun | [Repository](https://github.com/nice-bills/payrun), [landing component](https://github.com/nice-bills/payrun/blob/main/components/landing/Landing.tsx), [landing route](https://github.com/nice-bills/payrun/blob/main/app/page.tsx) | Leads with a concrete invoice attack, then exposes the checks and decision layers | The hero contains an authored invoice example. That does not establish it as a real customer's incident. This was source inspection, not an independently executed payment. |

ASSAY's current page was inspected visually in the browser. The public Shijima and SERVPIT URLs could not be fetched with the web research tool; no visual conclusions are asserted about them. X build links returned HTTP 403. Organizer and project sources supplied the award/project relationship.

## Decisions applied to Evi

- Home is the first top-navigation entry. Workspace is now `/workspace`.
- Home opens with an actual Verizon reporting-period comparison, with selectable real cases for AT&T, T-Mobile US, and Comcast.
- The hero opens the corresponding source explorer. It does not open an empty AI result grid.
- A second real case links Verizon's USD-million PDF scale to the base-USD observation in the SEC snapshot, following the user's international USD instruction.
- Source counts, dates, original files, accession IDs, hashes, and JSON pointers are inspectable.
- Source snapshots and metadata checks are clearly separate from future live SERV/Reppo outputs.
- The rejected organization/workspace selector card is permanently excluded by AGENTS.md and the user's global design preferences.
- Evi retains its own typography, palette, logo, and composition. No winner artwork or code was copied.

## What still matters for the Reppo entry

The [Edition 02 brief](https://www.openserv.ai/hackathon-2) asks for reliable agents that use feedback to produce measurable improvement in the Reppo track. A polished site, a large source count, and metadata comparisons do not demonstrate that improvement.

The strongest baseline for SEC records already has structured periods and units. Those records are useful for a public source explorer and direct context checks, but they are not evidence that Evi's unstructured-PDF interpretation outperforms an existing extractor. The remaining proof is the real Docling/SERV/Reppo workflow on frozen, held-out PDF labels, including regressions and missing facts.
