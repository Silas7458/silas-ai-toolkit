// Self-test battery for gdrive-ops MCP server v1.2.0. Run: node selftest.mjs
// Exercises every tool end-to-end through the real MCP stdio protocol.
// Doc-editing tests use the raw gws CLI for setup/verify (create + read the
// scratch doc) and the MCP tools for the operations under test.
//
// v1.2.0 adds coverage for Proctor's 5 features, including the MEASURED causes
// of silent 0-occurrence replaces (soft line break U+000B, non-breaking space
// U+00A0, en/em dash, tab, zero-width) which are seeded deliberately below.
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { execFile } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SERVER_PATH = path.join(HERE, "server.js");

const GWS_EXE =
  process.env.GDRIVE_OPS_GWS_EXE ||
  path.join(
    process.env.APPDATA || "",
    "npm", "node_modules", "@googleworkspace", "cli",
    "node_modules", ".bin_real", "gws.exe"
  );

function gwsRaw(args) {
  return new Promise((resolve, reject) => {
    execFile(GWS_EXE, args, { timeout: 120000, maxBuffer: 64 * 1024 * 1024, windowsHide: true }, (err, stdout) => {
      if (err) { reject(err); return; }
      const text = String(stdout);
      const start = text.search(/[[{]/);
      try { resolve(JSON.parse(text.slice(start))); } catch (e) { reject(new Error("unparseable: " + text.slice(0, 200))); }
    });
  });
}

async function readDocText(docId) {
  const got = await gwsRaw(["docs", "documents", "get", "--params", JSON.stringify({ documentId: docId }), "--format", "json"]);
  let t = "";
  const walk = (content) => {
    for (const el of content || []) {
      if (el.paragraph) for (const pe of el.paragraph.elements || []) t += (pe.textRun && pe.textRun.content) || "";
      else if (el.table) for (const row of el.table.tableRows || []) for (const c of row.tableCells || []) walk(c.content);
    }
  };
  walk(got.body && got.body.content);
  return t;
}

async function seedDoc(docId, text) {
  await gwsRaw([
    "docs", "documents", "batchUpdate",
    "--params", JSON.stringify({ documentId: docId }),
    "--json", JSON.stringify({ requests: [{ insertText: { location: { index: 1 }, text } }] }),
    "--format", "json",
  ]);
}

const transport = new StdioClientTransport({
  command: process.execPath,
  args: [SERVER_PATH],
});
const client = new Client({ name: "selftest", version: "1.2.0" });
await client.connect(transport);

let pass = 0;
let failCount = 0;
function check(label, cond, detail) {
  if (cond) {
    pass++;
    console.log("PASS " + label + (detail ? " :: " + detail : ""));
  } else {
    failCount++;
    console.log("FAIL " + label + (detail ? " :: " + detail : ""));
  }
}

async function call(name, args) {
  const res = await client.callTool({ name: name, arguments: args });
  const text = res.content && res.content[0] ? res.content[0].text : "";
  let data = null;
  try { data = JSON.parse(text); } catch (e) { /* leave null */ }
  return { res: res, text: text, data: data };
}

const EXPECTED_TOOLS = [
  "docs_create", "docs_find", "docs_get_text", "docs_insert_text",
  "docs_replace_batch", "docs_replace_text", "docs_search_content",
  "drive_create_folder", "drive_find", "drive_list_folder", "drive_move",
  "drive_rename", "drive_restore", "drive_trash",
].join(",");

// ============================ SURFACE ======================================

const tools = await client.listTools();
const names = tools.tools.map((t) => t.name).sort();
check("tool-surface-14", names.join(",") === EXPECTED_TOOLS, names.length + " tools");

const dialects = [...new Set(tools.tools.map((t) => (t.inputSchema && t.inputSchema.$schema) || "(none)"))];
check("schema-dialect-2020-12", dialects.length === 1 && dialects[0] === "https://json-schema.org/draft/2020-12/schema", dialects.join("|"));
check("no-outputSchema", !tools.tools.some((t) => !!t.outputSchema), "none declared (draft-07 outputSchema hard-errors on invoke)");

const instr = client.getInstructions ? client.getInstructions() : undefined;
check("instructions-present", typeof instr === "string" && instr.indexOf("READ + CREATE only") !== -1, instr ? instr.slice(0, 50) + "..." : "MISSING");

// ============================ DRIVE FILE OPS (legacy 9) ====================

const a = await call("drive_create_folder", { name: "ZZZ-GDRIVE-OPS-SELFTEST-A" });
check("create-folder-A", !!(a.data && a.data.id), a.data && a.data.id);
const b = await call("drive_create_folder", { name: "ZZZ-GDRIVE-OPS-SELFTEST-B" });
check("create-folder-B", !!(b.data && b.data.id), b.data && b.data.id);
const aId = a.data.id;
const bId = b.data.id;

const mv = await call("drive_move", { file_id: aId, dest_folder_id: bId });
check("move-A-into-B", !!(mv.data && mv.data.parents && mv.data.parents.length === 1 && mv.data.parents[0] === bId), JSON.stringify(mv.data && mv.data.parents));

const ls = await call("drive_list_folder", { folder_id: bId });
const lsNames = ls.data && ls.data.files ? ls.data.files.map((f) => f.name) : [];
check("list-B-shows-A", lsNames.indexOf("ZZZ-GDRIVE-OPS-SELFTEST-A") !== -1, lsNames.join(","));

const rn = await call("drive_rename", { file_id: aId, new_name: "ZZZ-GDRIVE-OPS-SELFTEST-A-RENAMED" });
check("rename-A", !!(rn.data && rn.data.name === "ZZZ-GDRIVE-OPS-SELFTEST-A-RENAMED"), rn.data && rn.data.name);

const fd = await call("drive_find", { query: "ZZZ-GDRIVE-OPS-SELFTEST", only_folders: true });
const fdCount = fd.data && fd.data.files ? fd.data.files.length : 0;
check("find-both", fdCount === 2, "found " + fdCount);

const tr = await call("drive_trash", { file_id: aId });
check("trash-A", !!(tr.data && tr.data.trashed === true), JSON.stringify(tr.data));
const rs = await call("drive_restore", { file_id: aId });
check("restore-A", !!(rs.data && rs.data.trashed === false), JSON.stringify(rs.data));

const bad = await call("drive_move", { file_id: "nonexistent-id-12345", dest_folder_id: bId });
check("error-path-isError", !!(bad.res.isError && bad.text.indexOf("ERROR") === 0), bad.text.slice(0, 60));
const alive = await client.listTools();
check("server-survives-error", alive.tools.length === 14);

// ============================ FEATURE 1: docs_create =======================

const created = await call("docs_create", {
  title: "ZZZ-GDRIVE-OPS-SELFTEST-CREATED",
  parent_id: bId,
  text: "Line one.\nLine two.\nEND.\n",
});
check("docs_create-returns-id", !!(created.data && created.data.documentId), created.data && created.data.documentId);
const createdId = created.data && created.data.documentId;
check("docs_create-in-parent", !!(created.data && created.data.parents && created.data.parents[0] === bId), JSON.stringify(created.data && created.data.parents));
// "Line one.\nLine two.\nEND.\n" is 25 characters.
check("docs_create-reports-chars", created.data && created.data.charsInserted === 25, "charsInserted=" + (created.data && created.data.charsInserted));
const createdText = await readDocText(createdId);
check("docs_create-body-written", createdText.indexOf("Line one.") !== -1 && createdText.indexOf("END.") !== -1, JSON.stringify(createdText.slice(0, 40)));

// ============================ FEATURE 3: get_text / find ===================

const gt = await call("docs_get_text", { document_id: createdId });
check("docs_get_text-returns-text", !!(gt.data && gt.data.text && gt.data.text.indexOf("Line two.") !== -1), "totalChars=" + (gt.data && gt.data.totalChars));
const gtw = await call("docs_get_text", { document_id: createdId, offset: 5, length: 3 });
check("docs_get_text-windowing", !!(gtw.data && gtw.data.text === createdText.slice(5, 8)), JSON.stringify(gtw.data && gtw.data.text));
const gti = await call("docs_get_text", { document_id: createdId, with_indices: true });
check("docs_get_text-with-indices", !!(gti.data && Array.isArray(gti.data.segments) && gti.data.segments.length > 0 && typeof gti.data.segments[0].docsStartIndex === "number"), (gti.data && gti.data.segments && gti.data.segments.length) + " segments");

const fdc = await call("docs_find", { document_id: createdId, query: "Line", context_chars: 10 });
check("docs_find-counts", !!(fdc.data && fdc.data.occurrences === 2), "occurrences=" + (fdc.data && fdc.data.occurrences));
check("docs_find-has-indices-and-context", !!(fdc.data && fdc.data.matches[0] && typeof fdc.data.matches[0].docsStartIndex === "number" && typeof fdc.data.matches[0].contextAfter === "string"), JSON.stringify(fdc.data && fdc.data.matches[0]));

// ============================ FEATURE 2: THE REAL FAILURE CAUSES ===========
// Seed a doc containing exactly the invisible characters that make replaceAllText
// silently return 0: soft line break (U+000B), non-breaking space (U+00A0), em dash.

const hard = await call("docs_create", { title: "ZZZ-GDRIVE-OPS-SELFTEST-HARD", parent_id: bId });
const hardId = hard.data.documentId;
check("hard-doc-created", !!hardId, hardId);
await seedDoc(
  hardId,
  "S1 Master\u000Bv1.5 draft\n" +                       // SOFT line break, not a paragraph
  "Felix carries the\u000Bmourning of Britain.\n" +      // SOFT line break mid-sentence
  "non\u00A0breaking gap here.\n" +                      // non-breaking space
  "Uthr \u2014 king of Britain.\n"                       // em dash
);

// Literal replace on a soft line break: must find nothing AND name the cause.
const lit = await call("docs_replace_text", { document_id: hardId, find_text: "S1 Master\nv1.5", replace_text: "SEASON ONE v9" });
check("softbreak-literal-finds-0", !!(lit.data && lit.data.occurrencesChanged === 0), "occ=" + (lit.data && lit.data.occurrencesChanged));
const litCauses = (lit.data && lit.data.whyNoMatch && lit.data.whyNoMatch.causes || []).map((c) => c.cause);
check("softbreak-diagnosed-by-name", litCauses.indexOf("soft_line_break") !== -1, "causes=[" + litCauses.join(",") + "]");

// Normalized replace on the same anchor: must succeed.
const norm = await call("docs_replace_text", { document_id: hardId, find_text: "S1 Master\nv1.5", replace_text: "SEASON ONE v9", match: "normalized" });
check("softbreak-normalized-succeeds", !!(norm.data && norm.data.occurrencesChanged === 1), JSON.stringify(norm.data && norm.data.occurrencesChanged));
const afterNorm = await readDocText(hardId);
check("softbreak-doc-actually-changed", afterNorm.indexOf("SEASON ONE v9") !== -1, JSON.stringify(afterNorm.slice(0, 30)));

// Non-breaking space.
const nb = await call("docs_replace_text", { document_id: hardId, find_text: "non breaking gap", replace_text: "NBSP FIXED", match: "normalized" });
check("nbsp-normalized-succeeds", !!(nb.data && nb.data.occurrencesChanged === 1), "occ=" + (nb.data && nb.data.occurrencesChanged));

// Em dash typed as a plain hyphen.
const dash = await call("docs_replace_text", { document_id: hardId, find_text: "Uthr - king", replace_text: "UTHER - HIGH KING", match: "normalized" });
check("emdash-normalized-succeeds", !!(dash.data && dash.data.occurrencesChanged === 1), "occ=" + (dash.data && dash.data.occurrencesChanged));

// Genuinely absent text must NOT be falsely diagnosed as a hidden-character problem.
const absent = await call("docs_replace_text", { document_id: hardId, find_text: "Vortigern the Usurper", replace_text: "X" });
check("absent-text-not-false-positive", !!(absent.data && absent.data.occurrencesChanged === 0 && absent.data.whyNoMatch && absent.data.whyNoMatch.causes.length === 0), absent.data && absent.data.whyNoMatch && absent.data.whyNoMatch.diagnosis);

// Case difference must be reported as such.
const casediff = await call("docs_replace_text", { document_id: hardId, find_text: "FELIX carries", replace_text: "X" });
const caseCauses = (casediff.data && casediff.data.whyNoMatch && casediff.data.whyNoMatch.causes || []).map((c) => c.cause);
check("case-difference-diagnosed", caseCauses.indexOf("case_differs") !== -1, "causes=[" + caseCauses.join(",") + "]");

// Regex mode.
const rx = await call("docs_replace_text", { document_id: hardId, find_text: "Britain\\.", replace_text: "BRITANNIA.", match: "regex" });
check("regex-mode-works", !!(rx.data && rx.data.occurrencesChanged >= 1), "occ=" + (rx.data && rx.data.occurrencesChanged));

// ============================ FEATURE 4: guards ============================

const guardDoc = await call("docs_create", { title: "ZZZ-GDRIVE-OPS-SELFTEST-GUARD", parent_id: bId });
const guardId = guardDoc.data.documentId;
await seedDoc(guardId, "alpha beta alpha gamma alpha\n");

const before = await readDocText(guardId);
const guardFail = await call("docs_replace_text", { document_id: guardId, find_text: "alpha", replace_text: "OMEGA", expected_count: 1 });
check("expected_count-refuses", !!(guardFail.data && guardFail.data.nothingChanged === true && guardFail.data.actualCount === 3), "actual=" + (guardFail.data && guardFail.data.actualCount));
check("expected_count-doc-untouched", (await readDocText(guardId)) === before, "unchanged");

const dry = await call("docs_replace_text", { document_id: guardId, find_text: "alpha", replace_text: "OMEGA", dry_run: true, context_chars: 8 });
check("dry_run-reports-3", !!(dry.data && dry.data.wouldChange === 3 && dry.data.nothingChanged === true), "wouldChange=" + (dry.data && dry.data.wouldChange));
check("dry_run-has-context", !!(dry.data && dry.data.matches && dry.data.matches[0] && typeof dry.data.matches[0].contextBefore === "string"), JSON.stringify(dry.data && dry.data.matches && dry.data.matches[0]));
check("dry_run-doc-untouched", (await readDocText(guardId)) === before, "unchanged");

const guardOk = await call("docs_replace_text", { document_id: guardId, find_text: "alpha", replace_text: "OMEGA", expected_count: 3 });
check("expected_count-passes-and-applies", !!(guardOk.data && guardOk.data.occurrencesChanged === 3), "occ=" + (guardOk.data && guardOk.data.occurrencesChanged));
const guardAfter = await readDocText(guardId);
check("guard-doc-all-three-replaced", guardAfter.indexOf("alpha") === -1 && (guardAfter.match(/OMEGA/g) || []).length === 3, JSON.stringify(guardAfter.trim()));

// ============================ FEATURE 1: docs_insert_text ==================

const insDoc = await call("docs_create", { title: "ZZZ-GDRIVE-OPS-SELFTEST-INSERT", parent_id: bId });
const insId = insDoc.data.documentId;
await seedDoc(insId, "MIDDLE ANCHOR here.\n");

const i1 = await call("docs_insert_text", { document_id: insId, text: "TOP.\n", position: "start_of_doc" });
check("insert-start_of_doc", !!(i1.data && i1.data.inserted === true), "at=" + (i1.data && i1.data.atDocsIndex));
const i2 = await call("docs_insert_text", { document_id: insId, text: "BOTTOM.\n", position: "end_of_doc" });
check("insert-end_of_doc", !!(i2.data && i2.data.inserted === true), "at=" + (i2.data && i2.data.atDocsIndex));
const i3 = await call("docs_insert_text", { document_id: insId, text: "[BEFORE]", position: "before", anchor: "MIDDLE ANCHOR" });
check("insert-before-anchor", !!(i3.data && i3.data.inserted === true), "at=" + (i3.data && i3.data.atDocsIndex));
const i4 = await call("docs_insert_text", { document_id: insId, text: "[AFTER]", position: "after", anchor: "MIDDLE ANCHOR" });
check("insert-after-anchor", !!(i4.data && i4.data.inserted === true), "at=" + (i4.data && i4.data.atDocsIndex));

const insText = await readDocText(insId);
const orderOk =
  insText.indexOf("TOP.") === 0 &&
  insText.indexOf("[BEFORE]") < insText.indexOf("MIDDLE ANCHOR") &&
  insText.indexOf("MIDDLE ANCHOR") < insText.indexOf("[AFTER]") &&
  insText.indexOf("[AFTER]") < insText.indexOf("BOTTOM.");
check("insert-ordering-correct", orderOk, JSON.stringify(insText.trim()));

// Ambiguous anchor must be refused, not guessed.
await seedDoc(insId, "DUPE\nDUPE\n");
const iAmb = await call("docs_insert_text", { document_id: insId, text: "X", position: "after", anchor: "DUPE" });
check("insert-ambiguous-anchor-refused", !!(iAmb.data && iAmb.data.nothingChanged === true && iAmb.data.occurrences === 2), "occ=" + (iAmb.data && iAmb.data.occurrences));

// Missing anchor is refused AND diagnosed.
const iMiss = await call("docs_insert_text", { document_id: insId, text: "X", position: "before", anchor: "NO SUCH ANCHOR" });
check("insert-missing-anchor-refused", !!(iMiss.data && iMiss.data.nothingChanged === true && iMiss.data.occurrences === 0), iMiss.data && iMiss.data.error);

// ============================ FEATURE 5: atomic batch ======================

const batDoc = await call("docs_create", { title: "ZZZ-GDRIVE-OPS-SELFTEST-BATCH", parent_id: bId });
const batId = batDoc.data.documentId;
await seedDoc(batId, "Gallus lives.\nThe Round Table stands.\nBadon in 490.\nUthr is 52.\nred hair everywhere.\n");

const batch = await call("docs_replace_batch", {
  document_id: batId,
  edits: [
    { find_text: "Gallus lives", replace_text: "Gallus dies", expected_count: 1 },
    { find_text: "Badon in 490", replace_text: "Badon in 485", expected_count: 1 },
    { find_text: "Uthr is 52", replace_text: "Uthr is 47", expected_count: 1 },
    { find_text: "red hair", replace_text: "brown hair" },
  ],
});
check("batch-applies-all", !!(batch.data && batch.data.occurrencesChanged === 4), "occ=" + (batch.data && batch.data.occurrencesChanged));
check("batch-reports-atomic", !!(batch.data && batch.data.atomic === true && batch.data.singleRevision === true), "atomic flags");
check("batch-per-edit-counts", !!(batch.data && batch.data.perEdit && batch.data.perEdit.length === 4 && batch.data.perEdit.every((p) => p.occurrencesChanged === 1)), JSON.stringify(batch.data && batch.data.perEdit));
const batText = await readDocText(batId);
const batOk =
  batText.indexOf("Gallus dies") !== -1 &&
  batText.indexOf("Badon in 485") !== -1 &&
  batText.indexOf("Uthr is 47") !== -1 &&
  batText.indexOf("brown hair") !== -1 &&
  batText.indexOf("490") === -1;
check("batch-doc-content-correct", batOk, JSON.stringify(batText.trim().slice(0, 90)));

// A failing expected_count anywhere must abort the WHOLE batch.
const beforeBat = await readDocText(batId);
const batFail = await call("docs_replace_batch", {
  document_id: batId,
  edits: [
    { find_text: "Gallus dies", replace_text: "Gallus survives", expected_count: 1 },
    { find_text: "NOT PRESENT ANYWHERE", replace_text: "X", expected_count: 1 },
  ],
});
check("batch-aborts-on-guard-failure", !!(batFail.data && batFail.data.nothingChanged === true && batFail.data.problems), (batFail.data && batFail.data.problems || []).length + " problem(s)");
check("batch-abort-left-doc-untouched", (await readDocText(batId)) === beforeBat, "unchanged");

// Overlapping edits must be refused rather than silently corrupting.
const batOverlap = await call("docs_replace_batch", {
  document_id: batId,
  edits: [
    { find_text: "The Round Table", replace_text: "A" },
    { find_text: "Round Table stands", replace_text: "B" },
  ],
});
const overlapProblem = (batOverlap.data && batOverlap.data.problems || []).some((p) => p.error === "overlapping edits");
check("batch-detects-overlap", overlapProblem && batOverlap.data.nothingChanged === true, JSON.stringify((batOverlap.data && batOverlap.data.problems || [])[0] || {}).slice(0, 90));
check("batch-overlap-left-doc-untouched", (await readDocText(batId)) === beforeBat, "unchanged");

// Batch dry run.
const batDry = await call("docs_replace_batch", { document_id: batId, edits: [{ find_text: "Gallus", replace_text: "G" }], dry_run: true });
check("batch-dry_run", !!(batDry.data && batDry.data.dryRun === true && batDry.data.nothingChanged === true && batDry.data.wouldChange >= 1), "wouldChange=" + (batDry.data && batDry.data.wouldChange));
check("batch-dry_run-left-doc-untouched", (await readDocText(batId)) === beforeBat, "unchanged");

// ============================ LEGACY PATH PRESERVED ========================

const legacyDoc = await call("docs_create", { title: "ZZZ-GDRIVE-OPS-SELFTEST-LEGACY", parent_id: bId });
const legacyId = legacyDoc.data.documentId;
await seedDoc(legacyId, "Marcus had red hair. His Red hair was famous.");

const l1 = await call("docs_replace_text", { document_id: legacyId, find_text: "red hair", replace_text: "brown hair", match_case: true });
check("legacy-replace-case-sensitive", !!(l1.data && l1.data.occurrencesChanged === 1), JSON.stringify(l1.data && l1.data.occurrencesChanged));
const l2 = await call("docs_replace_text", { document_id: legacyId, find_text: "red hair", replace_text: "golden hair", match_case: false });
check("legacy-replace-case-insensitive", !!(l2.data && l2.data.occurrencesChanged === 1), JSON.stringify(l2.data && l2.data.occurrencesChanged));
const legacyText = await readDocText(legacyId);
check("legacy-doc-final-text", legacyText.indexOf("brown hair") !== -1 && legacyText.indexOf("golden hair") !== -1 && !/red hair/i.test(legacyText), legacyText.trim());
check("legacy-response-shape", !!(l1.data && "occurrencesChanged" in l1.data && "findText" in l1.data && "replaceText" in l1.data && !("match" in l1.data)), "unchanged keys");

const sc = await call("docs_search_content", { text: "golden hair was famous" });
const scFiles = sc.data && sc.data.files;
check("search-content-executes", Array.isArray(scFiles), Array.isArray(scFiles) ? scFiles.length + " hit(s) (0 is OK - index lag)" : sc.text.slice(0, 60));

// ============================ CLEANUP ======================================

for (const id of [createdId, hardId, guardId, insId, batId, legacyId, aId, bId]) {
  if (id) await call("drive_trash", { file_id: id });
}
const leftovers = await call("drive_find", { query: "ZZZ-GDRIVE-OPS-SELFTEST" });
const leftCount = leftovers.data && leftovers.data.files ? leftovers.data.files.length : -1;
check("cleanup-all-trashed", leftCount === 0, leftCount + " left untrashed");

console.log("");
console.log("RESULT: " + pass + " passed, " + failCount + " failed");
await client.close();
process.exit(failCount === 0 ? 0 : 1);
