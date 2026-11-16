import { afterEach, describe, expect, it, vi } from 'vitest'
import { request } from './api'
import { z } from 'zod'
afterEach(() => vi.unstubAllGlobals())
describe('Live service boundary', () => {
  it('does not treat the static HTML fallback as a connected API', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>Evi</html>', { headers: { 'content-type': 'text/html' } })))
    await expect(request('/health', z.object({ status: z.literal('ok') }))).rejects.toThrow('not connected')
  })
  it('surfaces provider errors without substituting successful results', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { message: 'Reppo credits exhausted.' } }),
      { status: 402, headers: { 'content-type': 'application/json' } })))
    await expect(request('/evaluations', z.array(z.unknown()))).rejects.toThrow('Reppo credits exhausted.')
  })
  it('rejects malformed live data', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'all good trust me' }),
      { headers: { 'content-type': 'application/json' } })))
    await expect(request('/health', z.object({ status: z.literal('ok') }))).rejects.toThrow('unsupported response')
  })
})
