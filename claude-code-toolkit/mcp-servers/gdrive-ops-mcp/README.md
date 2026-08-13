# gdrive-ops MCP server

Gives Claude Desktop (or any MCP client) the Google Drive and Google Docs operations
the built-in Anthropic Google Drive connector lacks: **move, rename, create folder,
trash, restore**, and full Google Doc **create / read / locate / insert / replace**,
including atomic multi-edit batches.

Born 2026-07-26: the built-in connector is read + create only, which forced manual
file organization in Drive. This server wraps the `gws` CLI (Google Workspace CLI)
so the model can do the work itself.

**v1.2.0** added the Docs editing suite after real-world use surfaced five specific
frictions: no way to insert or create with content, no in-tool read/locate (so large
documents were being pulled through another connector just to find an anchor), no
safety guard against a too-broad anchor, no atomic batch, and replaces that silently
returned zero with no explanation.

## Safety model

- **No permanent delete exists.** `drive_trash` only moves items to the Drive trash
  (recoverable for 30 days via `drive_restore` or the Drive UI). The model cannot
  permanently destroy anything through this server.
- **Doc edits are revertible** through the document's own revision history.
- **`expected_count`** refuses an edit unless exactly N matches exist, so a too-broad
  anchor cannot silently clobber a second unintended occurrence.
- **`dry_run`** reports every match with surrounding context and changes nothing.
- **Batch edits validate before writing.** If any `expected_count` fails, or two edits
  target overlapping text, nothing at all is applied.
- **Matches spanning a non-text element** (inline image, page break, footnote marker)
  are refused rather than deleted, and reported in a `skipped` array.
- The server `instructions` block tells the model it HAS these abilities (so the
  capability is discoverable, not latent) and instructs it to get explicit user
  approval before bulk operations and to verify end state after every batch.

## Tools

### Drive file management

| Tool | Purpose |
|---|---|
| `drive_find` | Search files/folders by name, returns IDs |
| `drive_list_folder` | List a folder's children (also the verify step) |
| `drive_move` | Move a file/folder to another folder |
| `drive_rename` | Rename a file/folder |
| `drive_create_folder` | Create a folder (root or nested) |
| `drive_trash` | Move to trash (30-day recovery) |
| `drive_restore` | Restore from trash |
| `docs_search_content` | Find which Docs contain a phrase (Drive full-text) |

### Google Docs

| Tool | Purpose |
|---|---|
| `docs_create` | Create a Doc, optionally in a folder and with body text |
| `docs_get_text` | Read body text; supports `offset`/`length` windowing and per-segment Docs indices |
| `docs_find` | Locate every occurrence with char offset, Docs index range and context |
| `docs_insert_text` | Insert at `start_of_doc` / `end_of_doc` / `before` / `after` an anchor |
| `docs_replace_text` | Replace in place, with match modes, count guard and dry run |
| `docs_replace_batch` | Many replacements as ONE atomic edit / one revision entry |

## Why a Docs replace silently finds nothing

This is the single most confusing failure in the Docs API, and the common explanations
are wrong. Measured directly against live documents (2026-08-13):

**`replaceAllText` ALREADY handles these - they are not your problem:**

| Case | Result |
|---|---|
| Search string spans a paragraph break (`\n`) | matches fine |
| Search string spans a formatting split (bold mid-sentence creates separate text runs) | matches fine |
| Straight `'` in search vs curly `U+2019` in document | matches fine |
| Straight `"` in search vs curly `U+201C`/`U+201D` in document | matches fine |

**These are what actually return zero:**

| Search string has | Document actually contains | Result |
|---|---|---|
| newline `\n` | **soft line break `U+000B`** (SHIFT+ENTER) | **0** |
| plain space | **non-breaking space `U+00A0`** | **0** |
| hyphen `-` | en dash `U+2013` / em dash `U+2014` | **0** |
| space | tab | **0** |
| (nothing) | zero-width space `U+200B`, `U+FEFF`, soft hyphen `U+00AD` | **0** |

The soft line break is the nastiest: **every reader and every export renders it as a
newline**, so the caller has no way to see that the document stores a different
character. Text that looks identical on screen simply will not match.

**The fix:** pass `match: "normalized"`. And whenever a replace returns 0, this server
runs a diagnostic and names the cause in the response:

```json
{
  "occurrencesChanged": 0,
  "whyNoMatch": {
    "diagnosis": "FOUND, but the literal bytes differ. See causes below.",
    "causes": [
      {
        "cause": "soft_line_break",
        "wouldMatch": 1,
        "explanation": "The document uses a SOFT LINE BREAK (SHIFT+ENTER, U+000B) where your search string has a newline..."
      }
    ],
    "normalizedWouldMatch": 1
  }
}
```

If nothing matches under any normalization, the diagnostic instead reports the longest
prefix of your search string that *does* appear, where it appears, and what the document
actually continues with at that point - so you can see exactly where the two diverge.

## Match modes

Available on `docs_replace_text`, `docs_replace_batch`, `docs_find` and the anchor
matching in `docs_insert_text`.

- **`literal`** (default) - exact string matching. On `docs_replace_text` with no other
  new parameters this takes the original `replaceAllText` code path unchanged.
- **`normalized`** - recommended for prose anchors. Ignores whitespace *kind* and
  *amount* (spaces, newlines, soft line breaks, tabs, non-breaking spaces all collapse
  to one space), dash style, quote style, and invisible characters.
- **`regex`** - JavaScript regular expression over the document's plain text.

Normalized and regex modes work by pulling the document, building its plain text
alongside a per-character map back to real Docs API indices, matching against the
normalized form, then mutating with `deleteContentRange` + `insertText` at the mapped
coordinates - applied back-to-front so index shifts cannot corrupt later edits.

## Atomic batches

`docs_replace_batch` resolves every edit against a single snapshot, validates them all,
then emits one `batchUpdate`. That means one API round trip, **one revision-history
entry** instead of N, and no race between edits landing on the same document.

```json
{
  "document_id": "...",
  "edits": [
    { "find_text": "Badon in 490", "replace_text": "Badon in 485", "expected_count": 1 },
    { "find_text": "Uthr is 52",   "replace_text": "Uthr is 47",   "expected_count": 1 },
    { "find_text": "red hair",     "replace_text": "brown hair", "match": "normalized" }
  ]
}
```

## Prerequisites

1. Node 18+ (uses ESM + top-level await).
2. `gws` CLI installed globally and authenticated to the target Google account:

```
npm i -g @googleworkspace/cli
gws auth login
```

Auth rides the gws CLI's OS-keyring token. If `gws` works in your terminal, the
server works. The account the CLI is logged into is the account the model operates on.
**If gws auth breaks, every tool here breaks** - that is the single point of failure.

## Install

```
cd gdrive-ops-mcp
npm install
node selftest.mjs   # 63-check battery against your live Drive (creates + trashes ZZZ-* scratch items)
```

Add to `claude_desktop_config.json` (Windows: `%APPDATA%\Claude\`):

```json
"gdrive-ops": {
  "command": "C:\\Program Files\\nodejs\\node.exe",
  "args": ["C:\\path\\to\\gdrive-ops-mcp\\server.js"]
}
```

Restart Claude Desktop. The tools appear alongside the built-in connector's.

If your gws binary lives somewhere non-standard, set env var `GDRIVE_OPS_GWS_EXE`
to its full path (default: the npm global install location under `%APPDATA%`).

## JSON Schema dialect note

The MCP SDK generates tool schemas via `zod-to-json-schema`, which stamps
**draft-07**. Some clients (Claude Desktop among them) accept **2020-12 only** and
will hard-error on invocation when a tool declares a draft-07 `outputSchema` - while
still listing the tool perfectly, which makes it look like a server problem when it is
client-side validation. This server therefore declares **no `outputSchema` at all** and
relabels `inputSchema` to 2020-12 on the way out. Relabelling is safe here because
these schemas use only constructs identical in both dialects (type / properties /
required / additionalProperties / description / enum / items). Revisit if `$defs` or
tuple-form `items` are ever introduced.

## gws CLI gotcha worth knowing

`--params` carries URL/query parameters only; request-body fields (name, trashed,
parents on create) go in `--json`. Body fields passed via `--params` are silently
ignored - this server handles the split correctly for every operation.

Also: `documents.create` (Docs API) ignores `parents`, so `docs_create` creates the
file through the **Drive** API with `mimeType: application/vnd.google-apps.document`
and then inserts the body - that is the only way to land a new Doc inside a folder in
one operation.
