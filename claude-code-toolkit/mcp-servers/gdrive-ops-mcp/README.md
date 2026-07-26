# gdrive-ops MCP server

Gives Claude Desktop (or any MCP client) full Google Drive **write** operations that
the built-in Anthropic Google Drive connector lacks: **move, rename, create folder,
trash, restore** (plus find/list for ID resolution).

Born 2026-07-26: the built-in connector is read + create only, which forced manual
file organization in Drive. This server wraps the `gws` CLI (Google Workspace CLI)
so the model can do the file management itself.

## Safety model

- **No permanent delete exists.** `drive_trash` only moves items to the Drive trash
  (recoverable for 30 days via `drive_restore` or the Drive UI). The model cannot
  permanently destroy anything through this server.
- The server `instructions` block tells the model it HAS these abilities (so the
  capability is discoverable, not latent) and instructs it to get explicit user
  approval before bulk operations and to verify end state after every batch.

## Tools

| Tool | Purpose |
|---|---|
| `drive_find` | Search files/folders by name, returns IDs |
| `drive_list_folder` | List a folder's children (also the verify step) |
| `drive_move` | Move a file/folder to another folder |
| `drive_rename` | Rename a file/folder |
| `drive_create_folder` | Create a folder (root or nested) |
| `drive_trash` | Move to trash (30-day recovery) |
| `drive_restore` | Restore from trash |

## Prerequisites

1. Node 18+ (uses ESM + top-level await; selftest uses `import.meta.dirname`, Node 20.11+).
2. `gws` CLI installed globally and authenticated to the target Google account:

```
npm i -g @googleworkspace/cli
gws auth login
```

Auth rides the gws CLI's OS-keyring token. If `gws` works in your terminal, the
server works. The account the CLI is logged into is the account the model operates on.

## Install

```
cd gdrive-ops-mcp
npm install
node selftest.mjs   # 14-check battery against your live Drive (creates + trashes ZZZ-* scratch folders)
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

## gws CLI gotcha worth knowing

`--params` carries URL/query parameters only; request-body fields (name, trashed,
parents on create) go in `--json`. Body fields passed via `--params` are silently
ignored - this server handles the split correctly for every operation.
