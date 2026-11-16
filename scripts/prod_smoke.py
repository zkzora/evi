"""Local production smoke test (isolated copied state, separate port, provider execution disabled). No provider calls.

Usage: PYTHONIOENCODING=utf-8 backend/.venv/Scripts/python scripts/prod_smoke.py http://127.0.0.1:8100 <prod data dir> [--quick]
Results inspected here are PERSISTED historical results with their original timestamps, not a fresh processing run.
"""
import json
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE, DATA = sys.argv[1].rstrip("/"), Path(sys.argv[2])
QUICK = "--quick" in sys.argv
OUT = Path(__file__).resolve().parents[1] / "artifacts" / "release-smoke"
OUT.mkdir(parents=True, exist_ok=True)
results = []


def check(name, ok, detail=""):
    results.append({"check": name, "pass": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))


def get(path, headers=None):
    req = urllib.request.Request(BASE + path, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.headers.get("content-type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("content-type", ""), e.read()


def post(path, origin):
    req = urllib.request.Request(BASE + path, data=b"{}", method="POST",
                                 headers={"Content-Type": "application/json", "Origin": origin})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


calls_before = sqlite3.connect(DATA / "evi.sqlite3").execute("SELECT COUNT(*) FROM provider_calls").fetchone()[0]
s, ct, body = get("/api/v1/health")
h = json.loads(body)
check("health JSON, execution disabled", s == 200 and h["execution_enabled"] is False and h["processing_enabled"] is False
      and h["live_execution_enabled"] is False, json.dumps(h["components"]))
s, ct, body = get("/api/v1/ready")
check("readiness reports storage/sources/worker", s == 200 and json.loads(body)["ready"], body.decode()[:200])
for path in ("/", "/workspace?document=att-2q2025", "/data?company=verizon", "/benchmark"):
    s, ct, body = get(path)
    check(f"SPA deep link {path}", s == 200 and "text/html" in ct and b"<div id=\"root\"" in body)
s, ct, body = get("/api/v1/nope")
check("unknown API path is JSON 404, not SPA HTML", s == 404 and "application/json" in ct)
s, ct, body = get("/api/v1/documents")
docs = json.loads(body)["items"]
check("5 registered USD documents", len(docs) == 5 and {d["currency"] for d in docs} == {"USD"})
s, ct, body = get("/api/v1/documents/att-2q2025/source")
check("original PDF bytes served", s == 200 and body[:5] == b"%PDF-")
code, j = post("/api/v1/documents/att-2q2025/parse", BASE)
check("new processing refused server-side (execution disabled)", code == 503 and j["error"]["code"] == "execution_disabled")
code, j = post("/api/v1/documents/att-2q2025/parse", "https://evil.example")
check("cross-origin write refused", code == 403)
s, ct, body = get("/api/v1/versions/ver_63c7ce8b5e69_1")
v = json.loads(body)
check("persisted historical version readable with original timestamp", s == 200 and v["created_at"].startswith("2026-11-15"),
      f"created_at {v['created_at']} (original run time, not a fresh run)")
s, ct, body = get("/api/v1/evaluations")
evs = json.loads(body)["items"]
check("persisted Reppo records readable", len(evs) == 11 and all(e["status"] == "completed" for e in evs))

if not QUICK:
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE + "/", wait_until="networkidle")
        nav = [x.strip() for x in page.locator("nav").first.inner_text().splitlines() if x.strip()]
        check("Home opens without login; top navigation intact", nav[:6] == ["Home", "Workspace", "Real data", "Documents", "Feedback", "Benchmark"], " | ".join(nav))
        page.goto(BASE + "/workspace?document=att-2q2025", wait_until="networkidle")
        page.wait_for_selector(".fact-table tbody tr", timeout=30000)
        chips = {page.locator(".fact-table tbody tr").nth(i).locator(".badge").inner_text() for i in range(page.locator(".fact-table tbody tr").count())}
        check("AT&T partial context not shown as complete", chips == {"Supported · dates not printed"}, str(chips))
        page.locator(".fact-table tbody tr").first.click()
        page.wait_for_selector(".cert-coverage")
        page.locator(".cert-panel button", has_text="Re-verify").click()
        page.wait_for_selector(".cert-verify", timeout=30000)
        check("certificate re-verifies on the production server", "Verified" in page.locator(".cert-verify").inner_text())
        page.locator("summary", has_text="Export").first.click()
        with page.expect_download() as dl:
            page.locator("button", has_text="Download CSV").first.click()
        csv = Path(dl.value.path()).read_text(encoding="utf-8")
        check("CSV export carries coverage and provenance", "exact dates are not printed" in csv and "not_printed_in_source" in csv and "att-2q2025" in csv.lower() or "investors.att.com" in csv)
        page.screenshot(path=str(OUT / "prod-workspace-att-2q2025.png"))
        page.goto(BASE + "/workspace?document=verizon-fy2025", wait_until="networkidle")
        page.wait_for_selector(".fact-table tbody tr")
        page.locator("button", has_text="Run extraction").first.click()
        page.wait_for_timeout(800)
        txt = page.locator("dialog").first.inner_text() if page.locator("dialog").count() else ""
        check("Process action explains disabled processing (no job created)", "not enabled new processing" in txt or "connected" in txt.lower(), txt[:120])
        check("no browser page errors", not errors, "; ".join(errors[:2]))
        b.close()

calls_after = sqlite3.connect(DATA / "evi.sqlite3").execute("SELECT COUNT(*) FROM provider_calls").fetchone()[0]
check("no provider calls during smoke test", calls_before == calls_after, f"{calls_before} -> {calls_after}")
(OUT / ("smoke-quick.json" if QUICK else "smoke.json")).write_text(json.dumps({"base": BASE, "results": results}, indent=1))
sys.exit(0 if all(r["pass"] for r in results) else 1)
