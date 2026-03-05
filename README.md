# Silas AI Toolkit

**Agent prompts, video pipelines, playbooks, and Claude Code configurations powering the Tandem Team.**

A battle-tested collection of AI tools built across 67+ Claude Code sessions. Each tool is self-contained with its own README, requirements, and usage examples -- from agent prompt templates that guarantee consistent output quality, to video analysis pipelines that turn raw TikTok and YouTube content into structured intelligence.

---

## What's Inside

| Tool | Description |
|------|-------------|
| [**claude-code-toolkit/**](./claude-code-toolkit/) | Complete power-user blueprint for Claude Code -- agent prompt templates, custom slash commands, hooks, playbooks, protocols, MCP configs, and session management |
| [**tiktok-pipeline/**](./tiktok-pipeline/) | End-to-end TikTok video analysis: download, keyframe extraction, Whisper transcription, synced digest. Full CLI with configurable model, interval, and output directory |
| [**youtube-pipeline/**](./youtube-pipeline/) | End-to-end YouTube video analysis: download, keyframe extraction, Whisper transcription, synced digest. Full CLI with configurable model, interval, and output directory |
| [**rlm-query/**](./rlm-query/) | Query large documents with Recursive Language Models -- GPT-4o mini + RLM beat full GPT-4o by 34 points on long-document benchmarks |

---

## Claude Code Toolkit

The crown jewel of this repo. A complete blueprint for transforming Claude Code from a basic coding assistant into a full engineering command center.

### What's Different From Stock Claude Code?

| Capability | Stock Claude Code | With This Toolkit |
|-----------|------------------|-------------------|
| Session continuity | Every session starts from zero | Startup/shutdown protocols preserve state across sessions |
| Context management | Burns through context on raw file reads | Agent delegation protocol conserves context 2-3x |
| Multi-agent coordination | Single instance | Multiple Claude instances coordinate via Discord + file inboxes |
| Quality standards | Default behavior | Prime Directive enforces 100% completion, no lazy omissions |
| Agent prompts | Ad-hoc prompts, inconsistent quality | 10 battle-tested templates with built-in quality guardrails |

### Repository Structure

```
claude-code-toolkit/
  configs/           Config templates (CLAUDE.md, MCP servers, settings, hooks)
  agent-prompts/     10 reusable prompt templates + base quality rules
  agents/            6 custom agent definitions for Claude Code's /agents system
  commands/          9 custom slash commands
  playbooks/         Operational playbooks (context conservation, lessons learned, video analysis)
  protocols/         Coordination protocols (agent delegation, session management, notifications)
  scripts/           Infrastructure scripts (config guard, briefing compiler, webhook setup)
  memory/            Memory system templates
  examples/          Real-world usage patterns (agent delegation, research sprints, document processing)
```

See the full [Claude Code Toolkit README](./claude-code-toolkit/README.md) for setup instructions, key concepts, and detailed documentation.

---

## Agent Prompt Library

10 reusable prompt templates that solve the inconsistent-agent-output problem permanently. Every template includes role definition, step-by-step process, output format, and 10 mandatory quality rules inherited from `_base-rules.md`.

### Core Templates

| # | Template | When to Use |
|---|----------|-------------|
| 1 | **Video Analyzer** | Analyzing processed TikTok/YouTube videos -- keyframes + transcript + visual correlation |
| 2 | **Stack Evaluator** | Evaluating a tool/repo/skill against your installed stack -- verdict: install, skip, replace, or revisit |
| 3 | **Deep Comparison** | Merging multiple source analyses of the same topic into one non-redundant brief |
| 4 | **Research Synthesizer** | Consolidating parallel research agent outputs into a single decision-ready document |
| 5 | **Code Builder** | Building code deliverables that must be verified working before reporting complete |
| 6 | **Document Builder** | Creating professional .docx/.xlsx deliverables with formatting standards |
| 7 | **Codebase Explorer** | Mapping unfamiliar codebase architecture, patterns, and structure before taking action |
| 8 | **Web Researcher** | Multi-source web research with cross-validation, source tiering, and gap identification |
| 9 | **Audit / Reviewer** | Thorough code, security, PR, or architecture review -- severity-rated findings |
| 10 | **Deliverable QA** | Final quality gate before presenting any deliverable |

### Template Chaining Patterns

Templates are designed to be chained for complex workflows:

- **Research pipeline:** Web Researcher (x3-5 parallel) --> Research Synthesizer --> Document Builder --> Deliverable QA
- **Video analysis:** Video Analyzer (per video) --> Deep Comparison (if overlap) --> Stack Evaluator (per tool found)
- **Code project:** Codebase Explorer --> Code Builder --> Audit/Reviewer --> Deliverable QA

### Specialized Agents

6 custom agent definitions that plug directly into Claude Code's `/agents` system (YAML frontmatter, tool access, behavioral specs):

| Agent | Purpose |
|-------|---------|
| **Tandem Researcher** | Multi-source web research with cross-validation and source tiering |
| **Tandem Doc Builder** | Professional .docx/.xlsx deliverables with full build-verify cycle |
| **Tandem Deployer** | Vercel deploy-verify cycle -- deploys, confirms live, reports results |
| **Tandem QA** | Final quality gate -- catches issues before delivery |
| **Tandem Strategist** | 30,000-foot strategic integrity -- flags drift, applies Eisenhower Matrix |
| **Precedent Hunter** | Searches team history and memory for prior solutions before brute-force investigation |

---

## Custom Slash Commands

9 commands that extend Claude Code with specialized capabilities. Copy from `claude-code-toolkit/commands/` to `~/.claude/commands/`.

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

---

## Video Pipelines

Both pipelines follow the same architecture: **download --> extract audio --> extract keyframes --> transcribe --> generate synced digest**. They differ in keyframe interval to match typical content length.

### TikTok Pipeline

Optimized for short-form content (15-60 seconds). Extracts keyframes every **3 seconds** by default -- a 30-second TikTok produces ~10 keyframes for thorough analysis. Full CLI with configurable Whisper model, keyframe interval, and output directory.

```bash
cd tiktok-pipeline
pip install -r requirements.txt
python process-video.py "https://www.tiktok.com/@user/video/1234567890"
python process-video.py "https://www.tiktok.com/@user/video/1234567890" --model medium -i 5 -o ./my-output
python process-video.py --test   # verify tools
python process-video.py --help   # full CLI reference
```

### YouTube Pipeline

Optimized for long-form content (5-60+ minutes). Extracts keyframes every **15 seconds** by default -- a 10-minute video produces ~40 keyframes, capturing major scene transitions without generating hundreds of frames. Full CLI with configurable Whisper model, keyframe interval, and output directory.

```bash
cd youtube-pipeline
pip install -r requirements.txt
python process-video.py "https://www.youtube.com/watch?v=VIDEO_ID"
python process-video.py "https://www.youtube.com/watch?v=VIDEO_ID" --model medium -i 30 -o ./my-output
python process-video.py --test   # verify tools
python process-video.py --help   # full CLI reference
```

### Output

Both pipelines produce the same structured output per video:

```
output/{video_id}/
  video.mp4          # Downloaded video
  audio.wav          # Extracted audio (16kHz mono)
  transcript.txt     # Timestamped Whisper transcription
  digest.txt         # Keyframe-synced visual-to-speech digest
  metadata.json      # Video stats, creator info, processing details
  keyframes/         # PNG keyframes at configured intervals
```

---

## RLM Query

Query large documents using **Recursive Language Models** with Anthropic Claude. RLM solves the "context rot" problem where LLMs degrade as important details get buried in massive context windows.

- Handles 100+ page PDFs without losing details in the middle
- Cheaper models (Haiku, Sonnet) outperform expensive models on raw context
- Supports `.txt`, `.md`, `.json`, `.csv`, `.pdf`, `.xml`, `.html`, `.yaml`

```bash
cd rlm-query
pip install -r requirements.txt
python rlm-query.py document.pdf "What are the key findings?" --verbose
```

---

## Powers the Tandem Team

This toolkit is the engineering backbone of the **Tandem Team** -- a multi-agent Claude architecture where specialized AI agents coordinate across sessions, share context, and hand off work to each other.

| Agent | Interface | Role |
|-------|-----------|------|
| **Brother** | Claude Code (terminal) | Chief Engineer -- code, infrastructure, builds |
| **Proctor** | Claude Desktop (chat) | Strategic Coordinator -- planning, research, decisions |
| **Sister 2.0** | Claude Code RC Window | Real-time Qualification Layer |
| **Council** | n8n Automation Engine | Automated workflows -- briefs, notifications, archival |

The agent prompts, protocols, and playbooks in this toolkit are what make multi-agent coordination possible -- consistent output quality, structured handoffs, and shared operational knowledge.

See the [tandem-team](https://github.com/Silas7458/tandem-team) repo for the full architecture.

---

## Getting Started

### Prerequisites

- **Python 3.10+** (all tools)
- **[FFmpeg](https://ffmpeg.org/)** in PATH (video pipelines)
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** in PATH (video pipelines)
- **Anthropic API key** (RLM query)
- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** (claude-code-toolkit)

### Quick Start

**For video analysis:**
```bash
# TikTok
cd tiktok-pipeline && pip install -r requirements.txt
python process-video.py "https://www.tiktok.com/@user/video/ID" --alias "my-analysis"
python process-video.py --help   # see all options

# YouTube
cd youtube-pipeline && pip install -r requirements.txt
python process-video.py "https://www.youtube.com/watch?v=ID" --alias "my-analysis"
python process-video.py --help   # see all options
```

**For document querying:**
```bash
cd rlm-query && pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
python rlm-query.py my-document.pdf "Summarize the key findings"
```

**For Claude Code power-user setup:**
1. Read the [Setup Guide](./claude-code-toolkit/SETUP-GUIDE.md)
2. Copy and customize the [config templates](./claude-code-toolkit/configs/)
3. Install [agent prompts](./claude-code-toolkit/agent-prompts/) and [slash commands](./claude-code-toolkit/commands/)
4. Read the [Context Conservation playbook](./claude-code-toolkit/playbooks/context-conservation.md) -- this alone will double your productive session length

---

## Related Projects

| Repo | Description |
|------|-------------|
| [**tandem-team**](https://github.com/Silas7458/tandem-team) | Multi-agent Claude family architecture -- roles, protocols, coordination |
| [**tandem-blueprint**](https://github.com/Silas7458/tandem-blueprint) | Replication blueprint for building your own multi-agent Claude team |
| [**hospice-valuation-tool**](https://github.com/Silas7458/hospice-valuation-tool) | Full-stack hospice business valuation platform (React/Vite/Vercel) |

---

## Built With Claude Code

This entire toolkit was built, tested, and maintained using Claude Code. It is Claude Code building tools for Claude Code -- 67+ sessions of real-world usage distilled into reusable configurations, prompts, and pipelines.

---

## License

MIT
