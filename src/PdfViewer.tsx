import { useEffect, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight, ExternalLink, FileWarning, Minus, Plus, RotateCw, ScanLine } from 'lucide-react'
import { getDocument, GlobalWorkerOptions } from 'pdfjs-dist'
import type { PDFDocumentProxy, RenderTask } from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import type { Evidence, Report } from './types'

GlobalWorkerOptions.workerSrc = workerUrl
export default function PdfViewer({ report, url, evidence }: { report: Report; url: string; evidence: Evidence | null }) {
  const [doc, setDoc] = useState<PDFDocumentProxy | null>(null)
  const [page, setPage] = useState(report.source_page)
  const [width, setWidth] = useState(500)
  const [zoom, setZoom] = useState(100)
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const canvas = useRef<HTMLCanvasElement>(null)
  const viewport = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState({ width: 500, height: 700 })
  useEffect(() => {
    const el = viewport.current
    if (!el) return
    const observer = new ResizeObserver(entries => setWidth(Math.max(200, entries[0].contentRect.width - 40)))
    observer.observe(el); return () => observer.disconnect()
  }, [])
  useEffect(() => {
    let active = true
    setDoc(null); setError(''); setBusy(true); setPage(report.source_page); setZoom(100)
    const task = getDocument({ url })
    task.promise.then(value => { if (active) setDoc(value) }).catch(() => { if (active) { setError('This PDF could not be loaded. Retry or open the publisher’s original.'); setBusy(false) } })
    // Destroying a loading task mid-parse makes the PDF.js worker throw "Worker was terminated" inside the worker
    // thread. Let an in-flight load settle (its result is ignored via `active`), then release it.
    return () => { active = false; task.promise.then(() => task.destroy(), () => undefined).catch(() => undefined) }
  }, [url, report.source_page, attempt])
  useEffect(() => { if (evidence) setPage(evidence.page_number) }, [evidence])
  useEffect(() => {
    if (!doc || !canvas.current) return
    let active = true
    let task: RenderTask | undefined
    setBusy(true); setError('')
    doc.getPage(Math.min(page, doc.numPages)).then(pdfPage => {
      if (!active || !canvas.current) return
      const natural = pdfPage.getViewport({ scale: 1 })
      const view = pdfPage.getViewport({ scale: (width / natural.width) * zoom / 100 })
      const el = canvas.current
      const ratio = Math.min(window.devicePixelRatio || 1, 2)
      el.width = Math.ceil(view.width * ratio); el.height = Math.ceil(view.height * ratio)
      setSize({ width: view.width, height: view.height })
      task = pdfPage.render({ canvas: el, viewport: view, transform: [ratio, 0, 0, ratio, 0, 0] })
      return task.promise
    }).then(() => { if (active) setBusy(false) }).catch(error => {
      if (active && error?.name !== 'RenderingCancelledException') { setError('The page could not be rendered. Try another page or open the original PDF.'); setBusy(false) }
    })
    return () => { active = false; task?.cancel() }
  }, [doc, page, width, zoom])
  const box = evidence?.page_number === page && evidence.bbox && evidence.page_width && evidence.page_height
    ? { left: evidence.bbox.left / evidence.page_width * 100,
      top: (evidence.bbox.origin === 'TOPLEFT' ? evidence.bbox.top : evidence.page_height - evidence.bbox.top) / evidence.page_height * 100,
      width: (evidence.bbox.right - evidence.bbox.left) / evidence.page_width * 100,
      height: Math.abs(evidence.bbox.bottom - evidence.bbox.top) / evidence.page_height * 100 } : null
  return <div className="pdf-viewer">
    <div className="pdf-controls">
      <div className="control-group"><button className="icon-button" aria-label="Previous PDF page" disabled={page <= 1 || !doc} onClick={() => setPage(p => p - 1)}><ChevronLeft size={16} /></button>
        <label className="page-picker"><span className="sr-only">PDF page number</span><input aria-label="PDF page number" type="number" min={1} max={doc?.numPages || report.page_count} value={page} onChange={e => { const n = Number(e.target.value); if (n >= 1 && n <= (doc?.numPages || report.page_count)) setPage(n) }} /> <span>/ {doc?.numPages || report.page_count}</span></label>
        <button className="icon-button" aria-label="Next PDF page" disabled={!doc || page >= doc.numPages} onClick={() => setPage(p => p + 1)}><ChevronRight size={16} /></button></div>
      <div className="control-group zoom-controls"><button className="icon-button" aria-label="Zoom out" disabled={zoom <= 75} onClick={() => setZoom(z => z - 25)}><Minus size={15} /></button><span>{zoom}%</span><button className="icon-button" aria-label="Zoom in" disabled={zoom >= 175} onClick={() => setZoom(z => z + 25)}><Plus size={15} /></button></div>
      <a className="icon-button" href={`${url}#page=${page}`} target="_blank" rel="noreferrer" aria-label="Open full PDF"><ExternalLink size={16} /></a>
    </div>
    <div className="pdf-viewport" ref={viewport} aria-busy={busy}>
      {error ? <div className="pdf-error"><FileWarning size={30}/><h3>Source preview unavailable</h3><p>{error}</p><button className="button small" onClick={() => setAttempt(n => n + 1)}><RotateCw size={14}/> Retry</button><a href={report.source_url} target="_blank" rel="noreferrer">Open publisher source <ExternalLink size={13}/></a></div>
      : <><div className="pdf-paper" style={{ width: size.width, height: size.height }}><canvas ref={canvas} role="img" aria-label={`${report.issuer_name} original PDF, physical page ${page}`} style={{ width: size.width, height: size.height }} />
        {box && <div className="evidence-highlight" style={{ left: `${box.left}%`, top: `${box.top}%`, width: `${box.width}%`, height: `${box.height}%` }} aria-label="Cited source region"/>}
        {busy && <div className="pdf-loading"><ScanLine size={22}/><span>Rendering original page…</span></div>}</div>
        <div className="pdf-caption">Original publisher PDF <span>•</span> Physical page {page}</div></>}
    </div>
  </div>
}
