# Configuration Templates

This directory contains template versions of the three core configuration files for Claude Code. Each file has all secrets, personal details, and machine-specific paths replaced with `[PLACEHOLDER]` markers.

---

## Files

### CLAUDE.md.template
**What it is:** The master instruction file that Claude Code reads automatically at every session start. This is the most important file in your entire configuration.

**What to customize:**
- Replace all `[YOUR_*]` placeholders with your actual values
- Remove sections you do not need (e.g., multi-agent coordination if you run a single instance)
- Add your own sections for domain-specific instructions
- Keep the universal sections (Prime Directive, Eisenhower Matrix, Startup/Shutdown protocols)

**Where it goes:** `~/CLAUDE.md` (home directory) or your project root. Claude Code checks both locations.

---

### claude.json.template
**What it is:** The MCP server configuration file. Defines which external tools Claude Code can access.

**What to customize:**
- Add only the MCP servers you actually use
- Replace all `[PLACEHOLDER]` markers with real paths, tokens, and credentials
- Remove servers you do not need

**Where it goes:** `~/.claude.json`

**Security warning:** This file will contain API keys and tokens. NEVER commit the real version to version control. Add `.claude.json` to your `.gitignore`.

---

### settings.json.template
**What it is:** Claude Code's internal settings -- permissions, hooks, plugins, and environment variables.

**What to customize:**
- Adjust permission mode to your comfort level
- Add/remove hooks based on your workflow
- Enable/disable plugins
- Set environment variables

**Where it goes:** `~/.claude/settings.json`

---

## Configuration Loading Order

Claude Code loads configuration in this order (later files can override earlier ones):

1. `~/.claude/settings.json` -- Global settings (permissions, hooks, plugins)
2. `~/.claude/CLAUDE.md` -- Global instructions (applies to all projects)
3. `~/.claude.json` -- User-level MCP servers
4. `{project}/.claude.json` -- Project-level MCP servers
5. `{project}/CLAUDE.md` -- Project-level instructions
6. `~/.claude/projects/{project-hash}/memory/MEMORY.md` -- Auto-memory

Understanding this order matters when you have both global and project-level configurations.
