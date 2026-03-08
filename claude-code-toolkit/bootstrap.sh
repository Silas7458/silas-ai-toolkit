#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Brother Bootstrap Script — Tandem Team Setup Auditor & Gap Filler
# ═══════════════════════════════════════════════════════════════════════
#
# PURPOSE: Audit an existing Claude Code setup, detect what's already
# installed, identify gaps, and offer to fill them — WITHOUT overwriting
# anything that already exists.
#
# USAGE:
#   cd /path/to/silas-ai-toolkit/claude-code-toolkit
#   bash bootstrap.sh
#
# SAFE: This script NEVER overwrites existing files. It only creates
# files that don't exist yet. For files that DO exist, it reports
# what's different so you can merge manually.
# ═══════════════════════════════════════════════════════════════════════

set -e

# ── Colors ──────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# ── Path Detection ──────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="$HOME"
USERNAME="$(whoami)"
DOCUMENTS="$HOME_DIR/Documents"

# Windows path conversion (Git Bash / MSYS2)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    IS_WINDOWS=true
    WIN_HOME="C:\\Users\\$USERNAME"
    WIN_DOCUMENTS="$WIN_HOME\\Documents"
    APPDATA_DIR="$APPDATA"
else
    IS_WINDOWS=false
    WIN_HOME="$HOME_DIR"
    WIN_DOCUMENTS="$DOCUMENTS"
    APPDATA_DIR=""
fi

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  BROTHER BOOTSTRAP — Tandem Team Setup Auditor${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${CYAN}User:${NC}       $USERNAME"
echo -e "  ${CYAN}Home:${NC}       $HOME_DIR"
echo -e "  ${CYAN}Documents:${NC}  $DOCUMENTS"
echo -e "  ${CYAN}Platform:${NC}   $(uname -s) ($OSTYPE)"
echo -e "  ${CYAN}Toolkit:${NC}    $SCRIPT_DIR"
echo ""

# ── Counters ────────────────────────────────────────────────────────
FOUND=0
MISSING=0
CREATED=0
SKIPPED=0

check_exists() {
    local path="$1"
    local label="$2"
    if [ -e "$path" ]; then
        echo -e "  ${GREEN}✓${NC} $label"
        ((FOUND++))
        return 0
    else
        echo -e "  ${RED}✗${NC} $label"
        ((MISSING++))
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════
# PHASE 1: AUDIT — What's already here?
# ═══════════════════════════════════════════════════════════════════

echo -e "${BOLD}── PHASE 1: AUDIT ──────────────────────────────────────────${NC}"
echo ""

# ── 1A: Claude Code Installation ────────────────────────────────────
echo -e "${BLUE}[Claude Code Installation]${NC}"
if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "unknown")
    echo -e "  ${GREEN}✓${NC} Claude Code CLI installed (version: $CLAUDE_VERSION)"
    ((FOUND++))
else
    echo -e "  ${RED}✗${NC} Claude Code CLI not found — install with: npm install -g @anthropic-ai/claude-code"
    ((MISSING++))
fi
echo ""

# ── 1B: Core Config Files ──────────────────────────────────────────
echo -e "${BLUE}[Core Config Files]${NC}"
check_exists "$HOME_DIR/.claude" ".claude/ directory"
check_exists "$HOME_DIR/.claude.json" ".claude.json (MCP servers config)"
check_exists "$HOME_DIR/.claude/settings.json" "settings.json (permissions & hooks)"
check_exists "$HOME_DIR/CLAUDE.md" "~/CLAUDE.md (master instructions)"
check_exists "$HOME_DIR/.claude/projects" ".claude/projects/ (project memory)"
echo ""

# ── 1C: Team Directory Structure ───────────────────────────────────
echo -e "${BLUE}[Team Directory Structure]${NC}"
check_exists "$DOCUMENTS/claude-context" "claude-context/ (session state)"
check_exists "$DOCUMENTS/claude-context/session-state.md" "session-state.md"
check_exists "$DOCUMENTS/claude-context/next-session-prompt.md" "next-session-prompt.md"
check_exists "$DOCUMENTS/claude-context/session-snapshots" "session-snapshots/"
check_exists "$DOCUMENTS/claude-context/session-snapshots/archive" "session-snapshots/archive/"
check_exists "$DOCUMENTS/claude-context/deliverables" "deliverables/"
check_exists "$DOCUMENTS/claude-context/notifications" "notifications/"
check_exists "$DOCUMENTS/claude-context/activity-log.md" "activity-log.md"
check_exists "$DOCUMENTS/claude-family" "claude-family/ (team comms)"
check_exists "$DOCUMENTS/claude-family/standing-orders" "standing-orders/"
check_exists "$DOCUMENTS/claude-family/standing-orders/brother.md" "standing-orders/brother.md"
check_exists "$DOCUMENTS/claude-family/inbox-brother.md" "inbox-brother.md"
check_exists "$DOCUMENTS/claude-family/playbooks" "playbooks/"
echo ""

# ── 1D: Custom Commands ────────────────────────────────────────────
echo -e "${BLUE}[Custom Slash Commands]${NC}"
CMD_DIR="$HOME_DIR/.claude/commands"
check_exists "$CMD_DIR" "commands/ directory"
if [ -d "$CMD_DIR" ]; then
    CMD_COUNT=$(ls "$CMD_DIR"/*.md 2>/dev/null | wc -l)
    echo -e "  ${CYAN}ℹ${NC} Found $CMD_COUNT custom commands"
    # Check each toolkit command
    for cmd_file in "$SCRIPT_DIR/commands/"*.md; do
        cmd_name=$(basename "$cmd_file")
        if [ -f "$CMD_DIR/$cmd_name" ]; then
            echo -e "    ${GREEN}✓${NC} $cmd_name"
        else
            echo -e "    ${YELLOW}○${NC} $cmd_name (available in toolkit)"
        fi
    done
fi
echo ""

# ── 1E: Custom Agents ─────────────────────────────────────────────
echo -e "${BLUE}[Custom Agents]${NC}"
AGENT_DIR="$HOME_DIR/.claude/agents"
check_exists "$AGENT_DIR" "agents/ directory"
if [ -d "$AGENT_DIR" ]; then
    AGENT_COUNT=$(ls "$AGENT_DIR"/*.md 2>/dev/null | wc -l)
    echo -e "  ${CYAN}ℹ${NC} Found $AGENT_COUNT custom agents"
fi
if [ -d "$SCRIPT_DIR/agents" ]; then
    for agent_file in "$SCRIPT_DIR/agents/"*.md; do
        agent_name=$(basename "$agent_file")
        if [ -d "$AGENT_DIR" ] && [ -f "$AGENT_DIR/$agent_name" ]; then
            echo -e "    ${GREEN}✓${NC} $agent_name"
        else
            echo -e "    ${YELLOW}○${NC} $agent_name (available in toolkit)"
        fi
    done
fi
echo ""

# ── 1F: Hooks ──────────────────────────────────────────────────────
echo -e "${BLUE}[Hooks]${NC}"
HOOK_DIR="$HOME_DIR/.claude/hooks"
check_exists "$HOOK_DIR" "hooks/ directory"
if [ -d "$HOOK_DIR" ]; then
    HOOK_COUNT=$(find "$HOOK_DIR" -name "*.js" -o -name "*.mjs" 2>/dev/null | wc -l)
    echo -e "  ${CYAN}ℹ${NC} Found $HOOK_COUNT hook scripts"
fi
echo ""

# ── 1G: MCP Servers ───────────────────────────────────────────────
echo -e "${BLUE}[MCP Server Dependencies]${NC}"
# Check for key tools
for tool in node npm npx python3 pip docker git gh; do
    if command -v $tool &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $tool"
    else
        echo -e "  ${YELLOW}○${NC} $tool (not found — some MCP servers need this)"
    fi
done
echo ""

# ── 1H: Plugins ───────────────────────────────────────────────────
echo -e "${BLUE}[Installed Plugins]${NC}"
if command -v claude &> /dev/null; then
    # Check for key plugins by looking at settings
    if [ -f "$HOME_DIR/.claude/settings.json" ]; then
        for plugin in "feature-dev" "code-review" "pr-review-toolkit" "commit-commands" "code-simplifier"; do
            if grep -q "$plugin" "$HOME_DIR/.claude/settings.json" 2>/dev/null; then
                echo -e "  ${GREEN}✓${NC} $plugin"
            else
                echo -e "  ${YELLOW}○${NC} $plugin (not configured)"
            fi
        done
    else
        echo -e "  ${YELLOW}○${NC} No settings.json — can't check plugins"
    fi
fi
echo ""

# ═══════════════════════════════════════════════════════════════════
# PHASE 2: REPORT SUMMARY
# ═══════════════════════════════════════════════════════════════════

echo -e "${BOLD}── PHASE 2: SUMMARY ────────────────────────────────────────${NC}"
echo ""
echo -e "  ${GREEN}Found:${NC}   $FOUND items already set up"
echo -e "  ${RED}Missing:${NC} $MISSING items not yet installed"
echo ""

if [ "$MISSING" -eq 0 ]; then
    echo -e "  ${GREEN}${BOLD}All clear! Your setup looks complete.${NC}"
    echo ""
    exit 0
fi

# ═══════════════════════════════════════════════════════════════════
# PHASE 3: GAP FILL — Create only what's missing
# ═══════════════════════════════════════════════════════════════════

echo -e "${BOLD}── PHASE 3: GAP FILL ───────────────────────────────────────${NC}"
echo ""
echo -e "  ${YELLOW}This will create ONLY missing items. Nothing existing will be overwritten.${NC}"
echo ""
read -p "  Proceed with gap fill? (y/n): " CONFIRM
echo ""

if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo -e "  ${CYAN}Skipped. Run again when ready.${NC}"
    echo ""
    echo -e "  ${BOLD}Manual setup:${NC} Read QUICK-START.md for the paste-ready CLAUDE.md template,"
    echo -e "  or SETUP-GUIDE.md for the full step-by-step walkthrough."
    echo ""
    exit 0
fi

# ── 3A: Create Directory Structure ─────────────────────────────────
echo -e "${BLUE}[Creating missing directories...]${NC}"

for dir in \
    "$DOCUMENTS/claude-context" \
    "$DOCUMENTS/claude-context/session-snapshots" \
    "$DOCUMENTS/claude-context/session-snapshots/archive" \
    "$DOCUMENTS/claude-context/deliverables" \
    "$DOCUMENTS/claude-context/notifications" \
    "$DOCUMENTS/claude-family" \
    "$DOCUMENTS/claude-family/standing-orders" \
    "$DOCUMENTS/claude-family/playbooks" \
    "$HOME_DIR/.claude/commands" \
    "$HOME_DIR/.claude/agents" \
    "$HOME_DIR/.claude/hooks"
do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "  ${GREEN}+${NC} Created: $dir"
        ((CREATED++))
    fi
done
echo ""

# ── 3B: Create Missing State Files ─────────────────────────────────
echo -e "${BLUE}[Creating missing state files...]${NC}"

if [ ! -f "$DOCUMENTS/claude-context/session-state.md" ]; then
    cat > "$DOCUMENTS/claude-context/session-state.md" << 'STATE'
# Session State — Brother
**Last updated:** Not yet — fresh install
**Session:** 0 (pre-bootstrap)

## Current Status
Fresh install. No prior session history.

## Immediate Next Tasks
- Confirm Brother identity and protocols are working
- Test session save/restore cycle

## Blockers
None — clean start.

## Active Projects
None yet.
STATE
    echo -e "  ${GREEN}+${NC} Created: session-state.md"
    ((CREATED++))
fi

if [ ! -f "$DOCUMENTS/claude-context/next-session-prompt.md" ]; then
    cat > "$DOCUMENTS/claude-context/next-session-prompt.md" << 'PROMPT'
# Next Session Prompt
This is a fresh install. No prior session to hand off from.
Read session-state.md and announce readiness.
PROMPT
    echo -e "  ${GREEN}+${NC} Created: next-session-prompt.md"
    ((CREATED++))
fi

if [ ! -f "$DOCUMENTS/claude-context/activity-log.md" ]; then
    echo "# Activity Log" > "$DOCUMENTS/claude-context/activity-log.md"
    echo "" >> "$DOCUMENTS/claude-context/activity-log.md"
    echo "## $(date '+%Y-%m-%d') — Bootstrap" >> "$DOCUMENTS/claude-context/activity-log.md"
    echo "- Ran bootstrap.sh — initial setup" >> "$DOCUMENTS/claude-context/activity-log.md"
    echo -e "  ${GREEN}+${NC} Created: activity-log.md"
    ((CREATED++))
fi

if [ ! -f "$DOCUMENTS/claude-context/notifications/brother-queue.md" ]; then
    echo "# Brother Notification Queue" > "$DOCUMENTS/claude-context/notifications/brother-queue.md"
    echo "No pending notifications." >> "$DOCUMENTS/claude-context/notifications/brother-queue.md"
    echo -e "  ${GREEN}+${NC} Created: brother-queue.md"
    ((CREATED++))
fi

if [ ! -f "$DOCUMENTS/claude-family/inbox-brother.md" ]; then
    echo "# BROTHER INBOX" > "$DOCUMENTS/claude-family/inbox-brother.md"
    echo "No pending items." >> "$DOCUMENTS/claude-family/inbox-brother.md"
    echo -e "  ${GREEN}+${NC} Created: inbox-brother.md"
    ((CREATED++))
fi
echo ""

# ── 3C: Copy CLAUDE.md Template (if none exists) ───────────────────
echo -e "${BLUE}[CLAUDE.md setup...]${NC}"

if [ ! -f "$HOME_DIR/CLAUDE.md" ]; then
    if [ -f "$SCRIPT_DIR/QUICK-START.md" ]; then
        # Auto-replace the path placeholders with detected values
        sed \
            -e "s|{YOUR_HOME}|$HOME_DIR|g" \
            -e "s|{YOUR_NAME}|$USERNAME|g" \
            -e "s|{YOUR_BUSINESS}|My Project|g" \
            "$SCRIPT_DIR/QUICK-START.md" > "$HOME_DIR/CLAUDE.md"
        echo -e "  ${GREEN}+${NC} Created CLAUDE.md from QUICK-START template (paths auto-filled)"
        echo -e "  ${YELLOW}!${NC} Review ~/CLAUDE.md and customize {YOUR_NAME}, {YOUR_BUSINESS}, and preferences"
        ((CREATED++))
    else
        echo -e "  ${YELLOW}!${NC} No QUICK-START.md found in toolkit — copy CLAUDE.md.template from configs/"
    fi
else
    echo -e "  ${CYAN}ℹ${NC} CLAUDE.md already exists — not overwriting"
    echo -e "  ${CYAN}ℹ${NC} Compare with toolkit templates to see if there are patterns to adopt:"
    echo -e "      diff ~/CLAUDE.md $SCRIPT_DIR/QUICK-START.md"
fi
echo ""

# ── 3D: Copy Missing Commands ──────────────────────────────────────
echo -e "${BLUE}[Copying missing slash commands...]${NC}"

if [ -d "$SCRIPT_DIR/commands" ]; then
    for cmd_file in "$SCRIPT_DIR/commands/"*.md; do
        cmd_name=$(basename "$cmd_file")
        if [ ! -f "$HOME_DIR/.claude/commands/$cmd_name" ]; then
            cp "$cmd_file" "$HOME_DIR/.claude/commands/$cmd_name"
            echo -e "  ${GREEN}+${NC} Installed command: /$cmd_name"
            ((CREATED++))
        fi
    done
fi
echo ""

# ── 3E: Copy Missing Agents ───────────────────────────────────────
echo -e "${BLUE}[Copying missing custom agents...]${NC}"

if [ -d "$SCRIPT_DIR/agents" ]; then
    for agent_file in "$SCRIPT_DIR/agents/"*.md; do
        agent_name=$(basename "$agent_file")
        if [ ! -f "$HOME_DIR/.claude/agents/$agent_name" ]; then
            cp "$agent_file" "$HOME_DIR/.claude/agents/$agent_name"
            echo -e "  ${GREEN}+${NC} Installed agent: $agent_name"
            ((CREATED++))
        fi
    done
fi
echo ""

# ── 3F: Copy Missing Playbooks ────────────────────────────────────
echo -e "${BLUE}[Copying missing playbooks...]${NC}"

if [ -d "$SCRIPT_DIR/playbooks" ]; then
    for pb_file in "$SCRIPT_DIR/playbooks/"*.md; do
        pb_name=$(basename "$pb_file")
        if [ ! -f "$DOCUMENTS/claude-family/playbooks/$pb_name" ]; then
            cp "$pb_file" "$DOCUMENTS/claude-family/playbooks/$pb_name"
            echo -e "  ${GREEN}+${NC} Installed playbook: $pb_name"
            ((CREATED++))
        fi
    done
fi
echo ""

# ── 3G: Copy Missing Protocols ────────────────────────────────────
echo -e "${BLUE}[Copying missing protocols...]${NC}"

PROTO_DIR="$DOCUMENTS/claude-family/protocols"
if [ ! -d "$PROTO_DIR" ]; then
    mkdir -p "$PROTO_DIR"
fi
if [ -d "$SCRIPT_DIR/protocols" ]; then
    for proto_file in "$SCRIPT_DIR/protocols/"*.md; do
        proto_name=$(basename "$proto_file")
        if [ ! -f "$PROTO_DIR/$proto_name" ]; then
            cp "$proto_file" "$PROTO_DIR/$proto_name"
            echo -e "  ${GREEN}+${NC} Installed protocol: $proto_name"
            ((CREATED++))
        fi
    done
fi
echo ""

# ═══════════════════════════════════════════════════════════════════
# PHASE 4: NEXT STEPS
# ═══════════════════════════════════════════════════════════════════

echo -e "${BOLD}── PHASE 4: NEXT STEPS ─────────────────────────────────────${NC}"
echo ""
echo -e "  ${GREEN}Created $CREATED new items.${NC}"
echo ""
echo -e "  ${BOLD}Do these next:${NC}"
echo ""
echo -e "  1. ${CYAN}Review ~/CLAUDE.md${NC} — customize your name, business, preferences"
echo -e "     Open it, search for placeholder values, fill them in."
echo ""
echo -e "  2. ${CYAN}Start Claude Code${NC} — run 'claude' in your project directory"
echo -e "     Brother should announce himself and read session-state.md"
echo ""
echo -e "  3. ${CYAN}Test session save/restore${NC} — end the session, start a new one"
echo -e "     The new session should pick up where the last one left off"
echo ""
echo -e "  4. ${CYAN}Add MCP servers${NC} (when ready) — see SETUP-GUIDE.md Step 3"
echo -e "     Priority order: Playwright > Context7 > Firecrawl > Discord"
echo ""
echo -e "  5. ${CYAN}Re-run this script${NC} any time to check for new toolkit additions"
echo -e "     It will never overwrite — only fill gaps"
echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}Bootstrap complete. Welcome to the Tandem Team.${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""
