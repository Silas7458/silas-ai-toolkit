// probe-claims.mjs - S#328: reproduce the two canon_claims false-positive classes over real MCP stdio.
// Run: node probe-claims.mjs [Entity[:alias,alias] ...]   (default: the S#327 cases)
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const transport = new StdioClientTransport({ command: process.execPath, args: [path.join(here, "server.js")], stderr: "pipe" });
const client = new Client({ name: "probe-claims", version: "1.0.0" });
await client.connect(transport);

const specs = process.argv.slice(2).length ? process.argv.slice(2) : ["Gallus", "Valerius", "Dacus", "Portarius", "Felix", "Lucius:Lucius III", "Corvus", "Mardin"];
const FACTS = ["born (year)", "age at a point", "dies / falls (episode)", "age stated"];
for (const spec of specs) {
  const [entity, al] = spec.split(":");
  const aliases = al ? al.split(",") : undefined;
  const r = await client.callTool({ name: "canon_claims", arguments: { entity, aliases, max_examples: 6 } });
  const d = JSON.parse(r.content[0].text);
  console.log("\n##### " + entity + " (sentences " + d.sentences_scanned + ", conflicts " + d.conflicting_facts + ")");
  const show = (label, list) => {
    for (const c of list || []) {
      if (!FACTS.includes(c.fact)) continue;
      console.log("  [" + label + "] " + c.fact + ": " + c.values.map((v) => v.value + " x" + v.count).join(" | "));
      for (const v of c.values) for (const ex of v.examples || []) console.log("       " + v.value + " <- " + (ex.doc || "").split("/").pop().slice(0, 40) + ":" + ex.line + "  " + ex.sentence.slice(0, 170).replace(/\s+/g, " "));
    }
  };
  show("conflict", d.conflicts);
  for (const s of d.single_source_claims || []) {
    if (!FACTS.includes(s.fact)) continue;
    console.log("  [single] " + s.fact + ": " + s.value + " <- " + (s.doc || "").split("/").pop().slice(0, 40) + ":" + (s.example && s.example.line) + "  " + ((s.example && s.example.sentence) || "").slice(0, 170).replace(/\s+/g, " "));
  }
}
await client.close();
