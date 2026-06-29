#!/usr/bin/env python3
"""
NotebookLM cookie keepalive + health check - WEEKLY scheduled task.

Why this exists:
    notebooklm-py saves Google cookies to ~/.notebooklm/profiles/default/storage_state.json
    when you first log in. Google's server-side session invalidation kicks
    in after ~12 days of zero activity against those cookies. The purpose
    of this script is to (a) exercise the cookies so Google's activity
    clock resets, and (b) loud-fail immediately if they no longer auth,
    so we catch expiry BEFORE it blocks real work.

What this does (redesigned 2026-04-20 S205):
    1. Preflight: check long-lived cookies (SID/LSID) haven't expired on disk.
    2. Subprocess `npx notebooklm ls` - the same code path `/recall` uses.
       This both (a) keeps cookies alive via real API activity and
       (b) is an authoritative auth check.
    3. Parse stderr for known auth-failure signatures. The CLI exits 0
       even on AuthError (upstream bug), so stderr parsing is the truth.
    4. Never writes to storage-state.json. If cookies expire, the fix is
       `npx notebooklm login` - no amount of headless navigation fixes it.

What this does NOT do (anymore):
    - Launch a headless Chromium persistent context. The previous design
      "refreshed" cookies by visiting Google pages and saving whatever
      the browser context produced. In practice this OVERWROTE the good
      saved state with a degraded cookie set (5 cookies vs 45). The
      save-and-verify was the wrong primitive. This script no longer
      overwrites disk state.

Schedule:
    Weekly via Windows Task Scheduler. Sunday 9am is a low-contention slot.

Manual run:
    python3 C:/Users/silas/scripts/refresh-notebooklm-cookies.py

Logs:
    Each run appends a timestamped block to ~/.notebooklm/refresh-log.txt.

Exit codes:
    0 - keepalive call succeeded, auth is healthy
    1 - keepalive call reached the CLI but auth failed (AuthError / HTTP 302)
        -> run `npx notebooklm login` to re-auth
    2 - long-lived cookies (SID/LSID) already expired on disk
        -> run `npx notebooklm login` to re-auth
    3 - environmental failure (subprocess didn't run, npx missing, etc.)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


NLM_DIR = Path.home() / ".notebooklm"
STORAGE_PATH = NLM_DIR / "storage-state.json"
LOG_FILE = NLM_DIR / "refresh-log.txt"

CRITICAL_LONG_LIVED = {"SID", "__Secure-1PSID", "__Secure-3PSID", "LSID"}

AUTH_ERROR_PATTERNS = (
    "AuthError",
    "Failed to fetch tokens",
    "HTTP 302",
    "HTTP 401",
    "HTTP 403",
    "invalid_grant",
    "login again",
    "re-authenticate",
)

KEEPALIVE_TIMEOUT_SEC = 90


def log(msg: str) -> None:
    """Print AND append to log file."""
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_state(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def preflight(state: dict) -> tuple[bool, str]:
    now = time.time()
    cookies = {c.get("name"): c for c in state.get("cookies", [])}
    for name in CRITICAL_LONG_LIVED:
        c = cookies.get(name)
        if not c:
            return False, f"critical cookie {name!r} missing"
        exp = c.get("expires", -1)
        if exp > 0 and exp < now:
            return False, f"critical cookie {name!r} expired {(now - exp) / 86400:.1f} days ago"
    return True, "long-lived cookies present on disk"


def find_npx() -> str | None:
    """Resolve npx executable. On Windows it's npx.cmd; on POSIX it's npx."""
    candidate = "npx.cmd" if os.name == "nt" else "npx"
    from shutil import which
    return which(candidate) or which("npx")


def keepalive_call() -> tuple[int, str]:
    """Run `npx notebooklm ls` as both keepalive and auth verification.

    Returns (result_code, message):
        result_code: 0=auth OK, 1=auth failed, 3=environmental
    """
    npx = find_npx()
    if not npx:
        return 3, "npx not found on PATH - cannot invoke notebooklm CLI"

    try:
        proc = subprocess.run(
            [npx, "--yes", "notebooklm", "ls"],
            capture_output=True,
            text=True,
            timeout=KEEPALIVE_TIMEOUT_SEC,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 3, f"notebooklm ls timed out after {KEEPALIVE_TIMEOUT_SEC}s"
    except Exception as e:
        return 3, f"subprocess failed to spawn: {type(e).__name__}: {e}"

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    combined = stdout + "\n" + stderr

    for pattern in AUTH_ERROR_PATTERNS:
        if pattern in combined:
            snippet = combined.strip().splitlines()[0] if combined.strip() else ""
            return 1, f"auth failed ({pattern!r}): {snippet[:200]}"

    stdout_lines = [ln for ln in stdout.splitlines() if ln.strip()]
    if not stdout_lines:
        return 1, f"empty stdout and no auth error detected - ambiguous. stderr[:200]={stderr[:200]!r}"

    return 0, f"auth OK - ls returned {len(stdout_lines)} line(s) (first: {stdout_lines[0][:80]!r})"


def main() -> int:
    log("=" * 60)
    log("NotebookLM keepalive START (v2 - subprocess-based, no Playwright)")

    if not STORAGE_PATH.exists():
        log(f"FAIL: no storage state at {STORAGE_PATH} - run `npx notebooklm login`")
        return 1

    try:
        state = load_state(STORAGE_PATH)
    except Exception as e:
        log(f"FAIL: could not read storage state: {e}")
        return 1

    ok, msg = preflight(state)
    log(f"preflight: {msg}")
    if not ok:
        log("manual re-login required - run: npx notebooklm login")
        return 2

    rc, keepalive_msg = keepalive_call()
    log(f"keepalive: {keepalive_msg}")

    if rc == 0:
        log("NotebookLM keepalive OK - cookies authenticate")
        return 0
    if rc == 1:
        log("NotebookLM keepalive FAILED - auth dead. Run: npx notebooklm login")
        return 1
    log("NotebookLM keepalive ENVIRONMENTAL FAILURE - check npx / network")
    return 3


if __name__ == "__main__":
    rc = main()
    log(f"exit code: {rc}")
    sys.exit(rc)
