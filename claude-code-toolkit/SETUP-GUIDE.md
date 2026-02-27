# Setup Guide -- Claude Code Power User Configuration

Step-by-step guide for replicating this Claude Code configuration on a new machine. Each step builds on the previous one. By the end, you will have a Claude Code instance with session continuity, agent delegation, MCP integrations, and operational playbooks.

---

## Prerequisites

- **Claude Code CLI** installed ([official docs](https://docs.anthropic.com/en/docs/claude-code))
- A Claude Pro, Team, or Enterprise subscription
- Node.js 18+ and npm
- Python 3.10+ (for video pipelines and utility scripts)
- Git

---

## Step 1: Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

Verify:
```bash
claude --version
```

Run the initial setup:
```bash
claude
```

This creates the `~/.claude/` directory with default settings.

---

## Step 2: Set Up Your CLAUDE.md

The `CLAUDE.md` file is your master instruction file. Claude Code reads it automatically at every session start. Place it at your project root or home directory.

1. Copy the template:
   ```bash
   cp configs/CLAUDE.md.template ~/CLAUDE.md
   ```

2. Open `~/CLAUDE.md` and replace all `[PLACEHOLDER]` markers with your values:
   - `[YOUR_NAME]` -- your name
   - `[YOUR_DOCUMENTS_DIR]` -- your documents directory (e.g., `~/Documents`)
   - `[YOUR_CONTEXT_DIR]` -- where you want session state files
   - `[YOUR_TEAM_DIR]` -- where team communication files live (if using multi-agent)
   - Other placeholders as documented in the template

3. **Key sections to customize:**
   - **Identity Detection** -- If you only use one Claude instance, simplify this to a single role
   - **Startup Protocol** -- Add your own files to the startup read list
   - **Shutdown Protocol** -- Configure your archive and state file paths
   - **About You** -- Your preferences, company details, standing instructions

4. **Key sections to keep as-is:**
   - **Prime Directive** -- The quality standard. Works universally.
   - **Eisenhower Matrix** -- The prioritization framework. Works universally.
   - **Path Discipline** -- Adapt paths but keep the concept of canonical paths.

---

## Step 3: Configure MCP Servers

MCP servers extend Claude Code with external tools. Configure them in `~/.claude.json` under the `mcpServers` key.

1. Copy the template:
   ```bash
   # The template shows the structure -- you will need to install each server separately
   cat configs/claude.json.template
   ```

2. **Recommended MCP servers (in priority order):**

   **Tier 1 -- High Value:**
   - **Playwright** -- Browser automation. No API keys needed.
     ```bash
     npm install -g @playwright/mcp
     ```
   - **Docker MCP Gateway** -- If you use Docker for databases/services.
     ```bash
     docker pull mcp/gateway
     ```

   **Tier 2 -- Team/Communication:**
   - **Discord MCP** -- If coordinating multiple Claude instances or logging sessions.
     Requires a Discord bot token and server.
   - **Google Drive MCP** -- If you need document management.
     Requires Google OAuth credentials.

   **Tier 3 -- Platform-Specific:**
   - **Windows MCP** -- Desktop automation on Windows (screenshots, window management).
     ```bash
     pip install windows-mcp
     ```
   - **n8n MCP** -- If you use n8n for workflow automation.
     ```bash
     npx -y n8n-mcp
     ```

3. **Security note:** Never commit API keys, tokens, or credentials to version control. Use environment variables or a separate credentials file that is gitignored.

---

## Step 4: Set Up the Memory System

Claude Code has an auto-memory system that persists across sessions. It lives at:
```
~/.claude/projects/{project-path-hash}/memory/MEMORY.md
```

1. Review `memory/MEMORY.md.template` for patterns worth recording
2. Use Claude Code's `/remember` command to add entries during sessions
3. **What to save in memory:**
   - Permanent rules (e.g., "never use X approach, always use Y")
   - Error recovery patterns learned from failures
   - Key file locations and credentials references (never the actual credentials)
   - Behavioral corrections (e.g., "complete all items in a list, do not stop after the first one")
4. **What NOT to save:**
   - Temporary task state (use session-state files instead)
   - Actual secrets or API keys
   - Information that changes frequently

---

## Step 5: Configure Hooks

Hooks let you run custom code at specific points in Claude Code's lifecycle. Configure them in `~/.claude/settings.json`.

1. Copy the template:
   ```bash
   cp configs/settings.json.template ~/.claude/settings.json
   ```

2. **Available hook points:**
   - `SessionStart` -- Runs when a new session begins. Use for: loading context, registering the session, checking for updates.
   - `UserPromptSubmit` -- Runs before each user message is processed. Use for: injecting context, memory awareness checks.
   - `PreToolUse` -- Runs before a tool is executed. Use for: file ownership tracking, safety checks.
   - `PostToolUse` -- Runs after a tool executes. Use for: logging, window management, cleanup.

3. **Hook examples from this toolkit:**
   - **Session registration hook** -- Records session start in a central log
   - **Memory awareness hook** -- Injects relevant memory context before each prompt
   - **File claims hook** -- Tracks which agent last edited each file (multi-agent)
   - **Restore terminal hook** -- Returns focus to the terminal after window operations (Windows)

4. **Writing hooks:** Hooks are shell commands (or Node.js scripts). They receive context via stdin as JSON and can modify behavior by writing to stdout. See the [Claude Code docs](https://docs.anthropic.com/en/docs/claude-code/hooks) for the full API.

---

## Step 6: Set Up Playbooks

Playbooks are reference documents that Claude Code can read when it needs procedural knowledge. They live in a known directory referenced in CLAUDE.md.

1. Create your playbooks directory:
   ```bash
   mkdir -p ~/Documents/playbooks
   ```

2. Copy the playbooks from this toolkit:
   ```bash
   cp playbooks/context-conservation.md ~/Documents/playbooks/
   cp playbooks/lessons-learned.md ~/Documents/playbooks/
   cp playbooks/video-analysis.md ~/Documents/playbooks/
   ```

3. Reference the directory in your CLAUDE.md:
   ```markdown
   ## Playbooks
   How-to procedures and accumulated knowledge live in: `[YOUR_DOCUMENTS_DIR]/playbooks/`
   Check here FIRST when asked about a known capability.
   ```

4. **Add your own playbooks** as you accumulate domain-specific knowledge. Good candidates:
   - Deployment procedures
   - Database migration patterns
   - API integration recipes
   - Debugging checklists

---

## Step 7: Set Up Session State Files

Session state files provide continuity across Claude Code sessions. When one session ends, it writes state. When the next session starts, it reads that state.

1. Create the session state directory:
   ```bash
   mkdir -p ~/Documents/claude-context
   ```

2. Create the initial files:
   ```bash
   echo "# Session State\nNo active session." > ~/Documents/claude-context/session-state.md
   echo "# Session Archive" > ~/Documents/claude-context/claude-archive.md
   ```

3. Add these to your CLAUDE.md startup/shutdown protocols (already included in the template).

---

## Step 8: Configure Permissions

In `~/.claude/settings.json`, set your permission preferences:

```json
{
  "permissions": {
    "defaultMode": "bypassPermissions",
    "allow": [
      "Bash(*)",
      "Read(*)",
      "Write(*)",
      "Edit(*)",
      "WebSearch(*)",
      "WebFetch(*)",
      "Glob(*)",
      "Grep(*)",
      "mcp__*"
    ]
  }
}
```

**Options:**
- `"bypassPermissions"` -- Claude Code executes all tools without asking. Fastest workflow, requires trust.
- `"allowEdits"` -- Asks permission for destructive operations only.
- `"askEveryTime"` -- Asks for every tool use. Safest but slowest.

For power-user workflows, `bypassPermissions` with broad allow patterns is recommended. You can restrict specific tools if needed.

---

## Step 9: Test Your Configuration

Run these checks to verify everything is working:

1. **Start a session and verify CLAUDE.md loads:**
   ```bash
   cd ~
   claude
   ```
   Ask: "What are your startup instructions?" -- it should reference your CLAUDE.md content.

2. **Test MCP servers:**
   Ask: "List all available MCP tools." -- each configured server should appear.

3. **Test agent delegation:**
   Ask: "Spin up an agent to read [some large file] and summarize it." -- the agent should run in its own context.

4. **Test session state:**
   End the session. Start a new one. Ask: "What was happening in the last session?" -- it should read session-state.md.

5. **Test hooks:**
   Check that SessionStart hooks fire (look for their output or side effects).

---

## Recommended Next Steps

1. **Read the [Context Conservation playbook](./playbooks/context-conservation.md)** -- this is the single highest-value document in the toolkit
2. **Review the [protocols](./protocols/)** -- adopt session management and agent delegation at minimum
3. **Study the [examples](./examples/)** -- see real patterns for research, document processing, and agent orchestration
4. **Start building your own playbooks** -- every hard-won lesson is worth recording
5. **Iterate on your CLAUDE.md** -- it is a living document that improves with every session

---

## Troubleshooting

### MCP server not connecting
- Check that the command/binary exists at the configured path
- Run the command manually to see error output
- Verify environment variables are set correctly
- Restart Claude Code after config changes

### Hooks not firing
- Verify the hook script exists at the configured path
- Check that the script is executable
- Test the script manually: `node path/to/hook.js`
- Check the `timeout` value -- hooks that exceed it are killed silently

### CLAUDE.md not loading
- Ensure it is in the current working directory or home directory
- Check for syntax errors (malformed markdown can cause partial loads)
- Claude Code loads from multiple locations: project root, home dir, and `~/.claude/CLAUDE.md`

### Agent delegation fails
- Ensure your plan allows sub-agent usage
- Check that the `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` env var is set if using team features
- Agents inherit your MCP server configs but run in their own context

---

*This guide is a living document. Update it as your configuration evolves.*
