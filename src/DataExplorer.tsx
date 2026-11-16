import { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowDownToLine, ArrowRight, ArrowUpRight, Check, ChevronLeft, ChevronRight, Database, ExternalLink, FileSearch, Info, Loader2, Search, ShieldCheck, TriangleAlert } from 'lucide-react'
import { download } from './export'
import { contextCheck, exactAmount, filingURL, number, periodLabel, sourceLabel, sourceManifest, sourcePayloadSchema } from './source-data'
import type { SourcePayload, SourceRow } from './source-data'
import { metricNames } from './types'

export default function DataExplorer() {
  const [companyID, setCompanyID] = useState(() => new URLSearchParams(location.search).get('company') || 'verizon')
  const company = sourceManifest.companies.find(c => c.id === companyID) || sourceManifest.companies[0]
  const [data, setData] = useState<SourcePayload | null>(null)
  const [selected, setSelected] = useState<SourceRow | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [metric, setMetric] = useState(() => sourceManifest.companies.find(c => c.id === companyID)?.core_count === 0 ? 'all' : 'core')
  const [year, setYear] = useState('all')
  const [page, setPage] = useState(0)
  const [scale, setScale] = useState(9)
  const [expectedPeriod, setExpectedPeriod] = useState('12')
  const [expectedUnit, setExpectedUnit] = useState('USD')
  const [checked, setChecked] = useState(false)
  useEffect(() => {
    const abort = new AbortController()
    setLoading(true); setError(''); setData(null); setSelected(null)
    fetch(company.data_path, { signal: abort.signal }).then(async response => {
      if (!response.ok) throw new Error('The source snapshot could not be loaded.')
      const bytes = await response.arrayBuffer()
      const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('')
      if (digest !== company.data_sha256) throw new Error('The source file does not match its recorded hash. No observations have been substituted.')
      const parsed = sourcePayloadSchema.safeParse(JSON.parse(new TextDecoder().decode(bytes)))
      if (!parsed.success) throw new Error('The snapshot format could not be read. Retry or inspect the source manifest.')
      const payload = parsed.data
      if (payload.company !== company.id || payload.rows.length !== company.observation_count) throw new Error('The source snapshot does not match its manifest.')
      if (abort.signal.aborted) return
      setData(payload)
      const requestedCase = sourceManifest.cases.find(c => c.id === new URLSearchParams(location.search).get('source_case') && c.long.company === company.id)
      const featured = (requestedCase ?? sourceManifest.cases.find(c => c.long.company === company.id))?.long
      const annualCase = company.id === 'verizon' && new URLSearchParams(location.search).get('source_case') === 'verizon-fy2025-revenue'
        ? payload.rows.find(r => payload.concepts[r[0]].tag === 'Revenues' && r[2] === '2025-01-01' && r[3] === '2025-12-31' && r[5] === '0000732712-26-000007') : null
      setSelected(annualCase || (featured ? payload.rows.find(r => payload.concepts[r[0]].tag === featured.tag && r[2] === featured.start && r[3] === featured.end && r[5] === featured.accession) || null : payload.rows.find(r => payload.concepts[r[0]].metric === 'revenue' && r[1] === 'USD') || payload.rows.find(r => payload.concepts[r[0]].metric !== null) || payload.rows[0] || null))
    }).catch(e => { if (!abort.signal.aborted) setError(e instanceof Error ? e.message : 'Unable to read this source.') }).finally(() => { if (!abort.signal.aborted) setLoading(false) })
    return () => abort.abort()
  }, [company.id, company.data_path, company.data_sha256, company.observation_count, attempt])
  const urlCheck = useRef(new URLSearchParams(location.search))
  useEffect(() => {
    if (!selected) return
    // Deep links (e.g. the Try Evi walkthrough) may preset the intended context once, for the case's own observation.
    const q = urlCheck.current
    const caseRow = sourceManifest.cases.find(c => c.id === q.get('source_case'))?.long
    if (caseRow && q.get('expect_period') && selected[2] === caseRow.start && selected[3] === caseRow.end) {
      setExpectedPeriod(q.get('expect_period')!); setExpectedUnit(q.get('expect_unit') || selected[1]); setChecked(q.get('check') === '1')
      urlCheck.current = new URLSearchParams()
      setTimeout(() => document.querySelector('.context-check')?.scrollIntoView({ block: 'center' }), 300)
      return
    }
    setExpectedPeriod(selected[2] ? '12' : 'instant'); setExpectedUnit(selected[1]); setChecked(false)
  }, [selected])
  useEffect(() => { setPage(0) }, [companyID, query, metric, year])
  const filtered = useMemo(() => {
    if (!data) return []
    const q = query.trim().toLowerCase()
    return data.rows.filter(row => {
      const concept = data.concepts[row[0]]
      return (metric === 'all' || (metric === 'core' ? concept.metric !== null : concept.metric === metric)) && (year === 'all' || row[3].startsWith(year))
        && (!q || `${concept.label} ${concept.tag} ${row[1]} ${row[3]} ${row[5]} ${row[6]}`.toLowerCase().includes(q))
    })
  }, [data, query, metric, year])
  useEffect(() => {
    if (data && (!selected || !filtered.includes(selected))) setSelected(filtered[0] || null)
  }, [data, filtered])
  const pages = Math.max(1, Math.ceil(filtered.length / 25))
  const safePage = Math.min(page, pages - 1)
  const visible = filtered.slice(safePage * 25, (safePage + 1) * 25)
  const years = [...new Set(data?.rows.map(r => r[3].slice(0, 4)))].sort().reverse()
  const concept = selected && data ? data.concepts[selected[0]] : null
  const related = selected && data ? data.rows.filter(r => r !== selected && r[0] === selected[0] && r[1] === selected[1] && r[3] === selected[3] && r[5] === selected[5] && r[2] !== selected[2]) : []
  const result = selected ? contextCheck(selected[2], selected[3], selected[1], expectedPeriod, expectedUnit) : null
  const changeCompany = (id: string) => {
    setCompanyID(id); setQuery(''); setYear('all'); setMetric(sourceManifest.companies.find(c => c.id === id)?.core_count === 0 ? 'all' : 'core')
    const url = new URL(location.href); url.searchParams.set('company', id); url.searchParams.delete('source_case'); history.replaceState({}, '', url)
  }
  const exportRecord = () => {
    if (!selected || !concept) return
    const escaped = (text: string) => text.replaceAll('~', '~0').replaceAll('/', '~1')
    download(JSON.stringify({ company: company.name, cik: company.cik, taxonomy: concept.namespace, concept: concept.tag, label: concept.label,
      value: selected[4], unit: selected[1], start: selected[2], end: selected[3], accession: selected[5], filed: selected[7], form: selected[6],
      source: { publisher: sourceManifest.publisher, retrieved_on: sourceManifest.retrieved_on, url: company.source_url, sha256: company.source_sha256,
        json_pointer: `/facts/${escaped(concept.namespace)}/${escaped(concept.tag)}/units/${escaped(selected[1])}/${selected[11]}` },
      context_check: checked ? { engine: 'source-metadata-v1', expected_period: expectedPeriod, expected_unit: expectedUnit, ...result } : null,
      provenance: 'SEC published source snapshot; not a SERV extraction or Reppo evaluation' }, null, 2), `evi-${company.id}-${concept.tag}-${selected[3]}.json`, 'application/json')
  }
  return <div className="source-data-page">
    <div className="dataset-overview"><div><Database size={19}/><p><strong>{number(sourceManifest.total_observations)} USD observations.</strong> Six companies. Original reporting context.</p></div><a href="/datasets/manifest.json" target="_blank" rel="noreferrer">Source manifest <ArrowUpRight size={14}/></a></div>
    <div className="data-company-tabs" aria-label="Source company">{sourceManifest.companies.map(item => <button key={item.id} className={company.id === item.id ? 'selected' : ''} aria-pressed={company.id === item.id} onClick={() => changeCompany(item.id)}><span>{item.ticker}</span>{item.name}<small>{number(item.observation_count)}</small></button>)}</div>
    <div className="data-explorer-layout"><section className="panel source-records"><div className="panel-title"><div><h2>{company.name} <span className="count">{number(company.observation_count)}</span></h2><p>As-filed observations · {company.earliest_period_end.slice(0, 4)}–{company.latest_period_end.slice(0, 4)}</p></div><span className="dataset-label">SEC · USD SOURCE SNAPSHOT</span></div>
      <div className="data-filters"><label className="data-search"><Search size={16}/><input type="search" aria-label="Search source observations" placeholder="Search metric, date, or filing…" value={query} onChange={e => setQuery(e.target.value)}/></label><label><span className="sr-only">Metric scope</span><select aria-label="Metric scope" value={metric} onChange={e => setMetric(e.target.value)}><option value="core">3 core metrics</option><option value="revenue">Revenue</option><option value="operating_profit">Operating profit</option><option value="profit_attributable_to_owners">Profit attributable to owners</option><option value="all">All reported concepts</option></select></label><label><span className="sr-only">Period end year</span><select aria-label="Period end year" value={year} onChange={e => setYear(e.target.value)}><option value="all">All years</option>{years.map(y => <option key={y}>{y}</option>)}</select></label></div>
      {error ? <div className="data-error" role="alert"><TriangleAlert size={24}/><h3>Source data unavailable</h3><p>{error}</p><button className="button" onClick={() => setAttempt(n => n + 1)}>Retry source</button></div> : loading ? <div className="data-loading" role="status"><Loader2 size={22} className="spin"/><p>Reading {number(company.observation_count)} published observations…</p></div> : <>
        <div className="source-table-wrap"><table className="source-data-table"><thead><tr><th>REPORTED METRIC</th><th>AMOUNT · ORIGINAL UNIT</th><th>INTERVAL</th><th>PERIOD END</th><th><span className="sr-only">Inspect</span></th></tr></thead><tbody>{visible.map(row => { const c = data!.concepts[row[0]]; return <tr key={`${row[0]}-${row[1]}-${row[11]}`} className={selected === row ? 'selected' : ''}><td><button className="record-select" onClick={() => setSelected(row)}>{sourceLabel(c)}<small>{c.namespace}:{c.tag}</small></button></td><td><strong>{exactAmount(row[4])}</strong><small>{row[1]}</small></td><td><span className={`interval-pill ${row[2] ? '' : 'instant'}`}>{periodLabel(row[2], row[3])}</span></td><td>{row[3]}<small>{row[6]}</small></td><td><button className="icon-button" aria-label={`Inspect ${c.label}, ${periodLabel(row[2], row[3])}, ended ${row[3]}, filed ${row[7]}`} onClick={() => setSelected(row)}><ArrowUpRight size={15}/></button></td></tr> })}</tbody></table></div>
        {!filtered.length && <div className="data-no-matches"><FileSearch size={25}/><h3>No matching observations</h3><p>Try another metric, year, or search term.</p><button className="button" onClick={() => { setQuery(''); setMetric('all'); setYear('all') }}>Clear filters</button></div>}
        <div className="data-pagination"><span>{filtered.length ? number(safePage * 25 + 1) : 0}–{number(Math.min((safePage + 1) * 25, filtered.length))} of {number(filtered.length)}</span><div><button className="icon-button" aria-label="Previous records page" disabled={!safePage} onClick={() => setPage(p => p - 1)}><ChevronLeft size={16}/></button><span>{safePage + 1} / {pages}</span><button className="icon-button" aria-label="Next records page" disabled={safePage >= pages - 1} onClick={() => setPage(p => p + 1)}><ChevronRight size={16}/></button></div></div>
      </>}
    </section>
    <aside className="record-inspector panel" aria-label="Source observation inspector">{selected && concept ? <><div className="inspector-heading"><span className="overline">READ THE CONTEXT</span><ShieldCheck size={17}/></div><h2>{sourceLabel(concept)}</h2><p className="inspector-company">{company.name} · {selected[6]}</p><div className="source-value"><span>{selected[1]}{scale ? ` · ${scale === 9 ? 'BILLIONS' : 'MILLIONS'}` : ' · ORIGINAL UNITS'}</span><strong>{exactAmount(selected[4], scale)}</strong><label><span className="sr-only">Amount display scale</span><select aria-label="Amount display scale" value={scale} onChange={e => setScale(Number(e.target.value))}><option value={0}>Original units</option><option value={6}>Millions</option><option value={9}>Billions</option></select></label></div>
      <dl className="context-facts"><div><dt>Reporting interval</dt><dd>{periodLabel(selected[2], selected[3])}</dd></div><div><dt>Start date</dt><dd>{selected[2] || 'Not applicable'}</dd></div><div><dt>End date</dt><dd>{selected[3]}</dd></div><div><dt>Original unit</dt><dd>{selected[1]}</dd></div><div><dt>Filing date</dt><dd>{selected[7]}</dd></div></dl>
      {related.length > 0 && <div className="related-context"><div><Info size={15}/><strong>Same filing. Different interval.</strong></div>{related.slice(0, 3).map(row => <button key={row[11]} onClick={() => setSelected(row)}><span>{periodLabel(row[2], row[3])}</span><strong>{selected[1]} {exactAmount(row[4], 9)}B</strong><ArrowRight size={14}/></button>)}<p>Both values are reported in the same filing. Preserve the start date to distinguish them.</p></div>}
      <section className="context-check"><div className="check-heading"><h3>Check your intended context</h3><span>RULE-BASED</span></div><p>Does this observation fit the period and unit you intend to use?</p><div className="check-fields"><label>Expected period<select aria-label="Expected reporting period" value={expectedPeriod} onChange={e => { setExpectedPeriod(e.target.value); setChecked(false) }}><option value="3">3 months</option><option value="6">6 months</option><option value="9">9 months</option><option value="12">Full year</option><option value="instant">Point in time</option></select></label><label>Expected source unit<select aria-label="Expected source unit" value={expectedUnit} onChange={e => { setExpectedUnit(e.target.value); setChecked(false) }}><option value="USD">USD · base units</option><option value="USD millions">USD · millions</option><option value="USD billions">USD · billions</option></select></label></div><button className="button primary" onClick={() => setChecked(true)}><ShieldCheck size={15}/> Check this observation</button>
      {checked && result && <div className={`context-check-result ${result.period === 'pass' && result.unit === 'pass' ? 'success' : 'warning'}`} role="status">{result.period === 'pass' && result.unit === 'pass' ? <Check size={18}/> : <TriangleAlert size={18}/>}<div><strong>{result.period === 'pass' && result.unit === 'pass' ? 'Context matches your selection' : result.period === 'unknown' ? 'Period needs source review' : 'Context does not match'}</strong><p>{result.period === 'fail' ? `The source reports ${periodLabel(selected[2], selected[3]).toLowerCase()}, while you selected ${expectedPeriod === 'instant' ? 'a point in time' : expectedPeriod === '12' ? 'a full year' : `${expectedPeriod} months`}. ` : result.period === 'unknown' ? 'The exact dates need review; no period has been assumed. ' : 'Reporting interval matches. '}{result.unit === 'fail' ? `The source unit is ${selected[1]}, not ${expectedUnit}. No rescaling has been applied to the source value.` : 'Original unit matches.'}</p></div></div>}
      <p className="check-method">Checks the source metadata; no AI verdict or accounting accuracy is implied. Month labels use documented day ranges; exact dates remain authoritative.</p></section>
      <details className="source-provenance"><summary>Original source & provenance <ChevronRight size={13}/></summary><p>{concept.description}</p><code>{concept.namespace}:{concept.tag}</code><code>{selected[5]}</code><a href={filingURL(company.cik, selected[5])} target="_blank" rel="noreferrer">Open SEC filing <ExternalLink size={13}/></a><a href={company.source_url} target="_blank" rel="noreferrer">Original SEC API <ExternalLink size={13}/></a><a href={company.source_snapshot} target="_blank" rel="noreferrer">Downloaded source JSON <ExternalLink size={13}/></a><span>ORIGINAL SOURCE · SHA-256</span><code>{company.source_sha256}</code></details><button className="button export-observation" onClick={exportRecord}><ArrowDownToLine size={15}/> Export observation & evidence</button>
    </> : <div className="inspector-empty"><FileSearch size={26}/><h3>Select a source observation</h3><p>Read its interval and unit, inspect comparable contexts, and open its original filing.</p></div>}</aside></div>
    <p className="source-data-disclosure"><Info size={15}/><span>{sourceManifest.count_definition} Source snapshots were retrieved {sourceManifest.retrieved_on}; this page does not pretend to fetch a fresh live provider result. The frozen-label AI benchmark remains separate.</span></p>
  </div>
}
