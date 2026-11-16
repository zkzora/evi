# Evi frontend verification — latest USD release

Verified November 15, 2026 (Asia/Jakarta).

- Production build and TypeScript compilation pass.
- Automated suite: 4 files, 15 tests. Includes API validation, precision-preserving exports, period/unit context checks, every normalized source shard and its hashes, source-count reconciliation, and exact original SEC entries for featured comparisons.
- Real downloaded responses: 128,748 observations in their original units. Public USD-only shards: 103,644 observations; 4,037 observations across the three core metrics. These counts include repeated comparative disclosures, not unique facts or detected errors.
- Browser: Home, Real data, Documents, Workspace; top navigation and Home first. Rejected organization/workspace card is absent.
- Real period check: Verizon 9-month revenue 103.006 billion USD fails a full-year request; the same observation passes a 9-month request. An incompatible source unit is rejected.
- Real scale case: Verizon FY2025 PDF physical page 52 reports 138,191 in USD millions; the SEC source reports 138191000000 USD. The exact source observation opens from Home.
- PDF.js renders the original Verizon source at physical page 52; canvas and page controls were checked.
- Source search, year/metric filters, company selection, and pagination tested. Selected inspector record updates when filtering removes it.
- Actual downloaded JSON export inspected: correct amount, unit, interval, accession, original SHA-256, original-array JSON pointer, and the user's check result.
- Responsive checks at 375, 768, and 1280 pixels. No whole-page horizontal overflow in measured mobile/tablet layouts. Narrow source tables scroll inside their own panel.
- Windows preview watcher excludes artifacts and raw downloads, preventing file-lock watch failures when exporting QA artifacts.

Artifacts:
- evi-home-usd.jpg / evi-mobile.jpg: current Home preview.
- evi-data-usd.jpg: real source explorer and actual period mismatch.
- evi-usd-context-check.json: actual browser-exported USD observation and scale check.
- Older evi-desktop.jpg/evi-preview.jpg filenames now show the new top-navigation Home; the rejected layout is not reused.

No live Docling, SERV, Reppo, revision, accuracy benchmark, or public deployment was executed. Source snapshots are genuine published data, explicitly dated, and distinct from provider results. Claude Code continues the backend using documents 16–18. The local dev server remains available for the user's requested interactive preview.
