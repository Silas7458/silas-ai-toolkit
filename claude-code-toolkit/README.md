# Claude Code Power User Toolkit

**A complete blueprint for configuring Claude Code as a power-user engineering assistant.**

This toolkit documents and packages everything that makes a heavily-configured Claude Code instance different from a fresh install. It is the distillation of hundreds of sessions of real-world usage -- the configurations, protocols, lessons learned, MCP integrations, agent patterns, and operational playbooks that turn Claude Code from a basic coding assistant into a full engineering command center.

---

## What Makes This Different From Stock Claude Code?

A fresh Claude Code install gives you a capable coding assistant. This toolkit transforms it into something far more powerful:

| Capability | Stock Claude Code | With This Toolkit |
|-----------|------------------|-------------------|
| **Session continuity** | Every session starts from zero | Startup/shutdown protocols preserve state across sessions |
| **Task prioritization** | You decide what to work on | Eisenhower Matrix framework for systematic prioritization |
| **Context management** | Burns through context on raw file reads | Agent delegation protocol conserves context 2-3x |
| **Multi-agent coordination** | Single instance | Multiple Claude instances coordinate via Discord/file inboxes |
| **MCP integrations** | None configured | Browser automation, Discord, Google Drive, databases, desktop control |
| **Memory system** | Basic auto-memory | Structured memory with permanent lessons, error recovery patterns |
| **Quality standards** | Default behavior | Prime Directive enforces 100% completion, no lazy omissions |
| **Agent prompt templates** | Ad-hoc prompts, inconsistent quality | 10 battle-tested templates with built-in quality guardrails |
| **Deliverable coordination** | Files scattered everywhere | Shared folder, naming convention, Discord announcements |
| **Playbooks** | Learning from scratch each session | Accumulated hard-won lessons from real failures |

---

## Who Is This For?

- **Power users** who want Claude Code to be more than a coding assistant
- **Teams** running multiple Claude instances that need to coordinate
- **Anyone** who wants to replicate a battle-tested Claude Code configuration on a new machine
- **Developers** interested in MCP server integrations, hooks, and advanced workflows

---

## Repository Structure

```
claude-code-toolkit/
├── README.md                          # This file -- overview and quick start
├── SETUP-GUIDE.md                     # Step-by-step machine replication guide
├── INSTALLED-PLUGINS.md               # Third-party plugins manifest + install instructions
├── configs/
│   ├── CLAUDE.md.template             # Master instruction file template
│   ├── claude.json.template           # MCP server configuration (9 servers)
│   ├── settings.json.template         # Claude Code settings, hooks, and plugins
│   ├── claude-desktop-config.json.template  # Claude Desktop MCP config (for Proctor)
│   ├── README.md                      # Config file explanations
│   └── hooks/
│       ├── auto-format.js             # Post-tool: auto-formats code files with Prettier
│       ├── context-bracket.js         # UserPromptSubmit: injects context brackets
│       ├── restore-terminal.js        # PostToolUse: restores terminal after MCP clicks
│       └── dist/
│           ├── file-claims.mjs        # PreToolUse: file claim tracking
│           ├── memory-awareness.mjs   # PostToolUse: memory awareness integration
│           └── session-register.mjs   # SessionStart: session registration
├── commands/                          # Slash commands (copy to ~/.claude/commands/)
│   ├── diff-review.md                 # Generate visual HTML diff review
│   ├── fact-check.md                  # Verify document accuracy against codebase
│   ├── generate-slides.md             # Magazine-quality HTML slide decks
│   ├── generate-web-diagram.md        # Standalone HTML diagrams
│   ├── pg-query.md                    # PostgreSQL database query tool
│   ├── plan-review.md                 # Visual plan review (current vs proposed)
│   ├── project-recap.md               # Project mental model rebuild
│   ├── recall.md                      # Recall from memory system
│   └── remember.md                    # Store to memory system
├── agent-prompts/
│   ├── _base-rules.md                 # 10 mandatory quality rules for ALL agents
│   ├── INDEX.md                       # Template catalog with usage guide
│   ├── 01-video-analyzer.md           # Video content analysis (keyframes + transcript)
│   ├── 02-stack-evaluator.md          # Tool/repo evaluation against installed stack
│   ├── 03-deep-comparison.md          # Merge multiple sources into one brief
│   ├── 04-research-synthesizer.md     # Consolidate parallel agent outputs
│   ├── 05-code-builder.md             # Build + verify working code
│   ├── 06-document-builder.md         # Professional .docx/.xlsx creation
│   ├── 07-codebase-explorer.md        # Map unfamiliar codebase architecture
│   ├── 08-web-researcher.md           # Multi-source web research with validation
│   ├── 09-audit-reviewer.md           # Thorough code/security/PR review
│   └── 10-deliverable-qa.md           # Final quality gate before delivery
├── agents/                            # Custom agents (copy to ~/.claude/agents/)
│   ├── tandem-researcher.md           # Multi-source web research agent
│   ├── tandem-doc-builder.md          # Professional document builder agent
│   ├── tandem-deployer.md             # Vercel deploy-verify agent
│   ├── tandem-qa.md                   # Final QA inspection agent
│   ├── tandem-strategist.md           # Strategic integrity & drift detection agent
│   └── precedent-hunter.md            # Searches history for prior solutions
├── scripts/                           # Infrastructure scripts (sanitized)
│   ├── build_valuation_synthesis.py   # Valuation tool builder
│   ├── update_valuation_model_v3.py   # Valuation model updater
│   ├── claude-config-guard.ps1        # Hourly config integrity check (schtasks)
│   ├── compile-proctor-briefing.ps1   # Morning brief compiler
│   ├── wire-discord-webhooks.py       # Discord webhook setup
│   ├── launch-hidden.vbs              # VBS wrapper -- no console flash for scheduled tasks
│   └── ...                            # Additional utility scripts
├── playbooks/
│   ├── context-conservation.md        # Agent-first protocol (the crown jewel)
│   ├── lessons-learned.md             # Hard-won lessons from real failures
│   ├── video-analysis.md              # Video processing pipeline playbook
│   └── README.md                      # How to use playbooks
├── protocols/
│   ├── agent-delegation.md            # When to use agents vs do it yourself
│   ├── session-management.md          # Startup/shutdown checklist pattern
│   ├── multi-agent-coordination.md    # How multiple Claude instances coordinate
│   ├── notification-system.md         # Queue-based push notification protocol
│   └── README.md                      # Protocol overview
├── memory/
│   ├── MEMORY.md.template             # Auto-memory template with patterns
│   └── README.md                      # How the memory system works
└── examples/
    ├── agent-patterns.md              # Real agent delegation examples
    ├── research-sprint.md             # Parallel research agent patterns
    └── document-processing.md         # Large document processing patterns
```

---

## Quick Start

1. **Read the [Setup Guide](./SETUP-GUIDE.md)** -- step-by-step walkthrough for a new machine
2. **Copy and customize the [config templates](./configs/)** -- CLAUDE.md, MCP servers, settings
3. **Read the [Context Conservation playbook](./playbooks/context-conservation.md)** -- this alone will double your productive session length
4. **Review the [protocols](./protocols/)** -- adopt the ones that fit your workflow
5. **Study the [examples](./examples/)** -- see the patterns in action

---

## Key Concepts

### CLAUDE.md -- Your Master Instruction File

The `CLAUDE.md` file at your project root (or home directory) is automatically loaded by Claude Code at session start. It is the single most important configuration file. It defines:

- Identity and role detection
- Startup and shutdown procedures
- Quality standards (the "Prime Directive")
- Task prioritization framework
- Communication protocols
- File path conventions

See [configs/CLAUDE.md.template](./configs/CLAUDE.md.template) for a ready-to-customize version.

### Agent Delegation -- The Context Conservation Protocol

Claude Code can spin up sub-agents that run in their own context windows. This is the single biggest lever for productive sessions. Instead of burning your main context on 500-line file reads and multi-step research, you delegate to agents who return compact summaries.

**The math:** A 500-line file read costs ~500 lines in your context permanently. An agent reads the same file and returns a ~100-word summary. Over a session, this 5x savings compounds into 2-3x more useful work.

See [playbooks/context-conservation.md](./playbooks/context-conservation.md) for the full protocol.

### MCP Servers -- Extending Claude Code's Reach

Model Context Protocol (MCP) servers give Claude Code access to external tools and services. This toolkit documents configurations for:

- **Playwright** -- Browser automation (web scraping, testing, research)
- **Discord** -- Team communication and logging
- **Google Drive** -- Document management and sharing
- **Docker MCP Gateway** -- Database access, memory, sequential thinking
- **Windows MCP** -- Desktop automation (screenshots, clicks, window management)
- **n8n** -- Workflow automation integration

See [configs/claude.json.template](./configs/claude.json.template) for configuration details.

### Agent Prompt Templates -- Consistent Quality at Scale

When you delegate work to sub-agents, the quality of the output depends entirely on the quality of the prompt. Ad-hoc prompts produce inconsistent results -- agents skip steps, miss visual content, deliver incomplete work, or fabricate data.

This toolkit includes **10 reusable prompt templates** that solve this permanently. Each template includes:

- **Role and mission** with clear scope
- **Step-by-step process** the agent must follow
- **Output format** specifying exactly what to deliver
- **Quality rules** (10 mandatory rules baked into every template)
- **Anti-patterns** -- common mistakes the agent must avoid
- **Placeholders** for customization and example dispatches

Templates can be **chained** for complex workflows:
- **Research pipeline:** Web Researcher (x3-5 parallel) → Research Synthesizer → Document Builder → Deliverable QA
- **Video pipeline:** Video Analyzer (per video) → Deep Comparison → Stack Evaluator (per tool found)
- **Code project:** Codebase Explorer → Code Builder → Audit/Reviewer → Deliverable QA

See [agent-prompts/INDEX.md](./agent-prompts/INDEX.md) for the full catalog.

### Custom Agents -- Tandem Team Specialists

Beyond prompt templates, this toolkit includes **6 custom agent definitions** that plug directly into Claude Code's `/agents` system. These are standalone `.md` files with YAML frontmatter that define tool access, identity color, and full behavioral specifications.

| Agent | Purpose |
|-------|---------|
| **Tandem Researcher** | Multi-source web research with cross-validation and source tiering |
| **Tandem Doc Builder** | Professional .docx/.xlsx deliverables with full build-verify cycle |
| **Tandem Deployer** | Vercel deploy-verify cycle -- deploys, confirms live, reports results |
| **Tandem QA** | Final quality gate -- catches issues before any deliverable reaches the user |
| **Tandem Strategist** | 30,000-foot strategic integrity -- flags drift, applies Eisenhower Matrix |
| **Precedent Hunter** | Searches team history and memory for prior solutions before brute-force investigation |

To install, copy the files from `agents/` to `~/.claude/agents/` and they become available via `/agents` in Claude Code.

### Slash Commands -- Custom Tools

The toolkit includes **9 custom slash commands** that extend Claude Code with specialized capabilities:

| Command | Purpose |
|---------|---------|
| `/diff-review` | Visual HTML diff review of code changes |
| `/fact-check` | Verify document accuracy against the actual codebase |
| `/generate-slides` | Magazine-quality HTML slide decks |
| `/generate-web-diagram` | Standalone HTML architecture diagrams |
| `/pg-query` | Query PostgreSQL databases (read-only) |
| `/plan-review` | Visual comparison of current state vs proposed plan |
| `/project-recap` | Rebuild mental model of a project's current state |
| `/recall` | Retrieve from the structured memory system |
| `/remember` | Store durable learnings to the memory system |

To install, copy files from `commands/` to `~/.claude/commands/`.

### Hooks -- Session Lifecycle + Auto-Format

The toolkit includes **6 hooks** that fire at various points in the session lifecycle:

| Hook | Trigger | Purpose |
|------|---------|---------|
| `auto-format.js` | PostToolUse (Write/Edit) | Auto-formats code files with Prettier |
| `context-bracket.js` | UserPromptSubmit | Injects context brackets for memory/notification awareness |
| `restore-terminal.js` | PostToolUse (Windows MCP) | Restores terminal focus after desktop automation clicks |
| `session-register.mjs` | SessionStart | Registers session for tracking and continuity |
| `memory-awareness.mjs` | PostToolUse | Memory system integration hooks |
| `file-claims.mjs` | PreToolUse | Tracks file ownership claims across agents |

To install, copy `configs/hooks/` to `~/.claude/hooks/` and wire them in `settings.json`.

### Third-Party Plugins

This toolkit is designed to work alongside several third-party plugins. See [INSTALLED-PLUGINS.md](./INSTALLED-PLUGINS.md) for the complete list with install instructions. Key plugins include GSD (project management), Trail of Bits security tools, and Vercel deployment skills.

### Deliverable Coordination -- No Duplicate Work

When multiple agents produce deliverables, you need a system to prevent duplicate work and lost files. The protocol is simple:

1. **Single shared folder** with a naming convention: `{YYYY-MM-DD}-{agent}-{topic}.{ext}`
2. **Announce every deliverable** on Discord (or your team channel)
3. **Check the folder before starting work** to avoid duplicating a teammate's output

---

## Contributing

This toolkit is a living document. If you develop new protocols, discover new lessons, or build useful configurations, contributions are welcome.

---

## License

MIT
