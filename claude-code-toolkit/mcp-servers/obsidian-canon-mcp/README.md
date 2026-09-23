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

## HTTP mode - Proctor VOICE mode / claude.ai custom connector (S#343, 23 Sept 2026)

Local stdio servers are invisible to Claude voice mode, mobile and web: those surfaces only see
connectors attached to the account. `--http` serves the SAME tools over MCP Streamable HTTP so an
ngrok tunnel can publish them as a custom connector. stdio stays the default; nothing about the
Desktop path changed.

```
node server.js --http                 # 127.0.0.1:8790, stateless, fresh McpServer per request
node smoke-http.mjs                   # local checks: 404 on a wrong secret, tools/list, Butterfly Dragon
node smoke-http.mjs <public url>      # the same through the tunnel
powershell -File run-http.ps1         # server + ngrok, hidden; what the logon task runs
powershell -File stop-http.ps1        # kills both trees (never Proctor's stdio instance)
```

- Auth: claude.ai's connector form has no header field, so the secret rides in the path:
  `https://<domain>/mcp/<secret>` (`Authorization: Bearer <secret>` on `/mcp` also works). Wrong
  secret = plain 404 (a 401 would push claude.ai into OAuth discovery). The secret is NOT in this
  repo: `~/.obsidian-canon/http-secret` (env `OBSIDIAN_CANON_HTTP_SECRET` overrides).
- ngrok: `tools/ngrok/ngrok.exe`; static domain in `~/.obsidian-canon/ngrok-domain.txt`; the full
  connector URL is written to `~/.obsidian-canon/public-url.txt` on every start; logs beside it.
- Scheduled Task "Obsidian Canon HTTP" (at logon, interactive, hidden, no time limit, restarts x3).
  Edit it with Set-ScheduledTask only - `schtasks /change` wipes the run-as credentials.
- Read-only exposure: the only writes are `canon_pull` / `canon_fold`, and fold needs local gws creds.
- Env: `OBSIDIAN_CANON_HTTP_PORT` (default 8790) also switches HTTP mode on.

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
| `canon_section` | ONE section of a long doc by its line-start marker (`SECTION 5G`, `109`, `EPISODE 201`, `PART THREE`) instead of the whole 165K-char Master |
| `canon_outline_text` | The section markers (with line numbers) of a doc that has no markdown headings, to pick a `start=` for `canon_section` |
| `canon_episode` | EVERYTHING about one episode in one call, verbatim: Episode Map entry, Master section, State-compilation acts, amended blocks, character-file beats, every 00-series ruling line naming it, plus a ranked list of other docs that mention it. The way to load an episode without reading six compilations |
| `canon_ruling` | One ruling by number: text, doc/line/date, every variant (R-95 and R-95 REFINED), what it touches, and the chain of later rulings that supersede / refine / mention it. `superseded_by` is explicit |
| `canon_rulings` | The rulings index, newest first: filter by `query`, `episode`, `entity`, `since`; `open_only=true` lists the OPEN ITEMS / `[?]` questions with answered/unanswered. Reports coverage (rulings, docs) so nothing is silently missed |
| `canon_claims` | CONTRADICTION FINDER for one entity: every live sentence naming it, claims extracted (born, ages, death episode, killer, survives, sword, colors, horse, slot, seat, ladder rank, event years), grouped by fact, conflicting values side by side with doc + line + newest ruling. Candidates, never verdicts |
| `canon_fold` | THE FOLD: one call when Silas says "fold this into the corpus" (after gdrive-ops edits). Pull + re-embed + the list of Docs that changed. Not for ordinary edits |
| `canon_lookup` | Drive id <-> local path <-> Drive name / path (full manifest entry, incl. edit link) |
| `canon_outline` | Headings of a doc with line numbers |
| `canon_graph` | `backlinks`, `links`, `orphans`, `deadends`, `unresolved` from the vault's wikilinks (no Obsidian needed) |
| `canon_history` | git log of pulls, optionally for one doc, `since=` |
| `canon_diff` | git diff of one doc between two pulls |
| `canon_images` | Search the 215 image captions (Brother-described, non-canon) with Drive links |
| `canon_pull` | `lr-pull`: Drive -> mirror -> commit -> push. The only write. Background job with `status=true` polling; `dry_run=true` touches nothing. A real pull chains a semantic re-index + re-embed |
| `canon_semantic` | MEANING search (QMD folded in): plain-language questions, `mode` hybrid / vector / keyword, `rerank`, `live_only`. Local BM25 + vectors + LLM rerank |
| `canon_embed` | Refresh the semantic index (re-index + re-embed). Background job, `status=true` to poll, `force=true` to redo everything |
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

## Semantic search (QMD) - how it is wired

- QMD (`npm i -g @tobilu/qmd`, github.com/tobi/qmd) is NOT a second server. This server shells
  out to its CLI with `--format json` and folds the results into `canon_semantic`.
- Collection `canon` = the LIVE show text of this mirror: root Docs, `18 - Concept Art`, `19 - Video`,
  `STORY-SHAPE ATLAS`, `_SESSION LOG`, derived twins for html/docx/pdf, and the image galleries
  (162 files, ~6 MB). `_ARCHIVE` (superseded drafts, 4.5 MB) and `20 - HISTORICAL` (third-party
  sources, 7.9 MB, never canon) are deliberately NOT embedded: they doubled the corpus, blew the
  embed time cap, and are excluded from every default query anyway. They stay reachable through
  `canon_grep live_only=false`. Mask lives in the ledger entry (S#326). Index: `~/.cache/qmd/index.sqlite`.
- Embed cost on this laptop (Intel Iris Xe via Vulkan, 4 CPU cores): the first full pass ran
  ~45 min; after a pull only changed docs re-embed. The embed child sits at ~5.2-5.4 GB RAM for
  its whole run WITH or WITHOUT the batch caps (`--max-docs-per-batch 8 --max-batch-mb 4` are
  passed anyway); the footprint is the loaded models plus Vulkan buffers, not the documents. It
  is released the moment the child exits. If that is too much for a foreground work session,
  run `canon_embed` when the machine is idle, or set `QMD_FORCE_CPU=1` and re-measure.
  Models (~2 GB, local, downloaded once by `qmd pull`): embeddinggemma-300M, Qwen3-Reranker-0.6B,
  qmd-query-expansion-1.7B.
- Freshness: every real `canon_pull` chains `qmd update` + `qmd embed -c canon` in the background.
  `canon_info.semantic_index` shows files_indexed / vectors_embedded / ready.
- `keyword` mode needs no models and is instant. `hybrid` loads the models per call (seconds) and
  reranks with a local LLM; `rerank=false` skips that. Set `QMD_FORCE_CPU=1` in the server env if
  the CUDA path misbehaves.

## Process hygiene (no orphans)

- No daemons, no Bun. One child process per call (qmd / python / git / obsidian), gone when it
  returns. The one sanctioned long-lived process is the `--http` instance Silas asked for (S#343);
  its children obey the same registry and `stop-http.ps1` kills it with its tree.
- Every child is registered; when the server's stdin closes (Claude Desktop quit) or it exits, every
  registered child is killed with its whole tree (`taskkill /T /F`). Timeouts kill the tree too.
- The only long-lived process is the MCP server itself, owned by Claude Desktop.

## Files

- `server.js` - the server (ASCII only, ES module)
- `selftest.mjs` - MCP stdio client that exercises every tool
- `smoke-http.mjs` - MCP Streamable HTTP client for `--http` mode (local or through the tunnel)
- `run-http.ps1` / `stop-http.ps1` - the logon task's launcher and its kill switch
- `package.json` - deps: `@modelcontextprotocol/sdk`, `zod`
