#!/usr/bin/env node
/**
 * mcp-schema-shim - generic JSON Schema dialect relabeller for stdio MCP servers.
 *
 * WHY THIS EXISTS
 *   Claude Desktop's tool validator accepts JSON Schema 2020-12 ONLY. Any MCP server whose tools
 *   declare "$schema": "http://json-schema.org/draft-07/schema#" (everything built on
 *   zod-to-json-schema with default settings: @modelcontextprotocol/server-filesystem 2026.7.10 and
 *   2026.8.31, @perplexity-ai/mcp-server 1.2.0, ...) loads its tool list fine and then has EVERY call
 *   rejected client-side:
 *     invalid outputSchema: JSON Schema declares an unsupported dialect ("draft-07")
 *   Claude Code accepts draft-07, so the fault only shows in Desktop.
 *
 * WHAT IT DOES
 *   Transparent stdio proxy. Spawns the real server (the command after "--"), forwards stdin
 *   untouched, and rewrites only "$schema" strings on the way back. Everything else passes through
 *   byte-for-byte; non-JSON lines are preserved.
 *
 * IS RELABELLING SAFE?
 *   Only for schemas that use constructs meaning the same thing in both dialects (type, properties,
 *   required, additionalProperties, description, enum, items-as-object, default, minimum/maximum
 *   as numbers). Verify a new target with:  node shim.mjs --check -- <server command...>
 *   which lists every tool and flags dialect-sensitive constructs (definitions, boolean
 *   exclusiveMinimum/Maximum, tuple-form items, $ref into definitions).
 *
 * USAGE
 *   node shim.mjs -- node path/to/server.js arg1 arg2 ...
 *   node shim.mjs --check -- node path/to/server.js arg1 ...
 *
 * S#310 (perplexity, 12 Aug 2026) generalized in S#328 (filesystem, 6 Sep 2026).
 */

import { spawn } from "node:child_process";

const D2020 = "https://json-schema.org/draft/2020-12/schema";
const NL = String.fromCharCode(10);

const argv = process.argv.slice(2);
const check = argv[0] === "--check";
const sep = argv.indexOf("--");
if (sep < 0 || sep === argv.length - 1) {
  process.stderr.write("usage: node shim.mjs [--check] -- <server command> [args...]" + NL);
  process.exit(64);
}
const cmd = argv[sep + 1];
const cmdArgs = argv.slice(sep + 2);

function relabel(node, stats) {
  if (Array.isArray(node)) {
    for (const v of node) relabel(v, stats);
    return node;
  }
  if (node && typeof node === "object") {
    if (typeof node.$schema === "string" && node.$schema.indexOf("draft-07") >= 0) {
      node.$schema = D2020;
      if (stats) stats.relabelled++;
    }
    for (const k of Object.keys(node)) relabel(node[k], stats);
  }
  return node;
}

// dialect-sensitive constructs: report them, never rewrite them
function audit(node, path, out) {
  if (Array.isArray(node)) {
    node.forEach((v, i) => audit(v, path + "[" + i + "]", out));
    return;
  }
  if (!node || typeof node !== "object") return;
  if (Object.prototype.hasOwnProperty.call(node, "definitions")) out.push(path + ": 'definitions' (2020-12 uses $defs)");
  if (typeof node.exclusiveMinimum === "boolean" || typeof node.exclusiveMaximum === "boolean") out.push(path + ": boolean exclusiveMinimum/Maximum");
  if (Array.isArray(node.items)) out.push(path + ": tuple-form items (2020-12 uses prefixItems)");
  if (typeof node.$ref === "string" && node.$ref.indexOf("#/definitions/") === 0) out.push(path + ": $ref into definitions");
  for (const k of Object.keys(node)) audit(node[k], path + "." + k, out);
}

const isWin = process.platform === "win32";
// Node 18.20+/20.12+/22 refuse to spawn .cmd/.bat shims directly on Windows (EINVAL): go through ComSpec for those
const needsShell = isWin && /\.(cmd|bat)$/i.test(cmd);
const child = needsShell
  ? spawn(process.env.ComSpec || "cmd.exe", ["/c", cmd].concat(cmdArgs), { stdio: ["pipe", "pipe", "inherit"], env: process.env, windowsHide: true })
  : spawn(cmd, cmdArgs, { stdio: ["pipe", "pipe", "inherit"], env: process.env, windowsHide: true });

child.on("error", (e) => {
  process.stderr.write("mcp-schema-shim: cannot start " + cmd + ": " + e.message + NL);
  process.exit(1);
});

if (!check) process.stdin.pipe(child.stdin);

let buf = "";
child.stdout.on("data", (chunk) => {
  buf += chunk.toString("utf8");
  let nl;
  while ((nl = buf.indexOf(NL)) !== -1) {
    const line = buf.slice(0, nl);
    buf = buf.slice(nl + 1);
    const trimmed = line.trim();
    if (!trimmed.startsWith("{")) {
      if (!check) process.stdout.write(line + NL);
      continue;
    }
    let msg;
    try {
      msg = JSON.parse(trimmed);
    } catch (e) {
      if (!check) process.stdout.write(line + NL);
      continue;
    }
    if (check) {
      if (msg.id === 2 && msg.result && msg.result.tools) {
        const stats = { relabelled: 0 };
        const findings = [];
        for (const t of msg.result.tools) audit(t, t.name, findings);
        relabel(msg, stats);
        const leaks = JSON.stringify(msg).indexOf("draft-07") >= 0;
        process.stdout.write("tools: " + msg.result.tools.length + "; $schema relabelled: " + stats.relabelled + "; draft-07 leaks after relabel: " + (leaks ? "YES" : "0") + NL);
        process.stdout.write(findings.length ? "DIALECT-SENSITIVE CONSTRUCTS:" + NL + findings.map((f) => "  " + f).join(NL) + NL : "no dialect-sensitive constructs - relabelling is safe" + NL);
        child.kill();
        process.exit(findings.length || leaks ? 1 : 0);
      }
      continue;
    }
    relabel(msg, null);
    process.stdout.write(JSON.stringify(msg) + NL);
  }
});

child.stdout.on("end", () => {
  if (buf.length && !check) process.stdout.write(buf);
});

child.on("exit", (code, signal) => {
  process.exit(code === null ? (signal ? 1 : 0) : code);
});

for (const sig of ["SIGINT", "SIGTERM"]) {
  process.on(sig, () => {
    try {
      child.kill(sig);
    } catch (e) {}
  });
}

if (check) {
  const send = (o) => child.stdin.write(JSON.stringify(o) + NL);
  send({ jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "mcp-schema-shim-check", version: "1.0" } } });
  setTimeout(() => {
    send({ jsonrpc: "2.0", method: "notifications/initialized" });
    send({ jsonrpc: "2.0", id: 2, method: "tools/list" });
  }, 800);
  setTimeout(() => {
    process.stdout.write("TIMEOUT waiting for tools/list" + NL);
    child.kill();
    process.exit(2);
  }, 20000);
}
