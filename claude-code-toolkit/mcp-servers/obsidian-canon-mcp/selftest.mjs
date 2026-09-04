// selftest.mjs - drives server.js over real MCP stdio exactly as Claude Desktop does.
// Run: node selftest.mjs        (exit 0 = every check passed)
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [path.join(here, "server.js")],
  stderr: "pipe",
});
const client = new Client({ name: "selftest", version: "1.0.0" });
await client.connect(transport);

let failures = 0;
function check(name, cond, detail) {
  const tag = cond ? "PASS" : "FAIL";
  if (!cond) failures++;
  console.log(tag + "  " + name + (detail ? "  -- " + detail : ""));
}
async function call(name, args) {
  const r = await client.callTool({ name, arguments: args || {} });
  const text = r.content && r.content[0] && r.content[0].text;
  if (r.isError) return { error: text };
  try {
    return JSON.parse(text);
  } catch (e) {
    return { raw: text };
  }
}

const tools = await client.listTools();
const names = tools.tools.map((t) => t.name).sort();
console.log("tools: " + names.join(", "));
const expected = [
  "canon_info", "canon_list", "canon_read", "canon_grep", "canon_topic", "canon_lookup", "canon_outline",
  "canon_graph", "canon_history", "canon_diff", "canon_images", "canon_pull", "obsidian_search", "obsidian_cli",
];
check("all 14 tools registered", expected.every((n) => names.includes(n)) && names.length === expected.length, names.length + " tools");

const info = await call("canon_info");
check("canon_info", info.google_docs_live > 100 && /^ok/.test(info.search_selfcheck || ""), "live docs=" + info.google_docs_live + " last_pull=" + (info.last_pull || "").slice(0, 40) + " obsidian_running=" + info.obsidian_running);

const list = await call("canon_list", { query: "butterfly" });
check("canon_list query=butterfly", list.total >= 1, list.total + " files: " + (list.files || []).map((f) => f.path).join(" | ").slice(0, 200));

const topic = await call("canon_topic", { topic: "Butterfly Dragon" });
check("canon_topic Butterfly Dragon", topic.docs_matched >= 3 && topic.read_in_full_next.length >= 1, "docs=" + topic.docs_matched + " mentions=" + topic.total_mentions + " read_next=" + topic.read_in_full_next.slice(0, 3).join(" | "));

check("canon_list carries Drive ids", (list.files || []).some((f) => f.drive_id), (list.files || []).map((f) => f.drive_id).join(","));
check("canon_topic ranks the SPECIFICATION for full read", topic.read_in_full_next.some((p) => /SPECIFICATION\.txt$/.test(p)), topic.read_in_full_next.join(" | ").slice(0, 300));
check("canon_topic hides raw html when a twin exists", !topic.docs.some((d) => /\.html$/.test(d.file)), "");

const board = await call("canon_read", { file: "MANEUVER BOARD", limit: 3 });
check("canon_read html board -> derived .md twin", board.file && /\.html\.md$/.test(board.file.path), board.file ? board.file.path : board.error);

const spec = topic.read_in_full_next.find((p) => /SPECIFICATION\.txt$/i.test(p)) || topic.read_in_full_next[0];
const whole = await call("canon_read", { file: spec, whole: true });
check("canon_read whole=true on the spec", whole.done === true && whole.total_lines > 10 && whole.text.length === whole.text.length, spec + " lines=" + whole.total_lines + " chars=" + whole.total_chars);

const paged = await call("canon_read", { file: spec, offset: 1, limit: 5 });
check("canon_read paged", paged.done === false && paged.next_offset === 6 && paged.text.split("\n").length === 5, "next_offset=" + paged.next_offset);

const byFrag = await call("canon_read", { file: "BUTTERFLY DRAGON", limit: 3 });
check("canon_read by name fragment", !byFrag.error || /ambiguous/.test(byFrag.error), byFrag.error ? byFrag.error.split("\n")[0] : byFrag.file.path);

const md = await call("canon_read", { file: spec, format: "md", limit: 3 });
check("canon_read format=md twin", md.file && md.file.path.endsWith(".md"), md.file && md.file.path);

const g = await call("canon_grep", { pattern: "Commander's Sword", context: 1 });
check("canon_grep literal", g.total_matches > 0 && g.results[0].matches[0].line > 0, "files=" + g.files_matched + " matches=" + g.total_matches);

const gr = await call("canon_grep", { pattern: "R-15[0-9]", regex: true, context: 0, max_matches: 20 });
check("canon_grep regex", gr.total_matches > 0, "matches=" + gr.total_matches);

const ga = await call("canon_grep", { pattern: "Valerius", live_only: false, context: 0, max_files: 5 });
check("canon_grep live_only=false widens", ga.files_searched > g.files_searched, ga.files_searched + " > " + g.files_searched);

const lk = await call("canon_lookup", { query: "BUTTERFLY" });
check("canon_lookup name", lk.total >= 1 && lk.entries[0].id, lk.entries[0] && lk.entries[0].id + " " + lk.entries[0].name);

const lkId = await call("canon_lookup", { query: lk.entries[0].id });
check("canon_lookup by id", lkId.total === 1 && lkId.entries[0].local_files.length >= 1, (lkId.entries[0].local_files || [])[0]);

const readById = await call("canon_read", { file: lk.entries[0].id, limit: 2 });
check("canon_read by Drive id", readById.file && readById.file.drive_id === lk.entries[0].id, readById.file && readById.file.path);

const ol = await call("canon_outline", { file: "INDEX" });
check("canon_outline INDEX", ol.headings && ol.headings.length > 5, (ol.headings || []).length + " headings");

const links = await call("canon_graph", { op: "links", file: "INDEX" });
check("canon_graph links INDEX", links.total > 100, links.total + " links, unresolved=" + (links.links || []).filter((l) => !l.resolved).length);

const bl = await call("canon_graph", { op: "backlinks", file: spec });
check("canon_graph backlinks spec", bl.total >= 1 && bl.backlinks.includes("INDEX.md"), (bl.backlinks || []).join(" | "));

const un = await call("canon_graph", { op: "unresolved" });
check("canon_graph unresolved", typeof un.total === "number", un.total + " unresolved");

const orph = await call("canon_graph", { op: "orphans" });
check("canon_graph orphans", typeof orph.total === "number", orph.total + " orphans");

const hist = await call("canon_history", { n: 3 });
check("canon_history", hist.total === 3 && hist.commits[0].hash, hist.commits[0] && hist.commits[0].subject.slice(0, 60));

const hf = await call("canon_history", { file: spec, n: 5 });
check("canon_history per file", hf.total >= 1, hf.total + " commits touch " + spec.slice(0, 50));

const df = await call("canon_diff", { file: spec });
check("canon_diff", typeof df.diff === "string", (df.diff || "").length + " chars");

const im = await call("canon_images", { query: "pauldron green" });
check("canon_images", im.total >= 1 && im.images[0].link, im.total + " images; " + (im.images[0] && im.images[0].name || "").slice(0, 60));

const pull = await call("canon_pull", { dry_run: true, wait_seconds: 50 });
check("canon_pull dry_run starts + reports", !pull.error && /running|done|failed/.test(pull.status), "status=" + pull.status + " " + (pull.summary || []).slice(-2).join(" / ").slice(0, 160));
let pullFinal = pull;
for (let i = 0; i < 12 && pullFinal.status === "running"; i++) pullFinal = await call("canon_pull", { status: true, wait_seconds: 50 });
check("canon_pull dry_run completes", pullFinal.status === "done", "status=" + pullFinal.status + " " + (pullFinal.summary || []).slice(-3).join(" / ").slice(0, 240));

const esc = await call("canon_read", { file: "../../secret.txt" });
check("path escape rejected", !!esc.error, (esc.error || "").slice(0, 80));

const cliBad = await call("obsidian_cli", { command: "delete", args: { file: "INDEX" } });
check("obsidian_cli refuses write command", /whitelist/.test(cliBad.error || ""), (cliBad.error || "").slice(0, 80));

const cliOpen = await call("obsidian_cli", { command: "search:open", args: { query: "x" } });
check("obsidian_cli refuses UI command", /whitelist/.test(cliOpen.error || ""), (cliOpen.error || "").slice(0, 80));

if (info.obsidian_running) {
  const os = await call("obsidian_search", { query: "Commander's Sword", limit: 3 });
  check("obsidian_search (app running)", os.results && os.results.length > 0, "engine=" + os.engine);
  const oc = await call("obsidian_cli", { command: "vault" });
  check("obsidian_cli vault", /canon-mirror/.test(JSON.stringify(oc.output)), String(oc.output).slice(0, 60));
} else {
  const os = await call("obsidian_search", { query: "x" });
  check("obsidian_search explains app not running", /not running/.test(os.error || ""), (os.error || "").slice(0, 80));
}

await client.close();
console.log(failures ? "\n" + failures + " FAILURE(S)" : "\nALL PASSED");
process.exit(failures ? 1 : 0);
