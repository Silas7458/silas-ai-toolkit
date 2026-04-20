#!/usr/bin/env python3
"""Two-pass scrape:
    Pass 1: Load Palmetto JM HHH Medical Policies index, scrape ALL
            rows whose LCD-Title or Article-Title column contains
            'hospice'. This gives the authoritative list.
    Pass 2: For each discovered LCD and Article, render the CMS MCD
            detail page to PDF. Upload each to the Hospice regs folder.
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

from playwright.async_api import async_playwright


DRIVE_FOLDER_ID = "1zL6M_LdPtP52OyJNH0q0dy-j5PCg8z4u"
OUT_DIR = Path("palmetto-hospice-pdfs")
OUT_DIR.mkdir(exist_ok=True)

INDEX_URL = "https://palmettogba.com/jmhhh/did/8b3rw86238?cat=jmhhh-medical-policies"


def sanitize(s: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return s[:100] or "x"


async def discover_hospice_items(page) -> tuple[list[dict], list[dict]]:
    """Return (lcds, articles) each as list of {id, title}.

    Strategy: walk every table row; if row text contains 'hospice'
    (case-insensitive), extract LCD IDs (L\d+) and Article IDs (A\d+)
    plus the LCD Title and Article Title columns for naming.
    """
    print(f"Loading index: {INDEX_URL}")
    await page.goto(INDEX_URL, wait_until="domcontentloaded", timeout=60000)
    # React hydrate
    await page.wait_for_timeout(6000)
    # Scroll to bottom to force-render any virtualized table rows
    for _ in range(5):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(800)
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(500)

    rows = await page.locator("tr").all()
    lcds: dict[int, str] = {}
    articles: dict[int, str] = {}
    latest_lcd_title = ""
    latest_article_title = ""
    for row in rows:
        try:
            cells = await row.locator("td, th").all()
            if len(cells) < 2:
                continue
            texts = []
            for c in cells:
                t = (await c.inner_text() or "").strip()
                texts.append(t)
            row_text = " | ".join(texts)
        except Exception:
            continue
        if "hospice" not in row_text.lower():
            continue
        # Columns we expect: LCD Title | LCD ID | Article Title | Article ID | CPT codes
        lcd_title = texts[0] if len(texts) > 0 else ""
        lcd_id_cell = texts[1] if len(texts) > 1 else ""
        article_title = texts[2] if len(texts) > 2 else ""
        article_id_cell = texts[3] if len(texts) > 3 else ""
        for m in re.finditer(r"L(\d{5,6})", lcd_id_cell):
            lid = int(m.group(1))
            if lcd_title.strip():
                lcds[lid] = lcd_title.strip()
            elif lid not in lcds:
                lcds[lid] = ""
        for m in re.finditer(r"A(\d{5,6})", article_id_cell):
            aid = int(m.group(1))
            if article_title.strip():
                articles[aid] = article_title.strip()
            elif aid not in articles:
                articles[aid] = ""

    lcd_list = [{"id": i, "title": t} for i, t in sorted(lcds.items())]
    art_list = [{"id": i, "title": t} for i, t in sorted(articles.items())]
    return lcd_list, art_list


async def render_mcd(page, url: str, pdf_path: Path) -> tuple[bool, str]:
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        return False, f"goto: {type(e).__name__}: {e}"
    await page.wait_for_timeout(8000)
    try:
        body_text = await page.locator("body").inner_text()
    except Exception:
        body_text = ""
    if len(body_text) < 500:
        await page.wait_for_timeout(5000)
        try:
            body_text = await page.locator("body").inner_text()
        except Exception:
            pass
    if len(body_text) < 500:
        return False, f"body too short ({len(body_text)} chars)"
    try:
        await page.pdf(
            path=str(pdf_path),
            format="Letter",
            margin={"top": "0.5in", "right": "0.5in", "bottom": "0.5in", "left": "0.5in"},
            print_background=True,
        )
        return True, f"{pdf_path.stat().st_size:,} bytes"
    except Exception as e:
        return False, f"pdf: {type(e).__name__}: {e}"


def upload_to_drive(local_path: Path) -> tuple[bool, str]:
    metadata = {"name": local_path.name, "parents": [DRIVE_FOLDER_ID]}
    try:
        proc = subprocess.run(
            [
                "gws", "drive", "files", "create",
                "--json", json.dumps(metadata),
                "--upload", local_path.name,
                "--params", '{"fields":"id,size"}',
                "--api-version", "v3",
            ],
            capture_output=True, text=True, timeout=300,
            cwd=str(local_path.parent.resolve()),
            check=False,
        )
        if proc.returncode != 0:
            return False, f"gws rc={proc.returncode} stderr={(proc.stderr or proc.stdout or '')[:300]}"
        start = proc.stdout.find("{")
        data = json.loads(proc.stdout[start:])
        return True, f"drive_id={data.get('id')} size={data.get('size')}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 2000},
        )
        page = await ctx.new_page()

        lcds, articles = await discover_hospice_items(page)
        print(f"\nDiscovered {len(lcds)} hospice LCDs and {len(articles)} hospice Articles:")
        for l in lcds:
            print(f"  LCD L{l['id']}: {l['title'][:90]}")
        for a in articles:
            print(f"  ART A{a['id']}: {a['title'][:90]}")

        if not lcds and not articles:
            print("\nNo hospice items discovered; aborting.")
            await browser.close()
            return 1

        jobs = []
        for l in lcds:
            slug = sanitize(l["title"] or f"LCD-L{l['id']}")
            jobs.append({
                "kind": "LCD",
                "id": l["id"],
                "url": f"https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?LCDId={l['id']}",
                "filename": f"Palmetto-JMHHH-LCD-L{l['id']}-{slug}.pdf",
            })
        for a in articles:
            slug = sanitize(a["title"] or f"Article-A{a['id']}")
            jobs.append({
                "kind": "Article",
                "id": a["id"],
                "url": f"https://www.cms.gov/medicare-coverage-database/view/article.aspx?articleId={a['id']}",
                "filename": f"Palmetto-JMHHH-Article-A{a['id']}-{slug}.pdf",
            })

        rendered = []
        for i, job in enumerate(jobs, 1):
            pdf_path = OUT_DIR / job["filename"]
            print(f"\n[{i}/{len(jobs)}] {job['kind']} {job['id']}...", end=" ", flush=True)
            ok, msg = await render_mcd(page, job["url"], pdf_path)
            if ok:
                print(f"PDF {msg}")
                rendered.append({"job": job, "pdf": pdf_path})
            else:
                print(f"FAIL: {msg}")

        await browser.close()

    print(f"\n=== Uploading {len(rendered)} PDFs ===")
    uploaded = 0
    for r in rendered:
        ok, msg = upload_to_drive(r["pdf"])
        status = "OK" if ok else "FAIL"
        print(f"  [{status}] {r['pdf'].name[:100]} -> {msg}")
        if ok:
            uploaded += 1
    print(f"\nsummary: discovered_lcds={len(lcds)}  discovered_articles={len(articles)}  rendered={len(rendered)}  uploaded={uploaded}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
