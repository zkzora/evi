"""Browser end-to-end check against the running local stack (Vite :5173 -> API :8000 -> worker).

Usage: backend/.venv/Scripts/python scripts/e2e_browser.py [document_id]
Writes screenshots to artifacts/ and prints what was observed. It reads existing real versions and
does not start new provider calls.
"""
import json
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5173"
OUT = Path(__file__).resolve().parents[1] / "artifacts"
doc = sys.argv[1] if len(sys.argv) > 1 else "verizon-fy2025"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 960})  # clean context: no cookies, no login
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.goto(f"{BASE}/", wait_until="networkidle")
    nav = page.locator("nav").first.inner_text()
    print("top navigation:", " | ".join(x.strip() for x in nav.split("\n") if x.strip()))
    page.screenshot(path=str(OUT / "e2e-home.png"))

    page.goto(f"{BASE}/workspace?document={doc}", wait_until="networkidle")
    page.wait_for_selector(".fact-table tbody tr", timeout=30000)
    page.wait_for_timeout(2500)
    rows = page.locator(".fact-table tbody tr")
    print("fact rows:", rows.count())
    for i in range(rows.count()):
        print("  ", " | ".join(t.strip() for t in rows.nth(i).inner_text().split("\n") if t.strip())[:200])
    page.screenshot(path=str(OUT / f"e2e-workspace-{doc}.png"), full_page=False)

    for label in ["Value", "Metric", "Period", "Unit"]:
        tab = page.locator(".evidence-tabs button", has_text=label).first
        if tab.count() == 0:
            print("evidence tab missing:", label)
            continue
        tab.click()
        page.wait_for_timeout(1800)
        box = page.locator(".evidence-highlight")
        paper = page.locator(".pdf-paper")
        if box.count():
            b, pb = box.bounding_box(), paper.bounding_box()
            print(f"  {label}: highlight at {(b['x'] - pb['x']) / pb['width']:.3f},{(b['y'] - pb['y']) / pb['height']:.3f} "
                  f"size {b['width'] / pb['width']:.3f}x{b['height'] / pb['height']:.3f} of page")
        else:
            print(f"  {label}: no highlight rendered")
        page.screenshot(path=str(OUT / f"e2e-evidence-{label.lower()}-{doc}.png"))

    rows.nth(0).click()
    page.wait_for_selector(".cert-panel", timeout=20000)
    page.wait_for_timeout(1500)
    panel = page.locator(".cert-panel").first
    print("certificate:", " | ".join(x.strip() for x in panel.inner_text().splitlines() if x.strip())[:500])
    btn = page.locator(".cert-panel button", has_text="Re-verify")
    if btn.count():
        btn.click()
        page.wait_for_selector(".cert-verify", timeout=30000)
        print("re-verify:", page.locator(".cert-verify").inner_text())
    panel.scroll_into_view_if_needed()
    page.screenshot(path=str(OUT / f"e2e-certificate-{doc}.png"), full_page=False)
    url = page.url
    print("deep link:", url)
    page.reload(wait_until="networkidle")
    page.wait_for_selector(".fact-table tbody tr", timeout=30000)
    print("reload keeps selection:", page.url == url or "version=" in page.url)

    health = json.load(urllib.request.urlopen("http://127.0.0.1:8000/api/v1/health"))
    print("health:", {k: health[k] for k in ("live_execution_enabled", "processing_enabled")}, health["components"])
    print("page errors:", errors or "none")
    browser.close()
