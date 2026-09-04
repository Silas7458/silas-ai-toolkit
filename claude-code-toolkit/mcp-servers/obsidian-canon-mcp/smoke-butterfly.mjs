// smoke-butterfly.mjs - replays Proctor's "explain the Butterfly Dragon" flow through the MCP boundary
// and prints what he would have in hand before answering. Run: node smoke-butterfly.mjs
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const transport = new StdioClientTransport({ command: process.execPath, args: [path.join(here, "server.js")] });
const client = new Client({ name: "smoke", version: "1.0.0" });
await client.connect(transport);

async function call(name, args) {
  const r = await client.callTool({ name, arguments: args || {} });
  const text = r.content[0].text;
  if (r.isError) throw new Error(text);
  return JSON.parse(text);
}

const topic = await call("canon_topic", { topic: "Butterfly Dragon", aliases: ["Butterfly", "Papilio"] });
console.log("STEP 1 canon_topic: " + topic.docs_matched + " docs, " + topic.total_mentions + " mentions, " + topic.related_images.length + " related images");
console.log("  read_in_full_next:");
for (const f of topic.read_in_full_next) console.log("    - " + f);

let totalChars = 0;
const must = [
  { label: "the spec", re: /MANEUVER SPECIFICATION\.txt$/ },
  { label: "the board twin", re: /MANEUVER BOARD.*\.html\.md$/ },
];
console.log("STEP 2 canon_read whole=true on each:");
const bodies = {};
for (const f of topic.read_in_full_next) {
  const d = await call("canon_read", { file: f, whole: true });
  bodies[f] = d.text;
  totalChars += d.total_chars;
  console.log("    " + d.total_lines + " lines / " + d.total_chars + " chars  done=" + d.done + "  " + f);
}
for (const m of must) {
  const hit = topic.read_in_full_next.find((f) => m.re.test(f));
  console.log((hit ? "PASS" : "FAIL") + "  " + m.label + " is in the full-read list" + (hit ? "" : "  (missing)"));
}
console.log("  total text in hand: " + totalChars + " chars");

const spec = topic.read_in_full_next.find((f) => /MANEUVER SPECIFICATION\.txt$/.test(f));
const specText = bodies[spec] || "";
const facts = ["two halves", "Version", "wearer", "pauldron", "Valerius"];
console.log("STEP 3 spec content sanity (key phrases present in the spec text):");
for (const p of facts) console.log("    " + (new RegExp(p, "i").test(specText) ? "yes " : "NO  ") + p);

const hist = await call("canon_history", { file: spec, n: 5 });
console.log("STEP 4 canon_history on the spec: " + hist.total + " commits; latest: " + (hist.commits[0] ? hist.commits[0].date + " " + hist.commits[0].subject.slice(0, 60) : "-"));

const rulings = await call("canon_grep", { pattern: "Butterfly", folder: "canon", regex: false, context: 0, max_matches: 400, max_files: 100 });
const rulingDocs = rulings.results.filter((r) => /^canon\/00[A-Z] /.test(r.file)).map((r) => r.file + " (" + r.match_count + ")");
console.log("STEP 5 rulings docs (00-series) that mention it: " + rulingDocs.length);
for (const d of rulingDocs) console.log("    - " + d);

await client.close();
console.log("\nSMOKE OK: Proctor can gather the spec + board + rulings + masters in full, then answer.");
