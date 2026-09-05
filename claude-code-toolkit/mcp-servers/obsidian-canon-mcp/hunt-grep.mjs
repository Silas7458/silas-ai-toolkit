// hunt-grep.mjs - runs a list of canon_grep patterns (live docs only) over MCP stdio and
// prints every hit with doc + line. Run: node hunt-grep.mjs <patterns.json> [context]
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const patterns = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const ctx = Number(process.argv[3] || 0);

const transport = new StdioClientTransport({ command: process.execPath, args: [path.join(here, "server.js")], stderr: "pipe" });
const client = new Client({ name: "hunt-grep", version: "1.0.0" });
await client.connect(transport);

for (const p of patterns) {
  const args = Object.assign({ context: ctx, max_matches: 400 }, typeof p === "string" ? { pattern: p } : p);
  const r = await client.callTool({ name: "canon_grep", arguments: args });
  const text = r.content && r.content[0] && r.content[0].text;
  let j;
  try { j = JSON.parse(text); } catch (e) { j = { raw: text }; }
  console.log("\n##### " + JSON.stringify(args));
  if (j.error) { console.log("ERROR " + j.error); continue; }
  const files = j.files || j.results || j.matches || [];
  let n = 0;
  for (const f of files) {
    const hits = f.matches || f.hits || f.lines || [];
    for (const h of hits) {
      n++;
      const line = h.line || h.lineno || h.n;
      const txt = (h.text || h.content || h.snippet || "").replace(/\s+/g, " ");
      console.log("  " + String(f.path || f.file || f.doc).replace(/^canon\//, "").slice(0, 70) + ":" + line + "  " + txt.slice(0, 260));
    }
  }
  if (!n) console.log("  (no live hits)  keys=" + Object.keys(j).join(","));
}
await client.close();
process.exit(0);
