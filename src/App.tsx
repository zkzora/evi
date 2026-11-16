import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import { ArrowDownToLine, ArrowRight, ArrowUpRight, Braces, Check, CheckCheck, ChevronDown, ChevronRight, CircleHelp, Clock3, Columns3, Copy, Database, ExternalLink, FileCheck2, FileSearch, FileText, Files, FlaskConical, Info, Layers3, Link2, ListFilter, Loader2, Maximize2, MessageSquareText, PanelLeftClose, Play, RefreshCw, Search, Settings2, ShieldCheck, SlidersHorizontal, Sparkles, TriangleAlert, Unplug, X } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { House } from 'lucide-react'
import Home from './Home'
const DataExplorer = lazy(() => import('./DataExplorer'))
import { api } from './api'
import { sourceCatalog } from './catalog'
import { decimalDisplay, download, versionCSV } from './export'
import { metricNames } from './types'
import type { Benchmark, Check as CheckResult, Evaluation, Evidence, FactVersion, Job, Metric, Report, Run } from './types'
const PdfViewer = lazy(() => import('./PdfViewer'))
import CertificatePanel from './Certificate'
import Tour, { startTour } from './Tour'
import type { Capabilities } from './api'
import { capabilityLabel } from './availability'
const Experiments = lazy(() => import('./Experiments'))

type View = 'home' | 'workspace' | 'data' | 'documents' | 'feedback' | 'benchmark'
type EvidenceTab = 'value_ids' | 'metric_ids' | 'period_ids' | 'unit_ids'
const navigation: { id: View; title: string; icon: LucideIcon; path: string }[] = [
  { id: 'home', title: 'Home', icon: House, path: '/' },
  { id: 'workspace', title: 'Workspace', icon: Columns3, path: '/workspace' },
  { id: 'data', title: 'Real data', icon: Database, path: '/data' },
  { id: 'documents', title: 'Documents', icon: Files, path: '/documents' },
  { id: 'feedback', title: 'Feedback', icon: MessageSquareText, path: '/feedback' },
  { id: 'benchmark', title: 'Benchmark', icon: FlaskConical, path: '/benchmark' },
]
const metricList = Object.entries(metricNames) as [Metric, string][]
const sameTarget = (a: { fact_id: string }, b: { fact_id: string }) => { const ka = (a as { target_key?: string }).target_key, kb = (b as { target_key?: string }).target_key; return ka && kb ? ka === kb : a.fact_id === b.fact_id }
const unitLabels: Record<string, string> = { '1': 'units', '1000': 'thousand', '1000000': 'million', '1000000000': 'billion', '1000000000000': 'trillion' }
const terminalJobs = ['succeeded', 'failed', 'cancelled', 'blocked', 'outcome_unknown']
const viewFromURL = (): View => navigation.find(n => n.path === location.pathname)?.id || 'home'
const messageOf = (error: unknown) => error instanceof Error ? error.message : 'This action could not complete.'
const utc = (s: string) => s ? `${new Date(s).toISOString().slice(0, 16).replace('T', ' ')} UTC` : 'unknown time'
const date = (s: string) => new Date(s).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
function Badge({ tone = 'neutral', children }: { tone?: string; children: React.ReactNode }) { return <span className={`badge ${tone}`}><span className="status-dot"/>{children}</span> }
function Empty({ icon: Icon, title, children, action }: { icon: LucideIcon; title: string; children: React.ReactNode; action?: React.ReactNode }) {
  return <div className="empty-state"><div className="empty-art"><div className="empty-art-back"/><div className="empty-art-front"><Icon size={28} strokeWidth={1.4}/></div></div><h3>{title}</h3><p>{children}</p>{action}</div>
}
type Coverage = { complete_required_context: boolean; unique_supported_reading: boolean; exact_interval: string; label: string; source_interval?: { start_date: string; end_date: string } | null }
const coverageOf = (fact?: unknown) => (fact as { context_coverage?: Coverage } | undefined)?.context_coverage
function checkState(checks: CheckResult[], fact?: unknown) {
  if (checks.some(c => c.status === 'fail')) return { title: 'Needs review', tone: 'warning' }
  // coverage-v1: a unique supported reading with unknown exact dates is NOT shown as complete verification.
  const cov = coverageOf(fact)
  if (cov?.complete_required_context) return { title: 'Checks passed', tone: 'success' }
  if (cov?.unique_supported_reading) return { title: cov.exact_interval === 'not_printed_in_source' ? 'Supported · dates not printed' : 'Supported · context incomplete', tone: 'partial' }
  if (checks.length && checks.every(c => ['pass', 'not_applicable'].includes(c.status))) return { title: 'Checks passed', tone: 'success' }
  return { title: 'Unchecked', tone: 'neutral' }
}
function Dialog({ title, children, close }: { title: string; children: React.ReactNode; close: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => { const previous = document.activeElement as HTMLElement; ref.current?.showModal(); return () => previous?.focus() }, [])
  return <dialog ref={ref} className="dialog" onCancel={close} onClick={e => { if (e.target === ref.current) close() }}><div className="dialog-heading"><h2>{title}</h2><button className="icon-button" aria-label="Close dialog" onClick={close}><X size={19}/></button></div>{children}</dialog>
}

export default function App() {
  const [view, setView] = useState<View>(viewFromURL)
  const [reports, setReports] = useState<Report[]>(sourceCatalog)
  const [documentId, setDocumentId] = useState(() => {
    // Keep the requested ID until the server's registered documents are known; never silently swap records.
    return new URLSearchParams(location.search).get('document') || sourceCatalog[0].document_id
  })
  const [connection, setConnection] = useState<'checking' | 'connected' | 'offline'>('checking')
  const [serverReports, setServerReports] = useState(false)
  const [execution, setExecution] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [caps, setCaps] = useState<Capabilities | undefined>(undefined)
  const [tourStep, setTourStep] = useState(() => Number(new URLSearchParams(location.search).get('tour')) || 0)
  const closeTour = () => { const u = new URL(location.href); u.searchParams.delete('tour'); history.replaceState({}, '', u); setTourStep(0) }
  const [runs, setRuns] = useState<Run[]>([])
  const [runId, setRunId] = useState('')
  const initialSelection = useRef(new URLSearchParams(location.search))
  const [versionId, setVersionId] = useState('')
  const [version, setVersion] = useState<FactVersion | null>(null)
  const [parent, setParent] = useState<FactVersion | null>(null)
  const [factId, setFactId] = useState('')
  const [evidenceTab, setEvidenceTab] = useState<EvidenceTab>('value_ids')
  const [evidence, setEvidence] = useState<Evidence | null>(null)
  const [evidenceError, setEvidenceError] = useState('')
  const [search, setSearch] = useState('')
  const [metricFilter, setMetricFilter] = useState('all')
  const [issueFilter, setIssueFilter] = useState(false)
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>([])
  const [job, setJob] = useState<Job | null>(null)
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [modal, setModal] = useState<'settings' | 'help' | 'document' | null>(null)
  const [refresh, setRefresh] = useState(0)
  const [sourceExpanded, setSourceExpanded] = useState(false)
  const report = reports.find(d => d.document_id === documentId) || reports[0]
  useEffect(() => {
    if (connection === 'checking' || (connection === 'connected' && !serverReports)) return
    if (!reports.some(d => d.document_id === documentId)) {
      if (documentId !== reports[0].document_id) setError(`Document "${documentId}" is not registered. Showing ${reports[0].issuer_name} instead.`)
      setDocumentId(reports[0].document_id)
      const url = new URL(location.href); url.searchParams.set('document', reports[0].document_id); history.replaceState({}, '', url)
    }
  }, [reports, documentId, connection, serverReports])
  const selectedRun = runs.find(r => r.run_id === runId)
  const selectedFact = version?.facts.find(f => f.fact_id === factId) || version?.facts[0] || null
  const checks = version?.checks.filter(c => c.fact_id === selectedFact?.fact_id) || []
  const facts = version?.facts.filter(f => (metricFilter === 'all' || f.metric === metricFilter)
    && (!issueFilter || checkState(version.checks.filter(c => c.fact_id === f.fact_id)).tone === 'warning')
    && `${metricNames[f.metric]} ${f.metric_label} ${f.period.label}`.toLowerCase().includes(search.toLowerCase())) || []
  const issueCount = version?.facts.filter(f => checkState(version.checks.filter(c => c.fact_id === f.fact_id)).tone === 'warning').length || 0
  const [searchBox, setSearchBox] = useState<HTMLInputElement | null>(null)
  const sourceUrl = connection === 'connected' && !report.source_path ? api.source(report.document_id) : report.source_path || api.source(report.document_id)

  const navigate = useCallback((next: View, id = documentId) => {
    const url = new URL(location.href); url.pathname = navigation.find(n => n.id === next)!.path; url.searchParams.set('document', id)
    history.pushState({}, '', url); setView(next); window.scrollTo({ top: 0, behavior: 'instant' })
  }, [documentId])
  const selectDocument = (id: string) => {
    setDocumentId(id); setRunId(''); setVersionId(''); setVersion(null); setParent(null); setFactId(''); setEvidence(null); setError(''); setSearch(''); setMetricFilter('all')
    const url = new URL(location.href); url.searchParams.set('document', id); url.searchParams.delete('version'); history.replaceState({}, '', url)
  }
  useEffect(() => {
    const pop = () => { setView(viewFromURL()); setDocumentId(new URLSearchParams(location.search).get('document') || sourceCatalog[0].document_id) }
    window.addEventListener('popstate', pop); return () => window.removeEventListener('popstate', pop)
  }, [])
  useEffect(() => {
    const key = (e: KeyboardEvent) => { if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); searchBox?.focus() } }
    window.addEventListener('keydown', key); return () => window.removeEventListener('keydown', key)
  }, [searchBox])
  useEffect(() => { if (toast) { const timer = setTimeout(() => setToast(''), 4500); return () => clearTimeout(timer) } }, [toast])
  useEffect(() => {
    let active = true; setConnection('checking')
    api.health().then(async health => {
      if (!active) return
      setConnection('connected'); setExecution(health.live_execution_enabled); setProcessing(health.processing_enabled); setCaps(health.capabilities)
      try { const result = await api.documents(); if (active && result.items.length) setReports(result.items) }
      catch (e) { if (active) setError(messageOf(e)) }
      finally { if (active) setServerReports(true) }
    }).catch(() => { if (active) { setConnection('offline'); setExecution(false); setProcessing(false); setCaps(undefined) } })
    return () => { active = false }
  }, [refresh])
  useEffect(() => {
    if (connection !== 'connected' || !serverReports) return
    let active = true; setLoading(true); setError(''); setRuns([]); setVersion(null); setParent(null)
    api.runs(documentId).then(result => {
      if (!active) return
      const live = result.items.filter(r => r.mode === 'live')
      setRuns(live); setRunId(live.find(r => r.run_id === initialSelection.current.get('run'))?.run_id || live[0]?.run_id || '')
    }).catch(e => { if (active) setError(messageOf(e)) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [connection, serverReports, documentId, refresh])
  useEffect(() => {
    const requested = initialSelection.current.get('version')
    setVersionId(requested && selectedRun?.version_ids.includes(requested) ? requested : selectedRun?.version_ids.at(-1) || '')
  }, [selectedRun])
  useEffect(() => {
    const url = new URL(location.href)
    for (const [key, value] of [['run', runId], ['version', versionId], ['fact', factId]]) {
      if (value) url.searchParams.set(key, value); else url.searchParams.delete(key)
    }
    history.replaceState({}, '', url)
  }, [runId, versionId, factId])
  useEffect(() => {
    setVersion(null); setParent(null); setEvidence(null)
    if (!versionId) return
    let active = true; setLoading(true)
    api.version(versionId).then(async data => {
      if (!active) return
      if (!['serv_initial', 'serv_revision', 'manual'].includes(data.origin)) throw new Error('This version is not a supported live result.')
      setVersion(data); setFactId(data.facts.find(f => f.fact_id === initialSelection.current.get('fact'))?.fact_id || data.facts[0]?.fact_id || '')
      if (data.parent_version_id) { const previous = await api.version(data.parent_version_id); if (active) setParent(previous) }
    }).catch(e => { if (active) setError(messageOf(e)) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [versionId])
  useEffect(() => {
    setEvidence(null); setEvidenceError('')
    const id = selectedFact?.evidence[evidenceTab][0]
    if (!id || connection !== 'connected') return
    let active = true
    api.evidence(id).then(data => {
      if (data.document_id !== report.document_id || data.document_sha256 !== report.sha256) throw new Error('The evidence does not match this source version. No highlight has been applied.')
      if (active) setEvidence(data)
    }).catch(e => { if (active) setEvidenceError(messageOf(e)) })
    return () => { active = false }
  }, [selectedFact, evidenceTab, connection, report.document_id, report.sha256])
  useEffect(() => {
    if (connection !== 'connected') { setEvaluations([]); setBenchmarks([]); return }
    let active = true
    if (view === 'feedback') api.evaluations().then(data => { if (active) setEvaluations(data.items.filter(e => e.mode === 'reppo_live')) }).catch(e => { if (active) setError(messageOf(e)) })
    if (view === 'benchmark') api.benchmarks().then(data => { if (active) setBenchmarks(data.items) }).catch(e => { if (active) setError(messageOf(e)) })
    return () => { active = false }
  }, [view, connection, refresh])
  useEffect(() => {
    if (!job || terminalJobs.includes(job.status)) return
    let active = true
    const interval = setInterval(() => api.job(job.job_id).then(next => {
      if (!active) return
      setJob(next)
      if (next.status === 'succeeded') { setToast('Processing completed. Refreshing your results.'); setRefresh(n => n + 1) }
      if (['failed', 'blocked', 'outcome_unknown'].includes(next.status)) setError(next.error?.message || next.message || `Processing status: ${next.status}.`)
    }).catch(e => { if (active) { setError(messageOf(e)); clearInterval(interval) } }), 4000)
    return () => { active = false; clearInterval(interval) }
  }, [job?.job_id, job?.status])
  const pending = busy || Boolean(job && !terminalJobs.includes(job.status))
  const canProcess = connection === 'connected' && (caps ? caps.extraction.state === 'available' : processing)
  const canEvaluate = connection === 'connected' && (caps ? caps.evaluation.state === 'available' : execution)
  const liveAction = async (fn: () => Promise<Job>, needs: 'processing' | 'live' = 'live') => {
    if (connection !== 'connected' || !(needs === 'processing' ? processing : execution)) { setModal('settings'); return }
    setBusy(true); setError('')
    try {
      const next = await fn(); setJob(next); setToast(next.message || 'Your request has been submitted.')
      if (next.status === 'succeeded') setRefresh(n => n + 1)
      if (['failed', 'blocked', 'outcome_unknown'].includes(next.status)) setError(next.error?.message || next.message || `Processing status: ${next.status}.`)
    }
    catch (e) { setError(messageOf(e)) } finally { setBusy(false) }
  }
  // One explicit action: the server reuses a cached Docling parse (same hash/parser/pages) and continues to SERV extraction.
  const process = () => liveAction(() => api.parse(report.document_id), 'processing')
  const exportVersion = (format: 'csv' | 'json') => {
    if (!version?.facts.length) return
    const name = `${report.document_id}-${version.version_id}`.replace(/[^a-zA-Z0-9_-]/g, '_')
    download(format === 'csv' ? versionCSV(version, report.source_url, report.sha256) : JSON.stringify({ ...version, source_url: report.source_url, source_sha256: report.sha256 }, null, 2),
      `${name}.${format}`, format === 'csv' ? 'text/csv;charset=utf-8' : 'application/json')
    setToast(`${format.toUpperCase()} exported with source and version references.`)
  }
  const copy = async (text: string) => { try { await navigator.clipboard.writeText(text); setToast('Copied to clipboard.') } catch { setToast('Clipboard access is unavailable. Select the text to copy it.') } }
  const title = navigation.find(n => n.id === view)!.title

  const openData = (company = 'verizon', sourceCase?: string) => {
    navigate('data')
    const url = new URL(location.href); url.searchParams.set('company', company)
    if (sourceCase) url.searchParams.set('source_case', sourceCase); else url.searchParams.delete('source_case')
    history.replaceState({}, '', url)
  }
  return <div className={`app top-navigation ${view === 'home' ? 'is-home' : ''}`}>
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="site-header"><div className="site-header-inner">
      <a href="/" className="site-brand" aria-label="Evi home" onClick={e => { e.preventDefault(); navigate('home') }}><img src="/evi-symbol.svg" alt=""/><span>Evi<span>.</span></span></a>
      <nav className="site-nav" aria-label="Main navigation">{navigation.map(({ id, title, path }) => <a key={id} href={`${path}?document=${documentId}`} className={view === id ? 'active' : ''} aria-current={view === id ? 'page' : undefined} onClick={e => { e.preventDefault(); navigate(id) }}>{title}</a>)}</nav>
      <div className="site-header-actions"><button className="icon-button" aria-label="How Evi works" onClick={() => setModal('help')}><CircleHelp size={18}/></button><button className="icon-button" aria-label="Processing connection" onClick={() => setModal('settings')}><Settings2 size={18}/></button><a className="nav-cta" href="/workspace" onClick={e => { e.preventDefault(); navigate('workspace') }}>Open workspace <ArrowUpRight size={14}/></a></div>
    </div></header>
    <div className="main-shell">
      <main id="main" tabIndex={-1} className={view === 'home' ? 'landing-main' : ''}>
        {view !== 'home' && <div className="page-heading"><div><div className="eyebrow"><span/> {view === 'data' ? 'PUBLISHED FINANCIAL DATA' : 'SOURCE INTELLIGENCE'}</div><h1>{view === 'workspace' ? 'Evidence workspace' : view === 'data' ? 'Every figure has a context.' : view === 'documents' ? 'Your source library' : view === 'feedback' ? 'Feedback & revisions' : 'What the experiments measured.'}</h1><p>{view === 'workspace' ? 'Financial facts. The right period, the right unit, the original proof.' : view === 'data' ? 'Inspect real reported figures. Compare intervals. Check the context you intend to use.' : view === 'documents' ? 'Start with public financial reports. Keep their context within reach.' : view === 'feedback' ? 'An independent critique. A source-backed correction. A clear audit trail.' : 'Four arms on the same targets, every outcome counted. Real Reppo feedback has not shown a measured benefit.'}</p></div><div className="heading-actions"><button className="button small try-evi" onClick={startTour}><Sparkles size={14}/> Try Evi</button>{view !== 'data' && <button className={`connection-pill ${capabilityLabel(connection, caps).tone}`} onClick={() => setModal('settings')}><span className="status-dot"/>{capabilityLabel(connection, caps).text}<ChevronRight size={13}/></button>}<span className="heading-caption">No sign-in required</span></div></div>}
        {view === 'home' && <Home openData={openData} openWorkspace={() => navigate('workspace')} tryEvi={startTour}/>}
        {view === 'data' && <Suspense fallback={<div className="data-loading"><Loader2 className="spin" size={22}/>Loading the source explorer…</div>}><DataExplorer key={location.search.match(/company=([^&]+)/)?.[1] || 'verizon'}/></Suspense>}
        {error && <div className="error-banner" role="alert"><TriangleAlert size={18}/><p>{error}</p><button className="text-button" onClick={() => setRefresh(n => n + 1)}>Retry</button><button className="icon-button" aria-label="Dismiss error" onClick={() => setError('')}><X size={16}/></button></div>}
        {job && <div className="job-banner" role="status">{terminalJobs.includes(job.status) ? <Info size={17}/> : <Loader2 size={17} className="spin"/>}<div className="job-body"><span>{job.message || `Processing: ${job.status.replaceAll('_', ' ')}`}</span>
          {Array.isArray((job as { stages?: unknown[] }).stages) && <ol className="job-stages">{((job as unknown as { stages: { job_id: string; kind: string; status: string; message?: string; updated_at?: string }[] }).stages).map(st => <li key={st.job_id} className={st.status}><b>{st.kind === 'process_document' ? 'Parse (Docling)' : st.kind === 'extract_facts' ? 'Extract (SERV) + checks' : st.kind.replaceAll('_', ' ')}</b> · {st.status}{st.message ? ` · ${st.message}` : ''}{st.updated_at ? ` · ${date(st.updated_at)}` : ''}</li>)}</ol>}
          {(() => { const r = (job as { first_stage_result?: { parse_reused?: boolean; pages?: number[]; run_id?: string } }).first_stage_result; const res = (job as { result?: { run_id?: string; version_id?: string } }).result; return (r || res) ? <small>{r ? `${r.parse_reused ? 'Reused cached Docling parse' : 'Fresh Docling parse'} of page(s) ${r.pages?.join(', ')}` : ''}{(r?.run_id || res?.run_id) ? ` · run ${r?.run_id || res?.run_id}` : ''}{res?.version_id ? ` · version ${res.version_id}` : ''}</small> : null })()}</div><code>{job.job_id}</code>{terminalJobs.includes(job.status) && <button className="icon-button" onClick={() => setJob(null)} aria-label="Dismiss job status"><X size={15}/></button>}</div>}

        {view === 'workspace' && <>
          <section className="context-bar" aria-label="Report context"><div className="report-context-icon"><FileText size={20}/></div><div className="report-select-wrap"><label htmlFor="report-select">SOURCE DOCUMENT</label><div className="select-with-icon"><select id="report-select" value={report.document_id} onChange={e => selectDocument(e.target.value)}>{reports.map(d => <option key={d.document_id} value={d.document_id}>{d.issuer_name} · {d.period_label || d.title}</option>)}</select><ChevronDown size={14}/></div></div><div className="context-rule"/><div className="run-context"><label htmlFor="run-select">EXTRACTION RUN</label><select id="run-select" value={runId} disabled={!runs.length} onChange={e => setRunId(e.target.value)}>{!runs.length && <option value="">No extraction yet</option>}{runs.map(r => <option key={r.run_id} value={r.run_id}>{date(r.created_at)} · {r.status}</option>)}</select></div><div className="context-actions">{canProcess ? <button className="button primary" onClick={process} disabled={pending} aria-busy={pending}>{pending ? <Loader2 size={15} className="spin"/> : <Play size={14} fill="currentColor"/>}Process report</button> : <button className="button primary" disabled aria-describedby="processing-reason"><Play size={14}/>Process report</button>}</div></section>
          {!canProcess && connection !== 'checking' && <div className="availability-note" id="processing-reason" role="note"><Info size={15}/><p><strong>{capabilityLabel(connection, caps).text}.</strong> {caps?.extraction.reason || 'The processing service is not connected.'} {runs.length ? 'You are viewing stored results from earlier real runs; nothing is re-run.' : ''}</p>{runs.length > 0 && !versionId && <button className="text-button" onClick={() => setRunId(runs[0].run_id)}>Inspect latest stored run <ArrowRight size={13}/></button>}</div>}
          {version && <div className="stored-note" role="note"><Clock3 size={14}/><span>Stored result · run created {utc(selectedRun?.created_at || '')} · version {version.version_id} created {utc((version as { created_at?: string }).created_at || selectedRun?.created_at || '')} · {version.origin.replaceAll('_', ' ')}{(version as { arm?: string }).arm ? ` (arm ${(version as { arm?: string }).arm})` : ''}. Shown as recorded, not re-run.</span></div>}
          <section className="scope-strip" aria-label="Current scope"><div><span className="tiny-icon"><Layers3 size={16}/></span><strong>3</strong><span>financial metrics</span></div><div><span className="tiny-icon"><ScanCheckIcon/></span><strong>2</strong><span>semantic checks</span></div><div><span className="tiny-icon"><Link2 size={16}/></span><span>Every fact linked to its source</span></div><span className="scope-sector">TELECOM · USD</span></section>
          <div className={`workbench ${sourceExpanded ? 'source-expanded' : ''}`}>
            <section className="facts-panel panel" aria-label="Financial facts">
              <div className="panel-title"><div><h2>Financial facts <span className="count">{version?.facts.length || 0}</span></h2><p>Reported values, with their context intact.</p></div><div className="panel-actions"><button className="icon-button" title="Refresh live results" aria-label="Refresh live results" onClick={() => setRefresh(n => n + 1)}><RefreshCw size={16}/></button><details className="export-menu"><summary className={`button small ${!version?.facts.length ? 'disabled' : ''}`} aria-label="Export results"><ArrowDownToLine size={15}/> Export<ChevronDown size={12}/></summary><div className="popover"><button disabled={!version?.facts.length} onClick={() => exportVersion('csv')}>Download CSV</button><button disabled={!version?.facts.length} onClick={() => exportVersion('json')}>Download JSON</button>{!version?.facts.length && <p>Extract facts before exporting.</p>}</div></details></div></div>
              <div className="grid-tools"><div className="tabs"><button className={!issueFilter ? 'selected' : ''} onClick={() => setIssueFilter(false)}>All facts</button><button className={issueFilter ? 'selected' : ''} onClick={() => setIssueFilter(true)}>Needs review <span>{issueCount}</span></button></div><label className="metric-select"><ListFilter size={14}/><span className="sr-only">Filter metric</span><select value={metricFilter} onChange={e => setMetricFilter(e.target.value)}><option value="all">All metrics</option>{metricList.map(([key, name]) => <option key={key} value={key}>{name}</option>)}</select></label></div>
              <div className="table-search"><Search size={15}/><input ref={setSearchBox} type="search" aria-label="Search extracted facts" placeholder="Search a metric or reporting period…" value={search} onChange={e => setSearch(e.target.value)}/><kbd>⌘ K</kbd></div>
              <div className="fact-table-scroll"><table className="fact-table"><thead><tr><th>METRIC</th><th>REPORTED AMOUNT</th><th>PERIOD</th><th>CHECKS</th></tr></thead><tbody>{facts.map(f => { const state = checkState(version!.checks.filter(c => c.fact_id === f.fact_id), f); return <tr key={f.fact_id} className={selectedFact?.fact_id === f.fact_id ? 'selected-row' : ''}><td><button className="fact-select" onClick={() => setFactId(f.fact_id)}>{metricNames[f.metric]}<span>{f.metric_label}</span></button></td><td><strong className="mono">{f.reported_value ?? 'Unresolved'}</strong><span>{f.currency || 'Unknown currency'} {unitLabels[f.unit_scale || ''] || 'unknown scale'}</span></td><td><strong>{f.period.duration_months ? `${f.period.duration_months} months` : 'Unresolved'}</strong><span>{f.period.label}</span></td><td><Badge tone={state.tone}>{state.title}</Badge></td></tr> })}</tbody></table></div>
              {loading ? <div className="loading-block" role="status"><Loader2 className="spin" size={22}/><span>Loading stored results…</span></div> : !version?.facts.length ? <Empty icon={FileSearch} title="Start with the source." action={<button className="button" onClick={process} disabled={pending}><Play size={14}/> Process this report<ArrowRight size={14}/></button>}>Process the report to extract three financial metrics.<br/>Their reporting periods and units will appear here.</Empty> : !facts.length ? <Empty icon={Search} title="No facts match these filters." action={<button className="button" onClick={() => { setSearch(''); setMetricFilter('all'); setIssueFilter(false) }}>Clear filters</button>}>Try a different metric, period, or review status.</Empty> : null}
              {selectedFact && <div className="fact-details"><div className="detail-label">SELECTED FACT <span>{selectedFact.origin.replaceAll('_', ' ')}</span></div><h3>{metricNames[selectedFact.metric]}</h3><div className="fact-detail-grid"><div><label>Normalized amount</label><strong>{decimalDisplay(selectedFact.normalized_value)} {selectedFact.currency}</strong></div><div><label>Reporting interval</label><strong>{coverageOf(selectedFact)?.exact_interval === 'not_printed_in_source' ? `${selectedFact.period.duration_months ?? '?'} months · exact dates not printed in source` : `${selectedFact.period.start_date || coverageOf(selectedFact)?.source_interval?.start_date || (selectedFact.period as { derived_start_date?: string }).derived_start_date || '?'} → ${selectedFact.period.end_date || '?'}${!selectedFact.period.start_date && coverageOf(selectedFact)?.source_interval ? ' (start derived)' : ''}`}</strong></div></div>{checks.filter(c => c.status !== 'pass').map(c => <div key={c.check_id} className={`check-line ${c.status}`}>{c.status === 'fail' ? <TriangleAlert size={15}/> : <Info size={15}/>}<span>{c.check_type.replaceAll('_', ' ')}: {c.message}</span></div>)}{checks.some(c => c.status === 'pass') && <div className="check-line pass"><CheckCheck size={15}/><span>{checks.filter(c => c.status === 'pass').length} of {checks.length} checks passed</span></div>}{version && <CertificatePanel versionId={version.version_id} factId={selectedFact.fact_id} targetKey={(selectedFact as { target_key?: string }).target_key}/>}
                {parent && <div className="revision-diff"><h4>Source-backed revision</h4>{(['unit_scale','reported_value','currency'] as const).map(field => { const old = parent.facts.find(f => sameTarget(f, selectedFact))?.[field]; return old !== undefined && old !== selectedFact[field] ? <p key={field}>{field.replaceAll('_', ' ')}: <del>{old || 'Unresolved'}</del> <ArrowRight size={12}/> <strong>{selectedFact[field]}</strong></p> : null })}{(() => { const old = parent.facts.find(f => sameTarget(f, selectedFact))?.period; return old && JSON.stringify(old) !== JSON.stringify(selectedFact.period) ? <p>Period: <del>{old.label}</del> <ArrowRight size={12}/> <strong>{selectedFact.period.label}</strong></p> : null })()}</div>}
              </div>}
              <div className="fact-panel-bottom"><div><span className="status-dot"/>{version ? 'Stored live output' : 'No extracted results yet'}</div>{selectedRun && selectedRun.version_ids.length > 0 ? <label className="version-control">Version<select value={versionId} onChange={e => setVersionId(e.target.value)}>{selectedRun.version_ids.map((id, i) => <option key={id} value={id}>{i === 0 ? 'Initial' : `Revision ${i}`} · {id.slice(0, 8)}</option>)}</select></label> : <span>Source evidence stays unchanged</span>}</div>
              <div className="metric-scope"><span>IN SCOPE</span>{metricList.map(([key, name]) => <div key={key}><Check size={13}/>{name}</div>)}</div>
            </section>
            <section className="source-panel panel" aria-label="Original PDF evidence"><div className="panel-title"><div><h2><FileText size={17}/> Original source</h2><p>{report.issuer_name} · {report.page_count} pages</p></div><button className="icon-button" onClick={() => setSourceExpanded(x => !x)} aria-label={sourceExpanded ? 'Restore split view' : 'Expand source panel'}><Maximize2 size={16}/></button></div><div className="evidence-tabs">{([['value_ids','Value'],['metric_ids','Metric'],['period_ids','Period'],['unit_ids','Unit']] as [EvidenceTab,string][]).map(([key, label]) => <button key={key} className={evidenceTab === key ? 'selected' : ''} onClick={() => setEvidenceTab(key)}>{label}{key === evidenceTab && <span/>}</button>)}<span className="source-label"><Link2 size={12}/> Source PDF</span></div>
              <Suspense fallback={<div className="loading-block" role="status"><Loader2 size={21} className="spin"/>Loading the original PDF viewer…</div>}><PdfViewer report={report} url={sourceUrl} evidence={evidence}/></Suspense>
              <div className={`source-evidence-note ${evidenceError ? 'problem' : ''}`}><Info size={15}/><p>{evidenceError || (evidence ? evidence.text : `Original document preview. ${selectedFact ? 'No source anchor is available for this field yet.' : 'Select an extracted fact to see its supporting evidence.'}`)}</p></div><div className="source-footer"><a href={report.source_url} target="_blank" rel="noreferrer"><Link2 size={13}/> Publisher source<ArrowUpRight size={13}/></a><button className="text-button" onClick={() => setModal('document')}>Source details <ChevronRight size={13}/></button></div>
            </section>
          </div>
          <div className="method-bar"><span className="method-label">THE EVIDENCE PATH</span><div><FileText size={15}/> Original PDF <ChevronRight size={13}/><Database size={15}/> Docling <ChevronRight size={13}/><Sparkles size={15}/> SERV Reasoning <ChevronRight size={13}/><ShieldCheck size={15}/> Period & unit checks <ChevronRight size={13}/><MessageSquareText size={15}/> Reppo feedback</div><button className="text-button" onClick={() => setModal('help')}>How it works<ArrowUpRight size={13}/></button></div>
        </>}

        {view === 'documents' && <>
          <div className="section-toolbar"><div><h2>Public report library <span className="count">{reports.length}</span></h2><p>Original issuer documents. Financial results are extracted only after processing.</p></div><button className="button" onClick={() => setRefresh(n => n + 1)}><RefreshCw size={15}/> Refresh sources</button></div>
          <section className="document-list panel">{reports.map((d, i) => <article className="document-card" key={d.document_id}><div className="document-index">0{i + 1}</div><div className="document-symbol"><FileText size={25} strokeWidth={1.4}/><span>PDF</span></div><div className="document-copy"><div className="eyebrow">{d.issuer_name}</div><h3>{d.title}</h3><p>{d.period_label || 'Public financial report'} <span>·</span> {d.page_count} pages <span>·</span> Original publisher PDF</p><div className="document-hash"><ShieldCheck size={13}/><span>SHA-256</span><code>{d.sha256.slice(0, 20)}…</code></div></div><div className="document-actions"><Badge tone={d.parse_status === 'parsed' ? 'success' : 'neutral'}>{d.parse_status === 'parsed' ? 'Parsed' : d.parse_status === 'not_started' ? 'Not processed' : d.parse_status}</Badge><button className="button" onClick={() => { selectDocument(d.document_id); navigate('workspace', d.document_id) }}>Open workspace <ArrowRight size={15}/></button><a href={d.source_url} target="_blank" rel="noreferrer">Publisher original <ExternalLink size={12}/></a></div></article>)}</section>
          <div className="library-note"><Info size={18}/><div><h3>A focused corpus, a clearer comparison.</h3><p>The public workspace uses original USD-denominated telecom reports and three financial metrics. The Real data explorer provides published SEC observations alongside this PDF library. Source availability does not mean extraction or verification has completed.</p></div></div>
        </>}

        {view === 'feedback' && <>
          <section className="feedback-flow"><div><span>01</span><FileSearch size={20}/><h3>Extract the facts</h3><p>SERV interprets source context.</p></div><ArrowRight size={20}/><div><span>02</span><MessageSquareText size={20}/><h3>Get an external critique</h3><p>Reppo evaluates the exact version.</p></div><ArrowRight size={20}/><div><span>03</span><CheckCheck size={20}/><h3>Recheck the revision</h3><p>Every change needs source support.</p></div></section>
          <section className="panel"><div className="panel-title"><div><h2>This version <span className="count">{evaluations.filter(e => e.version_id === version?.version_id).length}</span></h2><p>{version ? <>Evaluations of exactly <code>{version.version_id}</code> ({report.issuer_name} · {report.period_label}).</> : 'Select a report version in the workspace.'}</p></div><button className="button small" disabled={!version || pending || !canEvaluate} title={canEvaluate ? 'Submit this exact version to Reppo' : caps?.evaluation.reason || 'Evaluation is not available'} onClick={() => version && liveAction(() => api.evaluate(version.version_id))}><Sparkles size={14}/> Evaluate this version</button></div>
            {!canEvaluate && <div className="availability-note" role="note"><Info size={15}/><p><strong>New evaluations are not available here.</strong> {caps?.evaluation.reason || 'The processing service is not connected.'} Recorded evaluations stay inspectable below.</p></div>}
            {!evaluations.some(e => e.version_id === version?.version_id) ? <p className="zero-state">No evaluation has been recorded for this version. Earlier evaluations belong to the specific versions listed in the history below; they are not attached to this one.</p>
              : <div className="evaluation-list">{evaluations.filter(e => e.version_id === version?.version_id).map(e => <EvaluationCard key={e.evaluation_id} e={e} revise={canProcess && !pending ? () => void liveAction(() => api.revise(e.version_id, e.evaluation_id), 'processing') : undefined}/>)}</div>}
          </section>
          <section className="panel"><div className="panel-title"><div><h2>Recorded evaluation history <span className="count">{evaluations.length}</span></h2><p>Every real Reppo evaluation, with the exact version it judged. Scores are evaluator opinions, not extraction accuracy.</p></div></div>
            {!evaluations.length ? <p className="zero-state">No evaluations are recorded on this server.</p> : <div className="eval-history"><table className="exp-table"><thead><tr><th>Recorded</th><th>Context</th><th>Report</th><th>Evaluated version</th><th>Status</th><th>Score</th><th>Credits</th></tr></thead><tbody>{evaluations.map(e => { const x = e as typeof e & { document_id?: string; run_id?: string; context?: string; packet?: string; credits_charged?: number | null }; return <tr key={e.evaluation_id}><td>{date(e.created_at)}</td><td>{x.context}<br/><small>{x.packet}</small></td><td>{x.document_id}</td><td>{x.document_id && x.run_id ? <a href={`/workspace?document=${x.document_id}&run=${x.run_id}&version=${e.version_id}`}><code>{e.version_id}</code></a> : <code>{e.version_id}</code>}</td><td>{e.status}</td><td>{e.result?.verdict.score ?? 'not returned'} {e.result ? `(${e.result.verdict.decision})` : ''}</td><td>{x.credits_charged ?? 'unknown'}</td></tr> })}</tbody></table></div>}
            <p className="settings-note">These evaluations were used by experiment arm D; see Benchmark for the C-versus-D comparison (no measured Reppo benefit).</p>
          </section><div className="inline-note"><ShieldCheck size={16}/><p>A critique is a hypothesis to check against the PDF. Unsupported changes stay unresolved.</p></div>
        </>}

        {view === 'benchmark' && <>
          <Suspense fallback={<div className="loading-block" role="status"><Loader2 className="spin" size={22}/>Loading published experiments…</div>}><Experiments/></Suspense>
          <div className="protocol-cards"><article><div className="protocol-icon"><Columns3 size={19}/></div><h3>Period correctness</h3><p>Does the extracted interval match the source heading, duration, and comparative year?</p></article><article><div className="protocol-icon"><SlidersHorizontal size={19}/></div><h3>Unit correctness</h3><p>Do the currency and monetary scale match the applicable source statement?</p></article><article><div className="protocol-icon"><ShieldCheck size={19}/></div><h3>A fair comparison</h3><p>Same initial evidence. Frozen labels. Every missing fact and regression included.</p></article></div>
        </>}
        <footer className="page-footer"><span><img className="footer-logo" src="/evi-symbol.svg" alt=""/> Evi <span className="footer-rule"/> Context is part of the number.</span><span>Source-backed financial review</span></footer>
      </main>
    </div>
    {tourStep > 0 && <Tour step={tourStep} caps={caps} close={closeTour} side={view === 'data' ? 'left' : 'right'}/>}
    {toast && <div className="toast" role="status"><Check size={17}/><span>{toast}</span><button className="icon-button" aria-label="Dismiss notification" onClick={() => setToast('')}><X size={15}/></button></div>}
    {modal === 'settings' && <Dialog title="Processing connection" close={() => setModal(null)}><div className="connection-state"><div className="connection-state-icon">{connection === 'connected' ? <CheckCheck size={27}/> : <Unplug size={27}/>}</div><h3>{capabilityLabel(connection, caps).text}</h3><p>{connection === 'connected' ? 'Each capability is reported by the server; connectivity alone does not mean processing is available.' : 'You can inspect the original PDFs now. Stored results need the service.'}</p></div>
      {caps && <div className="cap-list">{([['Stored results', caps.stored_results.available ? 'available' : 'unavailable', 'Earlier real runs with their original timestamps.'], ['Source re-verification', caps.source_verification.available ? 'available' : 'unavailable', caps.source_verification.reason], ['New extraction (Docling + SERV)', caps.extraction.state, caps.extraction.reason], ['New Reppo evaluation', caps.evaluation.state, caps.evaluation.reason]] as [string, string, string][]).map(([k, st, why]) => <div key={k} className="settings-line"><span>{k}<small>{why}</small></span><Badge tone={st === 'available' ? 'success' : st === 'busy' || st === 'budget_exhausted' ? 'warning' : 'neutral'}>{st.replaceAll('_', ' ')}</Badge></div>)}</div>}<div className="settings-line"><span>Access</span><strong>Guest · No sign-in required</strong></div><div className="settings-line"><span>API</span><code>{import.meta.env.VITE_API_BASE_URL || '/api/v1'}</code></div><p className="settings-note">Provider credentials stay on the server. No API key is requested from reviewers.</p><div className="dialog-footer"><button className="button" onClick={() => setModal(null)}>Continue inspecting sources</button><button className="button primary" onClick={() => { setRefresh(n => n + 1); setToast('Checking the processing connection…') }}><RefreshCw size={15}/> Check connection</button></div></Dialog>}
    {modal === 'help' && <Dialog title="A number is only half the story." close={() => setModal(null)}><p className="dialog-intro">Evi checks whether a financial figure keeps the reporting period and monetary unit of its original source.</p><div className="help-steps"><div><span>1</span><section><h3>Start with a public report</h3><p>Choose an original issuer PDF. Docling supplies its table structure and source locations.</p></section></div><div><span>2</span><section><h3>Check meaning, not just digits</h3><p>SERV interprets the context. Deterministic checks test period and unit consistency.</p></section></div><div><span>3</span><section><h3>Trace every correction</h3><p>Reppo critiques a fact version. A SERV revision must be supported by source evidence.</p></section></div></div><div className="help-example"><TriangleAlert size={18}/><p>“Nine months ended September” must never silently become a full-year result.</p></div><p className="settings-note">Source fidelity is not an audit of the issuer’s accounting. No login is required to use the workspace.</p><div className="dialog-footer"><button className="button primary" onClick={() => setModal(null)}>Back to workspace <ArrowRight size={15}/></button></div></Dialog>}
    {modal === 'document' && <Dialog title="Source provenance" close={() => setModal(null)}><div className="provenance-heading"><FileText size={30}/><div><h3>{report.issuer_name}</h3><p>{report.title}</p></div></div><div className="settings-line"><span>Physical pages</span><strong>{report.page_count}</strong></div><div className="settings-line"><span>Source availability</span><strong>{report.availability}</strong></div><div className="hash-block"><label>ORIGINAL PDF · SHA-256</label><code>{report.sha256}</code><button className="button small" onClick={() => void copy(report.sha256)}><Copy size={13}/> Copy hash</button></div><p className="settings-note">This hash identifies the original downloaded PDF. It does not establish extraction accuracy or verify the issuer’s financial statements.</p><div className="dialog-footer"><a className="button primary" href={report.source_url} target="_blank" rel="noreferrer">Open publisher source <ExternalLink size={15}/></a></div></Dialog>}
  </div>
}
function ScanCheckIcon() { return <FileCheck2 size={16}/> }

function EvaluationCard({ e, revise }: { e: Evaluation; revise?: () => void }) {
  return <article className="evaluation-card"><div className="evaluation-heading"><div><span className="eyebrow">REAL REPPO EVALUATION</span><h3>{e.eval_id || 'Submission awaiting provider ID'}</h3><p>{date(e.created_at)} · Version {e.version_id}</p></div><Badge tone={e.status === 'completed' ? 'success' : 'neutral'}>{e.status}</Badge></div>
    {e.result ? <><div className="verdict"><strong>{e.result.verdict.score ?? '—'}<small>{e.result.verdict.score == null ? 'not returned' : '/100'}</small></strong><div><h4>Evaluator score · {e.result.verdict.decision}</h4><p>{e.result.verdict.confidence} confidence · Not measured extraction accuracy</p></div></div>{e.result.verdicts.map((v, i) => <div className="critique" key={i}><h4>{v.criterion}<span>{v.score == null ? 'not returned' : `${v.score}/100`}</span></h4><p>{v.critique || 'No critique text returned by the provider.'}</p></div>)}{revise && <button className="button primary" onClick={revise}><Sparkles size={14}/> Revise with SERV (bounded; may change nothing)</button>}</>
      : <div className="pending-evaluation"><Clock3 size={20}/><p>Awaiting a settled result. Reppo evaluation is asynchronous.</p></div>}</article>
}
