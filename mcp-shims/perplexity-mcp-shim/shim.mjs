#!/usr/bin/env node
/**
 * perplexity-mcp-shim
 *
 * WHY THIS EXISTS
 *   @perplexity-ai/mcp-server@1.2.0 declares every tool's inputSchema AND outputSchema
 *   with "$schema": "http://json-schema.org/draft-07/schema#".
 *   Claude Desktop's tool validator accepts JSON Schema 2020-12 ONLY, so every call is
 *   rejected client-side with:
 *     invalid outputSchema: JSON Schema declares an unsupported dialect ("draft-07")
 *   before the request ever reaches Perplexity.
 *
 *   The package exposes no flag to change or omit the schema (checked: only
 *   PERPLEXITY_API_KEY / BASE_URL / LOG_LEVEL / TIMEOUT_MS / PROXY are read), and 1.2.0 is
 *   the newest published version. So we relabel the dialect in transit.
 *
 * IS RELABELLING SAFE?
 *   Yes for these schemas. They use only type / properties / required /
 *   additionalProperties / description / enum / items, all of which mean exactly the same
 *   thing in draft-07 and 2020-12. Nothing here uses the constructs that actually changed
 *   between dialects (definitions vs $defs, exclusiveMinimum form, items/prefixItems tuples).
 *
 * WHAT IT DOES
 *   Transparent stdio proxy. Spawns the real server, forwards stdin untouched, and rewrites
 *   only the "$schema" string on the way back. Everything else passes through unchanged.
 *   Non-JSON lines and partial lines are preserved.
 *
 * Built 2026-08-12, Session #310.
 */

import { spawn } from "node:child_process";

const D2020 = "https://json-schema.org/draft/2020-12/schema";

function relabel(node) {
  if (Array.isArray(node)) {
    for (const v of node) relabel(v);
    return node;
  }
  if (node && typeof node === "object") {
    if (typeof node.$schema === "string" && node.$schema.includes("draft-07")) {
      node.$schema = D2020;
    }
    for (const k of Object.keys(node)) relabel(node[k]);
  }
  return node;
}

// Node 18.20+/20.12+/22 refuse to spawn .cmd shims directly on Windows (EINVAL),
// so go through the comspec explicitly, exactly as the Desktop config used to.
const isWin = process.platform === "win32";
const child = isWin
  ? spawn(process.env.ComSpec || "cmd.exe",
      ["/c", "npx", "-y", "@perplexity-ai/mcp-server"],
      { stdio: ["pipe", "pipe", "inherit"], env: process.env, windowsHide: true })
  : spawn("npx", ["-y", "@perplexity-ai/mcp-server"],
      { stdio: ["pipe", "pipe", "inherit"], env: process.env });

process.stdin.pipe(child.stdin);

let buf = "";
child.stdout.on("data", (chunk) => {
  buf += chunk.toString("utf8");
  let nl;
  while ((nl = buf.indexOf("\n")) !== -1) {
    const line = buf.slice(0, nl);
    buf = buf.slice(nl + 1);
    const trimmed = line.trim();
    if (!trimmed.startsWith("{")) {
      process.stdout.write(line + "\n");
      continue;
    }
    try {
      const msg = JSON.parse(trimmed);
      relabel(msg);
      process.stdout.write(JSON.stringify(msg) + "\n");
    } catch {
      process.stdout.write(line + "\n"); // not JSON, pass through untouched
    }
  }
});

child.stdout.on("end", () => {
  if (buf.length) process.stdout.write(buf);
});

child.on("exit", (code, signal) => {
  process.exit(code === null ? (signal ? 1 : 0) : code);
});

for (const sig of ["SIGINT", "SIGTERM"]) {
  process.on(sig, () => { try { child.kill(sig); } catch {} });
}
