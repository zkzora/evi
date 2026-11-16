import { describe, expect, it } from 'vitest'
import { contextCheck, exactAmount, periodLabel } from './source-data'

describe('source context verification', () => {
  it('rejects a genuine nine-month interval requested as a full year', () => {
    expect(contextCheck('2026-01-01', '2026-09-30', 'USD', '12', 'USD')).toMatchObject({ period: 'fail', unit: 'pass', months: 9 })
  })
  it('accepts the same observation when the requested context matches', () => {
    expect(contextCheck('2026-01-01', '2026-09-30', 'USD', '9', 'USD')).toMatchObject({ period: 'pass', unit: 'pass' })
  })
  it('rejects a currency mismatch without converting the source amount', () => {
    expect(contextCheck('2026-01-01', '2026-09-30', 'USD', '9', 'IDR').unit).toBe('fail')
  })
  it('does not turn a point-in-time value into a period total', () => {
    expect(contextCheck(null, '2026-09-30', 'USD', '12', 'USD').period).toBe('unknown')
    expect(periodLabel(null, '2026-09-30')).toBe('Point in time')
  })
  it('preserves financial precision when formatting a large scaled value', () => {
    expect(exactAmount('9007199254740993123.125', 9)).toBe('9,007,199,254.740993123125')
  })
})
