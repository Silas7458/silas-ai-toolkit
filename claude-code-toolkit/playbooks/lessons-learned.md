# Playbook: Lessons Learned

Accumulated hard-won knowledge from real-world Claude Code operations. Organized by domain. Each lesson was learned through actual failure, not theory.

---

## n8n Workflow Automation

### Postgres 0-Row Silent Death (CRITICAL)
**Problem:** A Postgres node returning 0 rows silently kills the entire downstream chain. No error, no fallback, webhook returns HTTP 200 with 0 bytes.
**Fix:** ALWAYS set `alwaysOutputData: true` on every Postgres node. For critical paths, wrap queries in a CTE with `UNION ALL` to guarantee a sentinel row, then filter it out in the next Code node.

### Merge Node 3+ Branches Fails Silently
**Problem:** n8n Merge node in `chooseBranch` mode with 3+ parallel inputs produces empty output.
**Fix:** Chain nodes sequentially. Use `$('NodeName').all()` or `$('NodeName').first()` in Code nodes to reference any previously executed node by name -- no direct connection required.

### Prompt Escaping Hell
**Problem:** System prompts embedded as inline strings in HTTP Request nodes cause triple-nested escaping failures (JSON inside n8n expressions inside JSON body).
**Fix:** Store prompts in external JSON files. Load with `fs.readFileSync` in an Init Code node. Pass the prompts object through every intermediate node so downstream HTTP Request nodes can reference it.

### Import Duplicates
**Problem:** Importing workflow JSON without an `id` field creates a duplicate instead of updating.
**Fix:** Always include the workflow `id` in the JSON. After import, run `n8n list:workflow` to verify no duplicates. Then `n8n publish:workflow` + container restart -- imported workflows are always deactivated by default.

### Code Node Sandboxing
**Problem:** Code v2 nodes run in a sandboxed JS Task Runner that blocks `require('fs')`.
**Fix:** Use Code v1 (`typeVersion: 1`) for filesystem access. Note different API: `items[]` instead of `$input`.

---

## Docker and Containers

### Shell Redirection Scope
**Problem:** `docker exec container command 2>/dev/null` applies host-shell redirection, not container-shell.
**Fix:** Wrap in `sh -c`: `docker exec container sh -c "command 2>/dev/null"`.

### Git Bash Path Mangling
**Problem:** Git Bash (MSYS) translates `/data/` to `C:/Program Files/Git/data/` inside `docker exec` commands.
**Fix:** Set `MSYS_NO_PATHCONV=1` before any `docker exec` with container paths.

---

## Windows and Multi-Agent Operations

### Never Click Taskbar Buttons (CRITICAL)
**Problem:** Clicking a taskbar button to switch windows caused unpredictable minimize/close/toggle that killed an active Claude Code session and destroyed the entire context.
**Fix:** ALWAYS use `App mode=switch` by name when using Windows MCP. Never touch the taskbar.

### App Switch Lies About Focus
**Problem:** `App(mode="switch")` reports success but the terminal reclaims focus after every tool call. Messages typed to teammates go into your own terminal.
**Fix:** ALWAYS verify with a text-only Snapshot after every App switch. If Focused Window does not match target, STOP and retry.

### DPI-Aware Coordinates Required
**Problem:** Vision screenshot coordinates are scaled and wrong. Clicking at screenshot-derived coordinates hits the wrong window.
**Fix:** Always use `GetWindowRect` with `SetProcessDPIAware()` for real pixel positions. Never estimate from screenshots.

### Scheduled Task Window Flash
**Problem:** Windows scheduled tasks calling `powershell.exe -WindowStyle Hidden` still flash a console window because the OS spawns `conhost.exe` BEFORE PowerShell reads the `-WindowStyle Hidden` flag.
**Fix:** Use a VBScript wrapper that calls PowerShell via `WScript.Shell.Run` with window style 0 -- no console host ever created.

---

## Architecture and Process

### Infrastructure Before Product
**Problem:** Tunnel vision on product features while infrastructure deteriorated.
**Fix:** Never begin product-level work until platform infrastructure is verified operational. When in doubt: is the platform layer solid? If no, fix that first.

### Session State is Non-Negotiable
**Problem:** New sessions started with stale or missing context because prior sessions did not write state before ending.
**Fix:** Before ending ANY session: (1) update session-state.md, (2) append to session archive, (3) notify the user. No exceptions, including early termination.

### Deliverables Format
**Problem:** Documents produced in the wrong format (e.g., Markdown instead of required Word/Excel).
**Fix:** Always confirm the user's preferred output format. Reserve .md strictly for internal context files and developer notes unless told otherwise.

---

## Claude Code Specific

### Never Freeze on Errors
**Problem:** Claude Code hitting a tool error and then sitting there as if finished instead of recovering.
**Fix:** Retry once (transient errors often resolve). If retry fails, pivot to a different approach. If non-critical, skip and continue. ALWAYS communicate what happened.

### Complete the List
**Problem:** Given a numbered list of tasks, completing item 1 and then asking "what's next?" instead of continuing.
**Fix:** When given a numbered list, complete ALL items in sequence. Only stop if something is genuinely blocked. Do not ask permission between items.

### Session State is Primary on Restart
**Problem:** On restart, re-researching things already documented as complete in session-state.md.
**Fix:** Read session-state.md FIRST on every restart. Trust what it says. Morning briefs and other context files are supplementary, not primary.

---

## Meta

### Do Not Submit Garbage Lessons
**Problem:** Placeholder or test text submitted as lesson input pollutes the knowledge base.
**Fix:** Ensure every lesson contains a real problem, context, and takeaway before recording it.

---

*These lessons are universal. Adapt the specific tool references to your own stack, but the patterns apply broadly.*
