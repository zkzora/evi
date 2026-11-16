import type { FactVersion } from './types'

// coverage-v1 is an additive server view; exports keep 'exact dates not printed' distinct from complete verification.
const coverage = (f: unknown) => (f as { context_coverage?: { label: string; exact_interval: string } }).context_coverage
const csvCell = (value: unknown) => {
  let text = value == null ? '' : String(value)
  // Spreadsheet formula injection: preserve numbers but neutralize text commands.
  if (/^[=+@\t\r]/.test(text) || (/^-/.test(text) && !/^-\d/.test(text))) text = `'${text}`
  return `"${text.replace(/"/g, '""')}"`
}
export function versionCSV(version: FactVersion, sourceUrl: string, sourceHash: string, sourceKind = 'registered', pages = ''): string {
  const headers = ['version_id','origin','fact_id','metric','reported_value','currency','unit_scale','normalized_value',
    'start_date','end_date','duration_months','period_label','context_coverage','exact_interval','evidence_ids','checks','source_url','source_sha256',
    'source_kind','physical_pages','policy_version']
  const policy = String((version as unknown as { policy_version?: string }).policy_version ?? '')
  const rows = version.facts.map(f => [version.version_id, f.origin, f.fact_id, f.metric, f.reported_value, f.currency,
    f.unit_scale, f.normalized_value, f.period.start_date, f.period.end_date, f.period.duration_months,
    f.period.label, coverage(f)?.label ?? 'not assessed', coverage(f)?.exact_interval ?? 'not assessed', Object.values(f.evidence).flat().join(';'),
    version.checks.filter(c => c.fact_id === f.fact_id).map(c => `${c.check_type}:${c.status}`).join(';'), sourceUrl, sourceHash,
    sourceKind, pages, policy])
  return [headers, ...rows].map(row => row.map(csvCell).join(',')).join('\r\n')
}
export function download(content: string, filename: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }))
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click()
  setTimeout(() => URL.revokeObjectURL(url), 5000)
}
export function decimalDisplay(value: string | null): string {
  if (value === null) return 'Unresolved'
  if (!/^-?\d+(\.\d+)?$/.test(value)) return value
  const [integer, fraction] = value.split('.')
  return integer.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (fraction ? `.${fraction}` : '')
}
