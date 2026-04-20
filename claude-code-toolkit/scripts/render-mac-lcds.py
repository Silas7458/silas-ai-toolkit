#!/usr/bin/env python3
"""Render NGS and CGS umbrella hospice LCDs to PDF for extraction.

These are working-material PDFs - they go into /tmp/hospice-toolbox-source/
and are NOT uploaded to the Hospice regs Drive folder. Only the
synthesized disease-organized toolbox documents are uploaded.
"""

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright


LCDS = [
    (33393, "NGS-L33393-Hospice-Determining-Terminal-Status.pdf"),
    (34538, "CGS-L34538-Hospice-Determining-Terminal-Status.pdf"),
]

OUT = Path("/tmp/hospice-toolbox-source")
OUT.mkdir(parents=True, exist_ok=True)


async def render(page, lcd_id, fname):
    url = f"https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?LCDId={lcd_id}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        return f"goto fail: {e}"
    await page.wait_for_timeout(10000)  # long wait for Blazor render
    body = await page.locator("body").inner_text()
    if len(body) < 500:
        await page.wait_for_timeout(5000)
        body = await page.locator("body").inner_text()
    if len(body) < 500:
        return f"body too short: {len(body)} chars"
    pdf_path = OUT / fname
    await page.pdf(
        path=str(pdf_path),
        format="Letter",
        margin={"top": "0.5in", "right": "0.5in", "bottom": "0.5in", "left": "0.5in"},
        print_background=True,
    )
    return f"OK {pdf_path.stat().st_size:,} bytes"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 1600},
        )
        page = await ctx.new_page()
        for lcd_id, fname in LCDS:
            print(f"rendering L{lcd_id}... ", end="", flush=True)
            result = await render(page, lcd_id, fname)
            print(result)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
