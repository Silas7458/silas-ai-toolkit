# Protocol: Session Management

## Purpose

Claude Code sessions are ephemeral -- when a session ends, everything in context is lost. This protocol creates continuity by writing state to disk at session end and reading it at session start. The result: every new session picks up exactly where the last one left off.

---

## Session Lifecycle

```
SESSION START
  |
  v
[Read session-state.md]          <-- Where did we leave off?
[Read briefing/priorities]        <-- What is the current context?
[Read inbox/notifications]        <-- Any messages from teammates?
[Acknowledge to user]             <-- "Resuming from: [last state]"
  |
  v
[... productive work ...]
  |
  v
SESSION END (triggered by any of: user request, ~80% context, natural ending)
  |
  v
[Update session-state.md]         <-- Where are we NOW?
[Append to session archive]       <-- What happened this session?
[Notify user]                     <-- "State saved. Ready for next session."
```

---

## Startup Checklist

Execute this BEFORE generating any response to the user:

### Priority 1 -- Session State (MOST CURRENT)
```
Read: [YOUR_CONTEXT_DIR]/session-state.md
```
This is the single most important file. It has exactly where the last session left off, what is done, what is next, and any blockers. **Trust what it says.** Do not re-research things it documents as complete.

### Priority 2 -- Briefing/Priorities
```
Read: [YOUR_CONTEXT_DIR]/briefing.md
```
Current priorities and broader context. May be less current than session-state.md -- if they conflict, session-state wins.

### Priority 3 -- Inbox and Notifications
```
Read: [YOUR_TEAM_DIR]/inbox.md
Read: [YOUR_CONTEXT_DIR]/notifications/queue.md
```
Messages from teammates or automated systems. Process any HIGH priority notifications before starting other work.

### Priority 4 -- Communication Channels (if multi-agent)
```
Read recent messages from team chat (e.g., Discord #handoffs)
```
Catch any messages from teammates since the last session.

**DO NOT read on startup:** Archives (historical reference only, too large for routine loading), activity logs (briefing covers the recent entries).

---

## Shutdown Checklist

Execute this when ANY of these conditions are met:
- User says "wrap up", "that is it", "end session", or similar
- Context usage hits ~80%
- You are about to suggest starting a new session
- The conversation is clearly ending (final deliverable presented, no more tasks)

### Step 1 -- Update Session State
Write to `[YOUR_CONTEXT_DIR]/session-state.md`:
```markdown
# Session State
**Updated:** [YYYY-MM-DD HH:MM]
**Last active agent:** [your role/name]

## Current Status
[What is the current state of work? What was just completed?]

## Immediate Next Tasks
1. [Next thing to do]
2. [After that]
3. [Then this]

## Blockers
- [Anything preventing progress, or "None"]

## Recent Decisions
- [Key decisions made this session that affect future work]

## Files Modified This Session
- [path/to/file1] -- [what changed]
- [path/to/file2] -- [what changed]
```

### Step 2 -- Append to Session Archive
Append to `[YOUR_CONTEXT_DIR]/claude-archive.md`:
```markdown
---
## [YYYY-MM-DD] Session [N] -- [Brief Title]

**Duration:** [approximate]
**Role:** [your role]

### What Happened
- [Bullet points of work completed]

### Key Decisions
- [Decisions that affect future sessions]

### Lessons Learned
- [Anything worth recording for future reference]

### Pending for Next Session
- [What needs to happen next]
```

### Step 3 -- Notify User
Tell the user: "Session state saved. Archive updated. Ready to resume in next session."

---

## Session State File -- Best Practices

- **Overwrite, do not append.** Session state is "current snapshot", not history. The archive handles history.
- **Be specific.** "Working on feature X" is useless. "Completed API endpoint for /users, need to add auth middleware and write tests" is actionable.
- **Include file paths.** The next session needs to know which files matter.
- **Record blockers explicitly.** A blocker undocumented is a blocker rediscovered.
- **Keep it under 50 lines.** Session state is read every startup -- brevity matters.

---

## Handling Interrupted Sessions

Sometimes sessions end unexpectedly (crash, timeout, user closes terminal). To minimize state loss:

1. **Write session state after every major milestone**, not just at shutdown. If you just finished a complex task, update session-state.md immediately.
2. **Use auto-memory for critical facts.** Claude Code's `/remember` command persists across sessions even without explicit state files.
3. **The archive is your safety net.** Even if session-state.md is stale, the archive has the full history.

---

## Multiple Concurrent Sessions

If running multiple Claude Code instances:

1. **Each instance writes its own state** to session-state.md (or separate state files per role)
2. **Last writer wins** -- coordinate to avoid overwrites
3. **Use role prefixes** in state entries: `[Brother] Completed X`, `[Proctor] Decided Y`
4. **Cross-reference archives** -- each role's archive is a separate section or file

---

*This protocol is the foundation for all other protocols. Without session state, every session starts from zero and accumulates no institutional knowledge.*
