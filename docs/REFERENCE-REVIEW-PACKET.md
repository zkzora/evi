# Reference review packet — references-v1 (48 targets)

Reference file: `data/references/references-v1.json`, sha256 `cb02c74f4f3b0c195f10379c7990482fc90590f0587d2bd7bb1218db22841942`, provenance: **builder-drafted, source-reviewed against printed page text (pypdf/pdfium); PROVISIONAL - not independent human gold**. Independent review: **not performed**.

How to review: for each target, open the issuer PDF at the physical page (or the rendered page image with numbered boxes), confirm the printed amount, row, column year and interval heading, unit statement and scope, then record the outcome in `data/references/review/review-sheet-references-v1.json` (status `confirmed` / `corrected` / `ambiguous`, reviewer name, date, rationale, and proposed corrected fields). Corrections go into a NEW file `references-v2.json` with a change log; references-v1 is never edited. Machine re-verification of certificates is not a substitute for this review.

Known points needing a reviewer's judgment:
- **AT&T owner-attributable profit**: the draft uses "Net Income (Loss) Attributable to AT&T" (before preferred dividends), not "…Attributable to Common Stock". Confirm this policy is the intended definition of 'owners of the parent'.
- **AT&T exact dates**: the statement page prints "Third Quarter"/"Nine-Month Period" ("Second Quarter"/"Six-Month Period") and years but no end date. The draft sets end/start = null. Dates from the cover page or other pages would be outside the parsed statement-page coverage.
- **Verizon start dates**: printed headings state only the end; start dates are derived (month-end calendar rule). A reviewer should confirm Verizon reports calendar quarters/years (no 52/53-week convention).
- **Currency**: references use the code `USD`; the page prints "$" and "dollars".

## verizon-fy2025 — Annual Report on Form 10-K — 2025

- Issuer URL: https://www.verizon.com/about/sites/default/files/2025-Annual-Report-on-Form-10k.pdf
- SHA-256: `c804f30d5957b8b4d43d1714b6405c163510cab1e282a2a383b0205d129b1508`
- Physical page: 52 of 329
- Split / exposure: development; builder-exposed; featured in demos (Verizon)
- Rendered page with numbered target boxes: `artifacts/reference-review/verizon-fy2025-p52.png`

| # | Target | Printed row label | Printed amount | Scope | Unit / scale | Interval heading | Year header | Draft end / start | Date basis | Value-cell region (PDF pt, top-left origin) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `verizon-fy2025:revenue:12M:2025` | Total Operating Revenues | 138,191 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | header-row label states the table interval: Years Ended December 31, | 2025 | 2025-12-31 / 2025-01-01 | printed column heading (month-end calendar) | l 403, t 155, r 431, b 162 |
| 2 | `verizon-fy2025:operating_profit:12M:2025` | Operating Income | 29,259 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | header-row label states the table interval: Years Ended December 31, | 2025 | 2025-12-31 / 2025-01-01 | printed column heading (month-end calendar) | l 407, t 257, r 431, b 264 |
| 3 | `verizon-fy2025:profit_attributable_to_owners:12M:2025` | Net income attributable to Verizon | 17,174 | consolidated_parent | USD × 1000000 ("(dollars in millions, except per share amounts)") | header-row label states the table interval: Years Ended December 31, | 2025 | 2025-12-31 / 2025-01-01 | printed column heading (month-end calendar) | l 407, t 350, r 431, b 357 |
| 4 | `verizon-fy2025:revenue:12M:2024` | Total Operating Revenues | 134,788 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | header-row label states the table interval: Years Ended December 31, | 2024 | 2024-12-31 / 2024-01-01 | printed column heading (month-end calendar) | l 475, t 155, r 502, b 162 |
| 5 | `verizon-fy2025:operating_profit:12M:2024` | Operating Income | 28,686 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | header-row label states the table interval: Years Ended December 31, | 2024 | 2024-12-31 / 2024-01-01 | printed column heading (month-end calendar) | l 479, t 257, r 502, b 264 |
| 6 | `verizon-fy2025:profit_attributable_to_owners:12M:2024` | Net income attributable to Verizon | 17,506 | consolidated_parent | USD × 1000000 ("(dollars in millions, except per share amounts)") | header-row label states the table interval: Years Ended December 31, | 2024 | 2024-12-31 / 2024-01-01 | printed column heading (month-end calendar) | l 479, t 350, r 502, b 357 |

## verizon-fy2024 — Annual Report on Form 10-K — 2024

- Issuer URL: https://www.verizon.com/about/sites/default/files/2024-Annual-Report-on-Form-10k.pdf
- SHA-256: `05ad83ec2279c04683b50878f8aa8ff8c868aad481b205f52e316df63c403318`
- Physical page: 54 of 116
- Split / exposure: development; builder-exposed; featured in demos (Verizon)
- Rendered page with numbered target boxes: `artifacts/reference-review/verizon-fy2024-p54.png`

| # | Target | Printed row label | Printed amount | Scope | Unit / scale | Interval heading | Year header | Draft end / start | Date basis | Value-cell region (PDF pt, top-left origin) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `verizon-fy2024:revenue:12M:2024` | Total Operating Revenues | 134,788 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | header-row label states the table interval: Years Ended December 31, | 2024 | 2024-12-31 / 2024-01-01 | printed column heading (month-end calendar) | l 388, t 149, r 421, b 157 |
| 2 | `verizon-fy2024:operating_profit:12M:2024` | Operating Income | 28,686 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | header-row label states the table interval: Years Ended December 31, | 2024 | 2024-12-31 / 2024-01-01 | printed column heading (month-end calendar) | l 393, t 269, r 421, b 277 |
| 3 | `verizon-fy2024:profit_attributable_to_owners:12M:2024` | Net income attributable to Verizon | 17,506 | consolidated_parent | USD × 1000000 ("(dollars in millions, except per share amounts)") | header-row label states the table interval: Years Ended December 31, | 2024 | 2024-12-31 / 2024-01-01 | printed column heading (month-end calendar) | l 393, t 377, r 421, b 385 |
| 4 | `verizon-fy2024:revenue:12M:2023` | Total Operating Revenues | 133,974 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | header-row label states the table interval: Years Ended December 31, | 2023 | 2023-12-31 / 2023-01-01 | printed column heading (month-end calendar) | l 452, t 149, r 485, b 157 |
| 5 | `verizon-fy2024:operating_profit:12M:2023` | Operating Income | 22,877 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | header-row label states the table interval: Years Ended December 31, | 2023 | 2023-12-31 / 2023-01-01 | printed column heading (month-end calendar) | l 457, t 269, r 484, b 277 |
| 6 | `verizon-fy2024:profit_attributable_to_owners:12M:2023` | Net income attributable to Verizon | 11,614 | consolidated_parent | USD × 1000000 ("(dollars in millions, except per share amounts)") | header-row label states the table interval: Years Ended December 31, | 2023 | 2023-12-31 / 2023-01-01 | printed column heading (month-end calendar) | l 457, t 377, r 484, b 385 |

## verizon-3q2025 — 3Q 2025 Financial Statements

- Issuer URL: https://www.verizon.com/about/file/76633/download?token=P8wDXRsG
- SHA-256: `8b4249c1ca915374587570b79536c9dd9b46fc1b345a11285f51cbd8518697f4`
- Physical page: 1 of 10
- Split / exposure: development; builder-exposed; featured in demos (Verizon)
- Rendered page with numbered target boxes: `artifacts/reference-review/verizon-3q2025-p1.png`

| # | Target | Printed row label | Printed amount | Scope | Unit / scale | Interval heading | Year header | Draft end / start | Date basis | Value-cell region (PDF pt, top-left origin) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `verizon-3q2025:revenue:3M:2025` | Total Operating Revenues | 33,821 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | 3 Mos. Ended 9/30/25 | 3 Mos. Ended 9/30/25 | 2025-09-30 / 2025-07-01 | printed column heading (month-end calendar) | l 279, t 150, r 301, b 156 |
| 2 | `verizon-3q2025:operating_profit:3M:2025` | Operating Income | 8,105 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | 3 Mos. Ended 9/30/25 | 3 Mos. Ended 9/30/25 | 2025-09-30 / 2025-07-01 | printed column heading (month-end calendar) | l 283, t 265, r 301, b 271 |
| 3 | `verizon-3q2025:profit_attributable_to_owners:3M:2025` | Net income attributable to Verizon | 4,950 | consolidated_parent | USD × 1000000 ("(dollars in millions, except per share amounts)") | 3 Mos. Ended 9/30/25 | 3 Mos. Ended 9/30/25 | 2025-09-30 / 2025-07-01 | printed column heading (month-end calendar) | l 283, t 379, r 301, b 386 |
| 4 | `verizon-3q2025:revenue:3M:2024` | Total Operating Revenues | 33,330 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | 3 Mos. Ended 9/30/24 | 3 Mos. Ended 9/30/24 | 2024-09-30 / 2024-07-01 | printed column heading (month-end calendar) | l 343, t 150, r 364, b 156 |
| 5 | `verizon-3q2025:operating_profit:3M:2024` | Operating Income | 5,926 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | 3 Mos. Ended 9/30/24 | 3 Mos. Ended 9/30/24 | 2024-09-30 / 2024-07-01 | printed column heading (month-end calendar) | l 347, t 265, r 364, b 271 |
| 6 | `verizon-3q2025:profit_attributable_to_owners:3M:2024` | Net income attributable to Verizon | 3,306 | consolidated_parent | USD × 1000000 ("(dollars in millions, except per share amounts)") | 3 Mos. Ended 9/30/24 | 3 Mos. Ended 9/30/24 | 2024-09-30 / 2024-07-01 | printed column heading (month-end calendar) | l 347, t 379, r 364, b 386 |
| 7 | `verizon-3q2025:revenue:9M:2025` | Total Operating Revenues | 101,810 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | 9 Mos. Ended 9/30/25 | 9 Mos. Ended 9/30/25 | 2025-09-30 / 2025-01-01 | printed column heading (month-end calendar) | l 439, t 150, r 464, b 156 |
| 8 | `verizon-3q2025:operating_profit:9M:2025` | Operating Income | 24,255 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | 9 Mos. Ended 9/30/25 | 9 Mos. Ended 9/30/25 | 2025-09-30 / 2025-01-01 | printed column heading (month-end calendar) | l 443, t 265, r 464, b 271 |
| 9 | `verizon-3q2025:profit_attributable_to_owners:9M:2025` | Net income attributable to Verizon | 14,832 | consolidated_parent | USD × 1000000 ("(dollars in millions, except per share amounts)") | 9 Mos. Ended 9/30/25 | 9 Mos. Ended 9/30/25 | 2025-09-30 / 2025-01-01 | printed column heading (month-end calendar) | l 443, t 379, r 464, b 386 |
| 10 | `verizon-3q2025:revenue:9M:2024` | Total Operating Revenues | 99,107 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | 9 Mos. Ended 9/30/24 | 9 Mos. Ended 9/30/24 | 2024-09-30 / 2024-01-01 | printed column heading (month-end calendar) | l 507, t 150, r 528, b 156 |
| 11 | `verizon-3q2025:operating_profit:9M:2024` | Operating Income | 21,265 | consolidated | USD × 1000000 ("(dollars in millions, except per share amounts)") | 9 Mos. Ended 9/30/24 | 9 Mos. Ended 9/30/24 | 2024-09-30 / 2024-01-01 | printed column heading (month-end calendar) | l 507, t 265, r 528, b 271 |
| 12 | `verizon-3q2025:profit_attributable_to_owners:9M:2024` | Net income attributable to Verizon | 12,501 | consolidated_parent | USD × 1000000 ("(dollars in millions, except per share amounts)") | 9 Mos. Ended 9/30/24 | 9 Mos. Ended 9/30/24 | 2024-09-30 / 2024-01-01 | printed column heading (month-end calendar) | l 507, t 379, r 528, b 386 |

## att-3q2025 — 3Q 2025 Financial and Operational Schedules

- Issuer URL: https://investors.att.com/~/media/Files/A/ATT-IR-V2/financial-reports/quarterly-earnings/2025/3Q-2025/3Q25_ATT_Financial_and_Operational_Schedules_and_Non_GAAP_Reconciliations.pdf
- SHA-256: `064b25a85c218185f10509dec7838b3384351b80ce487b1b0e7c272a1ae8c2d0`
- Physical page: 2 of 20
- Split / exposure: issuer-separated holdout; builder read these pages while designing rules and transcribing references (not unseen)
- Rendered page with numbered target boxes: `artifacts/reference-review/att-3q2025-p2.png`

| # | Target | Printed row label | Printed amount | Scope | Unit / scale | Interval heading | Year header | Draft end / start | Date basis | Value-cell region (PDF pt, top-left origin) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `att-3q2025:revenue:3M:2025` | Total Operating Revenues | 30,709 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Third Quarter | 2025 | null / null | no end date printed on the statement page | l 289, t 178, r 315, b 189 |
| 2 | `att-3q2025:operating_profit:3M:2025` | Operating Income | 6,119 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Third Quarter | 2025 | null / null | no end date printed on the statement page | l 292, t 321, r 315, b 332 |
| 3 | `att-3q2025:profit_attributable_to_owners:3M:2025` | Net Income (Loss) Attributable to AT&T | 9,314 | consolidated_parent | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Third Quarter | 2025 | null / null | no end date printed on the statement page | l 269, t 436, r 318, b 447 |
| 4 | `att-3q2025:revenue:3M:2024` | Total Operating Revenues | 30,213 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Third Quarter | 2024 | null / null | no end date printed on the statement page | l 338, t 178, r 365, b 189 |
| 5 | `att-3q2025:operating_profit:3M:2024` | Operating Income | 2,116 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Third Quarter | 2024 | null / null | no end date printed on the statement page | l 341, t 322, r 365, b 333 |
| 6 | `att-3q2025:profit_attributable_to_owners:3M:2024` | Net Income (Loss) Attributable to AT&T | (174) | consolidated_parent | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Third Quarter | 2024 | null / null | no end date printed on the statement page | l 320, t 435, r 367, b 446 |
| 7 | `att-3q2025:revenue:9M:2025` | Total Operating Revenues | 92,182 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Nine-Month Period | 2025 | null / null | no end date printed on the statement page | l 435, t 178, r 461, b 189 |
| 8 | `att-3q2025:operating_profit:9M:2025` | Operating Income | 18,374 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Nine-Month Period | 2025 | null / null | no end date printed on the statement page | l 435, t 322, r 462, b 333 |
| 9 | `att-3q2025:profit_attributable_to_owners:9M:2025` | Net Income (Loss) Attributable to AT&T | 18,165 | consolidated_parent | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Nine-Month Period | 2025 | null / null | no end date printed on the statement page | l 417, t 436, r 463, b 447 |
| 10 | `att-3q2025:revenue:9M:2024` | Total Operating Revenues | 90,038 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Nine-Month Period | 2024 | null / null | no end date printed on the statement page | l 485, t 178, r 512, b 189 |
| 11 | `att-3q2025:operating_profit:9M:2024` | Operating Income | 13,723 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Nine-Month Period | 2024 | null / null | no end date printed on the statement page | l 485, t 321, r 512, b 332 |
| 12 | `att-3q2025:profit_attributable_to_owners:9M:2024` | Net Income (Loss) Attributable to AT&T | 6,868 | consolidated_parent | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Nine-Month Period | 2024 | null / null | no end date printed on the statement page | l 469, t 436, r 510, b 447 |

## att-2q2025 — 2Q 2025 Financial and Operational Schedules

- Issuer URL: https://investors.att.com/~/media/Files/A/ATT-IR-V2/financial-reports/quarterly-earnings/2025/2Q-2025/2Q25_ATT_Financial_and_Operational_Schedules_and_Non_GAAP_Reconciliations.pdf
- SHA-256: `0065aa98bd90d5f59d9b6c05c6921397c97e3fba5f49b3b53e1f6ae3a522450b`
- Physical page: 2 of 20
- Split / exposure: issuer-separated holdout; builder read these pages while designing rules and transcribing references (not unseen)
- Rendered page with numbered target boxes: `artifacts/reference-review/att-2q2025-p2.png`

| # | Target | Printed row label | Printed amount | Scope | Unit / scale | Interval heading | Year header | Draft end / start | Date basis | Value-cell region (PDF pt, top-left origin) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `att-2q2025:revenue:3M:2025` | Total Operating Revenues | 30,847 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Second Quarter | 2025 | null / null | no end date printed on the statement page | l 289, t 178, r 315, b 189 |
| 2 | `att-2q2025:operating_profit:3M:2025` | Operating Income | 6,501 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Second Quarter | 2025 | null / null | no end date printed on the statement page | l 292, t 321, r 314, b 332 |
| 3 | `att-2q2025:profit_attributable_to_owners:3M:2025` | Net Income Attributable to AT&T | 4,500 | consolidated_parent | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Second Quarter | 2025 | null / null | no end date printed on the statement page | l 269, t 435, r 316, b 446 |
| 4 | `att-2q2025:revenue:3M:2024` | Total Operating Revenues | 29,797 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Second Quarter | 2024 | null / null | no end date printed on the statement page | l 338, t 178, r 365, b 189 |
| 5 | `att-2q2025:operating_profit:3M:2024` | Operating Income | 5,760 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Second Quarter | 2024 | null / null | no end date printed on the statement page | l 341, t 321, r 365, b 332 |
| 6 | `att-2q2025:profit_attributable_to_owners:3M:2024` | Net Income Attributable to AT&T | 3,597 | consolidated_parent | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Second Quarter | 2024 | null / null | no end date printed on the statement page | l 320, t 435, r 366, b 446 |
| 7 | `att-2q2025:revenue:6M:2025` | Total Operating Revenues | 61,473 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Six-Month Period | 2025 | null / null | no end date printed on the statement page | l 435, t 178, r 461, b 189 |
| 8 | `att-2q2025:operating_profit:6M:2025` | Operating Income | 12,255 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Six-Month Period | 2025 | null / null | no end date printed on the statement page | l 435, t 322, r 462, b 333 |
| 9 | `att-2q2025:profit_attributable_to_owners:6M:2025` | Net Income Attributable to AT&T | 8,851 | consolidated_parent | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Six-Month Period | 2025 | null / null | no end date printed on the statement page | l 417, t 436, r 462, b 447 |
| 10 | `att-2q2025:revenue:6M:2024` | Total Operating Revenues | 59,825 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Six-Month Period | 2024 | null / null | no end date printed on the statement page | l 486, t 178, r 512, b 188 |
| 11 | `att-2q2025:operating_profit:6M:2024` | Operating Income | 11,607 | consolidated | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Six-Month Period | 2024 | null / null | no end date printed on the statement page | l 485, t 321, r 512, b 332 |
| 12 | `att-2q2025:profit_attributable_to_owners:6M:2024` | Net Income Attributable to AT&T | 7,042 | consolidated_parent | USD × 1000000 ("Dollars in millions except per share amounts Unaudited") | Six-Month Period | 2024 | null / null | no end date printed on the statement page | l 469, t 436, r 511, b 447 |

## Review status

0 of 48 targets reviewed. No reviewer has been assigned. This packet does not mark any reference as verified.
