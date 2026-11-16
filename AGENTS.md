# Evi implementation rules

Read CLAUDE.md, brand.md, and docs/16-frontend-live-integration-handoff.md.

## Explicit design hardening — November 15, 2026

- Never restore the rejected workspace selector card: avatar/initial + “Research workspace” + “Public access” + checkmark, or a cosmetic equivalent.
- Navigation belongs across the top. Home is the first menu entry and opens the public landing page. No sidebar.
- Public access does not need an account avatar or fake organization switcher.
- Show real financial source data and explain periods/units immediately. Counts are computed from downloaded records; repeated disclosure observations are not unique facts or detected errors.
- Source snapshots are real published data, not fresh SERV/Reppo runs. Keep those provenance types distinct. Do not fabricate results or accuracy.
- Retain English UI and the Evi name. Backend provider integration is Claude Code's next task.

## International USD presentation — latest instruction

The public landing, source explorer, and default PDF catalog use USD only. Do not convert IDR/EUR values to USD without an explicit, cited FX source and conversion policy; none is implemented. Preserve original raw sources for provenance. Public USD rows are selected from actual USD observations supplied by the SEC. The source-library default is Verizon's original USD report. Keep historical Indonesian PDFs archived for handoff rather than presenting their figures as USD.
