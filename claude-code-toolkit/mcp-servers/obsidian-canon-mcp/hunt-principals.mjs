// hunt-principals.mjs - runs canon_claims over every principal of THE LAST ROMAN through the
// real MCP stdio boundary (same path Claude Desktop uses) and writes one JSON per entity plus a
// summary. Run: node hunt-principals.mjs <outdir>
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const outdir = process.argv[2] || path.join(here, "hunt-out");
fs.mkdirSync(outdir, { recursive: true });

const PRINCIPALS = [
  { entity: "Valerius", aliases: ["Valerius Flavius"] },
  { entity: "Ambrosius", aliases: ["Uthr", "Uther"] },
  { entity: "Mardin", aliases: ["Mardin Afzar"] },
  { entity: "Elen", aliases: ["Helena", "Helena Septimia"] },
  { entity: "Dacus", aliases: ["Sebastian Dacus", "the Whistler"] },
  { entity: "Felix", aliases: ["Aulus Felix", "Lucky"] },
  { entity: "Portarius", aliases: ["Titus Portarius"] },
  { entity: "Maro", aliases: ["Gaius Maro"] },
  { entity: "Cato", aliases: ["Rufus Cato"] },
  { entity: "Cassian", aliases: [] },
  { entity: "Gallus", aliases: [] },
  { entity: "Weyland", aliases: ["Weyland Lucilpus"] },
  { entity: "Lanceanus", aliases: ["Vitellius Lanceanus", "Lancelot"] },
  { entity: "Africanus", aliases: [] },
  { entity: "Galaad", aliases: ["Galahad", "Galaad Castus"] },
  { entity: "Percennius", aliases: ["Percival", "Percennius Vala"] },
  { entity: "Drustan", aliases: ["Tristan", "Drustan Cunomari"] },
  { entity: "Hengist", aliases: ["Hengest"] },
  { entity: "Vortigern", aliases: [] },
  { entity: "Wipped", aliases: ["Wipped"] },
  { entity: "Wulfhere", aliases: [] },
  { entity: "Aelle", aliases: ["Aelle Bretwalda"] },
  { entity: "Brutus", aliases: ["Brutus Septimius"] },
  { entity: "Lucia", aliases: [] },
  { entity: "Lucius", aliases: ["Lucius Aurelianus", "Lucius III"] },
  { entity: "Corvus", aliases: ["Gnaeus Corvus", "the Crow"] },
  { entity: "Sibylla", aliases: [] },
  { entity: "Lady of the Lake", aliases: ["the Lady"] },
  { entity: "Younger Brother", aliases: ["the younger brother"] },
];

const transport = new StdioClientTransport({
  command: process.execPath,
  args: [path.join(here, "server.js")],
  stderr: "pipe",
});
const client = new Client({ name: "hunt-principals", version: "1.0.0" });
await client.connect(transport);

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

const summary = [];
for (const p of PRINCIPALS) {
  const t0 = Date.now();
  const res = await call("canon_claims", { entity: p.entity, aliases: p.aliases, max_examples: 6 });
  const ms = Date.now() - t0;
  const slug = p.entity.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  fs.writeFileSync(path.join(outdir, slug + ".json"), JSON.stringify(res, null, 2));
  const row = {
    entity: p.entity,
    ms,
    error: res.error || null,
    sentences: res.sentences_scanned,
    records_excluded: res.record_sentences_excluded,
    docs: res.docs_with_mentions,
    conflicting_facts: res.conflicting_facts,
    conflicts: (res.conflicts || []).map((c) => c.fact + ": " + c.values.map((v) => v.value + " x" + v.count + "/" + v.docs + "d").join(" | ")),
    single_source: (res.single_source_claims || []).length,
  };
  summary.push(row);
  console.log(p.entity + "  " + ms + "ms  sentences=" + row.sentences + " docs=" + row.docs + " conflicts=" + row.conflicting_facts + " single=" + row.single_source + (row.error ? "  ERROR " + row.error.slice(0, 100) : ""));
}
fs.writeFileSync(path.join(outdir, "_summary.json"), JSON.stringify(summary, null, 2));
await client.close();
process.exit(0);
