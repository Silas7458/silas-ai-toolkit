# Playbooks

Playbooks are reference documents containing accumulated procedural knowledge. Claude Code reads them when it needs to execute a known procedure or recall a hard-won lesson. They are the team's institutional memory.

---

## How Playbooks Work

1. **Store them in a known directory** referenced in your CLAUDE.md
2. **Tell Claude Code they exist** via your startup instructions: "Check playbooks/ FIRST when asked about a known capability"
3. **Claude Code reads them on demand** when a task matches a playbook topic
4. **You update them** when you learn something new and durable

---

## Playbooks in This Toolkit

### context-conservation.md
**The single most valuable document in this toolkit.** The agent-first protocol that maximizes useful context lifespan by delegating heavy work to sub-agents. Includes the decision flowchart, agent type selection guide, parallel patterns, and anti-patterns.

If you read only one file from this toolkit, read this one.

### lessons-learned.md
Hard-won lessons organized by domain: workflow automation (n8n), Docker, Windows multi-agent operations, and architecture/process. Every lesson was learned through real failure, not theory. Includes specific problem descriptions, root causes, and proven fixes.

### video-analysis.md
Pipeline playbook for processing TikTok and YouTube videos: download, keyframe extraction, Whisper transcription, and digest generation. Includes command references, flags, output structures, and team workflow patterns.

---

## Writing Your Own Playbooks

Good playbook candidates:
- **Procedures you repeat** -- deployment, database migrations, environment setup
- **Lessons from failures** -- bugs that took hours to diagnose, approaches that do not work
- **Domain-specific knowledge** -- API quirks, framework gotchas, platform limitations
- **Decision frameworks** -- how to choose between approaches

A good playbook entry has:
- **Problem** -- what went wrong or what needs to happen
- **Context** -- why it is not obvious
- **Solution/Fix** -- the proven approach
- **What does NOT work** -- approaches that seem right but fail (saves future time)

---

## Playbook Maintenance

- Review playbooks periodically -- remove entries that are no longer relevant
- Add new entries immediately when you learn something durable
- Keep entries concise -- a playbook is a reference, not a tutorial
- Organize by domain for fast lookup
