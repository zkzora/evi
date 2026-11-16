import type { Report } from './types'

// Real downloaded public source metadata. No extracted financial values or provider results.
export const archivedIndonesianReports: Report[] = [
  {
    document_id: 'telkom-9m2025', issuer_name: 'Telkom Indonesia', title: 'Nine-month financial statements',
    period_label: 'September 2025', source_page: 5, page_count: 114,
    source_path: '/sources/telkom-9m2025.pdf',
    source_url: 'https://www.telkom.co.id/minio/show/data/lampiran/1761831900844_original_FS-Telkom-Triwulan-III-2025-Eng-release.pdf',
    sha256: '5b9f0f7f2d4a870ecd35cfa80515e1b4ce622a02a09f9423212646c4f762e19f',
    parse_status: 'not_started', availability: 'downloaded',
  },
  {
    document_id: 'xl-q12025', issuer_name: 'XL Axiata', title: 'First-quarter financial statements',
    period_label: 'March 2025', source_page: 7, page_count: 132,
    source_path: '/sources/xl-q12025.pdf',
    source_url: 'https://staticxl.ext.xlaxiata.co.id/s3fs-public/media/documents/Reviewed%20FS%20XL%20Axiata%2031%20March%202025.pdf',
    sha256: 'abd83d733e76f343064ad8e12a8b70089be588d6c5261454b1b7797b6b474d42',
    parse_status: 'not_started', availability: 'downloaded',
  },
  {
    document_id: 'telkom-fy2024', issuer_name: 'Telkom Indonesia', title: 'Audited full-year financial statements',
    period_label: 'December 2024', source_page: 10, page_count: 121,
    source_path: '/sources/telkom-fy2024.pdf', source_url: 'https://www.telkom.co.id/minio/show/data/lampiran/1744930396440_original_Telkom%20FS%20English%20YE%202024_Release.pdf',
    sha256: '6f0d25edf4b458e7809e9e856bcc4b30aeddeec2a9d10295fd396b574c9047f0', parse_status: 'not_started', availability: 'downloaded',
  },
  {
    document_id: 'telkom-6m2025', issuer_name: 'Telkom Indonesia', title: 'Six-month financial statements',
    period_label: 'June 2025', source_page: 5, page_count: 113,
    source_path: '/sources/telkom-6m2025.pdf', source_url: 'https://www.telkom.co.id/minio/show/data/lampiran/1753965844498_original_FS%20Telkom%20Triwulan%20II%202025_Eng%20Release.pdf',
    sha256: '08eda2d78cc606ac340ed8b478ff7ab1d473cb471277fcbb6f95aaaa14e0b53e', parse_status: 'not_started', availability: 'downloaded',
  },
]

// Public international USD corpus. Original Indonesian PDFs remain archived, never silently converted.
export const sourceCatalog: Report[] = [
  {
    document_id: 'verizon-fy2025', issuer_name: 'Verizon', title: 'Annual Report on Form 10-K — 2025',
    period_label: 'December 2025 · USD', source_page: 52, page_count: 329, currency: 'USD',
    source_path: '/sources/verizon-fy2025.pdf', source_url: 'https://www.verizon.com/about/sites/default/files/2025-Annual-Report-on-Form-10k.pdf',
    sha256: 'c804f30d5957b8b4d43d1714b6405c163510cab1e282a2a383b0205d129b1508', parse_status: 'not_started', availability: 'downloaded',
  },
  {
    document_id: 'verizon-fy2024', issuer_name: 'Verizon', title: 'Annual Report on Form 10-K — 2024',
    period_label: 'December 2024 · USD', source_page: 54, page_count: 116, currency: 'USD',
    source_path: '/sources/verizon-fy2024.pdf', source_url: 'https://www.verizon.com/about/sites/default/files/2024-Annual-Report-on-Form-10k.pdf',
    sha256: '05ad83ec2279c04683b50878f8aa8ff8c868aad481b205f52e316df63c403318', parse_status: 'not_started', availability: 'downloaded',
  },
]
