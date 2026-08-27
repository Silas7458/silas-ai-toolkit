#!/usr/bin/env node
// gdrive-ops MCP server - Google Drive WRITE operations for Claude Desktop.
// Wraps the gws native CLI (Google Workspace CLI, auth via the OS keyring).
// NO permanent delete by design: trash only (30-day recovery).
//
// Prerequisite: gws CLI installed globally (npm i -g @googleworkspace/cli) and
// authenticated to the target Google account (run: gws auth login).
// Override the binary location with env var GDRIVE_OPS_GWS_EXE if needed.
//
// v1.2.0 (S#312 2026-08-13) - built to Proctor's own 5-feature request:
//   Feature 1  docs_insert_text / docs_create        (add text; create a doc WITH a body)
//   Feature 2  match modes on replace                (literal | normalized | regex)
//   Feature 3  docs_get_text / docs_find             (read + locate anchors in-tool)
//   Feature 4  expected_count / dry_run              (safety guard before mutating)
//   Feature 5  docs_replace_batch                    (all edits in ONE batchUpdate)
//
// MEASURED CORRECTION to the request's premise (probed live against scratch Docs, S#312):
//   replaceAllText ALREADY crosses paragraph breaks, ALREADY crosses textRun splits caused
//   by inline formatting, and ALREADY folds straight-vs-curly single AND double quotes.
//   Those were NOT the cause of the silent 0-occurrence failures. The real causes, each
//   verified returning 0:
//     1. SOFT LINE BREAK U+000B (SHIFT+ENTER) where the caller sends "\n". Every reader
//        renders it as a newline, so it is invisible to the caller. Most likely cause of
//        the reported "S1 Master<break>v1.5" failures.
//     2. NON-BREAKING SPACE U+00A0 vs a plain space.
//     3. hyphen "-" vs EN DASH U+2013 / EM DASH U+2014.
//     4. TAB vs space.
//     5. ZERO-WIDTH characters U+200B / U+FEFF / soft hyphen U+00AD inside the match.
//   Hence: quote-folding is kept only to mirror the API, and the normalizer targets the
//   five causes above. On any 0-result the server now NAMES which one it was.
//
// ADDITIVE ONLY: the 9 pre-existing tools keep their exact signatures. docs_replace_text
// takes the ORIGINAL replaceAllText path byte-for-byte unless a new parameter
// (match / expected_count / dry_run) is supplied.

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { execFile } from "node:child_process";
import path from "node:path";
import fs from "node:fs";
import os from "node:os";

const GWS_EXE =
  process.env.GDRIVE_OPS_GWS_EXE ||
  path.join(
    process.env.APPDATA || "",
    "npm", "node_modules", "@googleworkspace", "cli",
    "node_modules", ".bin_real", "gws.exe"
  );

const FOLDER_MIME = "application/vnd.google-apps.folder";
const DOC_MIME = "application/vnd.google-apps.document";
const FILE_FIELDS = "id,name,mimeType,parents,modifiedTime,trashed,webViewLink";

// documents.get on a large doc (the Season One Master is ~148K chars) returns multi-MB JSON.
const BIG_BUFFER = 64 * 1024 * 1024;
const BIG_TIMEOUT = 180000;

function gws(args, opts) {
  const o = opts || {};
  return new Promise((resolve, reject) => {
    execFile(
      GWS_EXE,
      args,
      {
        timeout: o.timeout || 60000,
        maxBuffer: o.maxBuffer || 16 * 1024 * 1024,
        windowsHide: true,
        cwd: o.cwd || undefined, // gws refuses --upload paths outside its cwd: stage there, pass a relative name
      },
      (err, stdout, stderr) => {
        if (err) {
          reject(new Error("gws failed: " + (String(stderr) || err.message).trim()));
          return;
        }
        const text = String(stdout);
        const start = text.search(/[[{]/);
        if (start === -1) {
          resolve({ raw: text.trim() });
          return;
        }
        try {
          resolve(JSON.parse(text.slice(start)));
        } catch (e) {
          reject(new Error("gws returned unparseable output: " + text.slice(0, 500)));
        }
      }
    );
  });
}

function ok(data) {
  return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
}

function fail(e) {
  return { isError: true, content: [{ type: "text", text: "ERROR: " + String((e && e.message) || e) }] };
}

// Escape a value for embedding in a Drive API q string literal.
function qEscape(s) {
  return s.replace(/\\/g, "\\\\").replace(/'/g, "\\'");
}

// ---------------------------------------------------------------------------
// DOC TEXT EXTRACTION
// Build the document's plain text plus a per-character map back to real Docs
// indices, so a match found in the flat text can be mutated with
// deleteContentRange + insertText at coordinates the API accepts.
// ---------------------------------------------------------------------------

function collectRuns(content, out) {
  for (const el of content || []) {
    if (el.paragraph) {
      for (const e of el.paragraph.elements || []) {
        if (e.textRun && typeof e.textRun.content === "string" && e.textRun.content.length) {
          out.push({ start: e.startIndex, text: e.textRun.content });
        }
      }
    } else if (el.table) {
      for (const row of el.table.tableRows || []) {
        for (const cell of row.tableCells || []) collectRuns(cell.content, out);
      }
    } else if (el.tableOfContents) {
      collectRuns(el.tableOfContents.content, out);
    }
  }
}

function extractDoc(doc) {
  const runs = [];
  collectRuns(doc && doc.body && doc.body.content, runs);
  runs.sort((a, b) => a.start - b.start);
  const parts = [];
  const map = [];
  for (const r of runs) {
    parts.push(r.text);
    for (let i = 0; i < r.text.length; i++) map.push(r.start + i);
  }
  return { text: parts.join(""), map, runs };
}

function bodyEndIndex(doc) {
  const content = (doc && doc.body && doc.body.content) || [];
  let end = 1;
  for (const el of content) if (typeof el.endIndex === "number" && el.endIndex > end) end = el.endIndex;
  return end;
}

async function getDoc(documentId) {
  return gws(
    ["docs", "documents", "get", "--params", JSON.stringify({ documentId }), "--format", "json"],
    { timeout: BIG_TIMEOUT, maxBuffer: BIG_BUFFER }
  );
}

// ---------------------------------------------------------------------------
// NORMALIZATION
// ---------------------------------------------------------------------------

// Quote folding mirrors what the Docs API already does natively, so "literal"
// mode via the positional engine behaves the same as replaceAllText.
const QUOTE_FOLD = {
  "\u2018": "'", "\u2019": "'", "\u201A": "'", "\u201B": "'", "\u2032": "'",
  "\u201C": '"', "\u201D": '"', "\u201E": '"', "\u201F": '"', "\u2033": '"',
};
const DASH_FOLD = {
  "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-",
  "\u2014": "-", "\u2015": "-", "\u2212": "-",
};
const DROP_CHARS = new Set(["\u200B", "\u200C", "\u200D", "\uFEFF", "\u00AD"]);
const WS_CHARS = new Set([
  " ", "\t", "\n", "\v", "\f", "\r",
  "\u00A0", "\u2002", "\u2003", "\u2007", "\u2009", "\u202F",
]);

// Produce a folded string alongside per-character source ranges into the raw text.
function buildVariant(text, mode) {
  const chars = [];
  const srcStart = [];
  const srcEnd = [];
  const norm = mode === "normalized";
  let i = 0;
  while (i < text.length) {
    const ch = text[i];
    if (norm && DROP_CHARS.has(ch)) { i++; continue; }
    if (norm && WS_CHARS.has(ch)) {
      let j = i;
      while (j < text.length && (WS_CHARS.has(text[j]) || DROP_CHARS.has(text[j]))) j++;
      chars.push(" "); srcStart.push(i); srcEnd.push(j);
      i = j;
      continue;
    }
    let out = ch;
    if (QUOTE_FOLD[ch]) out = QUOTE_FOLD[ch];
    else if (norm && DASH_FOLD[ch]) out = DASH_FOLD[ch];
    chars.push(out); srcStart.push(i); srcEnd.push(i + 1);
    i++;
  }
  return { s: chars.join(""), srcStart, srcEnd };
}

function rawRangeToMatch(text, map, rawStart, rawEnd) {
  const startIndex = map[rawStart];
  const endIndex = map[rawEnd - 1] + 1;
  // If the doc indices are not contiguous across the match, something that is not
  // text (an inline image, a page break, a footnote marker) sits inside the range.
  // deleteContentRange would destroy it, so such matches are reported and skipped.
  const spansNonText = endIndex - startIndex !== rawEnd - rawStart;
  return {
    rawStart,
    rawEnd,
    startIndex,
    endIndex,
    matchedText: text.slice(rawStart, rawEnd),
    spansNonText,
  };
}

function findMatches(text, map, needle, mode, matchCase) {
  const out = [];
  if (!needle || !needle.length) return out;
  if (mode === "regex") {
    let flags = "g";
    if (matchCase === false) flags += "i";
    let re;
    try {
      re = new RegExp(needle, flags);
    } catch (e) {
      throw new Error("invalid regex: " + e.message);
    }
    let m;
    let guard = 0;
    while ((m = re.exec(text)) !== null) {
      if (guard++ > 10000) break;
      if (m[0].length === 0) { re.lastIndex++; continue; }
      out.push(rawRangeToMatch(text, map, m.index, m.index + m[0].length));
    }
    return out;
  }
  const dv = buildVariant(text, mode);
  const nv = buildVariant(needle, mode);
  let hay = dv.s;
  let ned = nv.s;
  if (matchCase === false) { hay = hay.toLowerCase(); ned = ned.toLowerCase(); }
  if (!ned.length) return out;
  let from = 0;
  let k;
  while ((k = hay.indexOf(ned, from)) !== -1) {
    const rawStart = dv.srcStart[k];
    const rawEnd = dv.srcEnd[k + ned.length - 1];
    out.push(rawRangeToMatch(text, map, rawStart, rawEnd));
    from = k + ned.length;
  }
  return out;
}

function contextFor(text, m, chars) {
  const n = typeof chars === "number" ? chars : 80;
  return {
    before: text.slice(Math.max(0, m.rawStart - n), m.rawStart),
    after: text.slice(m.rawEnd, Math.min(text.length, m.rawEnd + n)),
  };
}

// ---------------------------------------------------------------------------
// DIAGNOSTICS - the point of the whole exercise: never return a bare 0 again.
// ---------------------------------------------------------------------------

const CAUSE_TESTS = [
  {
    id: "soft_line_break",
    explanation:
      "The document uses a SOFT LINE BREAK (SHIFT+ENTER, U+000B) where your search string has a newline. Every reader renders it as a newline so it looks identical. Use match:'normalized', or put a literal U+000B in find_text.",
    fn: (s) => s.replace(/\v/g, "\n"),
  },
  {
    id: "non_breaking_space",
    explanation:
      "The document uses a NON-BREAKING SPACE (U+00A0) where your search string has a normal space. Visually identical. Use match:'normalized'.",
    fn: (s) => s.replace(/\u00A0/g, " "),
  },
  {
    id: "dash_variant",
    explanation:
      "The document uses an EN DASH (U+2013) or EM DASH (U+2014) where your search string has a plain hyphen. Use match:'normalized'.",
    fn: (s) => s.replace(/[\u2010-\u2015\u2212]/g, "-"),
  },
  {
    id: "tab",
    explanation:
      "The document uses a TAB where your search string has spaces. Use match:'normalized'.",
    fn: (s) => s.replace(/\t/g, " "),
  },
  {
    id: "zero_width_char",
    explanation:
      "The document contains a ZERO-WIDTH character (U+200B / U+FEFF / soft hyphen U+00AD) inside the match. Completely invisible. Use match:'normalized'.",
    fn: (s) => s.replace(/[\u200B\u200C\u200D\uFEFF\u00AD]/g, ""),
  },
  {
    id: "whitespace_amount",
    explanation:
      "The document has a different AMOUNT of whitespace than your search string (a double space, or a line break where you typed one space). Use match:'normalized'.",
    fn: (s) => s.replace(/[ \t\n\v\f\r\u00A0]+/g, " "),
  },
];

function countPlain(hay, ned) {
  if (!ned.length) return 0;
  let n = 0;
  let i = 0;
  while ((i = hay.indexOf(ned, i)) !== -1) { n++; i += ned.length; }
  return n;
}

// Longest prefix of the needle that DOES appear, plus what the doc actually has there.
function longestMatchingPrefix(text, needle) {
  let lo = 1;
  let hi = needle.length;
  let best = 0;
  let bestAt = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    const at = text.indexOf(needle.slice(0, mid));
    if (at !== -1) { best = mid; bestAt = at; lo = mid + 1; } else { hi = mid - 1; }
  }
  if (!best) return null;
  return {
    matchedPrefixChars: best,
    matchedPrefix: needle.slice(0, best),
    foundAtCharIndex: bestAt,
    documentContinuesWith: text.slice(bestAt + best, bestAt + best + 40),
    yourSearchContinuesWith: needle.slice(best, best + 40),
  };
}

function diagnose(text, needle, matchCase) {
  const causes = [];
  for (const t of CAUSE_TESTS) {
    const n = countPlain(t.fn(text), t.fn(needle));
    if (n > 0) causes.push({ cause: t.id, wouldMatch: n, explanation: t.explanation });
  }
  const full = buildVariant(text, "normalized").s;
  const fullNeedle = buildVariant(needle, "normalized").s;
  const normalizedWouldMatch = countPlain(full, fullNeedle);
  const out = {
    diagnosis: causes.length
      ? "FOUND, but the literal bytes differ. See causes below."
      : "NOT FOUND by any normalization - the text genuinely differs.",
    causes,
    normalizedWouldMatch,
  };
  if (matchCase !== false) {
    const ci = countPlain(text.toLowerCase(), needle.toLowerCase());
    if (ci > 0 && countPlain(text, needle) === 0) {
      out.causes.push({
        cause: "case_differs",
        wouldMatch: ci,
        explanation: "The text exists but with different capitalization. Pass match_case:false.",
      });
      out.diagnosis = "FOUND, but the literal bytes differ. See causes below.";
    }
  }
  if (!causes.length && !normalizedWouldMatch) {
    const p = longestMatchingPrefix(text, needle);
    if (p) out.nearestPartialMatch = p;
  }
  return out;
}

// ---------------------------------------------------------------------------
// POSITIONAL MUTATION
// ---------------------------------------------------------------------------

// Apply replacements back-to-front in ONE batchUpdate so index shifts from a later
// (higher-index) edit cannot corrupt an earlier (lower-index) one.
async function applyPositional(documentId, ops) {
  const sorted = ops.slice().sort((a, b) => b.startIndex - a.startIndex);
  const requests = [];
  for (const op of sorted) {
    requests.push({ deleteContentRange: { range: { startIndex: op.startIndex, endIndex: op.endIndex } } });
    if (op.replaceText && op.replaceText.length) {
      requests.push({ insertText: { location: { index: op.startIndex }, text: op.replaceText } });
    }
  }
  if (!requests.length) return { applied: 0, requests: 0 };
  await gws(
    [
      "docs", "documents", "batchUpdate",
      "--params", JSON.stringify({ documentId }),
      "--json", JSON.stringify({ requests }),
      "--format", "json",
    ],
    { timeout: BIG_TIMEOUT, maxBuffer: BIG_BUFFER }
  );
  return { applied: sorted.length, requests: requests.length };
}

function overlaps(a, b) {
  return a.startIndex < b.endIndex && b.startIndex < a.endIndex;
}

// ---------------------------------------------------------------------------

const server = new McpServer(
  { name: "gdrive-ops", version: "1.3.0" },
  {
    instructions: [
      "gdrive-ops: full Google Drive FILE-MANAGEMENT (write ops) + GOOGLE DOC READING, WRITING, INSERTING and IN-PLACE EDITING for the connected Google Drive account.",
      "",
      "CAPABILITY NOTE - READ THIS: The built-in Anthropic Google Drive connector is READ + CREATE only (no move, no rename, no delete, no in-place edits). THIS server removes those limits. You CAN now: MOVE files/folders (drive_move), RENAME (drive_rename), CREATE folders (drive_create_folder), TRASH (drive_trash, recoverable 30 days), RESTORE (drive_restore), resolve names to IDs (drive_find, drive_list_folder), CREATE A GOOGLE DOC WITH BODY TEXT (docs_create), READ a doc's full text (docs_get_text), LOCATE exact anchors with character offsets (docs_find), INSERT text at a position or around an anchor (docs_insert_text), REPLACE text in place (docs_replace_text), and apply MANY edits in one atomic revision (docs_replace_batch).",
      "Never tell the user a Drive file operation or a Doc edit is impossible because 'the connector is read-only'. Use these tools instead - do it yourself, do not ask the user to do it by hand.",
      "",
      "NEW IN v1.3.0 (27 Aug 2026) - LARGE FILE UPLOADS AND THE STORY-SHAPE ATLAS: The built-in connector truncates any inline file over ~2 KB, so you could never push a real file into Drive from the sandbox. drive_upload_chunked fixes that: send the file in pieces under 1500 characters (encoding 'text', or 'base64' for binary / byte-exact text), same upload_id each call, and pass final:true with name + parent_id on the last piece. If a file with that name already exists in that folder it is UPDATED IN PLACE (same id, new revision) - so re-uploading atlas_data.json replaces it, never duplicates it. Never tell the user a file is 'too big to upload' - chunk it.",
      "atlas_rebuild runs THE LAST ROMAN Story-Shape Atlas build on Brother's Windows machine: pulls the current atlas_data.json from the Drive folder 'STORY-SHAPE ATLAS - SOURCE' (id 1yfXuxZCS7IR5u87B5_e_OR9FIdxApe0U), regenerates the HTML, verifies every hour holds to two landscape pages, renders the PDF with Chromium and the real fonts, and pushes HTML + PDF back to that folder. Read the returned summary for BUILD OK / SYNC OK or the STOP reason. It only works while Brother's PC is on.",
      "WORKFLOW (add or change an atlas hour): (1) drive_find the folder 'STORY-SHAPE ATLAS - SOURCE' and read the Google Doc '00 - READ ME FIRST - STORY-SHAPE ATLAS' in it. (2) Download atlas_data.json, edit it in your sandbox (one JSON entry per hour; rules in ATLAS-HANDOFF.md section (g)). (3) drive_upload_chunked the edited atlas_data.json into that folder (upload_id 'atlas-json', final name 'atlas_data.json'). (4) atlas_rebuild. (5) Mirror the hour into the Doc 'THE LAST ROMAN - STORY-SHAPE ATLAS - DATA & ANALYSIS' with docs_replace_text / docs_insert_text. You do NOT need Brother for any of these steps unless atlas_rebuild returns a STOP.",
      "",
      "READ AND LOCATE BEFORE YOU EDIT (cheaper than pulling the doc through another connector): docs_get_text returns the body text and accepts offset/length to window a large document; docs_find returns every occurrence of a phrase with its character offset and surrounding context. Use docs_find to confirm an anchor is unique BEFORE replacing on it.",
      "",
      "WHY A REPLACE SILENTLY FINDS NOTHING - measured, not guessed (S#312): the Docs API ALREADY crosses paragraph breaks, ALREADY crosses formatting splits, and ALREADY folds straight-vs-curly quotes, so none of those are the problem. The real causes are invisible characters: a SOFT LINE BREAK (SHIFT+ENTER, U+000B) that every reader shows as a newline; a NON-BREAKING SPACE (U+00A0); an EN or EM DASH where you typed a hyphen; a TAB; or a ZERO-WIDTH character. Pass match:'normalized' and all of those stop mattering. When a replace returns 0 this server now runs a diagnostic and NAMES the cause in the response - read it instead of guessing and retrying.",
      "",
      "MATCH MODES on docs_replace_text / docs_replace_batch / docs_find / docs_insert_text: 'literal' (default, exact, unchanged legacy behavior), 'normalized' (RECOMMENDED for prose anchors - ignores whitespace kind and amount, dash style, quote style, and invisible characters), 'regex' (JavaScript regex over the document text).",
      "",
      "SAFETY: pass expected_count to refuse the edit unless exactly that many matches exist - use it whenever an anchor might not be unique. Pass dry_run:true to see every match with context and change nothing. There is deliberately NO permanent-delete tool: drive_trash only moves to trash (30-day recovery via drive_restore). Every doc edit is revertible through the Doc's revision history.",
      "",
      "WORKFLOW (file ops): (1) drive_find or drive_list_folder to get exact IDs. (2) move/rename/trash. (3) drive_list_folder again to VERIFY.",
      "WORKFLOW (canon-change sweep): (1) docs_search_content to find candidate docs. (2) docs_find (match:'normalized') in each hit to confirm the anchor and its count. (3) docs_replace_batch with expected_count on each edit so the whole doc changes in ONE revision. (4) Report per-doc counts.",
      "",
      "HOUSE RULE: For routine tidying and single-doc swaps the user explicitly requested, just execute and report. For anything bigger - bulk file sweeps, trashing more than a couple of files, restructuring folder trees, or MULTI-DOC replace sweeps - state the exact plan and get the user's explicit approval BEFORE executing.",
    ].join("\n"),
  }
);

// Log every tool call to stderr - surfaces in Claude Desktop's mcp-server-gdrive-ops.log.
// Proves whether a request actually REACHED the server (an unanswered client-side approval
// prompt never arrives here and logs nothing - see S#300 7/27 incident). Zero protocol impact:
// MCP stdio uses stdout; stderr is the designated logging channel.
const _registerTool = server.tool.bind(server);
server.tool = (name, description, shape, handler) =>
  _registerTool(name, description, shape, async (args, extra) => {
    const t0 = Date.now();
    console.error("[gdrive-ops] " + name + " start " + JSON.stringify(args).slice(0, 300));
    try {
      const out = await handler(args, extra);
      console.error("[gdrive-ops] " + name + (out && out.isError ? " ERROR " : " done ") + (Date.now() - t0) + "ms");
      return out;
    } catch (e) {
      console.error("[gdrive-ops] " + name + " THREW " + (Date.now() - t0) + "ms " + String((e && e.message) || e));
      throw e;
    }
  });

const MATCH_ENUM = z.enum(["literal", "normalized", "regex"]);

// =========================== DRIVE FILE OPS (unchanged) ====================

server.tool(
  "drive_find",
  "Search the connected Google Drive for files or folders by name (matches 'name contains'). Returns id, name, mimeType, parents, modifiedTime. Use this to resolve names to file IDs before move/rename/trash operations.",
  {
    query: z.string().describe("Name text to search for"),
    only_folders: z.boolean().optional().describe("If true, return only folders"),
  },
  async ({ query, only_folders }) => {
    try {
      let q = "name contains '" + qEscape(query) + "' and trashed = false";
      if (only_folders) q += " and mimeType = '" + FOLDER_MIME + "'";
      const params = { q, fields: "files(" + FILE_FIELDS + ")", pageSize: 50 };
      return ok(await gws(["drive", "files", "list", "--params", JSON.stringify(params), "--format", "json"]));
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "drive_list_folder",
  "List the direct children of a Google Drive folder (folders first, then files, alphabetical). Returns id, name, mimeType, modifiedTime for each child. Use to inspect a folder and to VERIFY results after move/rename/trash operations.",
  {
    folder_id: z.string().describe("The ID of the folder to list"),
  },
  async ({ folder_id }) => {
    try {
      const params = {
        q: "'" + qEscape(folder_id) + "' in parents and trashed = false",
        fields: "files(" + FILE_FIELDS + ")",
        pageSize: 200,
        orderBy: "folder,name",
      };
      return ok(await gws(["drive", "files", "list", "--params", JSON.stringify(params), "--format", "json"]));
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "drive_move",
  "MOVE a file or folder into a different folder (removes it from all current parent folders). This is the operation the built-in Drive connector cannot do. Reversible by moving back.",
  {
    file_id: z.string().describe("The ID of the file or folder to move"),
    dest_folder_id: z.string().describe("The ID of the destination folder"),
  },
  async ({ file_id, dest_folder_id }) => {
    try {
      const meta = await gws([
        "drive", "files", "get",
        "--params", JSON.stringify({ fileId: file_id, fields: "id,name,parents" }),
        "--format", "json",
      ]);
      const removeParents = (meta.parents || []).join(",");
      const params = {
        fileId: file_id,
        addParents: dest_folder_id,
        removeParents: removeParents,
        fields: FILE_FIELDS,
      };
      return ok(await gws(["drive", "files", "update", "--params", JSON.stringify(params), "--format", "json"]));
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "drive_rename",
  "RENAME a file or folder (metadata only, content untouched). This is an operation the built-in Drive connector cannot do. Reversible by renaming back.",
  {
    file_id: z.string().describe("The ID of the file or folder to rename"),
    new_name: z.string().describe("The new name"),
  },
  async ({ file_id, new_name }) => {
    try {
      return ok(
        await gws([
          "drive", "files", "update",
          "--params", JSON.stringify({ fileId: file_id, fields: FILE_FIELDS }),
          "--json", JSON.stringify({ name: new_name }),
          "--format", "json",
        ])
      );
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "drive_create_folder",
  "CREATE a new folder in Google Drive, optionally inside a parent folder (defaults to My Drive root).",
  {
    name: z.string().describe("Name for the new folder"),
    parent_folder_id: z.string().optional().describe("ID of the parent folder (omit for My Drive root)"),
  },
  async ({ name, parent_folder_id }) => {
    try {
      const body = { name: name, mimeType: FOLDER_MIME };
      if (parent_folder_id) body.parents = [parent_folder_id];
      return ok(
        await gws([
          "drive", "files", "create",
          "--params", JSON.stringify({ fields: FILE_FIELDS }),
          "--json", JSON.stringify(body),
          "--format", "json",
        ])
      );
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "drive_trash",
  "Move a file or folder to the Drive TRASH. NOT a permanent delete: recoverable for 30 days via drive_restore or the Drive UI, then auto-purged by Google. This server has no permanent-delete capability by design.",
  {
    file_id: z.string().describe("The ID of the file or folder to move to trash"),
  },
  async ({ file_id }) => {
    try {
      return ok(
        await gws([
          "drive", "files", "update",
          "--params", JSON.stringify({ fileId: file_id, fields: "id,name,trashed" }),
          "--json", JSON.stringify({ trashed: true }),
          "--format", "json",
        ])
      );
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "drive_restore",
  "Restore a file or folder from the Drive trash back to its original location.",
  {
    file_id: z.string().describe("The ID of the trashed file or folder to restore"),
  },
  async ({ file_id }) => {
    try {
      return ok(
        await gws([
          "drive", "files", "update",
          "--params", JSON.stringify({ fileId: file_id, fields: "id,name,trashed,parents" }),
          "--json", JSON.stringify({ trashed: false }),
          "--format", "json",
        ])
      );
    } catch (e) {
      return fail(e);
    }
  }
);

// =========================== DOC READ / LOCATE (Feature 3) =================

server.tool(
  "docs_get_text",
  "READ a Google Doc's body as plain text. Returns the text plus its total character length. Use offset/length to window a large document instead of pulling all of it. Set with_indices:true to also get every text segment with its real Docs API start/end index (useful when you want to reason about exact positions). This exists so you never have to pull a large doc through another connector just to find an anchor.",
  {
    document_id: z.string().describe("The ID of the Google Doc to read"),
    offset: z.number().optional().describe("Character offset to start from (default 0)"),
    length: z.number().optional().describe("Number of characters to return (default: all)"),
    with_indices: z.boolean().optional().describe("Also return per-segment Docs API indices"),
  },
  async ({ document_id, offset, length, with_indices }) => {
    try {
      const doc = await getDoc(document_id);
      const { text, runs } = extractDoc(doc);
      const start = Math.max(0, offset || 0);
      const end = typeof length === "number" ? Math.min(text.length, start + length) : text.length;
      const out = {
        documentId: document_id,
        title: doc.title,
        revisionId: doc.revisionId,
        totalChars: text.length,
        returnedRange: { offset: start, length: end - start },
        truncated: end < text.length || start > 0,
        text: text.slice(start, end),
      };
      if (with_indices) {
        out.segments = runs.map((r) => ({
          docsStartIndex: r.start,
          docsEndIndex: r.start + r.text.length,
          text: r.text,
        }));
      }
      return ok(out);
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "docs_find",
  "LOCATE every occurrence of a phrase inside one Google Doc. Returns each hit with its character offset, its real Docs API index range, the exact matched text, and surrounding context. Use match:'normalized' when the anchor is prose that may contain invisible characters (soft line breaks, non-breaking spaces, en/em dashes). If nothing matches, the response explains WHY (naming the specific invisible-character cause) instead of returning a bare zero. Call this before a replace to confirm an anchor is unique.",
  {
    document_id: z.string().describe("The ID of the Google Doc to search"),
    query: z.string().describe("Text to locate"),
    context_chars: z.number().optional().describe("Characters of context around each hit (default 80)"),
    match: MATCH_ENUM.optional().describe("literal (default) | normalized | regex"),
    match_case: z.boolean().optional().describe("Match case exactly (default true)"),
  },
  async ({ document_id, query, context_chars, match, match_case }) => {
    try {
      const doc = await getDoc(document_id);
      const { text, map } = extractDoc(doc);
      const mode = match || "literal";
      const hits = findMatches(text, map, query, mode, match_case);
      const out = {
        documentId: document_id,
        title: doc.title,
        query,
        match: mode,
        occurrences: hits.length,
        matches: hits.map((m) => {
          const c = contextFor(text, m, context_chars);
          return {
            charIndex: m.rawStart,
            docsStartIndex: m.startIndex,
            docsEndIndex: m.endIndex,
            matchedText: m.matchedText,
            spansNonTextElement: m.spansNonText || undefined,
            contextBefore: c.before,
            contextAfter: c.after,
          };
        }),
      };
      if (!hits.length && mode !== "regex") out.whyNoMatch = diagnose(text, query, match_case);
      return ok(out);
    } catch (e) {
      return fail(e);
    }
  }
);

// =========================== DOC INSERT / CREATE (Feature 1) ===============

server.tool(
  "docs_insert_text",
  "INSERT new text into a Google Doc without replacing anything. position: 'start_of_doc' | 'end_of_doc' | 'before' | 'after'. For 'before'/'after' supply an anchor - the anchor must match EXACTLY ONCE or the insert is refused (so it can never land in the wrong place). Include newlines in your text to create new paragraphs. This is what to use for adding a changelog line, a new bullet, or a note - do not try to fake it by replacing nearby text.",
  {
    document_id: z.string().describe("The ID of the Google Doc"),
    text: z.string().describe("Text to insert (use \\n for new paragraphs)"),
    position: z.enum(["before", "after", "start_of_doc", "end_of_doc"]).describe("Where to insert"),
    anchor: z.string().optional().describe("Required for before/after: existing text to anchor on"),
    match: MATCH_ENUM.optional().describe("How to match the anchor: literal (default) | normalized | regex"),
    match_case: z.boolean().optional().describe("Match anchor case exactly (default true)"),
  },
  async ({ document_id, text, position, anchor, match, match_case }) => {
    try {
      if (!text || !text.length) return fail(new Error("text is empty - nothing to insert"));
      const doc = await getDoc(document_id);
      let index;
      if (position === "start_of_doc") {
        index = 1;
      } else if (position === "end_of_doc") {
        index = Math.max(1, bodyEndIndex(doc) - 1);
      } else {
        if (!anchor || !anchor.length) {
          return fail(new Error("position '" + position + "' requires an anchor"));
        }
        const { text: body, map } = extractDoc(doc);
        const mode = match || "literal";
        const hits = findMatches(body, map, anchor, mode, match_case);
        if (hits.length !== 1) {
          const detail = {
            error: hits.length === 0 ? "anchor not found" : "anchor is not unique",
            anchor,
            match: mode,
            occurrences: hits.length,
            nothingChanged: true,
          };
          if (!hits.length && mode !== "regex") detail.whyNoMatch = diagnose(body, anchor, match_case);
          if (hits.length > 1) {
            detail.matches = hits.map((m) => ({
              charIndex: m.rawStart,
              docsStartIndex: m.startIndex,
              contextBefore: contextFor(body, m, 60).before,
              contextAfter: contextFor(body, m, 60).after,
            }));
            detail.hint = "Lengthen the anchor until it is unique, or use docs_replace_batch with expected_count.";
          }
          return ok(detail);
        }
        index = position === "before" ? hits[0].startIndex : hits[0].endIndex;
      }
      await gws(
        [
          "docs", "documents", "batchUpdate",
          "--params", JSON.stringify({ documentId: document_id }),
          "--json", JSON.stringify({ requests: [{ insertText: { location: { index }, text } }] }),
          "--format", "json",
        ],
        { timeout: BIG_TIMEOUT, maxBuffer: BIG_BUFFER }
      );
      return ok({
        documentId: document_id,
        inserted: true,
        position,
        atDocsIndex: index,
        charsInserted: text.length,
      });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "docs_create",
  "CREATE a new Google Doc, optionally inside a folder and optionally with body text already in it. This is the tool to use for a new canon document - the built-in connector and drive_create_folder cannot do this. Returns the new document id and its webViewLink.",
  {
    title: z.string().describe("Title for the new document"),
    parent_id: z.string().optional().describe("ID of the folder to create it in (omit for My Drive root)"),
    text: z.string().optional().describe("Optional body text to insert (use \\n for paragraphs)"),
  },
  async ({ title, parent_id, text }) => {
    try {
      // files.create (Drive) rather than documents.create (Docs): only Drive honors parents.
      const body = { name: title, mimeType: DOC_MIME };
      if (parent_id) body.parents = [parent_id];
      const file = await gws([
        "drive", "files", "create",
        "--params", JSON.stringify({ fields: FILE_FIELDS }),
        "--json", JSON.stringify(body),
        "--format", "json",
      ]);
      const documentId = file && file.id;
      if (!documentId) throw new Error("Drive did not return a file id: " + JSON.stringify(file));
      let charsInserted = 0;
      if (text && text.length) {
        await gws(
          [
            "docs", "documents", "batchUpdate",
            "--params", JSON.stringify({ documentId }),
            "--json", JSON.stringify({ requests: [{ insertText: { location: { index: 1 }, text } }] }),
            "--format", "json",
          ],
          { timeout: BIG_TIMEOUT, maxBuffer: BIG_BUFFER }
        );
        charsInserted = text.length;
      }
      return ok({
        created: true,
        documentId,
        id: documentId,
        name: file.name,
        parents: file.parents,
        webViewLink: file.webViewLink,
        charsInserted,
      });
    } catch (e) {
      return fail(e);
    }
  }
);

// =========================== DOC REPLACE (Features 2 + 4) ==================

server.tool(
  "docs_replace_text",
  "EDIT a Google Doc IN PLACE: replace occurrences of text in the document body. Returns occurrencesChanged. DEFAULT BEHAVIOR IS UNCHANGED (exact-string replaceAllText) - but if it finds 0, the response now DIAGNOSES why and names the exact cause (soft line break, non-breaking space, en/em dash, tab, zero-width character, or case). Pass match:'normalized' to make all of those stop mattering. Pass expected_count to refuse the edit unless exactly that many matches exist. Pass dry_run:true to preview every match with context and change nothing. Revertible via the Doc's revision history.",
  {
    document_id: z.string().describe("The ID of the Google Doc to edit"),
    find_text: z.string().describe("Text to find"),
    replace_text: z.string().describe("Replacement text (empty string deletes the match)"),
    match_case: z.boolean().optional().describe("Match case exactly (default true)"),
    match: MATCH_ENUM.optional().describe("literal (default) | normalized (ignores invisible-character differences) | regex"),
    expected_count: z.number().optional().describe("Refuse to apply unless exactly this many matches exist"),
    dry_run: z.boolean().optional().describe("Report what would change, apply nothing"),
    context_chars: z.number().optional().describe("Context around each match in dry_run output (default 80)"),
  },
  async ({ document_id, find_text, replace_text, match_case, match, expected_count, dry_run, context_chars }) => {
    try {
      const usesNewFeatures =
        (match && match !== "literal") || typeof expected_count === "number" || dry_run === true;

      // ---- LEGACY PATH: byte-for-byte the pre-v1.2.0 behavior. ----
      if (!usesNewFeatures) {
        const body = {
          requests: [
            {
              replaceAllText: {
                containsText: { text: find_text, matchCase: match_case !== false },
                replaceText: replace_text,
              },
            },
          ],
        };
        const res = await gws([
          "docs", "documents", "batchUpdate",
          "--params", JSON.stringify({ documentId: document_id }),
          "--json", JSON.stringify(body),
          "--format", "json",
        ]);
        const occurrences =
          res && res.replies && res.replies[0] && res.replies[0].replaceAllText
            ? res.replies[0].replaceAllText.occurrencesChanged || 0
            : 0;
        const out = {
          documentId: document_id,
          findText: find_text,
          replaceText: replace_text,
          occurrencesChanged: occurrences,
        };
        // Additive: only fires on failure, so a successful legacy call is untouched.
        if (occurrences === 0) {
          try {
            const doc = await getDoc(document_id);
            const { text } = extractDoc(doc);
            out.whyNoMatch = diagnose(text, find_text, match_case);
            out.hint = "Re-run with match:'normalized' if a cause is listed above.";
          } catch (e) {
            out.whyNoMatch = { diagnosis: "diagnostic unavailable: " + String(e.message || e) };
          }
        }
        return ok(out);
      }

      // ---- POSITIONAL PATH: normalized/regex matching, count guard, dry run. ----
      const mode = match || "literal";
      const doc = await getDoc(document_id);
      const { text, map } = extractDoc(doc);
      const hits = findMatches(text, map, find_text, mode, match_case);

      if (typeof expected_count === "number" && hits.length !== expected_count) {
        const detail = {
          error: "expected_count guard: refused, nothing changed",
          documentId: document_id,
          findText: find_text,
          match: mode,
          expectedCount: expected_count,
          actualCount: hits.length,
          nothingChanged: true,
          matches: hits.map((m) => {
            const c = contextFor(text, m, context_chars);
            return { charIndex: m.rawStart, contextBefore: c.before, matchedText: m.matchedText, contextAfter: c.after };
          }),
        };
        if (!hits.length && mode !== "regex") detail.whyNoMatch = diagnose(text, find_text, match_case);
        return ok(detail);
      }

      const usable = hits.filter((m) => !m.spansNonText);
      const skipped = hits.filter((m) => m.spansNonText);

      if (dry_run) {
        const out = {
          documentId: document_id,
          dryRun: true,
          match: mode,
          findText: find_text,
          replaceText: replace_text,
          wouldChange: usable.length,
          nothingChanged: true,
          matches: usable.map((m) => {
            const c = contextFor(text, m, context_chars);
            return {
              charIndex: m.rawStart,
              docsStartIndex: m.startIndex,
              docsEndIndex: m.endIndex,
              matchedText: m.matchedText,
              contextBefore: c.before,
              contextAfter: c.after,
            };
          }),
        };
        if (skipped.length) {
          out.skipped = skipped.map((m) => ({
            charIndex: m.rawStart,
            matchedText: m.matchedText,
            reason: "match spans a non-text element (inline image, page break or footnote marker) - refused to avoid destroying it",
          }));
        }
        if (!hits.length && mode !== "regex") out.whyNoMatch = diagnose(text, find_text, match_case);
        return ok(out);
      }

      if (!usable.length) {
        const out = {
          documentId: document_id,
          findText: find_text,
          match: mode,
          occurrencesChanged: 0,
          nothingChanged: true,
        };
        if (skipped.length) {
          out.skipped = skipped.map((m) => ({
            charIndex: m.rawStart,
            matchedText: m.matchedText,
            reason: "match spans a non-text element - refused",
          }));
        } else if (mode !== "regex") {
          out.whyNoMatch = diagnose(text, find_text, match_case);
        }
        return ok(out);
      }

      const ops = usable.map((m) => ({ startIndex: m.startIndex, endIndex: m.endIndex, replaceText: replace_text }));
      const res = await applyPositional(document_id, ops);
      const out = {
        documentId: document_id,
        findText: find_text,
        replaceText: replace_text,
        match: mode,
        occurrencesChanged: res.applied,
        atomic: true,
      };
      if (skipped.length) {
        out.skipped = skipped.map((m) => ({
          charIndex: m.rawStart,
          matchedText: m.matchedText,
          reason: "match spans a non-text element - refused",
        }));
      }
      return ok(out);
    } catch (e) {
      return fail(e);
    }
  }
);

// =========================== ATOMIC BATCH (Feature 5) ======================

server.tool(
  "docs_replace_batch",
  "Apply MANY replacements to ONE Google Doc as a SINGLE atomic edit - one API call, one revision-history entry, no races between edits. Each edit takes find_text, replace_text and optionally match, match_case and expected_count. ALL edits are resolved against one snapshot of the document and validated BEFORE anything is written: if any expected_count fails, or two edits target overlapping text, NOTHING is applied and the response tells you which edit failed. Use this instead of firing 6-20 separate docs_replace_text calls.",
  {
    document_id: z.string().describe("The ID of the Google Doc to edit"),
    edits: z
      .array(
        z.object({
          find_text: z.string().describe("Text to find"),
          replace_text: z.string().describe("Replacement text (empty string deletes)"),
          match: MATCH_ENUM.optional().describe("literal (default) | normalized | regex"),
          match_case: z.boolean().optional().describe("Match case exactly (default true)"),
          expected_count: z.number().optional().describe("Refuse the WHOLE batch unless exactly this many matches"),
        })
      )
      .describe("The list of replacements to apply atomically"),
    dry_run: z.boolean().optional().describe("Validate and report, apply nothing"),
    context_chars: z.number().optional().describe("Context around each match in the report (default 80)"),
  },
  async ({ document_id, edits, dry_run, context_chars }) => {
    try {
      if (!Array.isArray(edits) || !edits.length) return fail(new Error("edits array is empty"));
      const doc = await getDoc(document_id);
      const { text, map } = extractDoc(doc);

      const resolved = [];
      const problems = [];
      for (let i = 0; i < edits.length; i++) {
        const ed = edits[i];
        const mode = ed.match || "literal";
        let hits;
        try {
          hits = findMatches(text, map, ed.find_text, mode, ed.match_case);
        } catch (e) {
          problems.push({ editIndex: i, findText: ed.find_text, error: String(e.message || e) });
          continue;
        }
        const usable = hits.filter((m) => !m.spansNonText);
        const skipped = hits.filter((m) => m.spansNonText);
        if (typeof ed.expected_count === "number" && usable.length !== ed.expected_count) {
          const p = {
            editIndex: i,
            findText: ed.find_text,
            match: mode,
            error: "expected_count mismatch",
            expectedCount: ed.expected_count,
            actualCount: usable.length,
          };
          if (!hits.length && mode !== "regex") p.whyNoMatch = diagnose(text, ed.find_text, ed.match_case);
          problems.push(p);
          continue;
        }
        if (!usable.length) {
          const p = { editIndex: i, findText: ed.find_text, match: mode, error: "no usable matches", actualCount: 0 };
          if (skipped.length) p.skippedSpanningNonText = skipped.length;
          else if (mode !== "regex") p.whyNoMatch = diagnose(text, ed.find_text, ed.match_case);
          problems.push(p);
          continue;
        }
        for (const m of usable) {
          resolved.push({
            editIndex: i,
            findText: ed.find_text,
            startIndex: m.startIndex,
            endIndex: m.endIndex,
            rawStart: m.rawStart,
            rawEnd: m.rawEnd,
            matchedText: m.matchedText,
            replaceText: ed.replace_text,
          });
        }
      }

      // Two edits hitting overlapping text would corrupt each other - refuse the batch.
      const sorted = resolved.slice().sort((a, b) => a.startIndex - b.startIndex);
      for (let i = 1; i < sorted.length; i++) {
        if (overlaps(sorted[i - 1], sorted[i])) {
          problems.push({
            error: "overlapping edits",
            detail:
              "edit #" + sorted[i - 1].editIndex + " (" + JSON.stringify(sorted[i - 1].matchedText) +
              ") and edit #" + sorted[i].editIndex + " (" + JSON.stringify(sorted[i].matchedText) +
              ") target overlapping text. Nothing was applied.",
          });
          break;
        }
      }

      if (problems.length) {
        return ok({
          documentId: document_id,
          error: "batch refused - nothing was applied",
          nothingChanged: true,
          editsRequested: edits.length,
          problems,
          resolvedSoFar: resolved.length,
        });
      }

      const report = resolved.map((r) => {
        const c = contextFor(text, r, context_chars);
        return {
          editIndex: r.editIndex,
          findText: r.findText,
          charIndex: r.rawStart,
          matchedText: r.matchedText,
          contextBefore: c.before,
          contextAfter: c.after,
        };
      });

      if (dry_run) {
        return ok({
          documentId: document_id,
          dryRun: true,
          nothingChanged: true,
          editsRequested: edits.length,
          wouldChange: resolved.length,
          matches: report,
        });
      }

      const res = await applyPositional(
        document_id,
        resolved.map((r) => ({ startIndex: r.startIndex, endIndex: r.endIndex, replaceText: r.replaceText }))
      );
      const perEdit = {};
      for (const r of resolved) perEdit[r.editIndex] = (perEdit[r.editIndex] || 0) + 1;
      return ok({
        documentId: document_id,
        atomic: true,
        singleRevision: true,
        editsRequested: edits.length,
        occurrencesChanged: res.applied,
        apiRequests: res.requests,
        perEdit: edits.map((ed, i) => ({
          editIndex: i,
          findText: ed.find_text,
          occurrencesChanged: perEdit[i] || 0,
        })),
      });
    } catch (e) {
      return fail(e);
    }
  }
);

// =========================== CONTENT SEARCH (unchanged) ====================

server.tool(
  "docs_search_content",
  "Find Google Docs whose BODY TEXT contains a phrase (Drive full-text search), optionally limited to one folder. Use to locate which docs still carry an outdated detail before an edit sweep. CAVEAT: Google's full-text index lags recent edits by minutes - confirm a doc's actual current content with docs_get_text or docs_find, not by re-searching.",
  {
    text: z.string().describe("Phrase to search for inside document bodies"),
    folder_id: z.string().optional().describe("Restrict the search to direct children of this folder (omit for whole Drive)"),
  },
  async ({ text, folder_id }) => {
    try {
      let q =
        "fullText contains '" + qEscape(text) + "' and mimeType = 'application/vnd.google-apps.document' and trashed = false";
      if (folder_id) q += " and '" + qEscape(folder_id) + "' in parents";
      const params = { q, fields: "files(" + FILE_FIELDS + ")", pageSize: 50 };
      return ok(await gws(["drive", "files", "list", "--params", JSON.stringify(params), "--format", "json"]));
    } catch (e) {
      return fail(e);
    }
  }
);

// ---------------------------------------------------------------------------
// TRANSPORT
// The SDK stamps draft-07 on generated inputSchemas (zod-to-json-schema default).
// The Desktop/Cowork validator accepts 2020-12 only for outputSchema and Proctor
// asked for 2020-12 throughout, so relabel on the way out. Safe here because these
// schemas use only constructs identical in both dialects (type / properties /
// required / additionalProperties / description / enum / items / array / object).
// Revisit if $defs or tuple-form items are ever introduced.
// No tool declares an outputSchema - that is what hard-errors on invocation.
// ---------------------------------------------------------------------------

const SCHEMA_2020_12 = "https://json-schema.org/draft/2020-12/schema";

const transport = new StdioServerTransport();
const _send = transport.send.bind(transport);
transport.send = (message, options) => {
  try {
    const tools = message && message.result && message.result.tools;
    if (Array.isArray(tools)) {
      for (const t of tools) {
        if (t && t.inputSchema && t.inputSchema.$schema) t.inputSchema.$schema = SCHEMA_2020_12;
        if (t && t.outputSchema) delete t.outputSchema;
      }
    }
  } catch (e) {
    console.error("[gdrive-ops] schema relabel skipped: " + String((e && e.message) || e));
  }
  return _send(message, options);
};

// =========================== v1.3.0 (S#317, 2026-08-27) ====================
// drive_upload_chunked: lets a chat sandbox push a file of ANY size into Drive even though a single
// tool-call parameter is truncated above ~2 KB on the client side. The caller sends the file in
// small pieces (text or base64, no blank lines); the server accumulates them in a temp file on
// Brother's machine and, on final:true, uploads via gws (+upload, or files update when a file of
// the same name already exists in the target folder, so re-uploads replace instead of duplicate).
// atlas_rebuild: runs the STORY-SHAPE ATLAS build on Brother's machine (pull atlas_data.json from
// Drive -> gen -> measure -> render -> pagemap -> push HTML/PDF/JSON back) and returns the summary.


const UPLOAD_DIR = path.join(os.tmpdir(), "gdrive-ops-uploads");
const ATLAS_DIR = process.env.GDRIVE_OPS_ATLAS_DIR ||
  path.join(process.env.USERPROFILE || os.homedir(), "Documents", "last-roman", "_tools", "story-shape-atlas");
const PYTHON_EXE = process.env.GDRIVE_OPS_PYTHON || "python";

function uploadPath(id) {
  if (!/^[A-Za-z0-9_.-]{1,64}$/.test(id)) throw new Error("upload_id must be 1-64 chars of [A-Za-z0-9_.-]");
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
  return path.join(UPLOAD_DIR, id + ".part");
}

async function findInFolder(name, parentId) {
  const q = "name = '" + qEscape(name) + "' and '" + qEscape(parentId) + "' in parents and trashed = false";
  const res = await gws(["drive", "files", "list", "--params", JSON.stringify({ q: q, fields: "files(id,name)", pageSize: 5 }), "--format", "json"]);
  return res && res.files && res.files[0] ? res.files[0].id : null;
}

server.tool(
  "drive_upload_chunked",
  [
    "UPLOAD A FILE OF ANY SIZE INTO DRIVE FROM A SANDBOX, IN CHUNKS. Use this when the built-in connector truncates or rejects a large inline file.",
    "Call repeatedly with the SAME upload_id: each call appends `chunk`. Keep every chunk under ~1500 characters and free of blank lines (that is the client-side truncation limit).",
    "encoding 'text' appends the chunk verbatim (utf-8); 'base64' decodes it (use for binary: PDF, images, or any text you want byte-exact - base64 has no blank lines by construction).",
    "On the LAST call pass final:true with name + parent_id (+ optional mime). If a file with that name already exists in parent_id it is UPDATED in place (same file id, new revision); otherwise it is created.",
    "Pass reset:true on the first call to discard any stale partial with the same upload_id. Returns bytes_so_far after each append and the Drive file record after the final upload.",
  ].join(" "),
  {
    upload_id: z.string().describe("Your own id for this upload session, e.g. 'atlas-json-206'"),
    chunk: z.string().optional().describe("Next piece of the file (omit on a final-only call)"),
    encoding: z.enum(["text", "base64"]).optional().describe("How `chunk` is encoded (default text)"),
    reset: z.boolean().optional().describe("Discard any existing partial for this upload_id before appending"),
    final: z.boolean().optional().describe("true = this is the last chunk; upload now"),
    name: z.string().optional().describe("Target filename in Drive (required with final)"),
    parent_id: z.string().optional().describe("Target folder id (required with final)"),
    mime: z.string().optional().describe("Content type override, e.g. application/json (default: detected from extension)"),
  },
  async ({ upload_id, chunk, encoding, reset, final, name, parent_id, mime }) => {
    try {
      const p = uploadPath(upload_id);
      if (reset && fs.existsSync(p)) fs.unlinkSync(p);
      if (chunk && chunk.length) {
        const buf = encoding === "base64" ? Buffer.from(chunk.replace(/\s+/g, ""), "base64") : Buffer.from(chunk, "utf8");
        fs.appendFileSync(p, buf);
      }
      const size = fs.existsSync(p) ? fs.statSync(p).size : 0;
      if (!final) return ok({ upload_id: upload_id, bytes_so_far: size, status: "accumulating" });
      if (!name || !parent_id) throw new Error("final:true requires name and parent_id");
      if (size === 0) throw new Error("nothing accumulated for upload_id " + upload_id);
      // gws detects the MIME type from the extension of the path it is given, so stage under the real name.
      const stagedName = upload_id + "__" + name.replace(/[\\/:*?"<>|]/g, "_");
      const staged = path.join(UPLOAD_DIR, stagedName);
      fs.renameSync(p, staged);
      let result;
      const existing = await findInFolder(name, parent_id);
      const args = existing
        ? ["drive", "files", "update", "--params", JSON.stringify({ fileId: existing, fields: FILE_FIELDS }), "--upload", stagedName, "--format", "json"]
        : ["drive", "+upload", stagedName, "--parent", parent_id, "--name", name, "--format", "json"];
      if (mime) args.push("--upload-content-type", mime);
      try {
        result = await gws(args, { timeout: BIG_TIMEOUT, maxBuffer: BIG_BUFFER, cwd: UPLOAD_DIR });
      } finally {
        try { fs.unlinkSync(staged); } catch (e) { /* ignore */ }
      }
      return ok({ upload_id: upload_id, bytes: size, action: existing ? "updated" : "created", file: result });
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "atlas_rebuild",
  [
    "REBUILD THE LAST ROMAN STORY-SHAPE ATLAS on Brother's machine and publish the outputs to the Drive folder 'STORY-SHAPE ATLAS - SOURCE'.",
    "Pipeline: pull the CURRENT atlas_data.json from Drive -> gen_atlas.py -> measure.py (refuses if any hour would spill to a 3rd page) -> render_pdf.py -> pagemap.py (verifies 4 + 2N + 1 pages) -> sync HTML, PDF and JSON back to Drive.",
    "Typical use: first drive_upload_chunked the edited atlas_data.json into the atlas folder, then call this. Takes ~60-90 s. Returns the build log; read the last lines for BUILD OK / SYNC OK or the STOP reason.",
    "Only works while Brother's PC is on (the generator and Chromium live there).",
    "FULL WORKFLOW to add or change an hour (Claude Desktop does not show server-level instructions, so it lives here): (1) drive_find the folder 'STORY-SHAPE ATLAS - SOURCE' and docs_get_text the Google Doc '00 - READ ME FIRST - STORY-SHAPE ATLAS' inside it. (2) Download atlas_data.json and edit it in your sandbox - one JSON entry per hour, rules in ATLAS-HANDOFF.md section (g): pct sums to 100, act minutes sum to rt, summary ~325-345 words. (3) drive_upload_chunked the edited atlas_data.json back into that folder (upload_id 'atlas-json', final name 'atlas_data.json'). (4) atlas_rebuild. (5) Mirror the hour into the Doc 'THE LAST ROMAN - STORY-SHAPE ATLAS - DATA & ANALYSIS' with docs_replace_text / docs_insert_text. Brother is not needed unless this tool returns a STOP.",
  ].join(" "),
  {
    pull: z.boolean().optional().describe("Pull atlas_data.json from Drive before building (default true). false = build from whatever is on Brother's disk."),
  },
  async ({ pull }) => {
    try {
      const args = [path.join(ATLAS_DIR, "build.py"), "--sync"];
      if (pull !== false) args.push("--pull");
      const out = await new Promise((resolve, reject) => {
        execFile(PYTHON_EXE, args, { cwd: ATLAS_DIR, timeout: 300000, maxBuffer: BIG_BUFFER, windowsHide: true },
          (err, stdout, stderr) => {
            const text = String(stdout) + (stderr ? "\n[stderr]\n" + String(stderr) : "");
            if (err) reject(new Error("build failed (exit " + (err.code || "?") + ")\n" + text.slice(-4000)));
            else resolve(text);
          });
      });
      const lines = out.split(/\r?\n/).filter((l) => /SPILLS:|TOTAL PAGES:|BUILD OK|SYNC OK|STOP:|FAILED|pulled|updated :|uploaded:/.test(l));
      return ok({ status: "ok", summary: lines, log_tail: out.slice(-1500) });
    } catch (e) {
      return fail(e);
    }
  }
);

await server.connect(transport);
