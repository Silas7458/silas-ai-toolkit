#!/usr/bin/env node
// obsidian-canon MCP server - THE LAST ROMAN canon mirror for Claude Desktop (Proctor).
//
// Gives Proctor the same power Brother has from the terminal, entirely on the BACK END:
// nothing here opens, focuses, restarts or launches the Obsidian window.
//
// CORE (pure node over the mirror on disk, works even when Obsidian is closed):
//   canon_info      vault facts, freshness, tool health
//   canon_list      list files (folder / ext / name filter, live-only by default)
//   canon_read      read a doc by name, path or Drive id; whole or paged; never silent-truncates
//   canon_grep      ripgrep-equivalent over the canonical text (.txt) with context lines
//   canon_topic     "explain X" starter: every doc ranked by relevance + matching lines + what to read in full
//   canon_lookup    Drive id <-> local path <-> Drive name (for gdrive-ops edits afterwards)
//   canon_outline   headings of a doc
//   canon_graph     backlinks / links / orphans / deadends / unresolved (wikilinks parsed from .md)
//   canon_history   git log of the mirror (what changed, when), optional per-file
//   canon_diff      git diff of a file between two pulls
//   canon_images    search the 215 image captions + Drive links
//   canon_pull      lr-pull: refresh the mirror from Drive (the ONLY write; commit + push, one-way)
//
// OPTIONAL (only when Obsidian is already running; strict read-only, no-UI whitelist):
//   obsidian_search search / search:context through Obsidian's own engine (.md only)
//   obsidian_cli    any whitelisted read-only CLI command (backlinks, links, outline, tags, ...)
//
// Rules baked in: Drive is the source of truth; the mirror is generated; no hand edits are possible
// through this server. .txt is the grep-canonical text of a Google Doc; .md is the same Doc with
// headings kept and punctuation escaped by Google (never grep exact strings in .md).
//
// v1.0.0 (S#326 2026-09-04)

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { execFile } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const VERSION = "1.0.0";

const VAULT = path.resolve(
  process.env.OBSIDIAN_CANON_VAULT || "C:/Users/silas/Documents/last-roman/canon-mirror"
);
const OBSIDIAN_EXE =
  process.env.OBSIDIAN_CLI_EXE ||
  path.join(process.env.LOCALAPPDATA || "", "Programs", "Obsidian", "Obsidian.com");
const PYTHON_EXE = process.env.OBSIDIAN_CANON_PYTHON || "C:/Python313/python.exe";
const GIT_EXE = fs.existsSync("C:/Program Files/Git/cmd/git.exe") ? "C:/Program Files/Git/cmd/git.exe" : "git";
const NPM_BIN = path.join(process.env.APPDATA || "", "npm");

const CANON_DIR = "canon"; // manifest local_files are relative to this folder
const SKIP_DIRS = new Set([".git", ".obsidian", "node_modules", "_tools"]);
const TEXT_EXT = new Set([".txt", ".md", ".html", ".json", ".sh", ".js", ".csv", ".base"]);
const IMAGE_EXT = new Set([".png", ".jpg", ".jpeg", ".webp", ".gif"]);
// Belt-and-braces on top of the manifest's own live flag (handoff S#325 skip list).
const NON_LIVE_RE = /(^|\/)(_ARCHIVE[^/]*|_SESSION LOG[^/]*|20 - HISTORICAL[^/]*|NOTES FROM BROTHER[^/]*)(\/|$)/i;

const BIG_BUFFER = 64 * 1024 * 1024;

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

function ok(data) {
  return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
}
function fail(e) {
  return { isError: true, content: [{ type: "text", text: "ERROR: " + String((e && e.message) || e) }] };
}
function toPosix(p) {
  return p.replace(/\\/g, "/");
}
function rel(abs) {
  return toPosix(path.relative(VAULT, abs));
}
function safeAbs(relPath) {
  const abs = path.resolve(VAULT, relPath);
  const r = path.relative(VAULT, abs);
  if (r.startsWith("..") || path.isAbsolute(r)) throw new Error("path escapes the vault: " + relPath);
  return abs;
}
function readText(abs) {
  let s = fs.readFileSync(abs, "utf8");
  if (s.charCodeAt(0) === 0xfeff) s = s.slice(1);
  return s;
}
function esc(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
function fold(s) {
  // ASCII-fold + lowercase for name matching (mirror names are already ASCII-folded).
  return String(s)
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[\u2013\u2014]/g, "-")
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201c\u201d]/g, '"')
    .toLowerCase();
}
function run(exe, args, opts) {
  const o = opts || {};
  return new Promise((resolve, reject) => {
    execFile(
      exe,
      args,
      {
        cwd: o.cwd || VAULT,
        timeout: o.timeout || 60000,
        maxBuffer: BIG_BUFFER,
        windowsHide: true,
        env: Object.assign({}, process.env, o.env || {}),
      },
      (err, stdout, stderr) => {
        if (err) reject(new Error((o.label || exe) + " failed: " + (String(stderr).trim() || err.message)));
        else resolve({ stdout: String(stdout), stderr: String(stderr) });
      }
    );
  });
}

// ---------------------------------------------------------------------------
// vault index (cached; invalidated when _manifest.json or the file walk changes)
// ---------------------------------------------------------------------------

let CACHE = null;
let CACHE_AT = 0;

function loadJson(name, fallback) {
  try {
    return JSON.parse(readText(path.join(VAULT, name)));
  } catch (e) {
    return fallback;
  }
}

function walk(dir, out) {
  let ents;
  try {
    ents = fs.readdirSync(dir, { withFileTypes: true });
  } catch (e) {
    return;
  }
  for (const d of ents) {
    if (d.isDirectory()) {
      if (SKIP_DIRS.has(d.name)) continue;
      walk(path.join(dir, d.name), out);
    } else if (d.isFile()) {
      out.push(rel(path.join(dir, d.name)));
    }
  }
}

function buildIndex() {
  const manifest = loadJson("_manifest.json", { files: [] });
  const byLocal = new Map();
  const byId = new Map();
  // manifest local_files are relative to canon/, the vault index is relative to the vault root
  for (const e of manifest.files || []) {
    byId.set(e.id, e);
    for (const lf of e.local_files || []) byLocal.set(CANON_DIR + "/" + toPosix(lf), e);
  }
  const files = [];
  walk(VAULT, files);
  files.sort();
  const set = new Set(files);
  const records = files.map((p) => {
    const ext = path.extname(p).toLowerCase();
    const m = byLocal.get(p) || null;
    const base = path.basename(p, ext);
    const twinTxt = ext === ".md" && set.has(p.slice(0, -3) + ".txt");
    // derived twin: html/docx/doc/pdf sources get "<source>.md" (derive.py); a Google Doc .txt gets "<name>.md"
    const mdTwin = ext === ".txt" ? (set.has(p.slice(0, -4) + ".md") ? p.slice(0, -4) + ".md" : null) : ext !== ".md" && set.has(p + ".md") ? p + ".md" : null;
    let live = true;
    if (m && m.live === false) live = false;
    if (NON_LIVE_RE.test(p)) live = false;
    return {
      path: p,
      ext,
      base,
      folder: toPosix(path.dirname(p)),
      is_text: TEXT_EXT.has(ext),
      is_image: IMAGE_EXT.has(ext),
      has_txt_twin: twinTxt,
      md_twin: mdTwin,
      generated: !m,
      live,
      drive_id: m ? m.id : null,
      drive_name: m ? m.name : null,
      drive_path: m ? m.drive_path : null,
      mime: m ? m.mime : null,
      modified: m ? m.modifiedTime : null,
      link: m ? m.link : null,
    };
  });
  return {
    manifest,
    byId,
    records,
    byPath: new Map(records.map((r) => [r.path, r])),
    byPathFold: new Map(records.map((r) => [fold(r.path), r])),
    images: loadJson("_image_descriptions.json", {}),
    imagesIndex: loadJson("images.json", null),
    derived: loadJson("_derived.json", {}),
  };
}

function index() {
  const now = Date.now();
  if (CACHE && now - CACHE_AT < 5000) return CACHE;
  CACHE = buildIndex();
  CACHE_AT = now;
  return CACHE;
}

// "canonical" scope: one text per Doc (the .txt), .md only when it has no .txt twin, plus other text types.
function canonicalText(r) {
  if (!r.is_text) return false;
  if (r.ext === ".json" || r.ext === ".base") return false; // data files (manifest, images.json, atlas_data.json) are not show prose; scope=all includes them
  if (r.ext === ".md" && r.has_txt_twin) return false; // the .txt is the canonical text of a Google Doc
  if (r.ext !== ".txt" && r.ext !== ".md" && r.md_twin) return false; // html/docx/pdf source: read its derived .md twin instead
  return true;
}

// Resolve a user reference (local path, Drive id, Drive name, basename, wikilink-ish name, substring).
function resolveRef(ref, opts) {
  const o = opts || {};
  const ix = index();
  const q = String(ref || "").trim();
  if (!q) throw new Error("empty file reference");
  const wantExt = o.ext || null; // ".txt" | ".md" | null

  const pick = (list) => {
    if (wantExt) {
      const f = list.filter((r) => r.ext === wantExt);
      if (f.length) return f;
    }
    return list;
  };

  // 1. exact local path (with or without extension)
  const qp = toPosix(q).replace(/^\.?\//, "");
  const direct = ix.byPath.get(qp) || ix.byPathFold.get(fold(qp));
  if (direct) return [direct];
  const noExt = [];
  for (const r of ix.records) {
    if (fold(r.folder + "/" + r.base) === fold(qp) || fold(r.path.replace(/\.[^.]+$/, "")) === fold(qp)) noExt.push(r);
  }
  if (noExt.length) return pick(noExt);

  // 2. Drive id
  const byId = ix.byId.get(q);
  if (byId) {
    const locals = (byId.local_files || []).map((lf) => ix.byPath.get(CANON_DIR + "/" + toPosix(lf))).filter(Boolean);
    if (locals.length) return pick(locals);
  }

  // 3. exact basename / Drive name
  const fq = fold(q).replace(/\.(txt|md)$/, "");
  const exact = ix.records.filter((r) => fold(r.base) === fq || (r.drive_name && fold(r.drive_name) === fq));
  if (exact.length) return pick(exact);

  // 4. substring on basename / drive name / drive path (live text first)
  const sub = ix.records.filter(
    (r) =>
      fold(r.base).includes(fq) ||
      (r.drive_name && fold(r.drive_name).includes(fq)) ||
      (r.drive_path && fold(r.drive_path).includes(fq))
  );
  return pick(sub);
}

function describe(r) {
  return {
    path: r.path,
    live: r.live,
    drive_id: r.drive_id,
    drive_name: r.drive_name,
    drive_path: r.drive_path,
    modified: r.modified,
    link: r.link,
  };
}

function chooseOne(ref, opts) {
  const list = resolveRef(ref, opts);
  if (!list.length) throw new Error("no file matches '" + ref + "'. Try canon_list with query=, or canon_lookup.");
  // Prefer live + canonical text if several
  const texts = list.filter((r) => r.is_text);
  const pool = texts.length ? texts : list;
  const live = pool.filter((r) => r.live);
  const cand = live.length ? live : pool;
  // one Doc -> its .txt and .md both match; prefer .txt unless caller asked for md
  const ext = (opts && opts.ext) || null;
  const uniqDocs = new Map();
  for (const r of cand) uniqDocs.set(r.path.replace(/\.(txt|md)$/, ""), true);
  if (uniqDocs.size > 1) {
    const err = new Error(
      "ambiguous reference '" + ref + "' (" + uniqDocs.size + " docs). Candidates:\n" +
        cand.slice(0, 25).map((r) => "  " + r.path + (r.live ? "" : "  [not live]")).join("\n")
    );
    throw err;
  }
  const want = ext || ".txt";
  let chosen = cand.find((r) => r.ext === want) || cand.find((r) => r.ext === ".txt") || cand.find((r) => r.ext === ".md") || cand[0];
  // an exact .txt path with format=md (or vice versa): swap to the twin when it exists
  if (want === ".md" && chosen.ext === ".txt" && chosen.md_twin && index().byPath.has(chosen.md_twin)) chosen = index().byPath.get(chosen.md_twin);
  else if (want === ".txt" && chosen.ext === ".md" && chosen.has_txt_twin) chosen = index().byPath.get(chosen.path.slice(0, -3) + ".txt") || chosen;
  // html/docx/doc/pdf source: hand back the readable derived .md twin (unless the raw source was asked for by exact path)
  if (chosen.md_twin && chosen.ext !== ".txt" && (want === ".md" || fold(ref) !== fold(chosen.path))) {
    const twin = index().byPath.get(chosen.md_twin);
    if (twin) return twin;
  }
  return chosen;
}

// ---------------------------------------------------------------------------
// text search (pure node; the ripgrep equivalent of Brother's native arm)
// ---------------------------------------------------------------------------

function makeRegex(pattern, o) {
  let src = o.regex ? pattern : esc(pattern);
  if (o.whole_word) src = "\\b(?:" + src + ")\\b";
  return new RegExp(src, o.case_sensitive ? "g" : "gi");
}

function scopeFiles(o) {
  const ix = index();
  let list = ix.records.filter((r) => r.is_text);
  const scope = o.scope || "canonical";
  if (scope === "canonical") list = list.filter(canonicalText);
  else if (scope === "txt") list = list.filter((r) => r.ext === ".txt");
  else if (scope === "md") list = list.filter((r) => r.ext === ".md");
  if (o.live_only !== false) list = list.filter((r) => r.live);
  if (o.folder) {
    const f = fold(toPosix(o.folder).replace(/\/$/, ""));
    list = list.filter((r) => fold(r.path).startsWith(f + "/") || fold(r.folder).includes(f));
  }
  if (o.ext) {
    const e = ("." + String(o.ext).replace(/^\./, "")).toLowerCase();
    list = list.filter((r) => r.ext === e);
  }
  return list;
}

function grep(pattern, o) {
  const re = makeRegex(pattern, o);
  const files = scopeFiles(o);
  const ctx = o.context == null ? 1 : Math.max(0, Math.min(10, o.context));
  const maxMatches = o.max_matches || 200;
  const maxFiles = o.max_files || 60;
  const out = [];
  let total = 0;
  let filesHit = 0;
  let truncated = false;
  for (const r of files) {
    let text;
    try {
      text = readText(safeAbs(r.path));
    } catch (e) {
      continue;
    }
    if (!re.test(text)) {
      re.lastIndex = 0;
      continue;
    }
    re.lastIndex = 0;
    const lines = text.split(/\r?\n/);
    const hits = [];
    for (let i = 0; i < lines.length; i++) {
      re.lastIndex = 0;
      if (re.test(lines[i])) {
        hits.push({
          line: i + 1,
          text: lines[i],
          before: ctx ? lines.slice(Math.max(0, i - ctx), i) : undefined,
          after: ctx ? lines.slice(i + 1, i + 1 + ctx) : undefined,
        });
      }
    }
    re.lastIndex = 0;
    total += hits.length;
    filesHit++;
    if (out.length < maxFiles) {
      const keep = hits.slice(0, Math.max(1, maxMatches - out.reduce((n, f) => n + f.matches.length, 0)));
      out.push({ file: r.path, live: r.live, match_count: hits.length, matches: keep });
      if (keep.length < hits.length) truncated = true;
    } else truncated = true;
  }
  out.sort((a, b) => b.match_count - a.match_count || a.file.localeCompare(b.file));
  return {
    pattern,
    regex: !!o.regex,
    case_sensitive: !!o.case_sensitive,
    scope: o.scope || "canonical",
    live_only: o.live_only !== false,
    files_searched: files.length,
    files_matched: filesHit,
    total_matches: total,
    truncated,
    results: out,
  };
}

// ---------------------------------------------------------------------------
// wikilink graph (pure node; Obsidian resolution rules, no app needed)
// ---------------------------------------------------------------------------

const WIKI_RE = /\[\[([^\]|#^]+)(?:#[^\]|]*)?(?:\^[^\]|]*)?(?:\|[^\]]*)?\]\]/g;
const MDLINK_RE = /\]\(([^)\s]+\.(?:md|txt|png|jpg|jpeg|webp|pdf|html))\)/gi;

function resolveLinkTarget(target, ix) {
  let t = toPosix(String(target).trim()).replace(/^\.?\//, "");
  try {
    t = decodeURIComponent(t);
  } catch (e) {}
  if (ix.byPath.has(t)) return ix.byPath.get(t);
  const f = fold(t);
  if (ix.byPathFold.has(f)) return ix.byPathFold.get(f);
  if (!/\.[a-z0-9]{1,5}$/i.test(t)) {
    if (ix.byPathFold.has(f + ".md")) return ix.byPathFold.get(f + ".md");
    if (ix.byPathFold.has(f + ".txt")) return ix.byPathFold.get(f + ".txt");
  }
  // shortest-path rule: match by basename
  const base = fold(path.basename(t).replace(/\.md$/i, ""));
  const cands = ix.records.filter((r) => fold(r.base) === base && (r.ext === ".md" || !r.is_text || r.ext !== ".txt"));
  if (cands.length === 1) return cands[0];
  if (cands.length > 1) {
    const md = cands.find((r) => r.ext === ".md");
    return md || cands[0];
  }
  return null;
}

let GRAPH = null;
let GRAPH_AT = 0;

function graph() {
  const ix = index();
  if (GRAPH && GRAPH_AT === CACHE_AT) return GRAPH;
  const links = new Map(); // src -> [{target, resolved}]
  const back = new Map(); // dst -> Set(src)
  const unresolved = new Map(); // target text -> Set(src)
  for (const r of ix.records) {
    if (r.ext !== ".md") continue;
    let text;
    try {
      text = readText(safeAbs(r.path));
    } catch (e) {
      continue;
    }
    const outs = [];
    const seen = new Set();
    const add = (raw) => {
      if (seen.has(raw)) return;
      seen.add(raw);
      const res = resolveLinkTarget(raw, ix);
      outs.push({ target: raw, resolved: res ? res.path : null });
      if (res) {
        if (!back.has(res.path)) back.set(res.path, new Set());
        back.get(res.path).add(r.path);
      } else {
        if (!unresolved.has(raw)) unresolved.set(raw, new Set());
        unresolved.get(raw).add(r.path);
      }
    };
    let m;
    WIKI_RE.lastIndex = 0;
    while ((m = WIKI_RE.exec(text))) add(m[1]);
    MDLINK_RE.lastIndex = 0;
    while ((m = MDLINK_RE.exec(text))) if (!/^https?:/i.test(m[1])) add(m[1]);
    links.set(r.path, outs);
  }
  GRAPH = { links, back, unresolved };
  GRAPH_AT = CACHE_AT;
  return GRAPH;
}

function headings(mdText) {
  const out = [];
  const lines = mdText.split(/\r?\n/);
  let inFence = false;
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (/^\s*```/.test(l)) inFence = !inFence;
    if (inFence) continue;
    const m = /^(#{1,6})\s+(.*)$/.exec(l);
    if (m) out.push({ level: m[1].length, heading: m[2].replace(/\\([#*_\-.!()[\]])/g, "$1").trim(), line: i + 1 });
  }
  return out;
}

// ---------------------------------------------------------------------------
// Obsidian CLI (optional, read-only, no UI). Never launches or focuses the app.
// ---------------------------------------------------------------------------

const CLI_READ_ONLY = new Set([
  "search", "search:context", "backlinks", "links", "outline", "orphans", "deadends", "unresolved",
  "tags", "tag", "aliases", "properties", "property:read", "files", "folders", "file", "folder",
  "vault", "read", "bases", "base:views", "base:query", "plugins", "plugins:enabled", "tasks",
  "bookmarks", "recents", "commands", "hotkeys", "diff",
]);

function obsidianRunning() {
  return run("tasklist", ["/FI", "IMAGENAME eq Obsidian.exe", "/NH"], { cwd: undefined, timeout: 15000 })
    .then((r) => /Obsidian\.exe/i.test(r.stdout))
    .catch(() => false);
}

async function obsidian(command, kv, flags) {
  if (!CLI_READ_ONLY.has(command)) throw new Error("command '" + command + "' is not on the read-only no-UI whitelist");
  if (!fs.existsSync(OBSIDIAN_EXE)) throw new Error("Obsidian CLI not found at " + OBSIDIAN_EXE);
  if (!(await obsidianRunning())) {
    throw new Error("Obsidian is not running. The CLI talks to the running app and this server never launches it (no foreground activity). Use the canon_* tools (they do not need Obsidian), or have Silas open Obsidian.");
  }
  const args = ["vault=canon-mirror", command];
  for (const [k, v] of Object.entries(kv || {})) if (v !== undefined && v !== null && v !== "") args.push(k + "=" + String(v));
  for (const f of flags || []) args.push(f);
  const r = await run(OBSIDIAN_EXE, args, { timeout: 90000, label: "obsidian " + command });
  return r.stdout.replace(/^\s*\n/, "");
}

// ---------------------------------------------------------------------------
// git
// ---------------------------------------------------------------------------

async function git(args) {
  const r = await run(GIT_EXE, args, { timeout: 60000, label: "git", env: { GIT_PAGER: "", PAGER: "" } });
  return r.stdout;
}

// ---------------------------------------------------------------------------
// server
// ---------------------------------------------------------------------------

const server = new McpServer(
  { name: "obsidian-canon", version: VERSION },
  {
    instructions: [
      "THE LAST ROMAN canon mirror (Obsidian vault) - read access for Proctor. Google Drive is the source of truth; this mirror is one-way and generated.",
      "For 'explain X' questions: canon_topic first (ranks every live doc), then canon_read the top docs IN FULL (whole=true or page through with offset until done=true). Do not answer from snippets when the doc is available.",
      "Text search: canon_grep (literal by default, regex=true for patterns). .txt is the canonical text of a Google Doc; .md is the same Doc with headings, punctuation escaped by Google.",
      "Live-only is the default everywhere (archives, session logs, historical and Brother's notes are excluded unless live_only=false).",
      "canon_lookup returns the Drive id for any doc so edits can be made on Drive with gdrive-ops; then canon_pull to refresh the mirror.",
      "Nothing here touches the Obsidian window. The obsidian_* tools only work when Obsidian is already running and are read-only.",
    ].join("\n"),
  }
);

server.tool(
  "canon_info",
  "Vault facts: path, counts (live / archived docs, images), last pull (git), freshness, Obsidian running or not, and a self-check of search. Call first if unsure the mirror is current.",
  {},
  async () => {
    try {
      const ix = index();
      const docs = ix.records.filter((r) => r.ext === ".txt");
      const live = docs.filter((r) => r.live).length;
      let lastPull = null;
      try {
        lastPull = (await git(["log", "-1", "--date=iso-strict", "--format=%h %ad %s"])).trim();
      } catch (e) {
        lastPull = "git unavailable: " + e.message;
      }
      let status = null;
      try {
        status = (await git(["status", "--porcelain"])).trim();
      } catch (e) {}
      const running = await obsidianRunning();
      const probe = grep("Valerius", { max_matches: 1, max_files: 1, context: 0 });
      return ok({
        server_version: VERSION,
        vault: VAULT,
        drive_root_id: ix.manifest.root_id,
        drive_account: ix.manifest.account,
        files_total: ix.records.length,
        google_docs: docs.length,
        google_docs_live: live,
        google_docs_archived: docs.length - live,
        images: ix.records.filter((r) => r.is_image).length,
        image_captions: Object.keys(ix.images || {}).length,
        last_pull: lastPull,
        uncommitted_changes: status ? status.split(/\r?\n/).length : 0,
        obsidian_running: running,
        obsidian_cli_available: running && fs.existsSync(OBSIDIAN_EXE),
        search_selfcheck: probe.total_matches > 0 ? "ok (" + probe.total_matches + " hits for Valerius)" : "FAILED - grep found nothing; mirror may be empty",
        how_to_refresh: "canon_pull (runs lr-pull: Drive -> mirror -> git -> GitHub)",
      });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_list",
  "List files in the mirror. Filters: folder (prefix or substring), ext (txt|md|png|...), query (name substring, ASCII-folded), live_only (default true). Google Docs appear as .txt (canonical text) and .md (headings). Returns Drive ids too.",
  {
    folder: z.string().optional().describe("Folder path prefix or substring, e.g. '18 - Concept Art' or 'Characters/Mardin'"),
    ext: z.string().optional().describe("Extension filter without dot: txt, md, png, jpg, html, pdf"),
    query: z.string().optional().describe("Case-insensitive substring on file name / Drive name / Drive path"),
    live_only: z.boolean().optional().describe("Default true: exclude archives, session logs, historical, Brother's notes"),
    docs_only: z.boolean().optional().describe("Default true: one row per Google Doc (the .txt); false = every file including .md twins and images"),
    limit: z.number().optional().describe("Max rows (default 300)"),
  },
  async ({ folder, ext, query, live_only, docs_only, limit }) => {
    try {
      const ix = index();
      let list = ix.records;
      if (docs_only !== false && !ext) list = list.filter((r) => r.ext === ".txt" || (r.ext === ".md" && !r.has_txt_twin) || (!r.is_image && r.ext !== ".md" && r.ext !== ".txt" && r.is_text));
      if (live_only !== false) list = list.filter((r) => r.live);
      if (folder) {
        const f = fold(toPosix(folder).replace(/\/$/, ""));
        list = list.filter((r) => fold(r.path).startsWith(f + "/") || fold(r.folder).includes(f));
      }
      if (ext) {
        const e = ("." + String(ext).replace(/^\./, "")).toLowerCase();
        list = list.filter((r) => r.ext === e);
      }
      if (query) {
        const q = fold(query);
        list = list.filter((r) => fold(r.path).includes(q) || (r.drive_name && fold(r.drive_name).includes(q)) || (r.drive_path && fold(r.drive_path).includes(q)));
      }
      const lim = limit || 300;
      return ok({
        total: list.length,
        shown: Math.min(lim, list.length),
        files: list.slice(0, lim).map((r) => ({
          path: r.path,
          live: r.live,
          drive_id: r.drive_id,
          drive_name: r.drive_name,
          modified: r.modified,
        })),
      });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_read",
  "Read a document by local path, Drive id, Drive name, or a distinctive part of its name. Returns the canonical .txt by default (format=md for headings). Paged: offset/limit in lines with done=false and next_offset when more remains; whole=true returns everything. NEVER answer from a partial read - keep paging until done=true.",
  {
    file: z.string().describe("Local path ('canon/.../X.txt'), Drive id, exact Drive name, or unique name fragment (e.g. 'BUTTERFLY DRAGON')"),
    format: z.enum(["txt", "md", "auto"]).optional().describe("auto (default) = .txt for Google Docs; md = headings-kept twin"),
    offset: z.number().optional().describe("1-based start line (default 1)"),
    limit: z.number().optional().describe("Lines per page (default 600, max 5000)"),
    whole: z.boolean().optional().describe("true = return the entire file regardless of limit"),
  },
  async ({ file, format, offset, limit, whole }) => {
    try {
      const ext = format === "md" ? ".md" : format === "txt" ? ".txt" : null;
      const r = chooseOne(file, { ext });
      if (!r.is_text) throw new Error(r.path + " is not a text file (" + r.ext + "). Use canon_images for pictures.");
      const text = readText(safeAbs(r.path));
      const lines = text.split(/\r?\n/);
      const start = Math.max(1, offset || 1);
      const lim = whole ? lines.length : Math.min(5000, limit || 600);
      const slice = lines.slice(start - 1, start - 1 + lim);
      const end = start - 1 + slice.length;
      const twin = r.md_twin ? r.md_twin : r.ext === ".md" && r.has_txt_twin ? r.path.slice(0, -3) + ".txt" : null;
      return ok({
        file: describe(r),
        twin,
        total_lines: lines.length,
        total_chars: text.length,
        from_line: start,
        to_line: end,
        done: end >= lines.length,
        next_offset: end >= lines.length ? null : end + 1,
        text: slice.join("\n"),
      });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_grep",
  "Search the canonical text of the whole corpus (ripgrep equivalent). Literal by default; regex=true for patterns; whole_word, case_sensitive, context lines (0-10). scope: canonical (default: one text per Doc + generated md), txt, md, all. Results ranked by match count with line numbers. Use live_only=false to include archives and session logs.",
  {
    pattern: z.string().describe("Text or regex to find"),
    regex: z.boolean().optional(),
    case_sensitive: z.boolean().optional(),
    whole_word: z.boolean().optional(),
    context: z.number().optional().describe("Lines of context before/after each hit (default 1)"),
    folder: z.string().optional().describe("Restrict to a folder (prefix or substring)"),
    ext: z.string().optional(),
    scope: z.enum(["canonical", "txt", "md", "all"]).optional(),
    live_only: z.boolean().optional(),
    max_matches: z.number().optional().describe("Default 200"),
    max_files: z.number().optional().describe("Default 60"),
  },
  async (a) => {
    try {
      return ok(grep(a.pattern, a));
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_topic",
  "Research starter for 'explain X' / 'tell me everything about X'. Searches every live doc for the topic (and optional aliases), ranks docs by relevance, shows the matching lines per doc, and lists exactly which docs to read in full next (canon_read whole=true). Follow up by reading them - do not stop at the snippets.",
  {
    topic: z.string().describe("Subject, e.g. 'Butterfly Dragon'"),
    aliases: z.array(z.string()).optional().describe("Other names / spellings to OR with the topic, e.g. ['Papilio', 'butterfly draco']"),
    live_only: z.boolean().optional().describe("Default true"),
    max_docs: z.number().optional().describe("Docs to show (default 40)"),
    lines_per_doc: z.number().optional().describe("Matching lines shown per doc (default 12)"),
  },
  async ({ topic, aliases, live_only, max_docs, lines_per_doc }) => {
    try {
      const terms = [topic].concat(aliases || []).filter(Boolean);
      const pattern = terms.map(esc).join("|");
      const g = grep(pattern, { regex: true, live_only, context: 0, max_matches: 100000, max_files: 100000 });
      const ix = index();
      const perDoc = lines_per_doc || 12;
      // One row per document: the atlas (html + md + pdf, each with a twin) must not appear three times.
      const docKey = (p) => fold(p).replace(/\.(html|pdf|docx|doc)\.md$/, "").replace(/\.(md|txt|html|pdf|docx|doc)$/, "");
      const twinRank = (p) => (/\.txt$/i.test(p) ? 0 : /\.html\.md$/i.test(p) ? 1 : /\.md$/i.test(p) && !/\.(pdf|docx|doc)\.md$/i.test(p) ? 2 : 3);
      const byKey = new Map();
      for (const f of g.results) {
        const k = docKey(f.file);
        const prev = byKey.get(k);
        if (!prev || twinRank(f.file) < twinRank(prev.file)) byKey.set(k, prev && prev.match_count > f.match_count ? Object.assign({}, f, { match_count: prev.match_count }) : f);
      }
      const topicFold = fold(topic);
      const rows = [...byKey.values()].map((f) => {
        const r = ix.byPath.get(f.file);
        const names = [r ? r.base : "", r && r.drive_name ? r.drive_name : ""].map(fold);
        const titleTopic = names.some((n) => n.includes(topicFold));
        const titleAlias = !titleTopic && terms.some((t) => names.some((n) => n.includes(fold(t))));
        return {
          file: f.file,
          drive_name: r ? r.drive_name : null,
          drive_id: r ? r.drive_id : null,
          modified: r ? r.modified : null,
          live: f.live,
          title_match: titleTopic || titleAlias,
          title_match_kind: titleTopic ? "topic" : titleAlias ? "alias" : null,
          match_count: f.match_count,
          lines: f.matches.slice(0, perDoc).map((m) => m.line + ": " + m.text.slice(0, 400)),
        };
      });
      // Docs ABOUT the topic first (exact topic in the title, then an alias), then everything else by mention count.
      rows.sort((a, b) => (b.title_match_kind === "topic") - (a.title_match_kind === "topic") || (b.title_match_kind === "alias") - (a.title_match_kind === "alias") || b.match_count - a.match_count || a.file.localeCompare(b.file));
      const docs = rows.slice(0, max_docs || 40);
      const titled = rows.filter((d) => d.title_match).map((d) => d.file);
      const heavy = rows.filter((d) => !d.title_match && d.match_count >= 5).map((d) => d.file);
      const readInFull = titled.concat(heavy).slice(0, Math.max(12, titled.length));
      const images = Object.entries(ix.images || {})
        .filter(([id, v]) => terms.some((t) => fold((v.name || "") + " " + (v.desc || "")).includes(fold(t))))
        .slice(0, 30)
        .map(([id, v]) => ({ drive_id: id, name: v.name, caption: v.desc, link: "https://drive.google.com/file/d/" + id + "/view" }));
      return ok({
        topic,
        terms,
        files_searched: g.files_searched,
        docs_matched: rows.length,
        files_matched_including_twins: g.files_matched,
        total_mentions: g.total_matches,
        read_in_full_next: readInFull,
        docs,
        related_images: images,
        note: "Ranked by mention count; title_match=true means the doc is ABOUT the topic. Read every doc in read_in_full_next with canon_read whole=true before answering; then check canon_history for recent changes to them.",
      });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_lookup",
  "Resolve a Drive id, Drive name, Drive path, or local path to the full manifest entry (id, name, Drive path, link, mime, modified, live, local files). Use the id with gdrive-ops to edit the source on Drive.",
  {
    query: z.string().describe("Drive id, name fragment, Drive path fragment, or local path"),
    limit: z.number().optional().describe("Default 25"),
  },
  async ({ query, limit }) => {
    try {
      const ix = index();
      const q = fold(query);
      let hits = [];
      if (ix.byId.has(query)) hits = [ix.byId.get(query)];
      else {
        const local = ix.byPath.get(toPosix(query)) || ix.byPathFold.get(q);
        if (local && local.drive_id) hits = [ix.byId.get(local.drive_id)];
        else
          hits = (ix.manifest.files || []).filter(
            (e) => fold(e.name).includes(q) || fold(e.drive_path).includes(q) || (e.local_files || []).some((lf) => fold(lf).includes(q))
          );
      }
      hits.sort((a, b) => (b.live === true) - (a.live === true) || fold(a.name).localeCompare(fold(b.name)));
      return ok({ total: hits.length, entries: hits.slice(0, limit || 25) });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_outline",
  "Headings of a document (from its .md twin) with line numbers, so a long doc can be read section by section via canon_read offset/limit on the .txt (line numbers differ between .md and .txt; use the heading text to locate with canon_grep).",
  { file: z.string().describe("Path, Drive id, Drive name or unique fragment") },
  async ({ file }) => {
    try {
      const r = chooseOne(file, { ext: ".md" });
      const md = r.ext === ".md" ? r : index().byPath.get(r.path.replace(/\.txt$/, ".md"));
      if (!md) throw new Error("no .md twin for " + r.path);
      const text = readText(safeAbs(md.path));
      return ok({ file: describe(md), total_lines: text.split(/\r?\n/).length, headings: headings(text) });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_graph",
  "Link graph computed from the vault's wikilinks / markdown links (no Obsidian needed). op=backlinks|links (needs file), orphans (no incoming), deadends (no outgoing), unresolved (links to nothing). INDEX.md links every Doc; galleries link images.",
  {
    op: z.enum(["backlinks", "links", "orphans", "deadends", "unresolved"]),
    file: z.string().optional().describe("For backlinks/links: path, Drive id, name or fragment"),
    live_only: z.boolean().optional().describe("Default true for orphans/deadends"),
    limit: z.number().optional().describe("Default 500"),
  },
  async ({ op, file, live_only, limit }) => {
    try {
      const ix = index();
      const g = graph();
      const lim = limit || 500;
      if (op === "backlinks" || op === "links") {
        if (!file) throw new Error("file is required for " + op);
        const r = chooseOne(file, { ext: ".md" });
        const targets = [r.path];
        if (r.ext === ".md" && r.has_txt_twin) targets.push(r.path.slice(0, -3) + ".txt");
        if (r.ext === ".txt") targets.push(r.path.slice(0, -4) + ".md");
        if (op === "backlinks") {
          const srcs = new Set();
          for (const t of targets) for (const s of g.back.get(t) || []) srcs.add(s);
          return ok({ file: describe(r), total: srcs.size, backlinks: [...srcs].sort().slice(0, lim) });
        }
        const outs = [];
        for (const t of targets) for (const l of g.links.get(t) || []) outs.push(l);
        return ok({ file: describe(r), total: outs.length, links: outs.slice(0, lim) });
      }
      if (op === "unresolved") {
        const rows = [...g.unresolved.entries()].map(([t, srcs]) => ({ target: t, sources: [...srcs] }));
        return ok({ total: rows.length, unresolved: rows.slice(0, lim) });
      }
      let mdFiles = ix.records.filter((r) => r.ext === ".md");
      if (live_only !== false) mdFiles = mdFiles.filter((r) => r.live);
      if (op === "orphans") {
        const rows = mdFiles.filter((r) => !(g.back.get(r.path) && g.back.get(r.path).size)).map((r) => r.path);
        return ok({ total: rows.length, orphans: rows.slice(0, lim), note: "Google-Doc .md files rarely link to each other; INDEX.md is the hub. .txt files are never linked (expected)." });
      }
      const rows = mdFiles.filter((r) => !(g.links.get(r.path) && g.links.get(r.path).length)).map((r) => r.path);
      return ok({ total: rows.length, deadends: rows.slice(0, lim) });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_history",
  "What changed in the mirror and when (git log of pulls). Optional file to see that doc's revisions; since='2026-09-01' or '3 days ago'. Each pull commit message counts new/updated/removed. Use canon_diff to see the actual text change.",
  {
    file: z.string().optional().describe("Path, Drive id, name or fragment to filter history to one doc"),
    since: z.string().optional().describe("git date, e.g. '2026-09-01' or '2 weeks ago'"),
    n: z.number().optional().describe("Max commits (default 20)"),
    show_files: z.boolean().optional().describe("Include the list of files touched per commit (default true when file is not given and n<=20)"),
  },
  async ({ file, since, n, show_files }) => {
    try {
      const args = ["log", "--date=iso-strict", "--format=%H%x09%h%x09%ad%x09%s", "-n", String(n || 20)];
      if (since) args.push("--since=" + since);
      let target = null;
      if (file) {
        const r = chooseOne(file);
        target = r.path;
      }
      const wantFiles = show_files == null ? (n || 20) <= 20 : show_files;
      if (wantFiles) args.push("--name-status");
      if (target) args.push("--", target, target.replace(/\.txt$/, ".md"));
      const out = await git(args);
      const commits = [];
      let cur = null;
      for (const line of out.split(/\r?\n/)) {
        if (!line.trim()) continue;
        const parts = line.split("\t");
        if (parts.length >= 4 && /^[0-9a-f]{40}$/.test(parts[0])) {
          cur = { hash: parts[1], date: parts[2], subject: parts.slice(3).join("\t"), files: [] };
          commits.push(cur);
        } else if (cur && /^[AMDRT]/.test(parts[0])) {
          cur.files.push({ status: parts[0], path: parts[parts.length - 1] });
        }
      }
      return ok({ file: target, total: commits.length, commits });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_diff",
  "Text diff of one document between two pulls (git). from/to are commit hashes from canon_history; to defaults to the current file; from defaults to the previous revision.",
  {
    file: z.string().describe("Path, Drive id, name or fragment"),
    from: z.string().optional().describe("Older commit hash (default: the revision before 'to')"),
    to: z.string().optional().describe("Newer commit hash (default: working tree)"),
    max_chars: z.number().optional().describe("Default 60000"),
  },
  async ({ file, from, to, max_chars }) => {
    try {
      const r = chooseOne(file);
      const args = ["diff", "--no-color", "-U2"];
      if (from && to) args.push(from, to);
      else if (from) args.push(from);
      else if (to) args.push(to + "~1", to);
      else args.push("HEAD~1");
      args.push("--", r.path);
      let out = await git(args);
      const cap = max_chars || 60000;
      const truncated = out.length > cap;
      if (truncated) out = out.slice(0, cap);
      return ok({ file: describe(r), from: from || (to ? to + "~1" : "HEAD~1"), to: to || "working tree", truncated, diff: out || "(no differences)" });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_images",
  "Search the concept-art / reference images by name or Brother's caption (captions are Brother-described, NOT canon). Returns Drive id + view link + local path. query empty = list a folder.",
  {
    query: z.string().optional().describe("Substring on image name or caption, e.g. 'pauldron green' or 'Mardin'"),
    folder: z.string().optional().describe("Restrict to a folder fragment, e.g. 'Characters/Mardin'"),
    limit: z.number().optional().describe("Default 60"),
  },
  async ({ query, folder, limit }) => {
    try {
      const ix = index();
      const q = query ? fold(query) : null;
      const terms = q ? q.split(/\s+/).filter(Boolean) : [];
      const byName = new Map();
      for (const r of ix.records) if (r.is_image) byName.set(fold(r.base + r.ext), r);
      const rows = [];
      for (const [id, v] of Object.entries(ix.images || {})) {
        const hay = fold((v.name || "") + " " + (v.desc || ""));
        if (terms.length && !terms.every((t) => hay.includes(t))) continue;
        const local = byName.get(fold(v.name || "")) || null;
        if (folder && local && !fold(local.path).includes(fold(folder))) continue;
        if (folder && !local) continue;
        rows.push({
          drive_id: id,
          name: v.name,
          caption: v.desc,
          caption_by: v.by,
          caption_date: v.date,
          local_path: local ? local.path : null,
          link: "https://drive.google.com/file/d/" + id + "/view",
        });
      }
      return ok({ total: rows.length, images: rows.slice(0, limit || 60), note: "Captions are Brother's descriptions, flagged non-canon. Open the link (or ask Brother) to see the picture itself." });
    } catch (e) {
      return fail(e);
    }
  }
);

// lr-pull runs 30 s to several minutes; MCP clients time out around 60 s, so the pull is a background
// job: the first call starts it and waits up to wait_seconds; later calls (status=true) report progress.
let PULL_JOB = null;

function pullSummary(text) {
  return text.split(/\r?\n/).filter((l) => /new|updated|removed|FAILED|nothing to commit|pushed|dry|would|error|Traceback/i.test(l)).slice(-25);
}

function startPull(dry_run, full) {
  const args = [path.join(VAULT, "_tools", "pull.py")];
  if (dry_run) args.push("--dry-run");
  else args.push("--push");
  if (full) args.push("--full");
  const env = {
    PYTHONIOENCODING: "utf-8",
    PYTHONUTF8: "1",
    PATH: [NPM_BIN, path.dirname(process.execPath), "C:/Program Files/Git/cmd", process.env.PATH || ""].join(path.delimiter),
  };
  const job = { id: Date.now().toString(36), dry_run: !!dry_run, full: !!full, started: new Date().toISOString(), finished: null, status: "running", exit_code: null, output: "" };
  const p = run(PYTHON_EXE, args, { timeout: 900000, env, label: "lr-pull" });
  job.promise = p
    .then((r) => {
      job.output = r.stdout + (r.stderr ? "\n[stderr]\n" + r.stderr : "");
      job.status = "done";
      job.exit_code = 0;
    })
    .catch((e) => {
      job.output = String(e.message || e);
      job.status = "failed";
      job.exit_code = 1;
    })
    .finally(() => {
      job.finished = new Date().toISOString();
      CACHE = null;
      GRAPH = null;
    });
  PULL_JOB = job;
  return job;
}

function jobView(job) {
  return {
    job_id: job.id,
    status: job.status,
    dry_run: job.dry_run,
    full: job.full,
    started: job.started,
    finished: job.finished,
    summary: job.status === "running" ? ["still running - call canon_pull again with status=true"] : pullSummary(job.output),
    log_tail: job.status === "running" ? null : job.output.slice(-3000),
  };
}

server.tool(
  "canon_pull",
  "Refresh the mirror from Google Drive (runs lr-pull: pull changed Docs -> commit -> push to the private GitHub repo). ONE-WAY, never touches Drive. Run after any edit made on Drive (RUNBOOK 4b). dry_run=true lists what would change and touches nothing. Runs in the background: returns when finished or after wait_seconds (default 45); if status is 'running', call again with status=true until done.",
  {
    dry_run: z.boolean().optional().describe("true = report only, no changes"),
    full: z.boolean().optional().describe("true = re-export everything (slow, only if the mirror looks wrong)"),
    status: z.boolean().optional().describe("true = do not start anything, report the current/last pull job"),
    wait_seconds: z.number().optional().describe("How long to wait for completion before returning 'running' (default 45, max 55)"),
  },
  async ({ dry_run, full, status, wait_seconds }) => {
    try {
      const wait = Math.min(55, Math.max(0, wait_seconds == null ? 45 : wait_seconds)) * 1000;
      let job = PULL_JOB;
      if (status) {
        if (!job) return ok({ status: "idle", note: "no pull has run in this session" });
      } else {
        if (job && job.status === "running") return ok(Object.assign({ note: "a pull is already running; not starting another" }, jobView(job)));
        job = startPull(dry_run, full);
      }
      if (job.status === "running" && wait > 0) {
        await Promise.race([job.promise, new Promise((res) => setTimeout(res, wait))]);
      }
      return ok(jobView(job));
    } catch (e) {
      CACHE = null;
      return fail(e);
    }
  }
);

server.tool(
  "obsidian_search",
  "Search through Obsidian's own engine (only .md files are indexed by Obsidian; the canonical .txt is NOT). Needs Obsidian already running; never opens or focuses it. Cross-checked against canon_grep: if Obsidian returns nothing but grep finds hits, the app's search is cold and the grep results are returned instead.",
  {
    query: z.string().describe("Obsidian search query (plain text; operators like path: file: line: are unreliable in the CLI)"),
    context: z.boolean().optional().describe("true (default) = matching lines with line numbers; false = file paths only"),
    folder: z.string().optional().describe("Limit to a folder path"),
    limit: z.number().optional().describe("Max files (default 50)"),
  },
  async ({ query, context, folder, limit }) => {
    try {
      const cmd = context === false ? "search" : "search:context";
      const raw = await obsidian(cmd, { query, path: folder, limit: limit || 50, format: "json" });
      let parsed = null;
      try {
        parsed = JSON.parse(raw);
      } catch (e) {
        parsed = null;
      }
      const empty = !parsed || (Array.isArray(parsed) && parsed.length === 0);
      if (empty) {
        const g = grep(query, { scope: "md", context: 0, max_matches: 200, max_files: limit || 50, live_only: false });
        return ok({
          engine: g.total_matches ? "grep-fallback" : "obsidian",
          note: g.total_matches
            ? "Obsidian's CLI search returned nothing (known cold-start bug in the app). canon_grep over the same .md files found " + g.total_matches + " hits; those are returned."
            : "No matches in Obsidian or grep.",
          results: g.total_matches ? g.results : [],
        });
      }
      return ok({ engine: "obsidian", results: parsed });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "obsidian_cli",
  "Run a whitelisted READ-ONLY Obsidian CLI command against the vault (backlinks, links, outline, orphans, deadends, unresolved, tags, tag, aliases, properties, property:read, files, folders, file, folder, vault, read, bases, base:query, plugins, tasks, bookmarks, recents, commands, search, search:context). Needs Obsidian running; never launches, opens, focuses or restarts it. key=value args go in args; bare flags (total, counts, verbose) in flags.",
  {
    command: z.string().describe("e.g. 'backlinks', 'outline', 'unresolved'"),
    args: z.record(z.string()).optional().describe("key=value pairs, e.g. {file: 'INDEX', format: 'json'}"),
    flags: z.array(z.string()).optional().describe("bare flags, e.g. ['total'] or ['counts']"),
  },
  async ({ command, args, flags }) => {
    try {
      const raw = await obsidian(command, args || {}, flags || []);
      let parsed = null;
      try {
        parsed = JSON.parse(raw);
      } catch (e) {}
      return ok({ command, output: parsed != null ? parsed : raw });
    } catch (e) {
      return fail(e);
    }
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
