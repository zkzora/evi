import { describe, expect, it } from 'vitest'
import { capabilityLabel } from './availability'
import { tourLinks } from './Tour'
import type { Capabilities } from './api'

const caps = (state: Capabilities['extraction']['state'], mode = 'live'): Capabilities => ({
  mode, stored_results: { available: true }, source_verification: { available: true, reason: '' },
  extraction: { state, reason: 'r' }, evaluation: { state: 'unavailable', reason: 'r' },
})

describe('capability-based availability', () => {
  it('never reports processing from connectivity alone', () => {
    expect(capabilityLabel('connected', caps('unavailable', 'archive')).text).toBe('Archive · stored results')
    expect(capabilityLabel('connected', caps('unavailable', 'archive')).text).not.toMatch(/connected|available/i)
    expect(capabilityLabel('connected', caps('available')).text).toBe('Live processing available')
    expect(capabilityLabel('connected', caps('busy')).text).toMatch(/busy/)
    expect(capabilityLabel('connected', caps('budget_exhausted')).text).toMatch(/allowance used/)
    expect(capabilityLabel('offline').text).toMatch(/offline/)
  })
  it('states why paid processing stopped (allowance used, ended, or absent) and keeps stored results', () => {
    const withCode = (state: Capabilities['extraction']['state'], code: string) => {
      const c = caps(state); c.extraction = { ...c.extraction, code } as Capabilities['extraction']; return c
    }
    expect(capabilityLabel('connected', withCode('budget_exhausted', 'allowance_exhausted')).text).toBe('Processing allowance used · stored results available')
    expect(capabilityLabel('connected', withCode('unavailable', 'allowance_expired')).text).toBe('Processing allowance ended · stored results available')
    expect(capabilityLabel('connected', withCode('unavailable', 'no_allowance')).text).toMatch(/No processing allowance/)
    expect(capabilityLabel('connected', withCode('budget_exhausted', 'daily_limit')).text).toBe('Processing allowance used today')
  })
  it('walkthrough deep links point at stored records and a real nine-month case', () => {
    expect(tourLinks.periodFullYear).toContain('expect_period=12')
    expect(tourLinks.periodNine).toContain('expect_period=9')
    expect(tourLinks.unitMismatch).toContain('expect_unit=USD+millions')
    expect(tourLinks.verizonFy2024).toContain('version=ver_b15ed7352811_5')
    for (const href of Object.values(tourLinks)) expect(href).not.toMatch(/parse|process\b/)
  })
})
