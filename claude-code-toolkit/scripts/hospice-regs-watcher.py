#!/usr/bin/env python3
"""
Hospice Regs Watcher - polls the executive.shelton@gmail.com Drive folder
"Hospice regs" and registers new PDFs as NotebookLM Drive sources in the
"Hospice Compliance" notebook. NO download + re-upload round-trip: the
notebooklm Python client's add_drive() tells NotebookLM to read directly
from Drive, preserving the file_id link for future source refreshes.

Architecture:
    Drive (source of truth) <-[file_id]-> NotebookLM source (ref, not copy)

    - Drive Desktop is NOT required.
    - Poll via gws subprocess, ingest via Python notebooklm client.
    - Manifest keyed by Drive file ID prevents re-ingestion. mtime change
      triggers re-ingest (creates a NEW source; Silas can delete the old
      via the NotebookLM UI or via source.delete if desired).

Account integrity (non-negotiable, per Silas's explicit instruction):
    1. gws drive about get must return executive.shelton@gmail.com.
    2. NotebookLM notebook list must contain at least one 'Amerix' notebook
       (canary that the right Google account is authed).
    3. Config-file account string must match gws identity.
    Any mismatch: script exits 1, logs LOUD, does NOT ingest.

Schedule:
    Windows Task Scheduler every 5 minutes. Lock file prevents overlap.

Manual run:
    python3 C:/Users/silas/scripts/hospice-regs-watcher.py

Logs:
    C:/Users/silas/.hospice-regs/watcher-log.txt

Exit codes:
    0 - ran clean (ingested 0+ files, no errors)
    1 - account integrity failed (wrong account detected somewhere)
    2 - config or manifest corrupt / missing
    3 - lock held by another instance, exited without work
    4 - gws or notebooklm API failed in a way that blocks ingest
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from shutil import which


CONFIG_PATH = Path("C:/Users/silas/.hospice-regs/config.json")


def log(msg: str, config: dict | None = None) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    if config is None:
        log_path = Path("C:/Users/silas/.hospice-regs/watcher-log.txt")
    else:
        log_path = Path(config.get("log_path", "C:/Users/silas/.hospice-regs/watcher-log.txt"))
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"config missing: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {"_comment": "auto-created by watcher", "ingested": {}}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "ingested" not in data:
        data["ingested"] = {}
    return data


def save_manifest(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    tmp.replace(path)


def acquire_lock(lock_path: Path) -> bool:
    """Best-effort lock. Returns False if lock is held and still fresh."""
    if lock_path.exists():
        try:
            age = time.time() - lock_path.stat().st_mtime
            if age < 600:
                return False
        except Exception:
            pass
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "w", encoding="utf-8") as f:
            f.write(f"{os.getpid()}\n{datetime.now().isoformat()}\n")
        return True
    except Exception:
        return False


def release_lock(lock_path: Path) -> None:
    try:
        if lock_path.exists():
            lock_path.unlink()
    except Exception:
        pass


def run_subprocess(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return p.returncode, p.stdout or "", p.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", f"timeout after {timeout}s: {' '.join(cmd[:3])}"
    except Exception as e:
        return -1, "", f"{type(e).__name__}: {e}"


def check_gws_account(expected: str) -> tuple[bool, str]:
    gws = which("gws")
    if not gws:
        return False, "gws CLI not on PATH"
    rc, stdout, stderr = run_subprocess(
        [gws, "drive", "about", "get", "--params", '{"fields":"user"}'], timeout=30
    )
    if rc != 0:
        return False, f"gws about get failed rc={rc} stderr={stderr[:200]!r}"
    try:
        start_idx = stdout.find("{")
        data = json.loads(stdout[start_idx:])
        email = data.get("user", {}).get("emailAddress", "")
        if email.lower() == expected.lower():
            return True, f"gws authed to {email}"
        return False, f"gws authed to {email!r}, expected {expected!r}"
    except Exception as e:
        return False, f"could not parse gws about response: {e}"


async def check_notebooklm_canary(canary_substring: str) -> tuple[bool, str, object]:
    """Returns (ok, message, client-context-manager-state).

    On success, returns the AuthTokens so the caller can reuse them and
    not re-authenticate.
    """
    try:
        from notebooklm.auth import extract_cookies_from_storage, fetch_tokens, AuthTokens
        from notebooklm.client import NotebookLMClient
    except Exception as e:
        return False, f"notebooklm python package not importable: {e}", None

    storage_path = Path("C:/Users/silas/.notebooklm/storage-state.json")
    if not storage_path.exists():
        return False, f"storage state missing: {storage_path}", None

    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            storage = json.load(f)
        cookies = extract_cookies_from_storage(storage)
        csrf, sid = await fetch_tokens(cookies)
        tokens = AuthTokens(cookies=cookies, csrf_token=csrf, session_id=sid)
        async with NotebookLMClient(auth=tokens) as client:
            notebooks = await client.notebooks.list()
            titles = [nb.title for nb in notebooks]
            if not any(canary_substring.lower() in (t or "").lower() for t in titles):
                return False, (
                    f"canary {canary_substring!r} not found in notebook titles "
                    f"(saw {titles[:5]}...) - wrong account?"
                ), None
            return True, f"notebooklm canary {canary_substring!r} present in {len(notebooks)} notebooks", tokens
    except Exception as e:
        return False, f"notebooklm auth check failed: {type(e).__name__}: {e}", None


def list_drive_pdfs(folder_id: str) -> tuple[bool, list[dict], str]:
    gws = which("gws")
    if not gws:
        return False, [], "gws not on PATH"
    q = f"'{folder_id}' in parents and trashed=false and mimeType='application/pdf'"
    params = json.dumps({
        "q": q,
        "fields": "files(id,name,modifiedTime,size,mimeType)",
        "pageSize": 100,
    })
    rc, stdout, stderr = run_subprocess([gws, "drive", "files", "list", "--params", params], timeout=60)
    if rc != 0:
        return False, [], f"gws list failed rc={rc} stderr={stderr[:200]!r}"
    try:
        start_idx = stdout.find("{")
        data = json.loads(stdout[start_idx:])
        return True, data.get("files", []), ""
    except Exception as e:
        return False, [], f"could not parse gws list response: {e}"


async def add_drive_source(
    tokens,
    notebook_id: str,
    file_id: str,
    title: str,
    mime_type: str,
) -> tuple[bool, str, str]:
    """Returns (ok, message, source_id)."""
    try:
        from notebooklm.client import NotebookLMClient
    except Exception as e:
        return False, f"import failed: {e}", ""
    try:
        async with NotebookLMClient(auth=tokens) as client:
            src = await client.sources.add_drive(
                notebook_id,
                file_id=file_id,
                title=title,
                mime_type=mime_type,
            )
            return True, f"ingested source_id={src.id[:12]}... title={src.title!r}", src.id
    except Exception as e:
        return False, f"add_drive raised {type(e).__name__}: {e}", ""


async def process_folder(config: dict, manifest: dict, tokens) -> tuple[int, int, int]:
    """Returns (new_ingested, skipped, failed)."""
    folder_id = config["drive_folder_id"]
    notebook_id = config["notebook_id"]
    max_per_run = config.get("max_files_per_run", 10)
    manifest_path = Path(config["manifest_path"])

    ok, files, err = list_drive_pdfs(folder_id)
    if not ok:
        log(f"drive list failed: {err}", config)
        return 0, 0, 1
    log(f"drive folder contains {len(files)} pdf(s)", config)

    new_ingested = 0
    skipped = 0
    failed = 0

    for f in files:
        if new_ingested >= max_per_run:
            log(f"max_files_per_run={max_per_run} reached; remaining picked up next run", config)
            break
        fid = f["id"]
        fname = f.get("name", fid)
        mtime = f.get("modifiedTime", "")
        mime = f.get("mimeType", "application/pdf")
        prev = manifest["ingested"].get(fid)
        if prev and prev.get("modifiedTime") == mtime:
            skipped += 1
            continue

        log(f"ingesting: {fname} (id={fid[:12]}...) mtime={mtime}", config)
        ok, msg, source_id = await add_drive_source(tokens, notebook_id, fid, fname, mime)
        if not ok:
            log(f"  ingest FAIL: {msg}", config)
            failed += 1
            continue
        log(f"  {msg}", config)

        manifest["ingested"][fid] = {
            "name": fname,
            "modifiedTime": mtime,
            "ingestedAt": datetime.now().isoformat(timespec="seconds"),
            "bytes": f.get("size"),
            "source_id": source_id,
        }
        save_manifest(manifest_path, manifest)
        new_ingested += 1

    return new_ingested, skipped, failed


async def run() -> int:
    log("=" * 60)
    log("Hospice Regs Watcher START (v2 - add_drive, no download round-trip)")

    try:
        config = load_config()
    except Exception as e:
        log(f"FAIL: config unreadable: {e}")
        return 2

    log(
        f"account={config['account']} notebook_id={config['notebook_id'][:12]}... "
        f"folder_id={config['drive_folder_id'][:12]}...",
        config,
    )

    lock_path = Path(config["lock_path"])
    if not acquire_lock(lock_path):
        log("another watcher instance appears active (fresh lock); exiting without work", config)
        return 3

    try:
        ok, msg = check_gws_account(config["account"])
        log(f"canary gws: {msg}", config)
        if not ok:
            log("ACCOUNT INTEGRITY FAILURE - refusing to ingest", config)
            return 1

        ok, msg, tokens = await check_notebooklm_canary(config["canary_notebook_title_substring"])
        log(f"canary notebooklm: {msg}", config)
        if not ok:
            log("ACCOUNT INTEGRITY FAILURE - refusing to ingest", config)
            return 1

        try:
            manifest = load_manifest(Path(config["manifest_path"]))
        except Exception as e:
            log(f"FAIL: manifest unreadable: {e}", config)
            return 2

        new_ingested, skipped, failed = await process_folder(config, manifest, tokens)
        log(f"done: ingested={new_ingested} skipped={skipped} failed={failed}", config)

        if failed > 0 and new_ingested == 0:
            return 4
        return 0
    finally:
        release_lock(lock_path)


def main() -> int:
    return asyncio.run(run())


if __name__ == "__main__":
    rc = main()
    log(f"exit code: {rc}")
    sys.exit(rc)
