# perplexity-mcp-shim

Makes `@perplexity-ai/mcp-server` usable from **Claude Desktop**.

## The problem

`@perplexity-ai/mcp-server@1.2.0` stamps every tool schema with:

```
"$schema": "http://json-schema.org/draft-07/schema#"
```

That is on **all 8 schemas** (4 tools x inputSchema + outputSchema). Claude Desktop's tool
validator accepts **JSON Schema 2020-12 only**, so every call is rejected client-side:

```
invalid outputSchema: JSON Schema declares an unsupported dialect ("draft-07").
The default validator supports JSON Schema 2020-12 only.
```

The tools still *list* fine, which makes this misleading - tool visibility is not proof the
tools work.

**Claude Code accepts draft-07**, so the same server works there unchanged. The fault is
Desktop-side validation, not the server, the API key, or the MCP bridge.

## Why a shim

The package exposes no way to change or omit the schema - it reads only
`PERPLEXITY_API_KEY`, `PERPLEXITY_BASE_URL`, `PERPLEXITY_LOG_LEVEL`,
`PERPLEXITY_TIMEOUT_MS`, `PERPLEXITY_PROXY` - and 1.2.0 is the newest published version.

## What it does

Transparent stdio proxy: spawns the real server, forwards stdin untouched, and rewrites only
the `$schema` string on the way back. Everything else passes through unchanged.

Relabelling is safe for these schemas: they use only `type` / `properties` / `required` /
`additionalProperties` / `description` / `enum` / `items`, all identical in meaning across
both dialects. If Perplexity later adds `$defs` or tuple-form `items`, revisit.

## Install

```json
"perplexity": {
  "command": "node",
  "args": ["C:\path\to\shim.mjs"],
  "env": { "PERPLEXITY_API_KEY": "pplx-..." }
}
```

Restart Claude Desktop, then make a **real call** - listing tools proves nothing.

## Windows gotcha

Node 18.20+/20.12+/22 refuse to spawn `.cmd` shims directly (`spawn EINVAL`). The shim routes
through `ComSpec`. Any stdio wrapper on Windows hits this.

Built 2026-08-12.
