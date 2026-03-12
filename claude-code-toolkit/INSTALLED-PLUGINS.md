# Installed Plugins & Skills

This manifest documents every third-party plugin, official plugin, and skill that must be
installed on a new machine to match this Claude Code configuration. Copying config files alone
is not sufficient — these must be installed separately.

---

## Plugins (managed by Claude Code plugin system)

### cctools-plugins (Community — GSD suite)

The `cctools-plugins` marketplace provides the GSD (Get Stuff Done) productivity suite.
Install all three components together — they share the same version and git SHA.

**Install command:**
```
claude plugin install voice@cctools-plugins
claude plugin install workflow@cctools-plugins
claude plugin install aichat@cctools-plugins
```

| Plugin | Version | What it provides |
|--------|---------|-----------------|
| `voice@cctools-plugins` | 1.10.3 | Voice input/output for Claude Code |
| `workflow@cctools-plugins` | 1.8.4 | GSD workflow engine — 11 agents, 27 commands, task/plan management |
| `aichat@cctools-plugins` | 1.8.4 | AI chat interface enhancements |

The GSD suite also installs two hook scripts into `~/.claude/hooks/`:
- `gsd-check-update.js` — runs on SessionStart, checks for GSD updates
- `gsd-statusline.js` — powers the custom status line in `settings.json`

These hooks are referenced in `configs/settings.json.template` and must be present.

---

### claude-plugins-official (Anthropic Official Plugins)

These install automatically when enabled in `settings.json` via the `enabledPlugins` block.
Claude Code fetches them from the `claude-plugins-official` marketplace on first launch.
No manual install command needed — enabling in config is sufficient.

| Plugin | Enabled by default | What it provides |
|--------|--------------------|-----------------|
| `feature-dev` | Yes | Feature development workflow and scaffolding |
| `code-review` | Yes | Structured code review commands |
| `pr-review-toolkit` | Yes | Pull request review workflow |
| `commit-commands` | Yes | Git commit helpers (`/commit`, `/commit-all`, etc.) |
| `claude-md-management` | Yes | CLAUDE.md file management commands |
| `code-simplifier` | Yes | Code simplification and refactoring commands |
| `vercel` | Yes | Vercel deployment commands (`/deploy`, `/logs`, etc.) |
| `skill-creator` | Yes | Build, modify, and benchmark custom skills |
| `frontend-design` | No (disabled) | Frontend design and CSS tooling |
| `hookify` | No (disabled) | Hook scaffolding and management |
| `playground` | No (disabled) | Interactive code playground |
| `plugin-dev` | No (disabled) | Plugin development scaffolding |
| `security-guidance` | No (disabled) | Security review and guidance commands |

### LSP Plugins (Language Server Protocol — Code Intelligence)

11 LSP plugins providing code intelligence via the LSP tool. Requires `ENABLE_LSP_TOOL=1` in settings.json env.
These auto-install when enabled in `settings.json`. Each plugin activates for its file type.

**Requires language servers installed globally:**
```bash
npm install -g typescript-language-server pyright vscode-langservers-extracted
pip install ast-grep-cli  # Companion structural search tool
```

| Plugin | Language | Language Server |
|--------|----------|----------------|
| `typescript-lsp` | TypeScript/JavaScript | typescript-language-server |
| `python-lsp` | Python | pyright |
| `go-lsp` | Go | gopls |
| `rust-lsp` | Rust | rust-analyzer |
| `java-lsp` | Java | eclipse.jdt.ls |
| `c-cpp-lsp` | C/C++ | clangd |
| `csharp-lsp` | C# | OmniSharp |
| `php-lsp` | PHP | intelephense |
| `kotlin-lsp` | Kotlin | kotlin-language-server |
| `ruby-lsp` | Ruby | ruby-lsp |
| `html-css-lsp` | HTML/CSS | vscode-langservers-extracted |

**9 LSP operations available:** goToDefinition, findReferences, hover, documentSymbol, workspaceSymbol, goToImplementation, prepareCallHierarchy, incomingCalls, outgoingCalls

**Token efficiency:** 250x reduction vs grep-based navigation (~52 tokens per LSP call vs ~11,536 for equivalent grep chain).

> **Known issue (2026-03):** On Windows, the LSP tool loads but language servers may fail to spawn (PATH inheritance bug in Claude Code's Node.js child_process). Keep plugins enabled — they'll auto-work when Anthropic fixes the spawn path.

---

## Skills (manual install — not managed by plugin system)

Skills live in `~/.claude/skills/` and are loaded by Claude Code automatically.
They are NOT in the plugin registry and must be copied or installed manually.

### Trail of Bits Security Skills

Four skills from Trail of Bits providing security analysis capabilities.
**Install method:** Copy skill directories into `~/.claude/skills/`.
Source: https://github.com/trailofbits/claude-security-skills (verify URL — install from official ToB repo)

| Skill | What it provides |
|-------|-----------------|
| `tob-codeql` | CodeQL query generation and security analysis |
| `tob-property-testing` | Property-based testing for security invariants |
| `tob-semgrep` | Semgrep rule generation for vulnerability detection |
| `tob-variant-analysis` | Variant analysis to find related vulnerabilities |

### Vercel Skills (symlinked from vercel plugin)

Three skills symlinked from the `vercel@claude-plugins-official` plugin install.
They are installed automatically when the vercel plugin is enabled — no separate action needed.
The `@` suffix on directory names indicates symlinks.

| Skill | What it provides |
|-------|-----------------|
| `vercel-composition-patterns@` | Vercel composition and architecture patterns |
| `vercel-react-best-practices@` | React best practices for Vercel deployments |
| `vercel-react-native-skills@` | React Native guidance for Vercel |

### web-design-guidelines (symlinked)

Symlinked skill (`web-design-guidelines@`) — installed automatically by a plugin, no manual action needed.

### Custom / Local Skills

These skills are custom-built and live in this repo under `claude-code-toolkit/skills/` (or must be copied manually):

| Skill | What it provides |
|-------|-----------------|
| `docx` | Read/write/edit Word documents via Python scripts |
| `xlsx` | Read/write Excel spreadsheets |
| `pdf` | PDF reading and extraction |
| `pptx` | PowerPoint file handling |
| `doc-coauthoring` | Multi-agent document co-authoring workflow |
| `visual-explainer` | Generate visual explanations and diagrams |
| `webapp-testing` | Web application testing patterns |
| `google-workspace` | Google Docs/Sheets/Calendar API helpers |
| `restore-session` | Session restore protocol |
| `n8n-code-javascript` | n8n JavaScript code node patterns |
| `n8n-code-python` | n8n Python code node patterns |
| `n8n-expression-syntax` | n8n expression syntax reference |
| `n8n-mcp-tools-expert` | n8n MCP tools usage guide |
| `n8n-node-configuration` | n8n node configuration patterns |
| `n8n-validation-expert` | n8n workflow validation and error catalog |
| `n8n-workflow-patterns` | n8n workflow architecture patterns |

---

## GSD Agents (`.claude/agents/`)

The following agent files must be present in `~/.claude/agents/`. They are part of the GSD
workflow system and the custom Tandem Team setup. Copy from `claude-code-toolkit/agents/`.

### GSD Core Agents (11)
| Agent | Purpose |
|-------|---------|
| `gsd-codebase-mapper.md` | Maps and understands codebase structure |
| `gsd-debugger.md` | Systematic debugging agent |
| `gsd-executor.md` | Executes planned tasks |
| `gsd-integration-checker.md` | Checks integration points and compatibility |
| `gsd-phase-researcher.md` | Research for specific project phases |
| `gsd-plan-checker.md` | Validates plans before execution |
| `gsd-planner.md` | Creates structured execution plans |
| `gsd-project-researcher.md` | Full project research and context gathering |
| `gsd-research-synthesizer.md` | Synthesizes research from multiple sources |
| `gsd-roadmapper.md` | Creates project roadmaps |
| `gsd-verifier.md` | Verifies completed work against requirements |

### Tandem Team Agents (6)
| Agent | Purpose |
|-------|---------|
| `tandem-deployer.md` | Deployment automation agent |
| `tandem-doc-builder.md` | Document generation agent (.docx/.xlsx) |
| `tandem-qa.md` | QA and testing agent |
| `tandem-researcher.md` | Deep research agent |
| `tandem-strategist.md` | Strategic analysis and planning agent |
| `precedent-hunter.md` | Finds precedents and prior art in codebase |

---

## MCP Servers (external dependencies)

These are referenced in `configs/claude-desktop-config.json.template` and require separate installation:

| Server | Install method | Default state |
|--------|---------------|---------------|
| `MCP_DOCKER` | Docker Desktop with MCP gateway support — `docker mcp gateway run` | Always enabled |
| `browser-use` | `uvx --from browser-use[cli] browser-use --mcp` (requires Python/uv) | Enabled |
| `Windows-MCP` | `uvx --from windows-mcp windows-mcp` (Windows only, requires Python/uv) | **Proctor only (Claude Desktop) — NOT needed for Brother (Claude Code terminal)** |
| `discord-mcp` | Download JAR from discord-mcp repo, requires Java 17+ (e.g. Amazon Corretto) | Always enabled |
| `google-drive-mcp` | OAuth-based Google Drive/Docs/Sheets MCP server | **Disabled by default — enable on-demand for Docs/Sheets/Slides editing (~16K tokens/turn)** |
| `firecrawl` | `npx -y firecrawl-mcp` (requires Firecrawl API key) | **Disabled by default — enable on-demand for web scraping (context overhead)** |
| `context7` | HTTP MCP server at `https://mcp.context7.com/mcp` (no auth) | Always enabled |
| `n8n-mcp` | `npx -y n8n-mcp` (stdio) | Always enabled |
| `voice@cctools-plugins` | Installed via plugin system (see Plugins section above) | **Disabled — high context overhead, enable only if needed** |
