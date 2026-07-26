// Self-test battery for gdrive-ops MCP server. Run: node selftest.mjs
// Exercises every tool end-to-end through the real MCP stdio protocol.
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { fileURLToPath } from "node:url";

const transport = new StdioClientTransport({
  command: process.execPath,
  args: [fileURLToPath(new URL("./server.js", import.meta.url))],
});
const client = new Client({ name: "selftest", version: "1.0.0" });
await client.connect(transport);

let pass = 0;
let failCount = 0;
function check(label, cond, detail) {
  if (cond) {
    pass++;
    console.log("PASS " + label + (detail ? " :: " + detail : ""));
  } else {
    failCount++;
    console.log("FAIL " + label + (detail ? " :: " + detail : ""));
  }
}

async function call(name, args) {
  const res = await client.callTool({ name: name, arguments: args });
  const text = res.content && res.content[0] ? res.content[0].text : "";
  let data = null;
  try { data = JSON.parse(text); } catch (e) { /* leave null */ }
  return { res: res, text: text, data: data };
}

// 1. Tool surface
const tools = await client.listTools();
const names = tools.tools.map((t) => t.name).sort();
check("tool-surface", names.join(",") === "drive_create_folder,drive_find,drive_list_folder,drive_move,drive_rename,drive_restore,drive_trash", names.join(","));

// 2. Instructions block surfaced through handshake
const instr = client.getInstructions ? client.getInstructions() : undefined;
check("instructions-present", typeof instr === "string" && instr.indexOf("READ + CREATE only") !== -1, instr ? instr.slice(0, 60) + "..." : "MISSING");

// 3. Create two scratch folders at root
const a = await call("drive_create_folder", { name: "ZZZ-GDRIVE-OPS-SELFTEST-A" });
check("create-folder-A", !!(a.data && a.data.id), a.data && a.data.id);
const b = await call("drive_create_folder", { name: "ZZZ-GDRIVE-OPS-SELFTEST-B" });
check("create-folder-B", !!(b.data && b.data.id), b.data && b.data.id);
const aId = a.data.id;
const bId = b.data.id;

// 4. Move A into B
const mv = await call("drive_move", { file_id: aId, dest_folder_id: bId });
check("move-A-into-B", !!(mv.data && mv.data.parents && mv.data.parents.length === 1 && mv.data.parents[0] === bId), JSON.stringify(mv.data && mv.data.parents));

// 5. List B shows A
const ls = await call("drive_list_folder", { folder_id: bId });
const lsNames = ls.data && ls.data.files ? ls.data.files.map((f) => f.name) : [];
check("list-B-shows-A", lsNames.indexOf("ZZZ-GDRIVE-OPS-SELFTEST-A") !== -1, lsNames.join(","));

// 6. Rename A
const rn = await call("drive_rename", { file_id: aId, new_name: "ZZZ-GDRIVE-OPS-SELFTEST-A-RENAMED" });
check("rename-A", !!(rn.data && rn.data.name === "ZZZ-GDRIVE-OPS-SELFTEST-A-RENAMED"), rn.data && rn.data.name);

// 7. Find both by prefix
const fd = await call("drive_find", { query: "ZZZ-GDRIVE-OPS-SELFTEST", only_folders: true });
const fdCount = fd.data && fd.data.files ? fd.data.files.length : 0;
check("find-both", fdCount === 2, "found " + fdCount);

// 8. Trash A, verify, restore A, verify
const tr = await call("drive_trash", { file_id: aId });
check("trash-A", !!(tr.data && tr.data.trashed === true), JSON.stringify(tr.data));
const rs = await call("drive_restore", { file_id: aId });
check("restore-A", !!(rs.data && rs.data.trashed === false), JSON.stringify(rs.data));

// 9. Cleanup: trash A then B (leaves nothing at root; recoverable 30 days)
const tr2 = await call("drive_trash", { file_id: aId });
check("cleanup-trash-A", !!(tr2.data && tr2.data.trashed === true));
const tr3 = await call("drive_trash", { file_id: bId });
check("cleanup-trash-B", !!(tr3.data && tr3.data.trashed === true));

// 10. Error path: move with bogus ID returns isError, server survives
const bad = await call("drive_move", { file_id: "nonexistent-id-12345", dest_folder_id: bId });
check("error-path-isError", !!(bad.res.isError && bad.text.indexOf("ERROR") === 0), bad.text.slice(0, 80));
const alive = await client.listTools();
check("server-survives-error", alive.tools.length === 7);

console.log("");
console.log("RESULT: " + pass + " passed, " + failCount + " failed");
await client.close();
process.exit(failCount === 0 ? 0 : 1);
