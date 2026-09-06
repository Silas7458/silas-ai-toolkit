# -*- coding: utf-8 -*-
"""
pull.py - THE LAST ROMAN canon mirror.  One-way: Google Drive -> local folder -> git.

Drive is the source of truth.  This script NEVER writes to Drive.
Everything under canon/ is generated.  Do not hand-edit anything under canon/.

What it does
  1. Walks the corpus root on Drive (executive.shelton account, via the gws CLI).
  2. For every Google Doc: exports text/plain  -> canon/<path>/<name>.txt  (BOM stripped; grep-canonical)
                          exports text/markdown -> canon/<path>/<name>.md  (base64 images stripped; headings kept)
  3. For every small non-Doc text-ish file (txt, md, docx, html, json, sh, js, pdf): downloads it as-is.
  4. Media (images, video, audio) is NOT mirrored.  images.json / media.json list what exists on Drive.
  5. Keys everything on the Drive file id.  Renames on Drive become renames here.
     Files trashed on Drive are deleted here (git keeps the last copy).
  6. Incremental: re-exports only when Drive modifiedTime changed or the local file is missing.
  7. Writes _manifest.json (id -> drive path, local path, mime, modifiedTime, live flag).
  8. With --push: git add/commit/push.  With --commit: add/commit only.

Usage
  python pull.py            incremental pull, no git
  python pull.py --push     incremental pull + commit + push   (the RUNBOOK fold-end step; bin/lr-pull.cmd)
  python pull.py --full     force re-export of everything
  python pull.py --dry-run  show what would change

Failure: raises non-zero, sends ONE Discord alert to #alerts, then stays silent until a pull succeeds.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CANON = os.path.join(REPO, "canon")
MANIFEST = os.path.join(REPO, "_manifest.json")
IMAGES_JSON = os.path.join(REPO, "images.json")
MEDIA_JSON = os.path.join(REPO, "media.json")
STATE = os.path.join(REPO, "_tools", ".pull-state.json")
LOCK = os.path.join(REPO, "_tools", ".pull.lock")
LOG = os.path.join(REPO, "_tools", "pull-log.txt")

ROOT_ID = "10WMaz4YJ-9gNKMlqyKAdpo2KYYAVDwUr"   # THE LAST ROMAN corpus root (Drive)
EXPECT_ACCOUNT = "executive.shelton@gmail.com"

DOC_MIME = "application/vnd.google-apps.document"
FOLDER_MIME = "application/vnd.google-apps.folder"
SHORTCUT_MIME = "application/vnd.google-apps.shortcut"
GOOGLE_PREFIX = "application/vnd.google-apps."
DOWNLOAD_MIMES = {
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/html": ".html",
    "application/json": ".json",
    "application/x-sh": ".sh",
    "application/javascript": ".js",
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}
IMAGE_MIMES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}
DOWNLOAD_MAX_BYTES = 15 * 1024 * 1024
IMAGE_MAX_BYTES = 40 * 1024 * 1024
# Non-live = an archive/session-log FOLDER segment, or an explicit bracketed marker in the name.
# Bare words in a title do NOT count: "CERDIC RETIRED" in the 00J ruling title and "TRANSCRIPT ARCHIVE
# INDEX" were false negatives that hid live docs from every live-only view (S#326, 4 Sept 2026).
LIVE_SKIP = re.compile(r"(^|/)_?ARCHIV|(^|/)_SESSION LOG|\(ARCHIVED|\[ARCHIVED|\(SUPERSEDED|\[SUPERSEDED|\(RETIRED|\[RETIRED|DO NOT SYNC", re.I)

SEGMENT_MAX = 90
LOCAL_PATH_MAX = 235

DISCORD_CLI = os.path.join(os.environ.get("APPDATA", ""), "npm", "node_modules", "agent-messenger",
                           "dist", "src", "platforms", "discordbot", "cli.js")
ALERTS_CHANNEL = "1475944941656998094"

GWS = shutil.which("gws")


# ----------------------------------------------------------------------------- helpers
def log(msg):
    line = "[%s] %s" % (dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), msg)
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def run(cmd, check=True, retries=3, **kw):
    """Run a subprocess with UTF-8 decoding. Retries transient gws failures."""
    last = None
    for attempt in range(1, retries + 1):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
        if r.returncode == 0 or not check:
            return r
        last = r
        log("  retry %d/%d rc=%s: %s" % (attempt, retries, r.returncode, (r.stderr or r.stdout).strip()[:300]))
        time.sleep(2 * attempt)
    raise RuntimeError("command failed: %s\n%s" % (" ".join(cmd[:4]), (last.stderr or last.stdout)[:1000]))


def gws_json(args):
    r = run([GWS] + args + ["--format", "json"])
    out = r.stdout.strip()
    # gws prints a "Using keyring backend" line on stderr, stdout is the JSON
    return json.loads(out) if out else {}


def ascii_fold(s):
    table = {
        "\u2014": "-", "\u2013": "-", "\u2212": "-", "\u00b7": "-",
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2026": "...", "\u00a7": "s", "\u2192": "to", "\u2190": "from",
    }
    for k, v in table.items():
        s = s.replace(k, v)
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if ord(ch) < 128)


def sanitize_segment(name):
    s = ascii_fold(name)
    # Windows-illegal chars AND wikilink-breaking chars (# = heading anchor, ^ = block ref, [ ] | = link syntax)
    s = re.sub(r'[<>:"|?*\\/\x00-\x1f#^\[\]]', "-", s)
    s = re.sub(r"\s+", " ", s).strip(" .")
    s = re.sub(r"-{2,}", "-", s)
    if not s:
        s = "untitled"
    if len(s) > SEGMENT_MAX:
        s = s[:SEGMENT_MAX].rstrip(" .-")
    return s


def short_id(fid):
    return re.sub(r"[^A-Za-z0-9]", "", fid)[-6:]


# ----------------------------------------------------------------------------- drive walk
def drive_list(folder_id):
    files, token = [], None
    while True:
        params = {
            "q": "'%s' in parents and trashed=false" % folder_id,
            "fields": "nextPageToken,files(id,name,mimeType,size,modifiedTime,md5Checksum,webViewLink,shortcutDetails)",
            "pageSize": 1000,
            "supportsAllDrives": True,
            "includeItemsFromAllDrives": True,
        }
        if token:
            params["pageToken"] = token
        d = gws_json(["drive", "files", "list", "--params", json.dumps(params)])
        files += d.get("files", [])
        token = d.get("nextPageToken")
        if not token:
            return files


def walk(folder_id, drive_path, local_dir, seen, out):
    """Depth-first walk. out: list of dict rows. seen: folder ids visited (loop guard)."""
    if folder_id in seen:
        return
    seen.add(folder_id)
    entries = drive_list(folder_id)
    # sort for stable output
    entries.sort(key=lambda f: (f["mimeType"] != FOLDER_MIME, f["name"].lower(), f["id"]))
    used_local = {}
    for f in entries:
        name = f["name"]
        dpath = drive_path + "/" + name
        if f["mimeType"] == SHORTCUT_MIME:
            log("  skip shortcut: %s" % dpath)
            continue
        seg = sanitize_segment(name)
        key = seg.lower()
        if key in used_local:
            seg = seg + "__" + short_id(f["id"])
            key = seg.lower()
        used_local[key] = f["id"]
        if f["mimeType"] == FOLDER_MIME:
            walk(f["id"], dpath, local_dir + "/" + seg, seen, out)
        else:
            out.append({
                "id": f["id"],
                "name": name,
                "drive_path": dpath,
                "local_dir": local_dir,
                "local_base": seg,
                "mime": f["mimeType"],
                "size": int(f.get("size", 0) or 0),
                "modifiedTime": f.get("modifiedTime", ""),
                "md5": f.get("md5Checksum", ""),
                # Drive randomly adds/removes ouid=... on webViewLink; keep the stable part only
                "link": (f.get("webViewLink", "") or "").split("?")[0],
                "live": not bool(LIVE_SKIP.search(dpath)),
            })


# ----------------------------------------------------------------------------- export
def strip_bom(b):
    return b[3:] if b.startswith(b"\xef\xbb\xbf") else b


DATA_URI = re.compile(rb"<data:image/[a-zA-Z0-9.+-]+;base64,[^>]*>")


def strip_data_uris(b):
    return DATA_URI.sub(b"<image-stripped-see-drive>", b)


def local_paths(row):
    """Return list of (mimeType_or_None, local relative path) outputs for a row."""
    base = row["local_base"]
    # ensure the full local path stays under the Windows limit
    prefix = os.path.join(CANON, row["local_dir"].strip("/").replace("/", os.sep))
    budget = LOCAL_PATH_MAX - len(prefix) - 1 - 5   # room for ".docx"
    if budget < 20:
        budget = 20
    if len(base) > budget:
        base = base[:budget - 7].rstrip(" .-") + "__" + short_id(row["id"])
    if row["mime"] == DOC_MIME:
        return [("text/plain", base + ".txt"), ("text/markdown", base + ".md")]
    ext = DOWNLOAD_MIMES.get(row["mime"]) or IMAGE_MIMES.get(row["mime"])
    if ext is None:
        return []
    root, cur = os.path.splitext(base)
    if cur.lower() != ext:
        base = base + ext
    return [(None, base)]


def export_doc(fid, mime, dest_abs):
    tmp = dest_abs + ".part"
    run([GWS, "drive", "files", "export", "--params",
         json.dumps({"fileId": fid, "mimeType": mime}), "--output", tmp])
    if not os.path.exists(tmp):
        raise RuntimeError("export produced no file for %s (%s)" % (fid, mime))
    with open(tmp, "rb") as f:
        b = f.read()
    if mime == "text/plain":
        b = strip_bom(b)
    elif mime == "text/markdown":
        b = strip_data_uris(b)
    # normalise line endings so git diffs are clean
    b = b.replace(b"\r\n", b"\n")
    with open(dest_abs, "wb") as f:
        f.write(b)
    os.remove(tmp)


def download_file(fid, dest_abs):
    tmp = dest_abs + ".part"
    # files.download is the async API and fails with backendError on plain files; files.get alt=media works
    r = run([GWS, "drive", "files", "get", "--params", json.dumps({"fileId": fid, "alt": "media"}), "--output", tmp])
    if not os.path.exists(tmp):
        # gws writes text-type responses (txt, md, json, html, sh) to stdout, not --output
        body = r.stdout
        if not body or not body.strip():
            raise RuntimeError("download produced no file and no stdout for %s" % fid)
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(body if body.endswith("\n") else body + "\n")
    os.replace(tmp, dest_abs)


# ----------------------------------------------------------------------------- index (Obsidian entry point)
INDEX = os.path.join(REPO, "INDEX.md")


def write_index(manifest):
    """Mechanical index: every mirrored .md as a wikilink, grouped by Drive folder, live first.
    Decides nothing about importance. Exists so Obsidian's graph/backlinks/search have one root."""
    groups = {}
    for row in manifest:
        mds = [lf for lf in row.get("local_files", []) if lf.lower().endswith(".md")]
        if not mds:
            continue
        folder = "/".join(row["drive_path"].split("/")[1:-1]) or "(corpus root)"
        groups.setdefault((not row["live"], folder), []).append((row["name"], mds[0], row["live"], row["link"]))
    lines = [
        "# THE LAST ROMAN - CANON INDEX (generated)",
        "",
        "Generated by `_tools/pull.py` on every pull. Do not edit. Drive is the source of truth; this mirror is one-way.",
        "Every entry is a Google Doc under the corpus root. `.md` = headings kept, images stripped, punctuation Google-escaped.",
        "`.txt` beside each `.md` is the faithful text for grep. Archive / superseded / session-log entries are listed last.",
        "",
    ]
    for (archived, folder) in sorted(groups):
        lines.append("## %s%s" % (folder, "  (not live)" if archived else ""))
        lines.append("")
        for name, md, live, link in sorted(groups[(archived, folder)], key=lambda x: x[0].lower()):
            target = md[:-3].replace("\\", "/")
            lines.append("- [[canon/%s|%s]]%s" % (target, name.replace("|", "-"),
                                                 ("  ([Drive](%s))" % link) if link else ""))
        lines.append("")
    # vault-readable twins (html/docx/doc/pdf -> md) and image galleries, from _derived.json
    try:
        st = json.load(open(os.path.join(REPO, "_derived.json"), encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    twins = sorted(o for k, v in st.items() if k != "_galleries" for o in v.get("outputs", []) if o.endswith(".md"))
    gals = sorted(st.get("_galleries", {}).get("outputs", []))
    if twins:
        lines.append("## Vault-readable twins (generated from html / docx / doc / pdf in the corpus)")
        lines.append("")
        for o in twins:
            lines.append("- [[canon/%s|%s]]" % (o[:-3], os.path.basename(o)[:-3]))
        lines.append("")
    if gals:
        lines.append("## Image galleries (generated; see IMAGES.md)")
        lines.append("")
        for o in gals:
            lines.append("- [[canon/%s|%s]]" % (o[:-3], os.path.dirname(o) or "(corpus root)"))
        lines.append("")
    with open(INDEX, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


# ----------------------------------------------------------------------------- alerting
def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except (OSError, ValueError):
        return {"alerted": False, "last_success": None, "last_failure": None}


def save_state(s):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)


def alert(msg):
    if not os.path.exists(DISCORD_CLI):
        log("  (no discord cli; alert not sent)")
        return
    try:
        subprocess.run(["node", DISCORD_CLI, "message", "send", ALERTS_CHANNEL,
                        "**[Last Roman canon mirror]** " + msg[:1500]],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    except Exception as e:  # noqa
        log("  alert send failed: %s" % e)


# ----------------------------------------------------------------------------- git
def git(args, check=True):
    return run(["git"] + args, check=check, retries=1, cwd=REPO)


def git_commit_push(summary, push):
    git(["add", "-A"])
    st = git(["status", "--porcelain"]).stdout.strip()
    if not st:
        log("git: nothing to commit")
        return False
    msg = "pull %s - %s" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M"), summary)
    git(["commit", "-q", "-m", msg])
    log("git: committed: %s" % msg)
    if push:
        r = git(["push", "-q"], check=False)
        if r.returncode != 0:
            raise RuntimeError("git push failed:\n" + (r.stderr or r.stdout))
        log("git: pushed")
    return True


# ----------------------------------------------------------------------------- lint
def run_lint():
    """Canon lint after every real pull (S#328 - Proctor parity: canon_pull / canon_fold call this script directly,
    not lr-pull.cmd, so the lint lives here). Advisory: prints the report, never changes the exit code."""
    lint = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lint.py")
    if not os.path.exists(lint):
        return
    try:
        r = subprocess.run([sys.executable, lint], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1"), timeout=300)
        out = (r.stdout or "").rstrip()
        if out:
            print(out)
        total = next((l for l in out.split("\n") if l.startswith("TOTAL:") or l.startswith("CLEAN")), "")
        log("lint: " + (total or "no TOTAL line (lint exit %d)" % r.returncode))
    except Exception as e:  # noqa
        log("lint FAILED (advisory): %s" % str(e)[:200])


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="re-export everything")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--push", action="store_true", help="commit and push")
    a = ap.parse_args()

    if GWS is None:
        raise SystemExit("gws CLI not found on PATH")
    if os.path.exists(LOCK):
        age = time.time() - os.path.getmtime(LOCK)
        if age < 3600:
            raise SystemExit("another pull is running (lock %ds old): %s" % (age, LOCK))
        log("stale lock (%ds) removed" % age)
        os.remove(LOCK)
    open(LOCK, "w").write(str(os.getpid()))
    state = load_state()
    t0 = time.time()
    try:
        log("pull START full=%s dry=%s" % (a.full, a.dry_run))
        who = gws_json(["drive", "about", "get", "--params", json.dumps({"fields": "user(emailAddress)"})])
        email = (who.get("user") or {}).get("emailAddress", "")
        if email != EXPECT_ACCOUNT:
            raise RuntimeError("gws is signed in as %r, expected %s" % (email, EXPECT_ACCOUNT))
        log("account OK: %s" % email)

        rows = []
        walk(ROOT_ID, "", "", set(), rows)
        log("drive walk: %d files" % len(rows))

        old = {}
        if os.path.exists(MANIFEST):
            try:
                old = {r["id"]: r for r in json.load(open(MANIFEST, encoding="utf-8"))["files"]}
            except (OSError, ValueError, KeyError):
                old = {}

        os.makedirs(CANON, exist_ok=True)
        new_manifest, n_new, n_upd, n_same, n_skip = [], 0, 0, 0, 0
        images, media, failures = [], [], []
        expected_local = set()

        for row in rows:
            outs = local_paths(row)
            is_image = row["mime"] in IMAGE_MIMES
            if row["mime"].startswith(("image/", "video/", "audio/")):
                (images if row["mime"].startswith("image/") else media).append(
                    {k: row[k] for k in ("id", "name", "drive_path", "mime", "size", "modifiedTime", "link")})
                if not is_image:
                    n_skip += 1
                    continue
            if not outs:
                log("  skip unknown mime %s: %s" % (row["mime"], row["drive_path"]))
                n_skip += 1
                continue
            if is_image and row["size"] > IMAGE_MAX_BYTES:
                log("  skip image too large (%d bytes): %s" % (row["size"], row["drive_path"]))
                n_skip += 1
                continue
            if not is_image and row["mime"] != DOC_MIME and row["size"] > DOWNLOAD_MAX_BYTES:
                log("  skip too large (%d bytes): %s" % (row["size"], row["drive_path"]))
                n_skip += 1
                continue
            rel_dir = row["local_dir"].strip("/")
            row["local_files"] = [(rel_dir + "/" + p).strip("/") for _, p in outs]
            for lf in row["local_files"]:
                expected_local.add(lf)
            prev = old.get(row["id"])
            need = a.full or prev is None or prev.get("modifiedTime") != row["modifiedTime"] \
                or prev.get("local_files") != row["local_files"] \
                or any(not os.path.exists(os.path.join(CANON, lf)) for lf in row["local_files"])
            # rename/move: old local files that differ from new ones get removed below (orphan sweep)
            if need:
                ok = True
                if not a.dry_run:
                    try:
                        for (mime, p), lf in zip(outs, row["local_files"]):
                            dest = os.path.join(CANON, lf)
                            os.makedirs(os.path.dirname(dest), exist_ok=True)
                            if mime:
                                export_doc(row["id"], mime, dest)
                            else:
                                download_file(row["id"], dest)
                    except Exception as e:  # noqa
                        ok = False
                        failures.append("%s: %s" % (row["drive_path"], str(e)[:200]))
                        log("  FAIL %s: %s" % (row["drive_path"][:90], str(e)[:200]))
                if ok:
                    if prev is None:
                        n_new += 1
                    else:
                        n_upd += 1
                    log("  %s %s" % ("NEW" if prev is None else "UPD", row["drive_path"][:110]))
                else:
                    # leave it out of the manifest so the next pull retries it
                    for lf in row["local_files"]:
                        expected_local.discard(lf)
                    continue
            else:
                n_same += 1
            new_manifest.append({k: row[k] for k in (
                "id", "name", "drive_path", "mime", "size", "modifiedTime", "md5", "link", "live", "local_files")})

        # orphan sweep: anything under canon/ not expected -> delete (Drive trash/rename/move)
        # ...except the vault-readable twins and galleries that derive.py generates (listed in _derived.json)
        try:
            sys.path.insert(0, HERE)
            import derive as derive_mod
            spared = derive_mod.derived_outputs()
        except Exception as e:  # noqa
            derive_mod, spared = None, set()
            log("  derive module unavailable: %s" % str(e)[:200])
        n_del = 0
        for dirpath, dirnames, filenames in os.walk(CANON, topdown=False):
            for fn in filenames:
                abs_p = os.path.join(dirpath, fn)
                rel = os.path.relpath(abs_p, CANON).replace(os.sep, "/")
                if rel in spared or fn == "_GALLERY.md" or fn.endswith(".part"):
                    continue
                if rel not in expected_local:
                    n_del += 1
                    log("  DEL %s" % rel)
                    if not a.dry_run:
                        os.remove(abs_p)
            if not a.dry_run and dirpath != CANON and not os.listdir(dirpath):
                os.rmdir(dirpath)

        if not a.dry_run:
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            # no timestamps in tracked files: a pull with no Drive changes must produce no diff
            with open(MANIFEST, "w", encoding="utf-8") as f:
                json.dump({"root_id": ROOT_ID, "account": email,
                           "files": new_manifest}, f, indent=1, ensure_ascii=False)
            with open(IMAGES_JSON, "w", encoding="utf-8") as f:
                json.dump({"count": len(images), "images": images}, f, indent=1, ensure_ascii=False)
            with open(MEDIA_JSON, "w", encoding="utf-8") as f:
                json.dump({"count": len(media), "media": media}, f, indent=1, ensure_ascii=False)
            state["last_pull_utc"] = stamp
            if derive_mod is not None:
                try:
                    derive_mod.derive(log)
                except Exception as e:  # noqa
                    log("  derive FAILED: %s" % str(e)[:300])
            write_index(new_manifest)

        summary = "%d new, %d updated, %d unchanged, %d removed, %d media/other skipped, %d FAILED" % (
            n_new, n_upd, n_same, n_del, n_skip, len(failures))
        log("pull DONE in %ds: %s" % (time.time() - t0, summary))

        if not a.dry_run and (a.commit or a.push):
            git_commit_push(summary, push=a.push)

        if not a.dry_run:
            run_lint()

        if failures:
            raise RuntimeError("%d file(s) failed (manifest written; next pull retries them):\n  " % len(failures)
                               + "\n  ".join(failures[:10]))

        if state.get("alerted"):
            alert("recovered: pull succeeded (%s)" % summary)
        state.update({"alerted": False, "last_success": dt.datetime.now().isoformat(), "last_summary": summary})
        save_state(state)
        return 0
    except Exception as e:  # noqa
        msg = "%s: %s" % (type(e).__name__, str(e)[:600])
        log("pull FAILED: " + msg)
        state["last_failure"] = dt.datetime.now().isoformat()
        state["last_failure_message"] = msg
        if not state.get("alerted"):
            alert("pull FAILED - " + msg + "  (no more alerts until a pull succeeds)")
            state["alerted"] = True
        save_state(state)
        return 1
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
