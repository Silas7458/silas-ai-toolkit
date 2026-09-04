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
import { execFile, spawnSync } from "node:child_process";
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
// Every subprocess this server starts is registered here and force-killed (whole tree) when the
// server goes away - Windows does NOT kill children when the parent dies, and orphaned node /
// python / llama.cpp processes eating RAM after Claude Desktop closes is exactly what Silas has
// been burned by. No daemons, no HTTP servers, no Bun: one child per call, gone when it returns.
const CHILDREN = new Set();
function killTree(child) {
  try {
    if (child.exitCode !== null || child.signalCode) return;
    if (process.platform === "win32") {
      // taskkill /T takes the child's own children (qmd -> llama.cpp workers, python -> gws/git)
      spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], { windowsHide: true, timeout: 10000 });
    } else child.kill("SIGKILL");
  } catch (e) {}
}
function killAllChildren() {
  for (const c of CHILDREN) killTree(c);
  CHILDREN.clear();
}
process.on("exit", killAllChildren);
for (const sig of ["SIGINT", "SIGTERM", "SIGHUP"]) {
  try {
    process.on(sig, () => {
      killAllChildren();
      process.exit(0);
    });
  } catch (e) {}
}
// Claude Desktop closing = our stdin closes. That is the reliable shutdown signal on Windows.
process.stdin.on("end", () => {
  killAllChildren();
  process.exit(0);
});
process.stdin.on("close", () => {
  killAllChildren();
  process.exit(0);
});

function run(exe, args, opts) {
  const o = opts || {};
  return new Promise((resolve, reject) => {
    const child = execFile(
      exe,
      args,
      {
        cwd: o.cwd || VAULT,
        timeout: o.timeout || 60000,
        killSignal: "SIGKILL",
        maxBuffer: BIG_BUFFER,
        windowsHide: true,
        env: Object.assign({}, process.env, o.env || {}),
      },
      (err, stdout, stderr) => {
        CHILDREN.delete(child);
        if (err) {
          // on timeout execFile only kills the direct child; take the tree too
          if (err.killed || err.signal) killTree(child);
          reject(new Error((o.label || exe) + " failed: " + (String(stderr).trim() || err.message)));
        } else resolve({ stdout: String(stdout), stderr: String(stderr) });
      }
    );
    CHILDREN.add(child);
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
// QMD (tobi/qmd) - semantic search folded into this server. QMD keeps its own index
// (~/.cache/qmd/index.sqlite) over the collection "canon" = this mirror. We shell out to
// its CLI with --format json (keeps the MCP process light; models load inside qmd).
// ---------------------------------------------------------------------------

const QMD_COLLECTION = process.env.OBSIDIAN_CANON_QMD_COLLECTION || "canon";

function qmdBin() {
  if (process.env.OBSIDIAN_CANON_QMD_BIN) return process.env.OBSIDIAN_CANON_QMD_BIN;
  const pkgDir = path.join(NPM_BIN, "node_modules", "@tobilu", "qmd");
  // bin/qmd is a launcher that spawns a SECOND node for dist/cli/qmd.js; call the real entry
  // directly so each query is exactly one child process, not two.
  const direct = path.join(pkgDir, "dist", "cli", "qmd.js");
  if (fs.existsSync(direct)) return direct;
  try {
    const pkg = JSON.parse(readText(path.join(pkgDir, "package.json")));
    const bin = typeof pkg.bin === "string" ? pkg.bin : pkg.bin && (pkg.bin.qmd || Object.values(pkg.bin)[0]);
    if (bin) return path.join(pkgDir, bin);
  } catch (e) {}
  return null;
}

async function qmd(args, opts) {
  const bin = qmdBin();
  if (!bin || !fs.existsSync(bin)) throw new Error("QMD is not installed (npm i -g @tobilu/qmd). Semantic search unavailable; canon_grep and canon_topic still work.");
  const o = opts || {};
  const r = await run(process.execPath, [bin].concat(args), {
    timeout: o.timeout || 240000,
    label: "qmd " + args[0],
    env: Object.assign({ QMD_NO_COLOR: "1", NO_COLOR: "1" }, o.env || {}),
  });
  return r.stdout;
}

// WARM MODE (opt-in, OBSIDIAN_CANON_QMD_WARM=1): keep ONE qmd HTTP child alive with the models
// loaded so semantic queries answer in seconds instead of paying the ~20-30 s model load per call.
// It is a tracked child of this server (killed with it), never a detached daemon. Costs ~2 GB RAM
// while Claude Desktop is open. Default is OFF (cold per-call, zero resident memory).
const QMD_WARM = /^(1|true|yes)$/i.test(String(process.env.OBSIDIAN_CANON_QMD_WARM || ""));
const QMD_PORT = parseInt(process.env.OBSIDIAN_CANON_QMD_PORT || "8181", 10);
let WARM = null; // { child, ready: Promise }

function warmQmd() {
  if (WARM) return WARM.ready;
  const bin = qmdBin();
  const child = execFile(process.execPath, [bin, "mcp", "--http", "--port", String(QMD_PORT)], {
    cwd: VAULT,
    windowsHide: true,
    maxBuffer: BIG_BUFFER,
    env: Object.assign({}, process.env, { QMD_NO_COLOR: "1", NO_COLOR: "1" }),
  }, () => {
    CHILDREN.delete(child);
    WARM = null; // died or was killed: next call cold-starts it again
  });
  CHILDREN.add(child);
  const ready = (async () => {
    const deadline = Date.now() + 120000;
    while (Date.now() < deadline) {
      try {
        const r = await fetch("http://127.0.0.1:" + QMD_PORT + "/health");
        if (r.ok) return true;
      } catch (e) {}
      await new Promise((res) => setTimeout(res, 500));
    }
    throw new Error("warm qmd did not come up on port " + QMD_PORT + " within 120 s");
  })();
  WARM = { child, ready };
  return ready;
}

async function qmdQueryWarm(searches, opts) {
  await warmQmd();
  const body = { searches, collection: QMD_COLLECTION, limit: opts.limit, rerank: !!opts.rerank };
  const r = await fetch("http://127.0.0.1:" + QMD_PORT + "/query", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(opts.timeout || 240000),
  });
  if (!r.ok) throw new Error("warm qmd /query HTTP " + r.status + ": " + (await r.text()).slice(0, 300));
  return r.json();
}

function parseQmdStatus(text) {
  const m1 = /Total:\s+(\d+)\s+files indexed/.exec(text);
  const m2 = /Vectors:\s+(\d+)\s+embedded/.exec(text);
  return { files_indexed: m1 ? +m1[1] : null, vectors_embedded: m2 ? +m2[1] : null, raw: text.trim().slice(0, 1500) };
}

// Chained after every real pull: re-index changed files, then refresh vectors. Background.
let EMBED_JOB = null;
function startEmbed(force) {
  const job = { id: Date.now().toString(36), started: new Date().toISOString(), finished: null, status: "running", output: "" };
  job.promise = qmd(["update"], { timeout: 600000 })
    // batch caps keep the embed child's RAM bounded (an uncapped first embed peaked at 5.4 GB on this box)
    .then((u) => qmd(["embed", "-c", QMD_COLLECTION, "--max-docs-per-batch", "8", "--max-batch-mb", "4"].concat(force ? ["-f"] : []), { timeout: 3600000 }).then((e) => (job.output = u + "\n" + e)))
    .then(() => {
      job.status = "done";
    })
    .catch((e) => {
      job.status = "failed";
      job.output = String(e.message || e);
    })
    .finally(() => {
      job.finished = new Date().toISOString();
    });
  EMBED_JOB = job;
  return job;
}
function embedView(job) {
  if (!job) return { status: "idle" };
  return { job_id: job.id, status: job.status, started: job.started, finished: job.finished, log_tail: job.status === "running" ? null : job.output.slice(-1200) };
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
      "Text search: canon_grep (literal by default, regex=true for patterns). Meaning search: canon_semantic (plain-language questions, no exact words needed; local BM25 + vectors + rerank). .txt is the canonical text of a Google Doc; .md is the same Doc with headings, punctuation escaped by Google.",
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
      let semantic = { installed: false };
      if (qmdBin()) {
        try {
          const st = parseQmdStatus(await qmd(["status"], { timeout: 60000 }));
          semantic = {
            installed: true,
            collection: QMD_COLLECTION,
            files_indexed: st.files_indexed,
            vectors_embedded: st.vectors_embedded,
            ready: !!(st.vectors_embedded && st.vectors_embedded > 0),
            reindex_job: embedView(EMBED_JOB),
          };
        } catch (e) {
          semantic = { installed: true, error: String(e.message || e).slice(0, 300) };
        }
      }
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
        semantic_index: semantic,
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
    whole: z.boolean().optional().describe("true = return the entire file regardless of limit (still paged at ~60K chars: keep calling with next_offset until done=true)"),
    max_chars: z.number().optional().describe("Page size cap in characters (default 60000; Claude Desktop truncates larger tool results)"),
  },
  async ({ file, format, offset, limit, whole, max_chars }) => {
    try {
      const ext = format === "md" ? ".md" : format === "txt" ? ".txt" : null;
      const r = chooseOne(file, { ext });
      if (!r.is_text) throw new Error(r.path + " is not a text file (" + r.ext + "). Use canon_images for pictures.");
      const text = readText(safeAbs(r.path));
      const lines = text.split(/\r?\n/);
      const start = Math.max(1, offset || 1);
      const lim = whole ? lines.length : Math.min(5000, limit || 600);
      let slice = lines.slice(start - 1, start - 1 + lim);
      // Claude Desktop truncates very large tool results; keep one page under ~60K chars and let the
      // caller continue from next_offset (a 90K-char character file overflowed in Proctor's Test C).
      const MAX_CHARS = Math.max(20000, Math.min(200000, max_chars || 60000));
      let chars = 0;
      let cut = slice.length;
      for (let i = 0; i < slice.length; i++) {
        chars += slice[i].length + 1;
        if (chars > MAX_CHARS && i > 0) {
          cut = i;
          break;
        }
      }
      const capped = cut < slice.length;
      if (capped) slice = slice.slice(0, cut);
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
        page_capped_by_chars: capped,
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

// ---------------------------------------------------------------------------
// Section / episode retrieval - the answer to "Proctor must read three Masters and three State
// compilations before he can write an episode". The Docs have no markdown headings; their sections
// start with text markers: "SECTION 5F - EPISODE 108 - ...", "108 - \"BUTTERFLY DRAGON\"", "EPISODE 201 - ...",
// "PART TWO - ...". A block runs from its marker line to the next marker line. Dashes in the Docs are
// em/en dashes (U+2014 / U+2013), matched by escape below - this file stays ASCII.
// ---------------------------------------------------------------------------

const DASH = "[\\u2014\\u2013\\-]";
const MARKER_RE = new RegExp("^(SECTION\\s+\\S+|PART\\s+\\S+|EPISODE\\s+\\d{3}\\b|[1-4]\\d{2}\\s*" + DASH + "|S[1-4]E\\d{2}\\b|CHAPTER\\s+\\S+|APPENDIX\\b)");

function normalizeEpisode(ep) {
  const s = String(ep).trim().toUpperCase();
  let m = /^S?([1-4])\s*[EX]\s*(\d{1,2})$/.exec(s);
  if (m) return { number: +m[1] * 100 + +m[2], code: "S" + m[1] + "E" + String(+m[2]).padStart(2, "0") };
  m = /^([1-4])(\d{2})$/.exec(s);
  if (m) return { number: +s, code: "S" + m[1] + "E" + m[2] };
  throw new Error("episode must look like 108, S1E08 or 1x08 (got '" + ep + "')");
}

function episodeStartRe(epi) {
  const n = String(epi.number);
  return new RegExp("^(SECTION\\s+\\S+\\s*" + DASH + "\\s*)?(EPISODE\\s+)?" + n + "(\\s*" + DASH + "|\\s*$|\\s*\\(|\\s*\\[|\\s*:)|^" + epi.code + "\\b", "i");
}

// A STRUCTURAL block ("SECTION 5F - EPISODE 108 - ...", "108 - \"TITLE\"", "EPISODE 201 - ...") runs to the
// next section marker. A BEAT paragraph inside a character file ("108: he ...", "204 (Act One): ...",
// "207-210: no beat written") is one paragraph: it ends at the next blank line or the next
// episode-numbered paragraph. Without this split a one-line beat swallowed the rest of the file.
const STRUCT_RE = new RegExp("^(SECTION\\s+\\S+\\s*" + DASH + "\\s*)?(EPISODE\\s+)?[1-4]\\d{2}\\s*(" + DASH + "\\s*[\"\\u201c\\u2018'(A-Za-z]|\\[|$)");
const BEAT_END_RE = new RegExp("^\\s*$|^(S[1-4]E\\d{2}|[1-4]\\d{2})\\b|^(SECTION|PART|EPISODE|CHAPTER|APPENDIX)\\b");

function sliceBlocks(lines, startRe, endRe, maxLinesPerBlock, beatEndRe, forceBeat) {
  const blocks = [];
  for (let i = 0; i < lines.length; i++) {
    if (!startRe.test(lines[i])) continue;
    // Character files write beats as "109 - He ..." (dash + capital), the same shape as a section
    // header, so the punctuation test is not enough there: under Characters/ every block is a beat.
    const structural = !beatEndRe || (!forceBeat && STRUCT_RE.test(lines[i]));
    const stop = structural ? endRe : beatEndRe;
    let j = i + 1;
    // Google Docs export one paragraph per line and the character files have no blank lines, so a
    // beat is exactly its own paragraph; only structural sections run on to the next marker.
    if (structural) while (j < lines.length && !stop.test(lines[j])) j++;
    const cap = maxLinesPerBlock || 100000;
    blocks.push({ kind: structural ? "section" : "beat", from_line: i + 1, to_line: j, truncated: j - i > cap, text: lines.slice(i, Math.min(j, i + cap)).join("\n") });
    i = j - 1;
  }
  return blocks;
}

server.tool(
  "canon_section",
  "Read ONE section of a long document instead of the whole thing (a Master is ~165K chars; one episode section is ~10K). start = text or regex matched at the beginning of a line (e.g. 'SECTION 5G', '109 -', 'EPISODE 201', 'PART THREE'); the section runs to the next section marker (SECTION / PART / EPISODE / 'nnn -' / SnEnn) or to end= if given. Use canon_outline_text first if unsure of the markers.",
  {
    file: z.string().describe("Path, Drive id, Drive name or unique fragment (e.g. 'SEASON ONE - THE SANCTUARY - MASTER')"),
    start: z.string().describe("Line-start text or regex that opens the section, e.g. 'SECTION 5G' or '^109'"),
    end: z.string().optional().describe("Optional regex for the line that closes the section (exclusive). Default: the next section marker"),
    regex: z.boolean().optional().describe("Treat start/end as regex (default: literal, anchored to line start, case-insensitive)"),
    max_lines: z.number().optional().describe("Cap per block (default 1500)"),
  },
  async ({ file, start, end, regex, max_lines }) => {
    try {
      const r = chooseOne(file);
      const text = readText(safeAbs(r.path));
      const lines = text.split(/\r?\n/);
      // A bare episode number ("108", "S1E08") means the EPISODE: match every marker form
      // ("SECTION 5F - EPISODE 108 - ...", "108 - \"TITLE\"", "EPISODE 108") and put the act-broken
      // structural section first, superseded stubs after (Proctor's Test B hit the stubs with start="108").
      let epi = null;
      try {
        if (!regex && /^(S?[1-4]\s*[EX]\s*\d{1,2}|[1-4]\d{2})$/i.test(String(start).trim())) epi = normalizeEpisode(start);
      } catch (e) {
        epi = null;
      }
      const startRe = epi ? episodeStartRe(epi) : new RegExp("^\\s*" + (regex ? start : esc(start)), "i");
      const endRe = end ? new RegExp(regex ? end : "^\\s*" + esc(end), "i") : MARKER_RE;
      let blocks = sliceBlocks(lines, startRe, endRe, max_lines || 1500, epi ? BEAT_END_RE : null);
      if (epi) blocks.sort((a, b) => (b.kind === "section") - (a.kind === "section") || b.text.length - a.text.length);
      if (!blocks.length) throw new Error("no line in " + r.path + " starts with '" + start + "'. Try canon_outline_text to see the markers.");
      return ok({ file: describe(r), total_lines: lines.length, episode: epi ? epi.code : null, blocks_found: blocks.length, blocks });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_outline_text",
  "The section markers of a document that has no markdown headings (Masters, State compilations, Episode Map): every line that starts with SECTION / PART / EPISODE / 'nnn -' / SnEnn, with line numbers. Use it to pick a start= for canon_section.",
  { file: z.string().describe("Path, Drive id, Drive name or unique fragment") },
  async ({ file }) => {
    try {
      const r = chooseOne(file);
      const lines = readText(safeAbs(r.path)).split(/\r?\n/);
      const markers = [];
      for (let i = 0; i < lines.length; i++) if (MARKER_RE.test(lines[i])) markers.push({ line: i + 1, text: lines[i].slice(0, 160) });
      return ok({ file: describe(r), total_lines: lines.length, markers });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_episode",
  "EVERYTHING the corpus holds about one episode, verbatim, in one call - the way to load an episode into a session without reading three Masters and three State compilations. Returns: the episode's blocks from every live doc that has a section for it (Episode Map entry, Master section, State compilation acts, amended blocks), every 00-series ruling line that names it, and a ranked list of other docs that mention it (character files etc.) for follow-up with canon_read. Retrieval, not a summary.",
  {
    episode: z.string().describe("108, S1E08 or 1x08"),
    max_lines_per_block: z.number().optional().describe("Cap per block (default 1200)"),
    include_mentions: z.boolean().optional().describe("Default true: list other live docs mentioning the episode with counts"),
  },
  async ({ episode, max_lines_per_block, include_mentions }) => {
    try {
      const epi = normalizeEpisode(episode);
      const startRe = episodeStartRe(epi);
      const ix = index();
      const docs = ix.records.filter((r) => r.live && canonicalText(r) && r.ext === ".txt");
      const blocks = [];
      const rulings = [];
      const mentions = [];
      const mentionRe = new RegExp("(^|[^0-9])" + epi.number + "([^0-9]|$)|\\b" + epi.code + "\\b", "i");
      let totalChars = 0;
      for (const r of docs) {
        let text;
        try {
          text = readText(safeAbs(r.path));
        } catch (e) {
          continue;
        }
        const lines = text.split(/\r?\n/);
        const beatOnly = /\/Characters\//i.test(r.path) || /CHARACTER (FILE|SKETCH|PROFILE)/i.test(r.base);
        const found = sliceBlocks(lines, startRe, MARKER_RE, max_lines_per_block || 1200, BEAT_END_RE, beatOnly);
        const isRuling = /^canon\/00[A-Z]\b/i.test(r.path) || /AUTHOR RULINGS|CANON AMENDMENTS/i.test(r.base);
        if (found.length && !isRuling) {
          for (const b of found) {
            totalChars += b.text.length;
            blocks.push(Object.assign({ file: r.path, drive_id: r.drive_id, drive_name: r.drive_name, modified: r.modified }, b));
          }
          continue;
        }
        let count = 0;
        const hits = [];
        for (let i = 0; i < lines.length; i++) {
          if (mentionRe.test(lines[i])) {
            count++;
            if (isRuling && hits.length < 40) hits.push({ line: i + 1, text: lines[i].slice(0, 600) });
          }
        }
        if (!count) continue;
        if (isRuling) rulings.push({ file: r.path, drive_id: r.drive_id, match_count: count, lines: hits });
        else if (include_mentions !== false) mentions.push({ file: r.path, drive_id: r.drive_id, drive_name: r.drive_name, match_count: count });
      }
      blocks.sort((a, b) => (/EPISODE MAP/i.test(b.file) - /EPISODE MAP/i.test(a.file)) || (/MASTER/i.test(b.file) - /MASTER/i.test(a.file)) || a.file.localeCompare(b.file));
      rulings.sort((a, b) => a.file.localeCompare(b.file));
      mentions.sort((a, b) => b.match_count - a.match_count);
      return ok({
        episode: epi.code + " (" + epi.number + ")",
        blocks_found: blocks.length,
        total_block_chars: totalChars,
        blocks,
        rulings_mentioning: rulings,
        other_docs_mentioning: mentions.slice(0, 40),
        note: "Blocks are verbatim canon text. Rulings override older episode text (the 00-series is newest-wins). For character detail, canon_read the top other_docs_mentioning in full.",
      });
    } catch (e) {
      return fail(e);
    }
  }
);

// ---------------------------------------------------------------------------
// RULINGS INDEX - every R-number in the 00-series, parsed from the author's own heading form
// ("R-110 - TITLE. [A - 16 Aug]"), with the supersession chain and the open items.
// ---------------------------------------------------------------------------

const MONTHS = { JANUARY: 1, FEBRUARY: 2, MARCH: 3, APRIL: 4, MAY: 5, JUNE: 6, JULY: 7, AUGUST: 8, SEPTEMBER: 9, OCTOBER: 10, NOVEMBER: 11, DECEMBER: 12 };
function pad2(n) {
  return String(n).padStart(2, "0");
}
const DATE_RANGE_RE = new RegExp("(\\d{1,2})(?:\\s*" + DASH + "\\s*\\d{1,2})?\\s+([A-Z]+)\\s+(\\d{4})", "i");
function parseDocDate(name) {
  let m = /(\d{4})-(\d{2})-(\d{2})/.exec(name);
  if (m) return m[1] + "-" + m[2] + "-" + m[3];
  m = DATE_RANGE_RE.exec(name);
  if (m && MONTHS[m[2].toUpperCase()]) return m[3] + "-" + pad2(MONTHS[m[2].toUpperCase()]) + "-" + pad2(m[1]);
  return null;
}
const RULING_HEAD_RE = new RegExp("^\\s*R-(\\d+)\\s*((?:REFINED|AMENDED|RESTATED|ADDENDUM|CLARIFIED)[A-Z]*)?\\s*(?:" + DASH + "|\\.|:)?\\s*(.*)$");
const RULING_END_RE = /^\s*(END OF 00|RIPPLE LIST|FOLDED \d|OPEN ITEMS?\b|OPEN QUESTIONS?\b)/i;
const REL_WORD = "(supersed\\w*|refine[sd]?|replace[sd]?|restate[sd]?|reopen\\w*|re-?open\\w*|close[sd]?|carr(?:ied|ies)|amend\\w*|extend\\w*|confirm\\w*|reassert\\w*|corrected|dead|retired|moot|withdrawn|overrid\\w*)";
const REL_FWD = new RegExp("\\b" + REL_WORD + "\\b[^.;\\n]{0,90}?\\bR-(\\d+)\\b", "gi");
const REL_BACK = new RegExp("\\bR-(\\d+)\\b[^.;\\n]{0,90}?\\b" + REL_WORD + "\\b", "gi");
const OPEN_CODE_RE = /\b(S[1-4]-O-\d+|O-\d+)\b/g;

let RULINGS = null;
let RULINGS_AT = 0;

function rulingsIndex() {
  const ix = index();
  if (RULINGS && RULINGS_AT === CACHE_AT) return RULINGS;
  const docs = ix.records.filter((r) => r.ext === ".txt" && r.folder === "canon" && /^00[A-Z]/.test(r.base) && r.live);
  const entries = [];
  const open = [];
  for (const r of docs) {
    let text;
    try {
      text = readText(safeAbs(r.path));
    } catch (e) {
      continue;
    }
    const lines = text.split(/\r?\n/);
    const code = (/^(00[A-Z](?:-ADD)?)/.exec(r.base) || [null, "00?"])[1];
    const date = parseDocDate(r.drive_name || r.base) || parseDocDate(lines[0] || "") || null;
    const banner = lines.slice(0, 8).map((l) => (/\[SUPERSEDED[^\]]*\]/i.exec(l) || [null])[0]).filter(Boolean)[0] || null;
    // rulings
    for (let i = 0; i < lines.length; i++) {
      const h = RULING_HEAD_RE.exec(lines[i]);
      if (!h) continue;
      let j = i + 1;
      let blanks = 0;
      while (j < lines.length && j - i < 120) {
        if (RULING_HEAD_RE.test(lines[j]) || RULING_END_RE.test(lines[j])) break;
        if (!lines[j].trim()) {
          blanks++;
          if (blanks >= 2) break;
        } else blanks = 0;
        j++;
      }
      const body = lines.slice(i, j).join("\n").trim();
      const mentions = new Set();
      let m;
      const mentionRe = /\bR-(\d+)\b/g;
      while ((m = mentionRe.exec(body))) if (+m[1] !== +h[1]) mentions.add("R-" + m[1]);
      const relations = [];
      REL_FWD.lastIndex = 0;
      while ((m = REL_FWD.exec(body))) if (+m[2] !== +h[1]) relations.push({ word: m[1].toLowerCase(), target: "R-" + m[2] });
      REL_BACK.lastIndex = 0;
      while ((m = REL_BACK.exec(body))) if (+m[1] !== +h[1]) relations.push({ word: m[2].toLowerCase(), target: "R-" + m[1] });
      const inlineNote = (/\[(SUPERSEDED|ANSWERED|CLOSED|RETIRED|DEAD)[^\]]{0,800}\]/i.exec(body) || [null])[0];
      if (inlineNote) {
        // a bracketed supersession note names what replaced it: that is a relation too
        const noteRe = /\bR-(\d+)\b/g;
        let nm;
        while ((nm = noteRe.exec(inlineNote))) if (+nm[1] !== +h[1]) relations.push({ word: "superseded-by (note)", target: "R-" + nm[1] });
      }
      entries.push({
        id: "R-" + h[1],
        num: +h[1],
        variant: h[2] ? h[2].trim() : null,
        title: (h[3] || "").replace(/\s+/g, " ").trim().slice(0, 220),
        doc: r.path,
        doc_code: code,
        drive_id: r.drive_id,
        date,
        line: i + 1,
        text: body,
        mentions: [...mentions],
        relations,
        inline_note: inlineNote,
        doc_banner: banner,
      });
      i = j - 1;
    }
    // open items: numbered lines under an OPEN ITEMS / OPEN QUESTIONS heading, plus any [?] line, plus O-codes
    let inOpen = false;
    for (let i = 0; i < lines.length; i++) {
      const l = lines[i];
      if (/^\s*(OPEN ITEMS?|OPEN QUESTIONS?)\b/i.test(l)) {
        inOpen = true;
        continue;
      }
      if (inOpen && (RULING_HEAD_RE.test(l) || /^\s*(RIPPLE LIST|END OF 00|FOLDED)/i.test(l))) inOpen = false;
      const numbered = inOpen && /^\s*\d+\.\s+\S/.test(l);
      const flagged = /\[\?\]/.test(l);
      const codes = [];
      let m;
      OPEN_CODE_RE.lastIndex = 0;
      while ((m = OPEN_CODE_RE.exec(l))) codes.push(m[1]);
      if (!numbered && !flagged && !codes.length) continue;
      if (!numbered && !flagged && codes.length && !/\b(open|pending|need|unruled|\[\?\])/i.test(l)) continue; // a code merely cited
      const answered = /\[(ANSWERED|CLOSED|RESOLVED)\b|\bCLOSED\b\s*[\[(:]|\bANSWERED\b/i.test(l);
      open.push({ doc: r.path, doc_code: code, date, line: i + 1, codes, answered, text: l.trim().slice(0, 500) });
    }
  }
  const byDate = (a, b) => String(b.date || "").localeCompare(String(a.date || "")) || b.doc_code.localeCompare(a.doc_code) || b.line - a.line;
  entries.sort(byDate);
  open.sort(byDate);
  const byId = new Map();
  for (const e of entries) {
    if (!byId.has(e.id)) byId.set(e.id, []);
    byId.get(e.id).push(e);
  }
  RULINGS = { entries, byId, open, docs: docs.map((d) => ({ path: d.path, date: parseDocDate(d.drive_name || d.base) })) };
  RULINGS_AT = CACHE_AT;
  return RULINGS;
}

function normalizeRulingId(s) {
  const m = /(\d+)/.exec(String(s));
  if (!m) throw new Error("ruling id must contain a number, e.g. R-68");
  return "R-" + +m[1];
}

function rulingView(e, withText) {
  return {
    id: e.id + (e.variant ? " " + e.variant : ""),
    title: e.title,
    doc: e.doc,
    doc_code: e.doc_code,
    date: e.date,
    line: e.line,
    drive_id: e.drive_id,
    inline_note: e.inline_note,
    doc_banner: e.doc_banner,
    relations: e.relations,
    mentions: e.mentions,
    text: withText ? e.text : undefined,
  };
}

server.tool(
  "canon_ruling",
  "One ruling by number (R-68, '68'): its text, where it lives (doc, line, date), every variant (e.g. R-95 and R-95 REFINED), what it touches, and the CHAIN - every later ruling that supersedes / refines / closes / mentions it, newest first. Read this before relying on any ruling: the 00-series is newest-wins.",
  { id: z.string().describe("R-68, 'R 68', '68'") },
  async ({ id }) => {
    try {
      const rid = normalizeRulingId(id);
      const rx = rulingsIndex();
      const entries = rx.byId.get(rid) || [];
      if (!entries.length) throw new Error(rid + " not found as a heading in any live 00-series doc (" + rx.entries.length + " rulings indexed). Try canon_rulings query=...");
      const later = [];
      for (const e of rx.entries) {
        if (e.id === rid) continue;
        const rel = e.relations.filter((x) => x.target === rid).map((x) => x.word);
        if (rel.length || e.mentions.includes(rid)) later.push(Object.assign({ how: rel.length ? rel : ["mentions"] }, rulingView(e, false)));
      }
      const newest = entries[0];
      const superseding = later.filter((x) => x.how.some((w) => /supersed|replace|retired|dead|moot|overrid|corrected|withdrawn/.test(w)) && String(x.date || "") >= String(newest.date || ""));
      const byNote = [...new Set(entries.flatMap((e) => e.relations.filter((x) => /superseded-by/.test(x.word)).map((x) => x.target)))];
      const status = byNote.length
        ? "SUPERSEDED by " + byNote.join(", ") + " (per the note on the ruling): " + String(newest.inline_note || "").slice(0, 240)
        : superseding.length
          ? "SUPERSEDED or amended by " + superseding.map((x) => x.id).join(", ") + " (see chain)"
          : newest.inline_note || newest.doc_banner
            ? "carries a note: " + String(newest.inline_note || newest.doc_banner).slice(0, 240)
            : "no later ruling supersedes it by name";
      return ok({
        id: rid,
        status,
        superseded_by: byNote.concat(superseding.map((x) => x.id.split(" ")[0])).filter((v, i, a) => a.indexOf(v) === i),
        entries: entries.map((e) => rulingView(e, true)),
        chain_later: later,
        touches: newest.relations,
        note: "Newest-wins: if chain_later names a superseding ruling, canon_ruling that id next.",
      });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_rulings",
  "Search the rulings index: every R-number in the 00-series, newest first. Filters: query (text in title/body), episode (108 / S2E07: rulings whose text names it), entity (a name), since (YYYY-MM-DD). open_only=true lists the OPEN ITEMS / [?] questions instead, with answered/unanswered. Coverage is reported so a ruling written outside the R-nnn heading form is never silently missed.",
  {
    query: z.string().optional(),
    episode: z.string().optional().describe("108, S1E08 or 1x08"),
    entity: z.string().optional().describe("Character / object name, matched case-insensitively in the ruling text"),
    since: z.string().optional().describe("YYYY-MM-DD"),
    open_only: z.boolean().optional(),
    with_text: z.boolean().optional().describe("Include the full ruling text (default false: heading + where)"),
    limit: z.number().optional().describe("Default 40"),
  },
  async ({ query, episode, entity, since, open_only, with_text, limit }) => {
    try {
      const rx = rulingsIndex();
      const lim = limit || 40;
      if (open_only) {
        let items = rx.open;
        if (query) items = items.filter((o) => fold(o.text).includes(fold(query)));
        if (since) items = items.filter((o) => String(o.date || "") >= since);
        return ok({ total_open_items: items.length, unanswered: items.filter((o) => !o.answered).length, items: items.slice(0, lim) });
      }
      let list = rx.entries;
      if (query) list = list.filter((e) => fold(e.title + " " + e.text).includes(fold(query)));
      if (entity) list = list.filter((e) => fold(e.text).includes(fold(entity)));
      if (episode) {
        const epi = normalizeEpisode(episode);
        const re = new RegExp("(^|[^0-9])" + epi.number + "([^0-9]|$)|\\b" + epi.code + "\\b|\\bE" + String(epi.number % 100).padStart(2, "0") + "\\b");
        list = list.filter((e) => re.test(e.text));
      }
      if (since) list = list.filter((e) => String(e.date || "") >= since);
      return ok({
        coverage: { rulings_indexed: rx.entries.length, distinct_ids: rx.byId.size, docs: rx.docs.length, open_items: rx.open.length },
        total: list.length,
        rulings: list.slice(0, lim).map((e) => rulingView(e, !!with_text)),
      });
    } catch (e) {
      return fail(e);
    }
  }
);

// ---------------------------------------------------------------------------
// CONTRADICTION FINDER - for one entity, every concrete claim the live corpus makes, grouped by
// fact, conflicting values side by side. CANDIDATES for the author to adjudicate, never verdicts.
// This is the mechanical form of the Hengist sweep (398 lines read by hand on 4 Sept 2026).
// ---------------------------------------------------------------------------

const COLOR_WORDS = "gold|golden|purple|silver|orange|yellow|black|red|blue|green|white|brown|grey|gray|bay|chestnut";
const SEASON_SPAN = "S[1-4](?:" + DASH + "S[1-4])?";
const CLAIM_RULES = [
  { fact: "born (year)", re: /\bborn\s+(?:c\.?\s*|~\s*|about\s*|circa\s*)?(\d{3})\b/gi, value: (m) => m[1] },
  { fact: "age at a point", re: /\b(\d{1,2})\s+(?:at|by)\s+(?:the\s+)?((?:S?[1-4]E\d{2}|E\d{1,2}|\d{3})\b|Badon|the supper|the pilot|the catastrophe|E1\b|101\b)/gi, value: (m) => m[1] + " at " + m[2] },
  { fact: "age stated", re: /\b(?:aged?|is|now)\s+(\d{2})\b(?=[\s,.;)]|$)(?![\d-])/gi, value: (m) => m[1], guard: (s) => /\b(age|aged|years? old|old)\b/i.test(s) },
  { fact: "dies / falls (episode)", re: /\b(?:dies|died|death|falls|fell|killed|is killed|slain)\b[^.;]{0,50}?\b(?:at|in|by)?\s*((?:S[1-4]E\d{2})|[1-4]\d{2})\b/gi, value: (m) => m[1] },
  { fact: "killed by (who)", re: /\b(?:killed by|dies at|slain by)\s+([A-Z][a-z]+)(?:'s hand)?\b/g, value: (m) => m[1] },
  { fact: "kills (who)", re: /\b([A-Z][A-Za-z]+)\s+kills\s+([A-Z][A-Za-z]+)\b/g, value: (m) => m[1] + " kills " + m[2] },
  { fact: "survives", re: new RegExp("\\bsurviv(?:es|ed|al)\\b[^.;]{0,40}?\\b(" + SEASON_SPAN + "|the series|Season (?:One|Two|Three)|\\d{3})\\b", "gi"), value: (m) => m[1] },
  { fact: "sword / spatha", re: new RegExp("\\b(spatha|sword|blade)\\b[^.;]{0,70}?\\b(lost|recovered|never (?:seen|recovered|shown)|in the cairn|cairn|kept|carries|redwood|bronze|brass|gold-hilted|golden|standard|Commander's Sword)\\b", "gi"), value: (m) => m[2].toLowerCase() },
  { fact: "seat color / draco color", re: new RegExp("\\b(" + COLOR_WORDS + ")\\b[^.;]{0,40}?\\b(draco|windsock|pauldron|seat|colou?r)\\b", "gi"), value: (m) => m[1].toLowerCase() },
  { fact: "horse", re: new RegExp("\\b(" + COLOR_WORDS + "|arabian|stallion|mare|gelding)\\b[^.;]{0,30}?\\b(horse|mare|stallion|arabian|gelding)\\b", "gi"), value: (m) => (m[1] + " " + m[2]).toLowerCase() },
  { fact: "column / slot", re: /\b(?:slot|position|rides(?: at)?|takes)\s*\(?([a-h]|X)\)?\b(?=[\s,.;)])/g, value: (m) => m[1] },
  { fact: "seat number", re: /\bSeat\s+(\d{1,2})\b/gi, value: (m) => "Seat " + m[1] },
  { fact: "rank on the ladder", re: /\B#(\d)\b/g, value: (m) => "#" + m[1], guard: (s) => /\b(ladder|antagonist|bench|rank)\b/i.test(s) },
  { fact: "location / seat of power", re: /\b(?:in|at|from|of)\s+(Kent|Glevum|Londinium|London|Corinium|Aquae Sulis|Afallon|Badon|Taron|Armenia|Persia|the Sanctuary|the Castra)\b/g, value: (m) => m[1], profile: true },
  // years are keyed by the event word next to them ("catastrophe 460", "Badon 490", "closed 435"), so different
  // events never collide as one fact; a bare year with no event word is profile-only
  { fact: "year", re: /\b(catastrophe|Badon|closed|closure|born|Aylesford|Crecganford|Deorham|Dyrham|Aesc|Kent|A\.?D\.?)\b[^.;]{0,25}?\b(4[0-9]{2}|5[0-7][0-9])\b|\b(4[0-9]{2}|5[0-7][0-9])\b[^.;]{0,12}?\b(catastrophe|Badon|closure|Aylesford|Crecganford)\b/gi, value: (m) => { const kw = (m[1] || m[4]).toLowerCase(); return (/^a\.?d\.?$/.test(kw) ? "a.d." : kw) + " " + (m[2] || m[3]); }, keyed: true },
];
// A claim is attributed to the entity only when the entity's name sits within this many characters BEFORE the
// match (or the match is the sentence's first clause): stops "Hengist's field warlord Wipped dies at 110" from
// being filed under Hengist.
const PROXIMITY = 90;
// tighter windows for facts that travel in lists ("Felix silver, Ambrosius purple, Gallus green")
const NEAR_BY_FACT = { "seat color / draco color": 35, "column / slot": 35, horse: 45, "seat number": 35 };
function nearEntity(sentence, matchIndex, nameRe, fact) {
  const span = NEAR_BY_FACT[fact] || PROXIMITY;
  const before = sentence.slice(Math.max(0, matchIndex - span), matchIndex);
  if (nameRe.test(fold(before))) return true;
  // name after the match inside a short clause ("dies at 110, Hengist ...") - allow 40 chars
  const after = sentence.slice(matchIndex, matchIndex + 40);
  return nameRe.test(fold(after)) && !/\b(and|with|by|under)\b/i.test(after.slice(0, 12));
}

const SENTENCE_SPLIT_RE = new RegExp("(?<=[.!?])\\s+(?=[A-Z\"\\u201c(\\[])");
function splitSentences(line) {
  return line.split(SENTENCE_SPLIT_RE).map((s) => s.trim()).filter((s) => s.length > 15);
}

server.tool(
  "canon_claims",
  "CONTRADICTION FINDER for one entity (character, object, place). Pulls every live sentence that names it, extracts concrete claims (birth year, ages, death episode, killer, survival, sword, colors, horse, slot, seat, ladder rank, places, years), groups them by fact, and puts CONFLICTING VALUES side by side with document + line + the newest ruling that names the entity and the value. Also lists single-source claims (where stragglers hide). Candidates for the author to adjudicate - never verdicts. Aliases widen the net (e.g. Ambrosius + Uthr).",
  {
    entity: z.string().describe("e.g. 'Valerius', 'Hengist', 'Commander's Sword'"),
    aliases: z.array(z.string()).optional().describe("Other names for the same entity"),
    live_only: z.boolean().optional().describe("Default true"),
    include_rulings: z.boolean().optional().describe("Default true: include the 00-series docs as sources (their dead-material lines will show as minority values - that is expected)"),
    max_examples: z.number().optional().describe("Sentences shown per value (default 4)"),
  },
  async ({ entity, aliases, live_only, include_rulings, max_examples }) => {
    try {
      const names = [entity].concat(aliases || []).map(fold).filter(Boolean);
      const nameRe = new RegExp("\\b(" + names.map(esc).join("|") + ")", "i");
      const files = scopeFiles({ scope: "canonical", live_only, ext: "txt" }).filter((r) => include_rulings !== false || !/^canon\/00[A-Z]/.test(r.path));
      const facts = new Map(); // fact -> Map(value -> {count, docs:Set, examples:[]})
      let sentencesScanned = 0;
      const perDoc = new Map();
      for (const r of files) {
        let text;
        try {
          text = readText(safeAbs(r.path));
        } catch (e) {
          continue;
        }
        if (!nameRe.test(fold(text))) continue;
        const lines = text.split(/\r?\n/);
        for (let i = 0; i < lines.length; i++) {
          if (!nameRe.test(fold(lines[i]))) continue;
          for (const s of splitSentences(lines[i])) {
            if (!nameRe.test(fold(s))) continue;
            sentencesScanned++;
            perDoc.set(r.path, (perDoc.get(r.path) || 0) + 1);
            for (const rule of CLAIM_RULES) {
              if (rule.guard && !rule.guard(s)) continue;
              rule.re.lastIndex = 0;
              let m;
              while ((m = rule.re.exec(s))) {
                const v = rule.value(m);
                if (!v) continue;
                if (!rule.profile && !nearEntity(s, m.index, nameRe, rule.fact)) continue;
                if (rule.fact === "kills (who)" && !nameRe.test(fold(v))) continue;
                if (!facts.has(rule.fact)) facts.set(rule.fact, new Map());
                const fm = facts.get(rule.fact);
                if (!fm.has(v)) fm.set(v, { count: 0, docs: new Set(), examples: [] });
                const slot = fm.get(v);
                slot.count++;
                slot.docs.add(r.path);
                if (slot.examples.length < (max_examples || 4)) slot.examples.push({ doc: r.path, line: i + 1, sentence: s.slice(0, 300) });
              }
            }
          }
        }
      }
      const rx = rulingsIndex();
      const newestRulingFor = (value) => {
        const e = rx.entries.find((x) => nameRe.test(fold(x.text)) && fold(x.text).includes(fold(String(value))));
        return e ? { id: e.id + (e.variant ? " " + e.variant : ""), date: e.date, doc_code: e.doc_code, line: e.line } : null;
      };
      const PROFILE_FACTS = new Set(CLAIM_RULES.filter((x) => x.profile).map((x) => x.fact));
      const conflicts = [];
      const profile = [];
      const single = [];
      for (const [fact, fm] of facts) {
        const values = [...fm.entries()].map(([value, d]) => ({ value, count: d.count, docs: d.docs.size, newest_ruling: newestRulingFor(value), examples: d.examples })).sort((a, b) => b.count - a.count);
        if (PROFILE_FACTS.has(fact)) {
          profile.push({ fact, values: values.map((v) => ({ value: v.value, count: v.count, docs: v.docs })) });
          continue;
        }
        if (values.length > 1) conflicts.push({ fact, values, minority: values.slice(1).map((v) => v.value) });
        for (const v of values) if (v.docs === 1) single.push({ fact, value: v.value, doc: [...fm.get(v.value).docs][0], example: v.examples[0] });
      }
      conflicts.sort((a, b) => b.values.length - a.values.length);
      return ok({
        entity,
        aliases: aliases || [],
        sentences_scanned: sentencesScanned,
        docs_with_mentions: perDoc.size,
        conflicting_facts: conflicts.length,
        conflicts,
        profile,
        single_source_claims: single.slice(0, 60),
        newest_rulings_naming_entity: rx.entries.filter((e) => nameRe.test(fold(e.text))).slice(0, 12).map((e) => rulingView(e, false)),
        note: "Heuristic extraction: values are grouped by regex, so a minority value can be a dead-material record ('DEAD: ...', 'was ...') rather than a live contradiction. Read the examples; the newest ruling column says what governs.",
      });
    } catch (e) {
      return fail(e);
    }
  }
);

// ---------------------------------------------------------------------------
// FOLD - the "fold this into the corpus" trigger. Ordinary gdrive-ops edits do NOT pull;
// the fold does: pull + re-embed + the list of Docs that changed.
// ---------------------------------------------------------------------------

server.tool(
  "canon_fold",
  "THE FOLD. Call this once when Silas says 'fold this into the corpus' (after the Drive edits are made with gdrive-ops): pulls Drive -> mirror -> GitHub, re-embeds what changed, and reports exactly which Docs changed. Do NOT call it after every edit. Background: returns when finished or after wait_seconds; if status is 'running', call again with status=true.",
  {
    status: z.boolean().optional().describe("true = report the current/last fold, start nothing"),
    wait_seconds: z.number().optional().describe("Default 50, max 55"),
  },
  async ({ status, wait_seconds }) => {
    try {
      const wait = Math.min(55, Math.max(0, wait_seconds == null ? 50 : wait_seconds)) * 1000;
      let job = PULL_JOB;
      if (status) {
        if (!job) return ok({ status: "idle", note: "no fold has run in this session" });
      } else {
        if (job && job.status === "running") return ok(Object.assign({ note: "a pull is already running; not starting another" }, jobView(job)));
        job = startPull(false, false);
      }
      if (job.status === "running" && wait > 0) await Promise.race([job.promise, new Promise((res) => setTimeout(res, wait))]);
      const view = jobView(job);
      if (job.status === "done") {
        let changed = [];
        let commit = null;
        if (!/nothing to commit/i.test(job.output)) {
          try {
            commit = (await git(["log", "-1", "--format=%h %s"])).trim();
            const diff = await git(["diff", "--name-status", "HEAD~1", "HEAD"]);
            const ix = index();
            changed = diff.split(/\r?\n/).filter(Boolean).map((l) => {
              const parts = l.split("\t");
              const st = parts[0];
              const p = parts[parts.length - 1];
              const rec = ix.byPath.get(p);
              return { status: st, path: p, drive_name: rec ? rec.drive_name : null, drive_id: rec ? rec.drive_id : null };
            }).filter((c) => /\.txt$/.test(c.path) || !/\.md$/.test(c.path));
          } catch (e) {
            changed = [{ error: String(e.message || e).slice(0, 200) }];
          }
        }
        return ok(Object.assign(view, { fold: "complete", commit, changed_docs: changed, docs_changed: changed.length, next: "The mirror is current. Any open canon_read pages from before the fold are stale." }));
      }
      return ok(Object.assign(view, { fold: job.status, next: job.status === "running" ? "call canon_fold status=true" : "see log_tail" }));
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
      // keep the semantic index in step with the mirror (background; reported via canon_embed status=true)
      if (!dry_run && qmdBin() && !/nothing to commit/i.test(job.output)) job.embed = startEmbed(false);
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
    semantic_reindex: job.embed ? embedView(job.embed) : job.dry_run ? "skipped (dry run)" : qmdBin() ? "pending" : "QMD not installed",
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
  "canon_semantic",
  "MEANING-based search over the whole corpus (QMD: BM25 + vector embeddings + LLM reranking, all local). Ask in plain language - 'scenes where a rider defies an order', 'why Valerius distrusts Mardin' - no exact words needed. mode=hybrid (default, best), vector (pure similarity), keyword (BM25 only, instant). Returns ranked passages with file, line, snippet and Drive id; then canon_read the doc for the full text. Complements canon_grep (exact) and canon_topic (mention counts).",
  {
    query: z.string().describe("Natural-language question or description. Advanced: a multi-line typed query, e.g. 'lex: Commander's Sword\\nvec: who carries the golden sword'"),
    mode: z.enum(["hybrid", "vector", "keyword"]).optional().describe("hybrid (default: keywords + meaning fused) | vector (meaning only) | keyword (BM25 only, instant, exact terms)"),
    limit: z.number().optional().describe("Max results (default 10, max 40)"),
    keywords: z.string().optional().describe("hybrid only: the exact-term half of the query (names, objects). Default: the query itself"),
    hypothesis: z.string().optional().describe("STRONGLY RECOMMENDED for abstract questions: 1-2 sentences guessing what the matching passage would SAY (who, what happens, where). Measured on this corpus: 'a rider defies an order' ranked a false positive first; adding a hypothesis put the right scene first. You do not need to be right, just plausible."),
    include_transcripts: z.boolean().optional().describe("Default false: raw dictation transcripts (THE-LAST-ROMAN-Transcript-*) are dropped from results because their conversational text dominates meaning search and they are superseded by the Masters. true = keep them"),
    expand: z.boolean().optional().describe("hybrid only: let QMD's local LLM rewrite the question into several sub-queries (default false: adds ~15-30 s on this machine)"),
    rerank: z.boolean().optional().describe("hybrid only: LLM reranking of the top candidates (default false: adds ~40 s+ on this machine)"),
    live_only: z.boolean().optional().describe("Default true: drop archives, session logs, historical, Brother's notes"),
    full: z.boolean().optional().describe("true = return the full matching document text instead of a snippet (large)"),
  },
  async ({ query, mode, limit, keywords, hypothesis, include_transcripts, expand, rerank, live_only, full }) => {
    try {
      const n = Math.min(40, Math.max(1, limit || 10));
      const cmd = mode === "vector" ? "vsearch" : mode === "keyword" ? "search" : "query";
      const fetchN = live_only === false && include_transcripts ? n : n * 3;
      const typed = /^(intent|lex|vec|hyde):/m.test(query);
      const one = (s) => String(s).replace(/\r?\n/g, " ").trim();
      // Default hybrid = a typed lex+vec(+hyde) document: skips the expansion model, keeps meaning + exact terms.
      const queryText = cmd === "query" && !typed && !expand
        ? "lex: " + one(keywords || query) + "\nvec: " + one(query) + (hypothesis ? "\nhyde: " + one(hypothesis) : "")
        : query;
      const TRANSCRIPT_RE = /(^|\/)THE-LAST-ROMAN-Transcript-/i;
      let rows;
      if (QMD_WARM && cmd !== "search") {
        const searches = cmd === "vsearch"
          ? [{ type: "vec", query }]
          : typed
            ? query.split(/\r?\n/).map((l) => /^(lex|vec|hyde):\s*(.*)$/.exec(l)).filter(Boolean).map((m) => ({ type: m[1], query: m[2] }))
            : [{ type: "lex", query: one(keywords || query) }, { type: "vec", query: one(query) }].concat(hypothesis ? [{ type: "hyde", query: one(hypothesis) }] : []);
        const data = await qmdQueryWarm(searches, { limit: fetchN, rerank: !!rerank, timeout: 240000 });
        rows = Array.isArray(data) ? data : data.results || data.items || data.hits || [];
      } else {
        const args = [cmd, queryText, "-c", QMD_COLLECTION, "-n", String(fetchN), "--format", "json", "--full-path"];
        if (cmd === "query" && !rerank) args.push("--no-rerank");
        if (cmd === "query" && rerank) args.push("-C", "8");
        if (full) args.push("--full");
        const out = await qmd(args, { timeout: 300000 });
        try {
          rows = JSON.parse(out.slice(out.search(/[[{]/)));
        } catch (e) {
          throw new Error("qmd returned unparseable output: " + out.slice(0, 400));
        }
        if (!Array.isArray(rows)) rows = rows.results || rows.items || [];
      }
      const ix = index();
      const results = [];
      for (const r of rows) {
        const abs = r.file || r.path || "";
        let relPath = null;
        try {
          relPath = rel(path.resolve(abs));
        } catch (e) {}
        const rec = relPath ? ix.byPath.get(relPath) || ix.byPathFold.get(fold(relPath)) : null;
        const live = rec ? rec.live : !NON_LIVE_RE.test(relPath || "");
        if (live_only !== false && !live) continue;
        if (!include_transcripts && TRANSCRIPT_RE.test(relPath || abs)) continue;
        results.push({
          file: relPath || abs,
          live,
          drive_id: rec ? rec.drive_id : null,
          drive_name: rec ? rec.drive_name : null,
          line: r.line != null ? r.line : null,
          score: r.score != null ? r.score : null,
          title: r.title || null,
          snippet: r.snippet || r.text || r.content || null,
        });
        if (results.length >= n) break;
      }
      let note = null;
      if (!results.length) {
        try {
          const st = parseQmdStatus(await qmd(["status"], { timeout: 60000 }));
          if (!st.vectors_embedded && cmd !== "search") note = "No vectors embedded yet - run canon_embed (or wait for the post-pull re-embed). keyword mode works without embeddings.";
        } catch (e) {}
      }
      if (!hypothesis && cmd === "query" && !typed && !expand) note = (note ? note + " " : "") + "Tip: for abstract questions pass hypothesis= (1-2 sentences guessing what the passage says) - it measurably improves ranking on this corpus.";
      return ok({ query, mode: mode || "hybrid", engine: (QMD_WARM && cmd !== "search" ? "qmd warm http " : "qmd ") + cmd, hypothesis: hypothesis || null, transcripts_filtered: !include_transcripts, expand: !!expand, rerank: !!rerank, live_only: live_only !== false, total: results.length, results, note });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "canon_embed",
  "Refresh the semantic index (QMD): re-index changed files and regenerate vector embeddings for the canon collection. Runs automatically after every real canon_pull; call manually if canon_semantic says vectors are missing. Background job: status=true reports progress. force=true re-embeds everything.",
  {
    status: z.boolean().optional().describe("true = report the current/last embed job, start nothing"),
    force: z.boolean().optional().describe("true = re-embed all documents (slow)"),
    wait_seconds: z.number().optional().describe("Wait up to this long before returning 'running' (default 30, max 55)"),
  },
  async ({ status, force, wait_seconds }) => {
    try {
      if (!qmdBin()) throw new Error("QMD is not installed (npm i -g @tobilu/qmd)");
      const wait = Math.min(55, Math.max(0, wait_seconds == null ? 30 : wait_seconds)) * 1000;
      let job = EMBED_JOB;
      if (!status) {
        if (job && job.status === "running") return ok(Object.assign({ note: "an embed is already running" }, embedView(job)));
        job = startEmbed(!!force);
      }
      if (job && job.status === "running" && wait > 0) await Promise.race([job.promise, new Promise((res) => setTimeout(res, wait))]);
      const st = parseQmdStatus(await qmd(["status"], { timeout: 60000 }));
      return ok(Object.assign(embedView(job), { files_indexed: st.files_indexed, vectors_embedded: st.vectors_embedded }));
    } catch (e) {
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
