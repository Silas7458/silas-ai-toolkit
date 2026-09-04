# obsidian-canon MCP server

Back-end access to THE LAST ROMAN canon mirror (the Obsidian vault at
`Documents/last-roman/canon-mirror`) for Claude Desktop / Proctor. Built S#326 (4 Sept 2026)
so Proctor can query the show the way Brother does from the terminal: grep, read, link graph,
git history, Drive-id lookup, image captions, and the sanctioned `lr-pull` refresh.

**Nothing in this server opens, focuses, restarts or launches the Obsidian window.**
The core tools are pure node over the files on disk and work with Obsidian closed.
The two `obsidian_*` tools talk to the official Obsidian CLI only when the app is already
running, through a strict read-only whitelist (no `open`, `search:open`, `restart`, `reload`,
`create`, `delete`, `move`, `append`, `eval`, ...).

## Install (already done on this machine)

```
cd C:\Users\silas\tools\obsidian-canon-mcp
npm install
node selftest.mjs        # 31 checks over real MCP stdio, exit 0 = all passed
```

`%APPDATA%\Claude\claude_desktop_config.json`:

```json
"obsidian-canon": {
  "command": "C:\\Program Files\\nodejs\\node.exe",
  "args": ["C:\\Users\\silas\\tools\\obsidian-canon-mcp\\server.js"]
}
```

Restart Claude Desktop after editing the config.

Env overrides: `OBSIDIAN_CANON_VAULT` (vault path), `OBSIDIAN_CLI_EXE` (Obsidian.com),
`OBSIDIAN_CANON_PYTHON` (python for pull.py).

## Tools

| Tool | What it does |
|---|---|
| `canon_info` | Vault facts: counts, last pull, uncommitted changes, Obsidian running, search self-check |
| `canon_list` | List files (folder / ext / name filter, live-only by default, Drive ids included) |
| `canon_read` | Read a doc by path, Drive id, Drive name or unique fragment. Paged (`offset`/`limit`, `done`, `next_offset`) or `whole=true`. `format=md` for the headings twin |
| `canon_grep` | ripgrep equivalent over the canonical text. Literal by default, `regex`, `whole_word`, `case_sensitive`, `context` 0-10, `scope` canonical/txt/md/all, `live_only` |
| `canon_topic` | "Explain X" starter: every live doc ranked by relevance, matching lines per doc, `read_in_full_next` list, related images |
| `canon_lookup` | Drive id <-> local path <-> Drive name / path (full manifest entry, incl. edit link) |
| `canon_outline` | Headings of a doc with line numbers |
| `canon_graph` | `backlinks`, `links`, `orphans`, `deadends`, `unresolved` from the vault's wikilinks (no Obsidian needed) |
| `canon_history` | git log of pulls, optionally for one doc, `since=` |
| `canon_diff` | git diff of one doc between two pulls |
| `canon_images` | Search the 215 image captions (Brother-described, non-canon) with Drive links |
| `canon_pull` | `lr-pull`: Drive -> mirror -> commit -> push. The only write. Background job with `status=true` polling; `dry_run=true` touches nothing |
| `obsidian_search` | Obsidian's own search (`.md` only) with grep fallback when the app's search is cold |
| `obsidian_cli` | Whitelisted read-only Obsidian CLI passthrough (backlinks, links, outline, tags, properties, files, vault, ...) |

## How Proctor should answer "explain the Butterfly Dragon"

1. `canon_topic topic="Butterfly Dragon"` -> ranked docs + `read_in_full_next`.
2. `canon_read file=<each doc in read_in_full_next> whole=true` (the spec, the board twin,
   the 00-series rulings that mention it, the Master / State docs).
3. `canon_history file=<spec>` to see when it last changed; `canon_diff` if needed.
4. Answer from the full text, citing doc names. Never from the snippets alone.

## Facts baked in

- Google Drive is the source of truth. The mirror is one-way and generated; the server has no
  way to hand-edit it. Edit on Drive with gdrive-ops, then `canon_pull`.
- `.txt` = canonical text of a Google Doc (what cascade tooling greps). `.md` = same Doc with
  headings kept and punctuation escaped by Google, so never grep exact strings in `.md`.
- html / docx / doc / pdf sources have a derived `<source>.md` twin; reads and searches use the
  twin, the raw source only by exact path.
- "Live" excludes `_ARCHIVE`, `_SESSION LOG`, `20 - HISTORICAL`, `NOTES FROM BROTHER` and
  anything the manifest marks `live: false`. `live_only=false` widens.
- Obsidian's CLI search only indexes `.md`; it also returns nothing after a cold start of the
  app (known bug). `obsidian_search` falls back to grep when that happens.
- The Obsidian CLI's output is swallowed under MSYS / Git Bash. The server uses node
  `execFile` (no shell), so this does not affect it; test the CLI by hand from PowerShell.

## Files

- `server.js` - the server (ASCII only, ES module)
- `selftest.mjs` - MCP stdio client that exercises every tool
- `package.json` - deps: `@modelcontextprotocol/sdk`, `zod`
