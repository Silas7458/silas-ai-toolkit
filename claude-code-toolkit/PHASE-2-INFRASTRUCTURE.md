# Phase 2 — Infrastructure & MCP Server Setup
# Tandem Team Bootstrap — After running bootstrap.sh
#
# PREREQUISITE: You ran bootstrap.sh and have Phase 1 working (Brother identity,
# session state, basic commands). This guide adds the power tools.
#
# HOW TO USE: Work through each section IN ORDER. Each section has:
#   - What it is and why you need it
#   - Install commands (copy-paste ready)
#   - Verification step (confirm it works before moving on)
#   - Troubleshooting if it fails
#
# ESTIMATED TIME: 1-2 hours for the full stack. You can stop after any section
# and pick up later — each section is independent once prerequisites are met.
# ═══════════════════════════════════════════════════════════════════════════════

---

## Prerequisites Check

Run these first. If any fail, install the missing tool before proceeding.

```bash
# All of these should return a version number
node --version        # Need 18+ (recommended 22+)
npm --version         # Comes with Node
npx --version         # Comes with Node
python3 --version     # Need 3.10+ (or python --version on Windows)
pip --version         # Comes with Python
git --version         # Need 2.30+
docker --version      # Need Docker Desktop installed and running
```

**Windows-specific:** Make sure Docker Desktop is running (check system tray).
Open Git Bash (not CMD or PowerShell) for all commands below.

---

## Section 1: Core Config Files (10 min)

These two files control everything. If you already have them from Phase 1, this section updates them with MCP server configs and permissions.

### 1A: .claude.json — MCP Server Configuration

This file tells Claude Code what external tools are available.

```bash
# Check if you already have one
cat ~/.claude.json 2>/dev/null && echo "EXISTS — review and merge" || echo "MISSING — will create"
```

**If MISSING:** Copy the template and fill in your paths:
```bash
cp silas-ai-toolkit/claude-code-toolkit/configs/claude.json.template ~/.claude.json
```

**If EXISTS:** You need to MERGE, not overwrite. Open both files side by side:
```bash
# See what the template has that you might be missing
diff ~/.claude.json silas-ai-toolkit/claude-code-toolkit/configs/claude.json.template
```

**After copying or merging, do these replacements:**
```
Find:     {{HOME_DIR}}
Replace:  Your actual home path (e.g., C:\Users\scotty)

Find:     YOUR_DISCORD_BOT_TOKEN_HERE
Replace:  Your Discord bot token (get in Section 5)

Find:     YOUR_DISCORD_SERVER_ID_HERE
Replace:  Your Discord server ID (get in Section 5)

Find:     YOUR_FIRECRAWL_API_KEY_HERE
Replace:  Your Firecrawl API key (get in Section 4)

Find:     YOUR_GITHUB_PAT_HERE
Replace:  Your GitHub personal access token (Settings → Developer → PATs)
```

**Remove the `_TEMPLATE_INFO` block** at the top — Claude Code doesn't expect it.

### 1B: settings.json — Permissions, Hooks, Plugins

This file controls what Claude Code can do without asking, what hooks fire, and which plugins are active.

```bash
cat ~/.claude/settings.json 2>/dev/null && echo "EXISTS" || echo "MISSING"
```

**If MISSING:**
```bash
cp silas-ai-toolkit/claude-code-toolkit/configs/settings.json.template ~/.claude/settings.json
```

**If EXISTS:** Merge missing sections. Key things to check:
- `permissions.allow` should include `"mcp__*"` for MCP tools to work
- `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` should be `"1"` for agent teams
- `enabledPlugins` section — enable the ones you want

**Do the same `{{HOME_DIR}}` replacement** in all hook paths.

### Verify:
```bash
# Should parse without errors
node -e "JSON.parse(require('fs').readFileSync(process.env.HOME+'/.claude.json','utf8')); console.log('claude.json: OK')"
node -e "JSON.parse(require('fs').readFileSync(process.env.HOME+'/.claude/settings.json','utf8')); console.log('settings.json: OK')"
```

---

## Section 2: Playwright CLI — Browser Automation (5 min)

**What:** Lets Brother control a web browser — click buttons, fill forms, scrape pages, test web apps.
**Why first:** Biggest force multiplier. No API keys needed. Works immediately.
**Note:** Playwright CLI replaces the deprecated Playwright MCP server. CLI is 4x more token-efficient.

### Install:
```bash
# Install Playwright and browser binaries
npx playwright install chromium
```

### Verify:
Start Claude Code and ask: `"Open google.com in a browser"`
Brother should launch a browser and navigate there using the Playwright CLI tools.

### Troubleshooting:
- "npx not found" → Install Node.js 18+
- Browser doesn't launch → Run `npx playwright install chromium` to install browser binaries

---

## Section 3: Context7 MCP — Library Documentation (2 min)

**What:** Live documentation lookup for any library/framework. Brother can query up-to-date docs instead of relying on training data.
**Why:** Makes coding 10x more accurate. Zero config needed.

### Install:
Already configured in the template as an HTTP MCP server — no local install needed:

```json
"context7": {
  "type": "http",
  "url": "https://mcp.context7.com/mcp"
}
```

Just make sure this block is in your `~/.claude.json` under `mcpServers`.

### Verify:
Start Claude Code and ask: `"Use Context7 to look up the latest React hooks documentation"`

---

## Section 4: Firecrawl MCP — Web Search & Scraping (5 min)

**What:** Web search, page scraping, site crawling, and data extraction.
**Why:** Brother can research anything on the web autonomously.

> **⚠️ Token Budget Note:** Firecrawl should be **DISABLED by default** (`"disabled": true` in your `.claude.json` config). It adds significant context overhead every turn. Enable it on-demand only when a task specifically requires web scraping, search, or crawling, then disable it again after. This was identified in the Session #119 token audit.

### Get API Key:
1. Go to https://www.firecrawl.dev/
2. Sign up (free tier gives 500 credits/month)
3. Copy your API key from the dashboard

### Install:
```bash
# Test the package
npx -y firecrawl-mcp --help
```

### Configure:
Add to `mcpServers` in `~/.claude.json` (or update the template placeholder):
```json
"firecrawl": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "firecrawl-mcp"],
  "env": {
    "FIRECRAWL_API_KEY": "fc-YOUR_ACTUAL_KEY_HERE"
  }
}
```

### Verify:
Start Claude Code and ask: `"Use Firecrawl to search for 'best practices for Claude Code MCP servers'"`

---

## Section 5: Discord MCP — Team Communication (20 min)

**What:** Read/write Discord messages. The backbone for team handoffs, logging, and alerts.
**Why:** Enables async communication between Brother and Proctor (and future agents).

### Step 1: Create a Discord Server
If you don't have one yet:
1. Open Discord → "+" button → "Create My Own" → "For me and my friends"
2. Name it something like "Tandem Team" or "[YourName] AI Ops"

### Step 2: Create Channels
Create these text channels (right-click category → Create Channel):

| Channel | Purpose |
|---------|---------|
| #handoffs | Cross-agent task handoffs and status updates |
| #brother-log | Brother session logs and build output |
| #proctor-log | Proctor session logs and decisions |
| #alerts | Infrastructure alerts and urgent notices |
| #session-archive | End-of-session summaries |

**Save each channel's ID** (right-click channel → Copy Channel ID). You'll need these for your CLAUDE.md.
(Enable Developer Mode first: Settings → App Settings → Advanced → Developer Mode)

### Step 3: Create a Discord Bot
1. Go to https://discord.com/developers/applications
2. "New Application" → name it "Tandem Bot" → Create
3. Go to "Bot" tab → "Reset Token" → **copy and save the token** (you can only see it once)
4. Under "Privileged Gateway Intents" → enable ALL three:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
5. Go to "OAuth2" tab → "URL Generator":
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `Read Message History`, `Read Messages/View Channels`, `Manage Messages`, `Add Reactions`
6. Copy the generated URL → open it in browser → select your server → Authorize

### Step 4: Install Java (required for discord-mcp JAR)
```bash
# Check if Java 17+ is installed
java -version

# If not installed:
# Windows: Download Amazon Corretto 17 from https://docs.aws.amazon.com/corretto/latest/userguide/downloads-list.html
# Or use winget:
# winget install Amazon.Corretto.17
```

### Step 5: Get discord-mcp
```bash
mkdir -p ~/tools/discord-mcp

# Download the JAR (check for latest release):
# Option A: Build from source if you have the repo
# Option B: Download from releases page
# Place the JAR at: ~/tools/discord-mcp/discord-mcp.jar
```

### Step 6: Configure
Update `~/.claude.json` with your real values:
```json
"discord-mcp": {
  "type": "stdio",
  "command": "C:\\Program Files\\Amazon Corretto\\jdk17.0.18_9\\bin\\java.exe",
  "args": ["-jar", "C:\\Users\\YOUR_USERNAME\\tools\\discord-mcp\\discord-mcp.jar"],
  "env": {
    "DISCORD_TOKEN": "YOUR_BOT_TOKEN_FROM_STEP_3",
    "DISCORD_GUILD_ID": "YOUR_SERVER_ID"
  }
}
```

**Get your Server ID:** Right-click your server name → Copy Server ID

### Verify:
Start Claude Code and ask: `"Read the last 5 messages from #handoffs"`

### Troubleshooting:
- "Bot not responding" → Check the bot is online in your Discord server (green dot)
- "Missing permissions" → Re-invite the bot with the OAuth URL from Step 3
- "Java not found" → Make sure the java path in the config matches your actual install

---

## Section 6: Docker + MCP Docker Gateway (15 min)

**What:** Docker Desktop + MCP Gateway gives Brother access to databases, memory services, and containerized tools.
**Why:** Postgres, n8n, and other services all run in Docker.

### Step 1: Docker Desktop
```bash
# Verify Docker is running
docker ps

# If not installed: Download from https://www.docker.com/products/docker-desktop/
# After install, make sure it's running (system tray icon)
```

### Step 2: MCP Docker Gateway
The Docker MCP Gateway lets Claude Code manage containers and connect to Docker-hosted databases.

```bash
# Pull the gateway
docker pull mcp/gateway 2>/dev/null || echo "May need manual setup — see Docker MCP docs"
```

The template already has the config:
```json
"MCP_DOCKER": {
  "command": "docker",
  "args": ["mcp", "gateway", "run"],
  "env": {
    "LOCALAPPDATA": "C:\\Users\\YOUR_USERNAME\\AppData\\Local",
    "ProgramData": "C:\\ProgramData",
    "ProgramFiles": "C:\\Program Files"
  }
}
```

### Step 3: PostgreSQL (optional but recommended)
If you need a database for your projects:

```bash
# Quick Postgres setup via Docker
docker run -d \
  --name postgres-dev \
  -e POSTGRES_USER=dev \
  -e POSTGRES_PASSWORD=devpass \
  -e POSTGRES_DB=main \
  -p 5432:5432 \
  postgres:16

# Verify
docker exec postgres-dev psql -U dev -d main -c "SELECT 1;"
```

### Verify:
```bash
docker ps  # Should show running containers
```
Start Claude Code and ask: `"List all running Docker containers"`

---

## Section 7: n8n — Workflow Automation (20 min)

**What:** n8n is a self-hosted workflow automation platform. It becomes your "Council" — handling scheduled tasks, automated briefings, notifications, and pipeline triggers.
**Why:** Automates everything that shouldn't require manual intervention: session archival, scheduled checks, webhook-triggered workflows.

### Step 1: Run n8n in Docker
```bash
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  --restart unless-stopped \
  n8nio/n8n:latest

# Wait for it to start
sleep 10

# Check it's running
docker logs n8n --tail 20
```

### Step 2: Initial Setup
1. Open http://localhost:5678 in your browser
2. Create your admin account (save these credentials!)
3. Go to Settings → API → Create an API key
4. **Save the API key** — Brother needs this to interact with n8n

### Step 3: n8n MCP Server
Already in the template:
```json
"n8n-mcp": {
  "type": "stdio",
  "command": "cmd",
  "args": ["/c", "npx", "-y", "n8n-mcp"],
  "env": {
    "MCP_MODE": "stdio",
    "LOG_LEVEL": "error",
    "DISABLE_CONSOLE_OUTPUT": "true"
  }
}
```

**Important n8n API auth pattern:**
When Brother calls the n8n API directly (not through MCP), use:
```
Header: X-N8N-API-KEY: your-api-key
```
NOT `Authorization: Bearer` — that returns 401 on n8n.

### Step 4: Starter Workflows
These are optional but powerful. Build them as you need them:

| Workflow | What it does | Trigger |
|----------|-------------|---------|
| Session Archive | Auto-archives session snapshots older than 7 days | Cron: daily |
| Inbox Cleanup | Clears processed inbox messages older than 3 days | Cron: every 12h |
| Notification Relay | Forwards Discord alerts to notification queue files | Webhook |
| Health Check | Pings all services and reports status | Cron: hourly |

### Verify:
```bash
curl -s http://localhost:5678/api/v1/workflows -H "X-N8N-API-KEY: YOUR_KEY" | head -20
```
Start Claude Code and ask: `"List my n8n workflows"`

### Troubleshooting:
- n8n won't start → Check port 5678 isn't in use: `netstat -ano | grep 5678`
- API returns 401 → Use `X-N8N-API-KEY` header, not Bearer
- Container keeps restarting → Check logs: `docker logs n8n`

---

## Section 8: Windows MCP — Desktop Automation (10 min, Proctor only, Windows only)

**What:** Screen reading, clicking, typing, window management. Proctor can see and interact with the desktop.
**Why:** Enables Proctor (Claude Desktop Chat tab) to perform GUI automation tasks.

> **⚠️ Proctor Only.** Brother (Claude Code terminal) does NOT need Windows MCP. Brother has Bash, Playwright, and direct file access which covers all the same ground. Only install this if you're setting up Proctor (Claude Desktop Chat tab) for GUI automation. Keeping it on Brother wastes ~20+ deferred tool definitions per turn.

### Install:
```bash
# Need Python's uvx (comes with uv package manager)
pip install uv
# Or if you already have uvx:
uvx --version
```

The template config:
```json
"windows-mcp": {
  "type": "stdio",
  "command": "C:\\Users\\YOUR_USERNAME\\.local\\bin\\uvx.exe",
  "args": ["--from", "windows-mcp<2", "--with", "fastmcp<3", "windows-mcp"],
  "env": {
    "PYTHONIOENCODING": "utf-8"
  }
}
```

**Update the command path** to where your `uvx.exe` actually lives:
```bash
which uvx    # Git Bash
where uvx    # CMD
```

### Verify:
Start Claude Code and ask: `"Take a screenshot of my desktop"`

### Troubleshooting:
- "uvx not found" → `pip install uv` then check path
- Screenshot is blank → Make sure the terminal isn't minimized
- Permission errors → Run terminal as Administrator for first use

---

## Section 9: Google Drive MCP (15 min, optional — DISABLED by default)

**What:** Read/write Google Docs, Sheets, and Slides directly from Claude Code.
**Why:** Create and manage documents without leaving the terminal.

> **⚠️ Token Budget Note:** Google Drive MCP should be **DISABLED by default** (`"disabled": true` in your `.claude.json` config). It burns ~16K tokens/turn when loaded. Brother enables it on-demand when a task requires Google Docs/Sheets/Slides editing, then disables it again after. A `/google-toggle` skill handles this automatically.
>
> **Tasks that NEED Google Drive MCP:**
> - Creating/editing Google Docs, Sheets, Slides, or Presentations
> - Formatting documents (text styles, paragraph styles, tables)
> - Inserting images, smart chips, or comments into Google Docs
> - PDF conversion via Google Drive
>
> **Tasks that do NOT need it (use `gws` CLI instead):**
> - Listing Drive files
> - Downloading/uploading files
> - Reading spreadsheet data (`gws sheets read`)
> - Calendar operations
> - Gmail operations
> - Basic Drive file management

### Step 1: Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Enable these APIs:
   - Google Drive API
   - Google Docs API
   - Google Sheets API
   - Google Slides API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
   - Application type: Desktop app
   - Download the `client_secret.json` file

### Step 2: Install
```bash
# Create config directory
mkdir -p ~/.config/google-drive-mcp

# Place your client_secret.json
cp /path/to/downloaded/client_secret.json ~/.config/google-drive-mcp/

# Install the server
npm install -g google-drive-mcp
```

### Step 3: First-time Auth
```bash
# Run once to complete OAuth flow (opens browser)
google-drive-mcp auth
```

### Step 4: Configure
Update the template entry in `~/.claude.json`:
```json
"google-drive-mcp": {
  "type": "stdio",
  "command": "YOUR_PATH_TO/start-server.cmd",
  "args": [],
  "env": {
    "GOOGLE_DRIVE_OAUTH_CREDENTIALS": "YOUR_PATH_TO/client_secret.json"
  }
}
```

### Verify:
Start Claude Code and ask: `"List my recent Google Drive files"`

---

## Section 10: LSP Plugins — Code Intelligence (5 min)

**What:** Language Server Protocol gives Brother 9 code intelligence operations: `goToDefinition`, `findReferences`, `hover`, `documentSymbol`, `workspaceSymbol`, `goToImplementation`, `prepareCallHierarchy`, `incomingCalls`, `outgoingCalls`.
**Why:** 250x token reduction vs grep-based code navigation. Finding a function definition via LSP = ~52 tokens. Via grep = ~11,536 tokens. This is the biggest token efficiency gain available.

> **Token efficiency data (measured):** A single `documentSymbol` call returns structured symbols for an entire file in ~52 tokens. The equivalent grep-based approach (search, read file, parse, filter) burns ~11,536 tokens. That's a 250:1 ratio per navigation action. Over a session with 20+ code lookups, this saves 200K+ tokens.

### Step 1: Install Language Servers
```bash
# Install the language servers that the LSP plugins will use
npm install -g typescript-language-server pyright vscode-langservers-extracted

# Verify they're on PATH
typescript-language-server --version   # Should return 5.x+
pyright --version                       # Should return 1.x+
```

### Step 2: Enable LSP Environment Variable
Add to `env` in `~/.claude/settings.json`:
```json
"ENABLE_LSP_TOOL": "1"
```
(Already in the settings template.)

### Step 3: Enable LSP Plugins
Add to `enabledPlugins` in `~/.claude/settings.json`:
```json
"typescript-lsp@claude-plugins-official": true,
"python-lsp@claude-plugins-official": true,
"go-lsp@claude-plugins-official": true,
"rust-lsp@claude-plugins-official": true,
"java-lsp@claude-plugins-official": true,
"c-cpp-lsp@claude-plugins-official": true,
"csharp-lsp@claude-plugins-official": true,
"php-lsp@claude-plugins-official": true,
"kotlin-lsp@claude-plugins-official": true,
"ruby-lsp@claude-plugins-official": true,
"html-css-lsp@claude-plugins-official": true
```
(All 11 are already in the settings template.)

Enable only the languages you work with. Unused plugins have zero runtime cost — they only load when you open a file of that type.

### Step 4: Install ast-grep (Companion Tool)
```bash
# ast-grep for structural code search (complements LSP)
pip install ast-grep-cli
sg --version   # Should return 0.41+
```

**When to use which:**
- **LSP** — Symbol navigation, definitions, references, hover docs. Fastest and cheapest.
- **ast-grep** — Structural pattern matching (e.g., "find all functions with 3 args"). More flexible than LSP for pattern queries.
- **Grep** — Text search, regex patterns, config/doc files. Fallback when LSP/ast-grep don't apply.

### Verify:
Start Claude Code and ask: `"Use documentSymbol on src/app/page.tsx"` — it should return all symbols in the file.

> **Known issue (2026-03):** On Windows, the LSP tool loads and all 9 operations appear, but language servers may fail to spawn due to a PATH inheritance bug in Claude Code's Node.js child_process. The plugins are correctly configured — this is an Anthropic bug that will be fixed in a future update. Keep plugins enabled so they auto-activate when fixed.

### Priority Rule for Code Navigation
**LSP FIRST, ast-grep SECOND, grep LAST.** Add this to your CLAUDE.md:
```markdown
## Tool Priority: LSP FIRST, ast-grep SECOND
When navigating code, ALWAYS prefer LSP tools before grep, glob, bash, or Read-and-scan.
LSP is faster, more accurate, and cheaper on tokens. Use ast-grep for structural pattern
matching. Only fall back to grep/glob for non-code text search, regex patterns, or config files.
```

---

## Section 11: Plugins (5 min)

Official and community plugins add slash commands and workflows.

### Official Plugins (auto-install when enabled in settings.json):
These are already in the settings template. Just make sure they're set to `true`:
```json
"feature-dev@claude-plugins-official": true,
"code-review@claude-plugins-official": true,
"pr-review-toolkit@claude-plugins-official": true,
"commit-commands@claude-plugins-official": true,
"claude-md-management@claude-plugins-official": true,
"code-simplifier@claude-plugins-official": true,
"skill-creator@claude-plugins-official": true
```

### GSD Plugin (community — manual install):
GSD (Get Stuff Done) adds project management, task tracking, and workflow agents.
```bash
claude plugin install workflow@cctools-plugins
claude plugin install aichat@cctools-plugins
```

> **⚠️ Voice Plugin Note:** The voice plugin (`voicemode`) was disabled in the token audit — it adds significant context overhead every turn. Only enable if you specifically need voice interaction:
> ```bash
> claude plugin install voice@cctools-plugins   # Only if you need voice
> ```

### Verify:
Start Claude Code and type `/` — you should see all your installed slash commands listed.

---

## Section 12: Credential Vault (5 min)

Create a single file for all secrets. **NEVER commit this file.**

```bash
cat > ~/Documents/claude-context/council-config.json << 'VAULT'
{
  "_WARNING": "THIS FILE CONTAINS SECRETS — NEVER COMMIT TO GIT",
  "discord": {
    "bot_token": "YOUR_DISCORD_BOT_TOKEN",
    "guild_id": "YOUR_SERVER_ID",
    "channels": {
      "handoffs": "CHANNEL_ID",
      "brother_log": "CHANNEL_ID",
      "proctor_log": "CHANNEL_ID",
      "alerts": "CHANNEL_ID",
      "session_archive": "CHANNEL_ID"
    }
  },
  "n8n": {
    "api_key": "YOUR_N8N_API_KEY",
    "base_url": "http://localhost:5678"
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "user": "dev",
    "password": "devpass",
    "database": "main"
  },
  "firecrawl": {
    "api_key": "YOUR_FIRECRAWL_KEY"
  },
  "github": {
    "pat": "YOUR_GITHUB_PAT"
  },
  "google": {
    "oauth_email": "YOUR_GOOGLE_EMAIL",
    "credentials_path": "PATH_TO/client_secret.json"
  }
}
VAULT

echo "council-config.json" >> ~/Documents/claude-context/.gitignore
```

**Tell Brother about it** by adding to your CLAUDE.md:
```markdown
## Credentials
All API keys and secrets: ~/Documents/claude-context/council-config.json
Read this FIRST before asking me for credentials.
```

---

## Section 13: Hooks — Automated Guardrails (5 min)

Hooks fire automatically on specific Claude Code events (PreToolUse, PostToolUse, etc.) and enforce protocols mechanically instead of relying on the honor system.

### Skill Zero PreToolUse Hook

**What:** Counts tool calls in a session. If the agent hits 4+ tool calls without Skill Zero (swarm-first-planning gate check) output being visible in the conversation, it warns.
**Why:** Enforces planning-before-execution mechanically. Without this, agents skip the planning gate 100% of the time when not explicitly reminded.

Add this to `hooks.PreToolUse` in your `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hook": "bash {{HOME_DIR}}/.claude/hooks/skill-zero-gate.sh"
      }
    ]
  }
}
```

The hook script (`~/.claude/hooks/skill-zero-gate.sh`) checks for Skill Zero output markers in the conversation context. If 4+ tool calls have fired without the planning template being visible, the hook emits a warning that blocks execution until the agent runs the gate check.

**How it works:**
1. Every tool call increments a counter (tracked in a temp file per session)
2. The hook checks whether Skill Zero markers (e.g., `GATE CHECK`, `swarm-first-planning`) appeared in the conversation
3. If counter >= 4 and no markers found, the hook returns a warning message
4. The agent sees the warning and must run the planning gate before continuing

> **Note:** Replace `{{HOME_DIR}}` with your actual home path. The hook script template is provided in `claude-code-toolkit/hooks/skill-zero-gate.sh`.

---

## Section 14: StatusLine — Ambient Token Meter (2 min)

The statusLine is a persistent bar at the bottom of your Claude Code terminal. It updates after every assistant message and shows you what matters at a glance — model, directory, context usage, and **cumulative session token burn** (including background agents).

**Why this matters:** When Brother spawns 4 parallel agents, your context window might show 30% but you've burned 400K+ tokens across those agents. The token meter makes that visible without switching windows.

**What it shows:**
```
Opus 4.6 │ my-project │ ██████░░░░ 60% │ 341K tokens
```

- **Context bar:** Green (<63%), Yellow (<81%), Orange (<95%), Red/skull (95%+)
- **Token count:** Blue, cumulative for the session (resets each new session)

### Install

The statusLine script is already in this repo:

```bash
# Copy the statusLine script to your hooks folder
cp claude-code-toolkit/configs/hooks/gsd-statusline.js ~/.claude/hooks/gsd-statusline.js
```

Then add this to your `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "node \"{{HOME_DIR}}/.claude/hooks/gsd-statusline.js\""
  }
}
```

> **Note:** Replace `{{HOME_DIR}}` with your actual home path (e.g., `C:/Users/scotty`).

### Verify

Start a new Claude Code session. After your first message, you should see the status bar at the bottom with model name, context bar, and token count.

### How it works

Claude Code's statusLine API pushes a JSON blob to the script via stdin after every assistant message. The blob includes `context_window.total_input_tokens`, `context_window.total_output_tokens`, `context_window.remaining_percentage`, and more. The script formats and colorizes the output. Zero API token cost — it's free metadata.

### Customization

You can generate a custom statusLine from natural language using `/statusline` in Claude Code. But the provided script is battle-tested and includes the token meter that stock statusLines don't have.

---

## Post-Install Checklist

After completing the sections above, run through this checklist:

```
[ ] .claude.json has all MCP servers configured with real paths
[ ] settings.json has permissions, plugins, and hooks configured
[ ] Playwright: "Open google.com" works
[ ] Context7: Library doc lookup works
[ ] Firecrawl: DISABLED by default ("disabled": true) — enable on-demand for web scraping
[ ] Discord: Read/send messages works (if installed)
[ ] Docker: Containers visible and manageable
[ ] n8n: API responds, workflows listable (if installed)
[ ] Windows MCP: Proctor (Claude Desktop) ONLY — do NOT enable for Brother
[ ] Google Drive: DISABLED by default ("disabled": true) — enable on-demand via /google-toggle
[ ] LSP: ENABLE_LSP_TOOL=1 in settings.json env block
[ ] LSP: Language servers installed (typescript-language-server, pyright, vscode-langservers-extracted)
[ ] LSP: 11 LSP plugins enabled in settings.json enabledPlugins
[ ] LSP: ast-grep installed (pip install ast-grep-cli)
[ ] Plugins: /slash commands appear (voice plugin disabled unless needed)
[ ] Plugins: skill-creator plugin enabled
[ ] Skill Zero hook: PreToolUse gate check configured in settings.json
[ ] StatusLine: Token meter visible at bottom of terminal after first message
[ ] council-config.json created with all credentials
[ ] CLAUDE.md updated to reference credential vault
```

### Re-run bootstrap to confirm:
```bash
cd silas-ai-toolkit/claude-code-toolkit
bash bootstrap.sh
```
Everything should show green checkmarks now.

---

## What's Next — Phase 3

Once infrastructure is stable, Phase 3 covers:
- **Proctor setup** (Claude Desktop as strategic coordinator)
- **Cross-agent communication** (Discord dual-write protocol)
- **Automated workflows** (n8n Council Engine — briefings, archival, health checks)
- **Knowledge Layer** (RAG-backed memory with webhook ingestion)
- **Advanced hooks** (session registration, memory awareness, file claims)
- **Swarm-first planning** (mandatory agent decomposition protocol)

Phase 3 will be pushed to this repo when you're ready. Pull and run bootstrap.sh — it'll pick up everything new.
