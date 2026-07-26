#!/usr/bin/env node
// gdrive-ops MCP server - Google Drive WRITE operations for Claude Desktop.
// Wraps the gws native CLI (Google Workspace CLI, auth via OS keyring).
// NO permanent delete by design: trash only (30-day recovery).
//
// Prerequisite: gws CLI installed globally (npm i -g @googleworkspace/cli) and
// authenticated to the target Google account (run: gws auth login).
// Override the binary location with env var GDRIVE_OPS_GWS_EXE if needed.

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { execFile } from "node:child_process";
import path from "node:path";

const GWS_EXE =
  process.env.GDRIVE_OPS_GWS_EXE ||
  path.join(
    process.env.APPDATA || "",
    "npm", "node_modules", "@googleworkspace", "cli",
    "node_modules", ".bin_real", "gws.exe"
  );

const FOLDER_MIME = "application/vnd.google-apps.folder";
const FILE_FIELDS = "id,name,mimeType,parents,modifiedTime,trashed,webViewLink";

function gws(args) {
  return new Promise((resolve, reject) => {
    execFile(
      GWS_EXE,
      args,
      { timeout: 60000, maxBuffer: 16 * 1024 * 1024, windowsHide: true },
      (err, stdout, stderr) => {
        if (err) {
          reject(new Error("gws failed: " + (String(stderr) || err.message).trim()));
          return;
        }
        const text = String(stdout);
        const start = text.search(/[[{]/);
        if (start === -1) {
          resolve({ raw: text.trim() });
          return;
        }
        try {
          resolve(JSON.parse(text.slice(start)));
        } catch (e) {
          reject(new Error("gws returned unparseable output: " + text.slice(0, 500)));
        }
      }
    );
  });
}

function ok(data) {
  return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
}

function fail(e) {
  return { isError: true, content: [{ type: "text", text: "ERROR: " + String((e && e.message) || e) }] };
}

// Escape a value for embedding in a Drive API q string literal.
function qEscape(s) {
  return s.replace(/\\/g, "\\\\").replace(/'/g, "\\'");
}

const server = new McpServer(
  { name: "gdrive-ops", version: "1.0.0" },
  {
    instructions: [
      "gdrive-ops: full Google Drive FILE-MANAGEMENT (write ops) for the authenticated Google account.",
      "",
      "CAPABILITY NOTE - READ THIS: The built-in Anthropic Google Drive connector is READ + CREATE only (no move, no rename, no delete). THIS server removes that limit. You CAN now: MOVE files/folders between folders (drive_move), RENAME files and folders (drive_rename), CREATE folders (drive_create_folder), TRASH items (drive_trash - recoverable for 30 days), RESTORE items from trash (drive_restore), and resolve names to IDs (drive_find, drive_list_folder).",
      "Never tell the user a Drive file operation is impossible because 'the connector is read-only'. Use these tools instead. Reorganizing folders (archiving superseded draft versions, sorting current vs archive) is exactly what this server is for - do it yourself, do not ask the user to move files by hand.",
      "",
      "SAFETY MODEL: There is deliberately NO permanent-delete tool. drive_trash only moves items to the Drive trash (auto-purges after 30 days, restorable until then via drive_restore or the Drive UI). You cannot permanently destroy anything with this server.",
      "",
      "WORKFLOW: (1) drive_find or drive_list_folder to get exact file IDs. (2) drive_move / drive_rename / drive_trash as needed. (3) drive_list_folder again to VERIFY the end state. Always verify after a batch.",
      "",
      "HOUSE RULE: For routine tidying (a few moves/renames the user asked for), just execute and report. For anything bigger - bulk sweeps, trashing more than a couple of files, restructuring folder trees - state the exact plan to the user and get explicit approval BEFORE executing.",
    ].join("\n"),
  }
);

server.tool(
  "drive_find",
  "Search Google Drive for files or folders by name (matches 'name contains'). Returns id, name, mimeType, parents, modifiedTime. Use this to resolve names to file IDs before move/rename/trash operations.",
  {
    query: z.string().describe("Name text to search for"),
    only_folders: z.boolean().optional().describe("If true, return only folders"),
  },
  async ({ query, only_folders }) => {
    try {
      let q = "name contains '" + qEscape(query) + "' and trashed = false";
      if (only_folders) q += " and mimeType = '" + FOLDER_MIME + "'";
      const params = { q, fields: "files(" + FILE_FIELDS + ")", pageSize: 50 };
      return ok(await gws(["drive", "files", "list", "--params", JSON.stringify(params), "--format", "json"]));
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "drive_list_folder",
  "List the direct children of a Google Drive folder (folders first, then files, alphabetical). Returns id, name, mimeType, modifiedTime for each child. Use to inspect a folder and to VERIFY results after move/rename/trash operations.",
  {
    folder_id: z.string().describe("The ID of the folder to list"),
  },
  async ({ folder_id }) => {
    try {
      const params = {
        q: "'" + qEscape(folder_id) + "' in parents and trashed = false",
        fields: "files(" + FILE_FIELDS + ")",
        pageSize: 200,
        orderBy: "folder,name",
      };
      return ok(await gws(["drive", "files", "list", "--params", JSON.stringify(params), "--format", "json"]));
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "drive_move",
  "MOVE a file or folder into a different folder (removes it from all current parent folders). This is the operation the built-in Drive connector cannot do. Reversible by moving back.",
  {
    file_id: z.string().describe("The ID of the file or folder to move"),
    dest_folder_id: z.string().describe("The ID of the destination folder"),
  },
  async ({ file_id, dest_folder_id }) => {
    try {
      const meta = await gws([
        "drive", "files", "get",
        "--params", JSON.stringify({ fileId: file_id, fields: "id,name,parents" }),
        "--format", "json",
      ]);
      const removeParents = (meta.parents || []).join(",");
      const params = {
        fileId: file_id,
        addParents: dest_folder_id,
        removeParents: removeParents,
        fields: FILE_FIELDS,
      };
      return ok(await gws(["drive", "files", "update", "--params", JSON.stringify(params), "--format", "json"]));
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "drive_rename",
  "RENAME a file or folder (metadata only, content untouched). This is an operation the built-in Drive connector cannot do. Reversible by renaming back.",
  {
    file_id: z.string().describe("The ID of the file or folder to rename"),
    new_name: z.string().describe("The new name"),
  },
  async ({ file_id, new_name }) => {
    try {
      return ok(
        await gws([
          "drive", "files", "update",
          "--params", JSON.stringify({ fileId: file_id, fields: FILE_FIELDS }),
          "--json", JSON.stringify({ name: new_name }),
          "--format", "json",
        ])
      );
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "drive_create_folder",
  "CREATE a new folder in Google Drive, optionally inside a parent folder (defaults to My Drive root).",
  {
    name: z.string().describe("Name for the new folder"),
    parent_folder_id: z.string().optional().describe("ID of the parent folder (omit for My Drive root)"),
  },
  async ({ name, parent_folder_id }) => {
    try {
      const body = { name: name, mimeType: FOLDER_MIME };
      if (parent_folder_id) body.parents = [parent_folder_id];
      return ok(
        await gws([
          "drive", "files", "create",
          "--params", JSON.stringify({ fields: FILE_FIELDS }),
          "--json", JSON.stringify(body),
          "--format", "json",
        ])
      );
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "drive_trash",
  "Move a file or folder to the Drive TRASH. NOT a permanent delete: recoverable for 30 days via drive_restore or the Drive UI, then auto-purged by Google. This server has no permanent-delete capability by design.",
  {
    file_id: z.string().describe("The ID of the file or folder to move to trash"),
  },
  async ({ file_id }) => {
    try {
      return ok(
        await gws([
          "drive", "files", "update",
          "--params", JSON.stringify({ fileId: file_id, fields: "id,name,trashed" }),
          "--json", JSON.stringify({ trashed: true }),
          "--format", "json",
        ])
      );
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "drive_restore",
  "Restore a file or folder from the Drive trash back to its original location.",
  {
    file_id: z.string().describe("The ID of the trashed file or folder to restore"),
  },
  async ({ file_id }) => {
    try {
      return ok(
        await gws([
          "drive", "files", "update",
          "--params", JSON.stringify({ fileId: file_id, fields: "id,name,trashed,parents" }),
          "--json", JSON.stringify({ trashed: false }),
          "--format", "json",
        ])
      );
    } catch (e) {
      return fail(e);
    }
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
