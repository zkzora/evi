import { describe, expect, it } from 'vitest'
import { decimalDisplay, versionCSV } from './export'
import { benchmarkSchema, versionSchema } from './types'

describe('Exact analyst exports', () => {
  it('formats large decimal strings without rounding through a floating point number', () => {
    expect(decimalDisplay('123456789012345678901.25')).toBe('123,456,789,012,345,678,901.25')
    expect(decimalDisplay(null)).toBe('Unresolved')
    expect(decimalDisplay('-1000000.01')).toBe('-1,000,000.01')
  })
  it('keeps missing results, original interval, scale, and source provenance in the export', () => {
    const version = versionSchema.parse({ version_id: 'v1', run_id: 'r1', origin: 'serv_initial', facts: [{
      fact_id: 'f1', document_id: 'source', metric: 'revenue', metric_label: 'Revenue', scope: 'consolidated',
      reported_value: null, currency: 'IDR', unit_scale: '1000000', normalized_value: null,
      period: { start_date: '2025-01-01', end_date: '2025-09-30', duration_months: 9, kind: 'year_to_date', label: 'Nine months' },
      evidence: { value_ids: [], metric_ids: [], period_ids: ['p1'], unit_ids: ['u1'] }, origin: 'serv_initial',
    }] })
    const csv = versionCSV(version, 'https://issuer.example/report.pdf', 'source-hash')
    expect(csv).toContain('"2025-09-30","9","Nine months","not assessed","not assessed"')
    expect(csv).toContain('"IDR","1000000",""')
    expect(csv).toContain('https://issuer.example/report.pdf')
    expect(csv).toContain('source-hash')
    expect(csv.split('\r\n')).toHaveLength(2)
  })
  it('escapes spreadsheet command text rather than executing source text on open', () => {
    const version = versionSchema.parse({ version_id: '=HYPERLINK("x")', run_id: 'r', origin: 'serv_initial', facts: [{
      fact_id: 'f', document_id: 'd', metric: 'revenue', metric_label: 'Revenue', scope: 'consolidated',
      reported_value: '0', currency: 'IDR', unit_scale: '1', normalized_value: '0', origin: 'serv_initial',
      period: { start_date: null, end_date: null, duration_months: null, kind: 'unknown', label: '@malicious' },
      evidence: { value_ids: [], metric_ids: [], period_ids: [], unit_ids: [] },
    }] })
    expect(versionCSV(version, 'https://issuer.example', 'hash')).toContain("'@malicious")
    expect(versionCSV(version, '', '')).toContain("'=HYPERLINK")
  })
})
describe('Measured results contract', () => {
  it('rejects missing denominators and impossible accuracy counts', () => {
    const data = { benchmark_id: 'b', split: 'holdout', created_at: '2026-11-15', document_count: 2,
      baseline: { correct: 4, total: 3 }, revised: { correct: 1, total: 3 }, regressions: 0, label_provenance: 'Human reviewed' }
    expect(benchmarkSchema.safeParse(data).success).toBe(false)
    expect(benchmarkSchema.safeParse({ ...data, baseline: { correct: 0, total: 0 } }).success).toBe(false)
  })
  it('keeps an unprinted exact interval distinct from complete verification (coverage-v1)', () => {
    const version = versionSchema.parse({ version_id: 'v2', run_id: 'r2', origin: 'serv_initial', facts: [{
      fact_id: 'f2', document_id: 'att-2q2025', metric: 'revenue', metric_label: 'Total Operating Revenues', scope: 'consolidated',
      reported_value: '30847', currency: 'USD', unit_scale: '1000000', normalized_value: '30847000000',
      period: { start_date: null, end_date: null, duration_months: 3, kind: 'quarter', label: 'Second Quarter 2025' },
      evidence: { value_ids: ['v'], metric_ids: ['m'], period_ids: ['p'], unit_ids: ['u'] }, origin: 'serv_initial',
      context_coverage: { label: 'Supported reading; exact interval dates are not printed in the source', exact_interval: 'not_printed_in_source',
        complete_required_context: false, unique_supported_reading: true },
    }] })
    const csv = versionCSV(version, 'https://issuer.example/att.pdf', 'h')
    expect(csv).toContain('"","","3","Second Quarter 2025","Supported reading; exact interval dates are not printed in the source","not_printed_in_source"')
    expect(csv).not.toContain('complete period and unit context')
  })
})
