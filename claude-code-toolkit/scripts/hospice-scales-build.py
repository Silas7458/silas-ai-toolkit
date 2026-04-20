#!/usr/bin/env python3
"""Build one expanded PDF reference per hospice assessment scale.

For each scale: structured content (what it measures, scoring math,
interpretation bands, hospice relevance, worked examples, picture-fit
framing, pitfalls). Render to PDF via Playwright (headless Chrome),
upload each to the Hospice regs Drive folder. Watcher ingests into
NotebookLM for /hospice-ask queries.

Philosophy: hospice appropriateness is a CONSTELLATION of findings
painting a 6-month-prognosis picture. Scales quantify fragments of
the picture. Every scale doc emphasizes 'what else should be true'
alongside a concerning score - never treat a single scale value as
pass/fail for hospice eligibility.
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
OUT_DIR = Path("hospice-scales-pdfs")
OUT_DIR.mkdir(exist_ok=True)


CSS = """
<style>
@page { size: Letter; margin: 0.65in; }
body { font-family: 'Georgia', 'Times New Roman', serif; font-size: 11pt; line-height: 1.5; color: #222; margin: 0; }
h1 { font-size: 20pt; color: #1a3a52; border-bottom: 3px double #1a3a52; padding-bottom: 6px; margin: 0 0 4pt 0; }
h2 { font-size: 13pt; color: #1a3a52; border-bottom: 1px solid #c0c8d0; padding-bottom: 3px; margin-top: 18pt; margin-bottom: 6pt; }
h3 { font-size: 11.5pt; color: #2a4a62; margin-top: 12pt; margin-bottom: 4pt; }
.meta { font-size: 9.5pt; color: #555; font-style: italic; margin-bottom: 12pt; }
.meta strong { color: #1a3a52; font-style: normal; }
.tag { display: inline-block; background: #e8eef2; color: #1a3a52; padding: 2px 8px; border-radius: 4px; font-size: 9pt; font-family: 'Arial', sans-serif; margin-right: 4px; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 10pt; }
th { background: #1a3a52; color: white; padding: 5px 8px; text-align: left; border: 1px solid #1a3a52; }
td { padding: 4px 8px; border: 1px solid #bbb; vertical-align: top; }
tr:nth-child(even) td { background: #f6f9fb; }
.callout { background: #fff8e6; border-left: 4px solid #d4a017; padding: 8px 12px; margin: 10pt 0; font-size: 10.5pt; }
.callout-label { font-weight: bold; color: #8a6a10; font-family: 'Arial', sans-serif; font-size: 9.5pt; text-transform: uppercase; letter-spacing: 0.5px; }
.picture { background: #eef5ea; border-left: 4px solid #4a7a3a; padding: 8px 12px; margin: 10pt 0; font-size: 10.5pt; }
.picture-label { font-weight: bold; color: #2d5a1a; font-family: 'Arial', sans-serif; font-size: 9.5pt; text-transform: uppercase; letter-spacing: 0.5px; }
.example { background: #f0f3fa; border: 1px solid #c8d0e0; padding: 10pt; margin: 8pt 0; font-size: 10.5pt; border-radius: 3px; }
.example-label { font-weight: bold; color: #2a4a7a; font-family: 'Arial', sans-serif; font-size: 9.5pt; text-transform: uppercase; letter-spacing: 0.5px; }
ul, ol { margin: 4pt 0 8pt 20pt; padding: 0; }
li { margin-bottom: 3pt; }
code { font-family: 'Consolas', monospace; background: #eee; padding: 1px 4px; border-radius: 2px; font-size: 10pt; }
.footer { margin-top: 24pt; padding-top: 8pt; border-top: 1px solid #ccc; font-size: 9pt; color: #666; font-style: italic; }
</style>
"""


def html_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def md_to_html(text: str) -> str:
    """Lightweight conversion: paragraphs, bullets, bold via **, code via ``."""
    text = html_escape(text)
    # bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # convert blocks
    blocks = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("- "):
            items = [line[2:].strip() for line in block.split("\n") if line.strip().startswith("- ")]
            items_html = "".join(f"<li>{i}</li>" for i in items)
            blocks.append(f"<ul>{items_html}</ul>")
        elif re.match(r"^\d+\.\s", block):
            items = [re.sub(r"^\d+\.\s*", "", line).strip() for line in block.split("\n") if re.match(r"^\d+\.\s", line)]
            items_html = "".join(f"<li>{i}</li>" for i in items)
            blocks.append(f"<ol>{items_html}</ol>")
        else:
            blocks.append(f"<p>{block.replace(chr(10), '<br>')}</p>")
    return "\n".join(blocks)


def build_table(headers: list[str], rows: list[list[str]]) -> str:
    thead = "".join(f"<th>{html_escape(h)}</th>" for h in headers)
    body_rows = []
    for r in rows:
        cells = "".join(f"<td>{html_escape(str(c))}</td>" for c in r)
        body_rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def render_scale_html(scale: dict) -> str:
    """Render a scale dict into a full HTML document."""
    acronym = scale["acronym"]
    full = scale["full_name"]
    category = scale["category"]
    source = scale.get("source", "")
    summary = scale.get("summary", "")

    parts = []
    parts.append(f"<h1>{html_escape(acronym)} — {html_escape(full)}</h1>")
    parts.append(
        f'<div class="meta">'
        f'<span class="tag">{html_escape(category)}</span>'
        f'<strong>Original publication / source:</strong> {html_escape(source)}'
        f'</div>'
    )

    if summary:
        parts.append(f"<p><strong>Summary.</strong> {md_to_html(summary).lstrip('<p>').rstrip('</p>')}</p>")

    def section(title, body_html):
        return f"<h2>{html_escape(title)}</h2>{body_html}"

    if scale.get("what_it_measures"):
        parts.append(section("What it measures", md_to_html(scale["what_it_measures"])))

    if scale.get("scoring"):
        parts.append(section("How to score", md_to_html(scale["scoring"])))
        if scale.get("scoring_table"):
            parts.append(build_table(scale["scoring_table"]["headers"], scale["scoring_table"]["rows"]))

    if scale.get("interpretation"):
        parts.append(section("Interpretation and prognosis", md_to_html(scale["interpretation"])))
        if scale.get("interpretation_table"):
            parts.append(build_table(scale["interpretation_table"]["headers"], scale["interpretation_table"]["rows"]))

    if scale.get("when_to_use"):
        parts.append(section("When to use", md_to_html(scale["when_to_use"])))

    if scale.get("hospice_relevance"):
        parts.append(section("Hospice relevance", md_to_html(scale["hospice_relevance"])))

    if scale.get("worked_examples"):
        parts.append("<h2>Worked examples</h2>")
        for ex in scale["worked_examples"]:
            parts.append(
                f'<div class="example">'
                f'<div class="example-label">Example — {html_escape(ex["label"])}</div>'
                f'{md_to_html(ex["body"])}'
                f'</div>'
            )

    if scale.get("picture_fit"):
        parts.append("<h2>How this fits the picture</h2>")
        parts.append(
            f'<div class="picture">'
            f'<div class="picture-label">PICTURE-PAINTING</div>'
            f'{md_to_html(scale["picture_fit"])}'
            f'</div>'
        )

    if scale.get("pitfalls"):
        parts.append("<h2>Common pitfalls</h2>")
        parts.append(
            f'<div class="callout">'
            f'<div class="callout-label">PITFALLS</div>'
            f'{md_to_html(scale["pitfalls"])}'
            f'</div>'
        )

    if scale.get("references"):
        parts.append(section("References", md_to_html(scale["references"])))

    parts.append(
        '<div class="footer">Generated for the Amerix Hospice Compliance knowledge corpus. '
        'Part of a reference series on hospice assessment scales and the picture-painting '
        'approach to terminal prognosis determination. Scales quantify fragments of the '
        'clinical picture and never substitute for medical director judgment.</div>'
    )

    body = "\n".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html_escape(acronym)} — {html_escape(full)}</title>
{CSS}
</head>
<body>
{body}
</body>
</html>"""


def sanitize_filename(s: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return s[:100]


async def render_pdf(page, html: str, pdf_path: Path) -> None:
    await page.set_content(html, wait_until="networkidle")
    await page.pdf(
        path=str(pdf_path),
        format="Letter",
        margin={"top": "0.65in", "right": "0.65in", "bottom": "0.65in", "left": "0.65in"},
        print_background=True,
    )


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
            return False, f"rc={proc.returncode} stderr={(proc.stderr or proc.stdout or '')[:200]}"
        start = proc.stdout.find("{")
        data = json.loads(proc.stdout[start:])
        return True, f"id={data.get('id')} size={data.get('size')}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


# ----------------------------------------------------------------------------
# SCALE CONTENT
# ----------------------------------------------------------------------------
# Each scale below is written to be NotebookLM-queryable at the level of
# "given these inputs, what would this patient's score be and what does
# that mean for hospice eligibility?"

from hospice_scales_content import SCALES  # loaded from sibling data file


async def main():
    print(f"Rendering {len(SCALES)} scale references...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(viewport={"width": 900, "height": 1200})
        page = await ctx.new_page()
        pdfs = []
        for i, scale in enumerate(SCALES, 1):
            html = render_scale_html(scale)
            fname = f"Hospice-Scale-{scale['acronym']}-{sanitize_filename(scale['full_name'])}.pdf"
            pdf_path = OUT_DIR / fname
            print(f"  [{i}/{len(SCALES)}] {scale['acronym']}... ", end="", flush=True)
            try:
                await render_pdf(page, html, pdf_path)
                size = pdf_path.stat().st_size
                print(f"PDF {size:,} bytes")
                pdfs.append(pdf_path)
            except Exception as e:
                print(f"FAIL: {type(e).__name__}: {e}")
        await browser.close()

    print(f"\nUploading {len(pdfs)} PDFs to Drive...")
    uploaded = 0
    for p in pdfs:
        ok, msg = upload_to_drive(p)
        status = "OK" if ok else "FAIL"
        print(f"  [{status}] {p.name} -> {msg}")
        if ok:
            uploaded += 1
    print(f"\nsummary: rendered={len(pdfs)}/{len(SCALES)}  uploaded={uploaded}/{len(pdfs)}")
    return 0 if uploaded == len(SCALES) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
