# mcp-schema-shim

Claude Desktop's tool validator accepts JSON Schema 2020-12 only. Servers built on zod-to-json-schema with default
settings stamp `"$schema": "http://json-schema.org/draft-07/schema#"` on every tool's input and output schema; the
tools list fine and then EVERY call is rejected client-side ("invalid outputSchema: JSON Schema declares an
unsupported dialect"). Claude Code accepts draft-07, so Brother never sees the failure - Proctor does.

Known offenders: `@modelcontextprotocol/server-filesystem` 2026.7.10 (the Desktop "Filesystem" extension) and
2026.8.31 (newest); `@perplexity-ai/mcp-server` 1.2.0 (see ../perplexity-mcp-shim, the S#310 original).

`shim.mjs` is a transparent stdio proxy: it spawns the real server (the command after `--`), forwards stdin
untouched, and rewrites only `$schema` strings on the way back.

    node shim.mjs --check -- node node_modules/@modelcontextprotocol/server-filesystem/dist/index.js C:\some\dir
    node shim.mjs -- node node_modules/@modelcontextprotocol/server-filesystem/dist/index.js C:\dir1 C:\dir2

`--check` lists the tool count, how many schemas were relabelled, whether any draft-07 leaked, and flags the
constructs that DO differ between dialects (definitions, boolean exclusiveMinimum, tuple items, $ref into
definitions) - relabelling is only safe when it reports none.

Desktop config entry (claude_desktop_config.json, mcpServers):

    "filesystem": { "command": "C:\Program Files\nodejs\node.exe",
                    "args": ["C:\Users\<you>\tools\mcp-schema-shim\shim.mjs", "--",
                             "C:\Program Files\nodejs\node.exe",
                             "C:\Users\<you>\tools\mcp-schema-shim\node_modules\@modelcontextprotocol\server-filesystem\dist\index.js",
                             "C:\dir1", "C:\dir2"] }

Disable the built-in Filesystem extension (Settings > Extensions) so two identically named tool sets do not
coexist. Remove the shim when upstream ships 2020-12 schemas. Built S#328 (6 Sep 2026).
