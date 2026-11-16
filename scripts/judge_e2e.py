"""Public judge-path verification from a CLEAN browser context (no cookies, no login). Makes no provider calls.

Usage: PYTHONIOENCODING=utf-8 backend/.venv/Scripts/python scripts/judge_e2e.py https://evi-lovat.vercel.app
Writes artifacts/judge-release/judge-e2e-<host>.json and screenshots. Inspected results are STORED historical runs.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = sys.argv[1].rstrip("/")
HOST = BASE.split("//")[1].replace(".", "_").replace(":", "_")
OUT = ROOT / "artifacts" / "judge-release"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "src"))
results = []


def check(name, ok, detail=""):
    results.append({"check": name, "pass": bool(ok), "detail": str(detail)[:300]})
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))


def http(path, method="GET", origin=None):
    req = urllib.request.Request(BASE + path, method=method, data=b"{}" if method == "POST" else None,
                                 headers={"Content-Type": "application/json", **({"Origin": origin} if origin else {})})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.headers.get("content-type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("content-type", ""), e.read()


def links():
    src = (ROOT / "src" / "Tour.tsx").read_text(encoding="utf-8")
    return {k: v for k, v in re.findall(r"(verizon3q|verizonFy2024|att2q): ws\(([^)]*)\)", src)}


V3Q = "/workspace?document=verizon-3q2025&run=run_3f60316ec62f4d0bb449&version=ver_3f60316ec62f_5&fact=run_3f60316ec62f4d0bb449%3Ar5%3Averizon-3q2025%3Arevenue%3A3M%3A2025"
FY24 = "/workspace?document=verizon-fy2024&run=run_b15ed73528114efe9b3e&version=ver_b15ed7352811_5&fact=run_b15ed73528114efe9b3e%3Averizon-fy2024%3Arevenue%3A12M%3A2024"
ATT = "/workspace?document=att-2q2025&run=run_325e06e62b8c46e58b4d&version=ver_325e06e62b8c_5&fact=run_325e06e62b8c46e58b4d%3Aatt-2q2025%3Arevenue%3A3M%3A2025"

# ---- API and bundle checks
s, ct, b = http("/api/v1/health")
h = json.loads(b)
caps = h.get("capabilities", {})
check("health reports capabilities (not connectivity)", s == 200 and caps.get("extraction", {}).get("state") in ("unavailable", "available", "busy", "budget_exhausted"),
      f"mode={caps.get('mode')} extraction={caps.get('extraction', {}).get('state')} evaluation={caps.get('evaluation', {}).get('state')}")
s, ct, b = http("/api/v1/nope")
check("unknown API route is a JSON error", s == 404 and "application/json" in ct)
if caps.get("extraction", {}).get("state") == "available":
    # Never POST a parse here when processing is live: it would start a real, paid SERV job.
    check("new processing refused server-side when unavailable", True, "skipped: processing is available (no POST sent)")
else:
    s, ct, b = http("/api/v1/documents/att-2q2025/parse", "POST", BASE)
    check("new processing refused server-side when unavailable", s in (403, 429, 503) and "application/json" in ct, f"{s} {b[:120]!r}")
s, ct, b = http("/api/v1/experiments")
check("published experiments served", s == 200 and json.loads(b)["schema"] == "evi.public-experiments/1")
s, ct, index = http("/")
assets = re.findall(rb'/assets/[^"\']+\.js', index)
bundle = index + b"".join(http(a.decode())[2] for a in assets[:6])
local_env = ROOT / "backend" / ".env"
keys = [l.split("=", 1)[1].strip().encode() for l in local_env.read_text().splitlines() if "=" in l and l.split("=", 1)[0].endswith("KEY") and len(l.split("=", 1)[1].strip()) >= 12] if local_env.exists() else []
check("no provider secrets in served HTML/JS", not any(k in bundle for k in keys) and b"REPPO_API_KEY" not in bundle and b"SERV_API_KEY" not in bundle,
      f"{len(assets)} bundles scanned")

with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 1440, "height": 960}, accept_downloads=True)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "favicon" not in m.text else None)

    # 1. Home -> Try Evi -> period mismatch
    page.goto(BASE + "/", wait_until="networkidle")
    page.get_by_role("button", name=re.compile("Try Evi")).first.click()
    page.wait_for_url(re.compile(r"/data\?.*tour=1"))
    page.wait_for_selector("text=Context does not match", timeout=40000)
    body = page.inner_text("main")
    check("Try Evi opens a real nine-month observation checked as Full year -> mismatch", "Context does not match" in body and "reports 9 months, while you selected a full year" in body,
          re.search(r"The source reports [^.]*\.", body).group(0) if re.search(r"The source reports [^.]*\.", body) else "")
    page.screenshot(path=str(OUT / "01-period-mismatch.png"))
    page.locator(".tour-card a", has_text="Check as 9 months").click()
    page.wait_for_selector("text=Context matches your selection", timeout=40000)
    check("same observation checked as 9 months -> match", True)
    page.screenshot(path=str(OUT / "02-period-match.png"))
    page.locator(".tour-card a", has_text="Try a unit mismatch").click()
    page.wait_for_selector("text=Context does not match", timeout=40000)
    check("unit mismatch (USD millions vs base USD) -> mismatch", "millions" in page.inner_text("main").lower())
    page.screenshot(path=str(OUT / "03-unit-mismatch.png"))

    # 2. Run a real extraction (capability-dependent)
    page.locator(".tour-card a", has_text="Next").click()
    page.wait_for_url(re.compile(r"/workspace\?.*tour=2"))
    page.wait_for_function("() => { const el = document.querySelector('.connection-pill'); return el && !el.textContent.includes('Checking') }", timeout=30000)
    pill = page.locator(".connection-pill").inner_text()
    btn = page.get_by_role("button", name=re.compile("Process report")).first
    if caps.get("extraction", {}).get("state") == "available":
        check("processing available is stated accurately", "Live processing available" in pill, pill)
    else:
        note = page.locator(".availability-note").first.inner_text()
        check("archive state is explicit; Process disabled with inline reason", btn.is_disabled() and "Archive" in pill and "archive" in note.lower(), f"{pill} | {note[:120]}")
    page.screenshot(path=str(OUT / "04-processing-availability.png"))

    # 3. Inspect evidence
    page.goto(BASE + V3Q + "&tour=3", wait_until="networkidle")
    page.wait_for_selector(".fact-table tbody tr")
    page.wait_for_selector(".stored-note")
    check("stored result labelled with original timestamps", "Stored result" in page.locator(".stored-note").inner_text() and "ver_3f60316ec62f_5" in page.locator(".stored-note").inner_text(),
          page.locator(".stored-note").inner_text())
    page.wait_for_selector(".cert-panel")
    page.locator(".cert-panel button", has_text="Re-verify").click()
    page.wait_for_selector(".cert-verify", timeout=40000)
    check("certificate re-verifies from registered source on the server", "Verified" in page.locator(".cert-verify").inner_text())
    check("revision lineage shown ($ -> USD accepted)", "currency" in page.inner_text(".fact-details").lower())
    page.wait_for_selector(".evidence-highlight", timeout=20000)
    page.screenshot(path=str(OUT / "05-verizon-3q-evidence.png"))
    page.goto(BASE + FY24, wait_until="networkidle")
    page.wait_for_selector(".evidence-highlight", timeout=30000)
    bx, pb = page.locator(".evidence-highlight").bounding_box(), page.locator(".pdf-paper").bounding_box()
    rel = ((bx["x"] - pb["x"]) / pb["width"], (bx["y"] - pb["y"]) / pb["height"])
    check("FY2024 offset-coordinate page: value highlight inside the page at the revenue cell", 0.55 < rel[0] < 0.75 and 0.15 < rel[1] < 0.25, f"{rel[0]:.3f},{rel[1]:.3f}")
    page.screenshot(path=str(OUT / "06-verizon-fy2024-offset.png"))
    page.goto(BASE + ATT, wait_until="networkidle")
    page.wait_for_selector(".fact-table tbody tr")
    chips = {page.locator(".fact-table tbody tr").nth(i).locator(".badge").inner_text() for i in range(page.locator(".fact-table tbody tr").count())}
    check("AT&T partial context retained (no guessed dates)", chips == {"Supported · dates not printed"}, chips)
    page.screenshot(path=str(OUT / "07-att-partial-context.png"))

    # deep link survives reload + menu navigation
    page.goto(BASE + V3Q, wait_until="networkidle")
    page.reload(wait_until="networkidle")
    page.wait_for_selector(".fact-table tbody tr")
    check("deep link restored after reload", "version=ver_3f60316ec62f_5" in page.url and "fact=" in page.url)
    with page.expect_download() as dl:
        page.locator("summary", has_text="Export").first.click()
        page.locator("button", has_text="Download CSV").first.click()
    csv = Path(dl.value.path()).read_text(encoding="utf-8")
    check("CSV export keeps provenance and coverage", "verizon.com" in csv and "context_coverage" in csv and "ver_3f60316ec62f_5" in csv)
    page.locator("nav a", has_text="Feedback").click()
    page.wait_for_selector("text=Recorded evaluation history")
    page.wait_for_timeout(1500)
    zero = page.locator(".zero-state").first.inner_text() if page.locator(".zero-state").count() else ""
    rows = page.locator(".eval-history tbody tr").count()
    links_ok = page.locator(".eval-history a[href*='/workspace?document=']").count()
    check("Feedback: honest zero state for this revision version", "No evaluation has been recorded for this version" in zero)
    check("Feedback: all recorded evaluations with exact evaluated-version links", rows == 11 and links_ok == 11, f"{rows} rows, {links_ok} lineage links")
    page.screenshot(path=str(OUT / "08-feedback-history.png"), full_page=True)
    page.locator("nav a", has_text="Workspace").click()
    page.wait_for_selector(".fact-table tbody tr")
    check("menu navigation keeps the selected version", "ver_3f60316ec62f_5" in page.url)

    # 5. Published experiments
    page.goto(BASE + "/benchmark", wait_until="networkidle")
    page.wait_for_selector(".exp-card")
    txt = page.inner_text("main")
    check("Benchmark shows both experiments and the null Reppo finding", page.locator(".exp-card").count() == 2 and txt.count("Arm D equals arm C") == 2)
    check("Benchmark shows provisional references and 0/48 human review", "human review 0/48" in txt and "not independently reviewed" in txt)
    check("experiment b labelled development evidence", "Development evidence" in txt)
    page.screenshot(path=str(OUT / "09-benchmark.png"), full_page=True)
    check("no browser errors", not errors, "; ".join(errors[:3]))

    # small screen
    m = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True).new_page()
    for name, path in (("home", "/"), ("workspace", ATT), ("benchmark", "/benchmark")):
        m.goto(BASE + path, wait_until="networkidle")
        m.wait_for_timeout(1500)
        over = m.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        check(f"small screen {name}: no horizontal page scroll", over <= 1, f"overflow {over}px")
        m.screenshot(path=str(OUT / f"10-mobile-{name}.png"))
    br.close()

(OUT / f"judge-e2e-{HOST}.json").write_text(json.dumps({"base": BASE, "provider_calls_made_by_this_check": 0, "results": results}, indent=1))
print(f"{sum(r['pass'] for r in results)}/{len(results)} passed")
sys.exit(0 if all(r["pass"] for r in results) else 1)
