"""Browser check (coverage-v1): an AT&T fact whose exact dates are not printed must not look like complete verification,
while a Verizon 3Q fact with printed dates shows complete coverage. Read-only; no provider calls.

Usage: PYTHONIOENCODING=utf-8 backend/.venv/Scripts/python scripts/e2e_partial_context.py
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5173"
OUT = Path(__file__).resolve().parents[1] / "artifacts" / "proof-integrity"
ok = True

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_context(viewport={"width": 1440, "height": 1000}).new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    for doc, expect_complete in (("att-2q2025", False), ("verizon-3q2025", True)):
        page.goto(f"{BASE}/workspace?document={doc}", wait_until="networkidle")
        page.wait_for_selector(".fact-table tbody tr", timeout=30000)
        page.wait_for_timeout(1500)
        rows = page.locator(".fact-table tbody tr")
        chips = [rows.nth(i).locator(".badge").inner_text().strip() for i in range(rows.count())]
        rows.nth(0).click()
        page.wait_for_selector(".cert-coverage", timeout=20000)
        cov = page.locator(".cert-coverage").first
        complete = cov.get_attribute("data-complete") == "true"
        interval = page.locator(".fact-detail-grid").inner_text().replace("\n", " ")
        badge = page.locator(".cert-badge").first.inner_text()
        title = page.locator("h1, .report-select-wrap select").first.inner_text()[:60]
        print(f"{doc}: rows={rows.count()} chips={sorted(set(chips))} badge={badge!r} complete={complete}")
        print(f"   coverage: {cov.inner_text()}")
        print(f"   interval: {interval}")
        print(f"   url: {page.url}")
        good = (complete == expect_complete) and (doc in page.url) and \
            (expect_complete or ("Checks passed" not in chips and "not printed" in interval and "partial" in badge.lower()))
        ok &= good
        print("   PASS" if good else "   FAIL")
        page.locator(".cert-panel").first.scroll_into_view_if_needed()
        page.screenshot(path=str(OUT / f"e2e-coverage-{doc}.png"))
    print("page errors:", errors or "none")
    ok &= not errors
    b.close()
sys.exit(0 if ok else 1)
