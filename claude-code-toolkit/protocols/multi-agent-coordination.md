# Protocol: Multi-Agent Coordination

## Purpose

Multiple Claude Code instances can run simultaneously, each with a distinct role. This protocol defines how they communicate, coordinate, and avoid stepping on each other. It is the result of hundreds of sessions of real multi-agent operation, including many failures that taught us what does and does not work.

---

## When to Use Multi-Agent

Multi-agent is valuable when:
- **Different interfaces serve different purposes** -- e.g., one instance in a terminal (engineering), another in a GUI (coordination/research)
- **Parallel workstreams** that benefit from separate context windows
- **Specialized roles** that need different MCP server configurations
- **Monitoring/oversight** where one instance watches another's progress

Multi-agent is NOT needed when:
- A single Claude Code instance with agent delegation covers your needs
- The overhead of coordination exceeds the benefit of parallelism
- You are working on a single focused task

---

## Role Definition

Each Claude Code instance gets a clear, non-overlapping role:

| Role | Interface | Responsibilities | Does NOT Do |
|------|-----------|-----------------|-------------|
| **Engineer** | Claude Code CLI (terminal) | Code, builds, infrastructure, git, technical problem-solving | Strategy, business documents, monitoring others unprompted |
| **Coordinator** | Claude Desktop Chat | Strategic decisions, research, task assignment, oversight | Direct code edits, terminal commands |
| **Reviewer** | Claude Desktop Code tab | Code review, visual diffs, parallel branches | Primary development, strategic decisions |

**Key principle:** Roles do not overlap. If two instances can both do a task, assign it to exactly one. Ambiguity causes duplicate work or dropped tasks.

---

## Communication Channels

### Primary: Discord (or equivalent chat platform)
Set up a Discord server with purpose-specific channels:

| Channel | Purpose |
|---------|---------|
| **#handoffs** | Cross-agent task handoffs and status updates (DEFAULT inbox) |
| **#engineer-log** | Engineer session logs, build output, completions |
| **#coordinator-log** | Coordinator session logs, decisions |
| **#alerts** | Infrastructure alerts, failures, urgent notices |
| **#session-archive** | End-of-session summaries |

**Rules:**
- Prefix every message with `**[Role]**` -- e.g., `**[Engineer]**`, `**[Coordinator]**`
- Handoffs go to #handoffs, not direct messages
- Session start/end announcements go to the role's log channel
- Read #handoffs on startup to catch messages from teammates

### Fallback: File-Based Inboxes
When the chat platform is unavailable:
```
[YOUR_TEAM_DIR]/inbox-engineer.md
[YOUR_TEAM_DIR]/inbox-coordinator.md
[YOUR_TEAM_DIR]/inbox-reviewer.md
```

**Message format:**
```markdown
## [YYYY-MM-DD HH:MM] | [Sender] --> [Recipient] | [Subject]

[Message content. Keep concise but complete.]

**Files created/modified:** [list]
**Status:** [Complete / In Progress / Blocked]
**Next steps:** [what happens next]
```

---

## Handoff Protocol

When one agent completes work that another agent needs:

1. **Write the output** to the shared deliverables directory
2. **Post to #handoffs** with: what was done, file locations, what the next agent needs to do
3. **Append a notification** to the receiving agent's queue file (if using the notification system)

**Example handoff:**
```
**[Engineer]** Completed API endpoint refactoring.
- Modified: src/api/users.ts, src/api/auth.ts
- Added: src/api/middleware/rateLimit.ts
- Tests passing: 47/47
- **For Reviewer:** Please review the rate limiting middleware approach.
  I chose token bucket over sliding window -- see comments in rateLimit.ts.
```

---

## Conflict Prevention

### File Ownership
- Each agent tracks which files they modify
- Before editing a file, check if another agent recently modified it
- If conflict detected, coordinate via #handoffs before proceeding

### Session State
- Each agent maintains awareness of shared session-state.md
- Before writing to shared state files, read the current content first
- Use role-prefixed entries to avoid overwriting each other

### Task Assignment
- Tasks are assigned to ONE agent, never shared
- If a task spans roles (e.g., "build and review"), split it into explicit subtasks
- The Coordinator (or user) is the authority on task assignment disputes

---

## Monitoring Protocol

When one agent needs to check on another's status:

### Method 1: Check Output (Preferred)
Read the files, logs, and deliverables the other agent produced:
```
Check their deliverables directory
Read their log channel messages
Read session-state.md for their latest entry
```

### Method 2: Desktop Automation (Windows MCP)
If you need to see another agent's screen:
1. Get the target window's real coordinates (DPI-aware, not estimated)
2. Switch focus to the target window
3. Read the screen content
4. Switch back to your own window

**Critical lessons from real usage:**
- `App(mode="switch")` reports success but may not actually transfer focus -- always verify
- Never click taskbar buttons (causes unpredictable window state changes)
- Screenshot coordinates are scaled and wrong -- always use system APIs for real pixel positions
- Your terminal reclaims focus after every tool call -- verify focus before every interaction

### Method 3: Chat/Inbox
Simply ask via #handoffs: `**[Coordinator]** @Engineer status update on the API refactoring?`

---

## Standing Rules

1. **Do not monitor teammates unprompted.** Only check on other agents when asked by the user.
2. **Do not make decisions outside your role.** If uncertain, ask via #handoffs or escalate to the user.
3. **Announce session starts and ends.** Post to your log channel so teammates know when you are active.
4. **Archive every session.** The agent active when a session ends is responsible for archiving, regardless of role.
5. **Never alter another agent's window.** Do not minimize, resize, or close windows belonging to other agents.

---

*Multi-agent coordination adds complexity. Only adopt it when the benefits of parallelism and specialization clearly outweigh the coordination overhead. For most users, a single Claude Code instance with agent delegation is sufficient.*
