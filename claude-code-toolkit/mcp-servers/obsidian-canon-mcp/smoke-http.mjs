// smoke-http.mjs - drives the HTTP-mode server over real MCP Streamable HTTP exactly as claude.ai's
// connector client does: initialize, tools/list, canon_info, canon_topic "Butterfly Dragon".
// Run: node smoke-http.mjs                 (local: reads ~/.obsidian-canon/http-secret, port 8790)
//      node smoke-http.mjs <full url>      (e.g. the public https://xxx.ngrok-free.app/mcp/<secret>)
// Exit 0 = every check passed. Also probes that a wrong secret gets 404 (not 401).
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const secretFile = path.join(os.homedir(), ".obsidian-canon", "http-secret");
let url = process.argv[2];
if (!url) {
  const secret = fs.readFileSync(secretFile, "utf8").trim();
  url = "http://127.0.0.1:8790/mcp/" + secret;
}
const base = url.replace(/\/mcp\/[^/]+\/?$/, "");
console.log("target " + base + "/mcp/<secret>");

let failures = 0;
function check(name, cond, detail) {
  const tag = cond ? "PASS" : "FAIL";
  if (!cond) failures++;
  console.log(tag + "  " + name + (detail ? "  -- " + detail : ""));
}

// 1. wrong secret must be a plain 404 with no OAuth hint
const bad = await fetch(base + "/mcp/wrong-secret", {
  method: "POST",
  headers: { "content-type": "application/json", accept: "application/json, text/event-stream" },
  body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "initialize", params: {} }),
});
check("wrong secret -> 404", bad.status === 404, "status=" + bad.status);
check("no WWW-Authenticate on 404", !bad.headers.get("www-authenticate"));

// 2. healthz
const hz = await fetch(base + "/healthz");
const hzText = await hz.text();
check("/healthz 200", hz.status === 200, hzText.trim());

// 3. real MCP session
const t0 = Date.now();
const transport = new StreamableHTTPClientTransport(new URL(url));
const client = new Client({ name: "smoke-http", version: "1.0.0" });
await client.connect(transport);
check("initialize over Streamable HTTP", true, (Date.now() - t0) + " ms");

const tools = await client.listTools();
const names = tools.tools.map((t) => t.name);
check("tools/list >= 23 tools", names.length >= 23, names.length + " tools");
for (const n of ["canon_info", "canon_topic", "canon_read", "canon_section", "canon_semantic", "canon_rulings"]) {
  check("tool present: " + n, names.includes(n));
}

async function call(name, args) {
  const r = await client.callTool({ name, arguments: args || {} });
  const text = r.content[0].text;
  if (r.isError) throw new Error(text);
  return JSON.parse(text);
}

const info = await call("canon_info", {});
check("canon_info answers", info && typeof info === "object", "vault=" + (info.vault || info.path || "?"));

const t1 = Date.now();
const topic = await call("canon_topic", { topic: "Butterfly Dragon", aliases: ["Butterfly", "Papilio"] });
check(
  "canon_topic Butterfly Dragon finds docs",
  topic.docs_matched > 0 && Array.isArray(topic.read_in_full_next) && topic.read_in_full_next.length > 0,
  topic.docs_matched + " docs, " + topic.total_mentions + " mentions, " + (Date.now() - t1) + " ms"
);
if (topic.read_in_full_next && topic.read_in_full_next.length) {
  const d = await call("canon_read", { file: topic.read_in_full_next[0], whole: true });
  check("canon_read whole doc returns text", typeof d.text === "string" && d.total_chars > 1000, d.total_chars + " chars");
}

// 4. a second, independent session must work (stateless: fresh server per request, no session id needed)
const t2 = new StreamableHTTPClientTransport(new URL(url));
const c2 = new Client({ name: "smoke-http-2", version: "1.0.0" });
await c2.connect(t2);
const l2 = await c2.listTools();
check("second concurrent client sees the same tools", l2.tools.length === names.length);
await c2.close();
await client.close();

console.log(failures === 0 ? "ALL PASSED" : failures + " FAILED");
process.exit(failures === 0 ? 0 : 1);
