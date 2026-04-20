#!/usr/bin/env python3
"""Seed-ingest hospice regulatory docs to the Hospice regs Drive folder.

Downloads each URL to ./hospice-seed/, then uploads to Drive via gws.
The watcher will pick them up on its next 5-min cycle and register them
as NotebookLM Drive sources.

Run from C:/Users/silas/ so gws --upload accepts the relative paths.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from shutil import which


DRIVE_FOLDER_ID = "1zL6M_LdPtP52OyJNH0q0dy-j5PCg8z4u"
STAGING_DIR_NAME = "hospice-seed"

DOCS = [
    # Federal foundation
    ("CMS-MBPM-Ch9-Hospice.pdf",
     "https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/bp102c09.pdf",
     "federal"),
    ("CMS-Claims-Ch11-Hospice.pdf",
     "https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/clm104c11.pdf",
     "federal"),
    ("CMS-SOM-AppendixM-Hospice.pdf",
     "https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/downloads/som107ap_m_hospice.pdf",
     "federal"),
    ("CMS-HOPE-Guidance-Manual-v1.00.pdf",
     "https://www.cms.gov/files/document/hope-guidance-manualv100.pdf",
     "federal"),
    ("42-CFR-Part-418-Hospice-CoPs-2024.pdf",
     "https://www.govinfo.gov/content/pkg/CFR-2024-title42-vol3/pdf/CFR-2024-title42-vol3-part418.pdf",
     "federal"),
    ("CAHPS-Hospice-QAG-v12.0.pdf",
     "https://hospicecahpssurvey.org/globalassets/hospice-cahps4/quality-assurance-guidelines/cahps-hospice-survey-quality-assurance-guideline-v12.0.pdf",
     "federal"),
    ("CAHPS-Hospice-QAG-AppR-TechCorrections-Dec2025.pdf",
     "https://hospicecahpssurvey.org/globalassets/hospice-cahps4/quality-assurance-guidelines/technical-corrections-dec-2025/appendix-r_cahps-hospice-qag-v12.0-web-materials---english_rev-12_05_2025.pdf",
     "federal"),
    ("OIG-OEI-02-17-00021-Hospice-Deficiencies.pdf",
     "https://oig.hhs.gov/oei/reports/oei-02-17-00021.pdf",
     "federal"),
    ("OIG-OEI-02-17-00020-Hospice.pdf",
     "https://oig.hhs.gov/oei/reports/oei-02-17-00020.pdf",
     "federal"),
    # Texas
    ("TX-DSHS-Hospice-Service-Standard.pdf",
     "https://www.dshs.texas.gov/sites/default/files/hivstd/taxonomy/files/hospice.pdf",
     "texas"),
    ("TX-TMHP-LTC-Hospice-User-Guide.pdf",
     "https://www.tmhp.com/sites/default/files/file-library/ltc/LTC-Hospice-User-Guide.pdf",
     "texas"),
    ("TX-TMPPM-2025-03-FullManual.pdf",
     "https://www.tmhp.com/sites/default/files/file-library/resources/provider-manuals/tmppm/archives/2025-03-TMPPM.pdf",
     "texas"),
]

MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB ceiling; anything bigger we'll flag and skip


def log(msg: str) -> None:
    print(msg, flush=True)


def download(url: str, dest: Path) -> tuple[bool, int, str]:
    if dest.exists() and dest.stat().st_size > 0:
        return True, dest.stat().st_size, "cached"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            [
                "curl", "-sSL", "--fail-with-body", "-A",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "-o", str(dest), url,
            ],
            capture_output=True, text=True, timeout=300,
        )
        if proc.returncode != 0:
            try:
                if dest.exists():
                    dest.unlink()
            except Exception:
                pass
            return False, 0, f"curl rc={proc.returncode} stderr={(proc.stderr or '')[:200]}"
        if not dest.exists() or dest.stat().st_size == 0:
            return False, 0, "curl produced empty file"
        return True, dest.stat().st_size, "downloaded"
    except subprocess.TimeoutExpired:
        return False, 0, "curl timeout 300s"
    except Exception as e:
        return False, 0, f"{type(e).__name__}: {e}"


def is_pdf_valid(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            head = f.read(5)
        return head.startswith(b"%PDF-")
    except Exception:
        return False


def upload_to_drive(local_path: Path, drive_name: str) -> tuple[bool, str]:
    gws = which("gws")
    if not gws:
        return False, "gws not on PATH"
    rel = local_path.name
    staging = local_path.parent
    metadata = {"name": drive_name, "parents": [DRIVE_FOLDER_ID]}
    try:
        proc = subprocess.run(
            [
                gws, "drive", "files", "create",
                "--json", json.dumps(metadata),
                "--upload", rel,
                "--upload-content-type", "application/pdf",
                "--params", '{"fields":"id,name,size,webViewLink"}',
                "--api-version", "v3",
            ],
            capture_output=True, text=True, timeout=300,
            cwd=str(staging),
            check=False,
        )
        if proc.returncode != 0:
            return False, f"gws rc={proc.returncode} stderr={(proc.stderr or '')[:200]}"
        try:
            start = proc.stdout.find("{")
            data = json.loads(proc.stdout[start:])
            return True, f"uploaded drive_id={data.get('id')} size={data.get('size')}"
        except Exception:
            return True, f"uploaded (unparsed response): {proc.stdout[:200]}"
    except subprocess.TimeoutExpired:
        return False, "gws upload timeout 300s"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main() -> int:
    base = Path(STAGING_DIR_NAME)
    base.mkdir(exist_ok=True)

    total = len(DOCS)
    ok = 0
    skipped_size = 0
    failed = 0

    for i, (name, url, cat) in enumerate(DOCS, 1):
        log(f"\n[{i}/{total}] {name}  [{cat}]")
        log(f"  url: {url}")
        dest = base / name

        d_ok, size, d_msg = download(url, dest)
        if not d_ok:
            log(f"  DOWNLOAD FAIL: {d_msg}")
            failed += 1
            continue
        log(f"  download: {d_msg} size={size:,} bytes ({size/1024/1024:.2f} MB)")

        if not is_pdf_valid(dest):
            log(f"  PDF VALIDATION FAIL: file does not start with %PDF- (got HTML instead?)")
            failed += 1
            continue

        if size > MAX_UPLOAD_BYTES:
            log(f"  SKIPPED (> {MAX_UPLOAD_BYTES/1024/1024:.0f} MB upload ceiling). File staged at {dest}. Upload manually if desired.")
            skipped_size += 1
            continue

        u_ok, u_msg = upload_to_drive(dest, name)
        if not u_ok:
            log(f"  UPLOAD FAIL: {u_msg}")
            failed += 1
            continue
        log(f"  {u_msg}")
        ok += 1

    log(f"\n=== summary: {ok} uploaded | {skipped_size} size-skipped | {failed} failed | total {total} ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
