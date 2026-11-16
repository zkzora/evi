import { useState } from 'react'
import { ArrowRight, FileUp, Info, Loader2 } from 'lucide-react'
import { api } from './api'
import type { Report } from './types'

export type UploadLimits = { max_bytes: number; max_pages: number; retention_hours: number; per_session_active?: number }
export const defaultUploadLimits: UploadLimits = { max_bytes: 10 * 1024 * 1024, max_pages: 250, retention_hours: 24 }
const mib = (n: number) => `${Math.round(n / 1024 / 1024)} MiB`

/** Upload dialog body: states the supported inputs and limits BEFORE upload. Upload only registers the file. */
export function UploadForm({ limits, onUploaded, close }: { limits: UploadLimits; onUploaded: (doc: Report) => void; close: () => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [label, setLabel] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submit = async () => {
    if (!file) return
    if (file.size > limits.max_bytes) { setError(`This file is ${(file.size / 1024 / 1024).toFixed(1)} MiB; the limit is ${mib(limits.max_bytes)}.`); return }
    setBusy(true); setError('')
    try { onUploaded(await api.upload(file, label)) } catch (e) { setError(e instanceof Error ? e.message : 'The upload failed.') } finally { setBusy(false) }
  }
  return <div className="upload-form">
    <ul className="upload-rules">
      <li><strong>Supported input:</strong> an English-language telecom financial report in USD with an income statement (annual or interim).
        Evi reads three metrics: consolidated revenue, operating profit (operating income) and net income attributable to the parent.</li>
      <li><strong>Limits:</strong> one unencrypted PDF, at most {mib(limits.max_bytes)} and {limits.max_pages} pages.</li>
      <li><strong>What is sent where:</strong> uploading only stores the file and counts its pages. When you press Process, Docling parses the
        one page you selected on Evi’s server, and that page’s text and table cells are sent to SERV for extraction. Reppo is never called automatically.</li>
      <li><strong>Privacy and retention:</strong> the PDF and its results belong to this browser session only and are deleted {limits.retention_hours} hours after upload. No account or API key is needed.</li>
      <li><strong>Boundaries:</strong> no OCR, no currency conversion, no automatic sector or language detection. A layout the checker cannot bind is reported as unsupported, not guessed.</li>
    </ul>
    <label className="upload-field"><span>PDF file</span><input type="file" accept="application/pdf,.pdf" onChange={e => { setFile(e.target.files?.[0] ?? null); setError('') }}/></label>
    <label className="upload-field"><span>Label (optional, shown only to you; never used as evidence)</span><input type="text" maxLength={80} value={label} placeholder="e.g. Example Telecom 2025 annual report" onChange={e => setLabel(e.target.value)}/></label>
    {error && <p className="upload-error" role="alert">{error}</p>}
    <div className="dialog-footer"><button className="button" onClick={close}>Cancel</button>
      <button className="button primary" disabled={!file || busy} aria-busy={busy} onClick={() => void submit()}>{busy ? <Loader2 size={15} className="spin"/> : <FileUp size={15}/>}Upload PDF</button></div>
  </div>
}

/** Page selection for an uploaded PDF: physical page index, explicit confirmation, then Process. */
export function UploadPageControls({ report, page, setPage, confirmed, setConfirmed, canProcess, pending, reason, onProcess }: {
  report: Report; page: number; setPage: (n: number) => void; confirmed: boolean; setConfirmed: (b: boolean) => void
  canProcess: boolean; pending: boolean; reason?: string; onProcess: () => void
}) {
  const valid = Number.isInteger(page) && page >= 1 && page <= report.page_count
  return <div className="upload-page-controls">
    <label className="upload-field compact"><span>Physical page (1–{report.page_count})</span>
      <input type="number" min={1} max={report.page_count} value={page} onChange={e => { setPage(Number(e.target.value)); setConfirmed(false) }}/></label>
    <label className="upload-confirm"><input type="checkbox" checked={confirmed} disabled={!valid} onChange={e => setConfirmed(e.target.checked)}/>
      Page {valid ? page : '?'} is the income statement</label>
    <button className="button primary" disabled={!canProcess || !confirmed || !valid || pending} aria-busy={pending} onClick={onProcess} title={canProcess ? undefined : reason}>
      {pending ? <Loader2 size={15} className="spin"/> : <ArrowRight size={14}/>}Process page {valid ? page : ''}</button>
    <p className="upload-hint"><Info size={13}/> The physical page is the PDF’s own page index (what the viewer shows), not the page number printed on the page.</p>
  </div>
}
