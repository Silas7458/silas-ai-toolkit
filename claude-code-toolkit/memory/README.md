# Memory System

Claude Code has an auto-memory system that persists across sessions. It stores information in a `MEMORY.md` file that is automatically loaded into context at session start.

---

## How It Works

- **Location:** `~/.claude/projects/{project-path-hash}/memory/MEMORY.md`
- **Scope:** Per-project. Each project directory gets its own memory file.
- **Loaded automatically:** Claude Code reads this file at the start of every session in that project.
- **Written via `/remember`:** Use the `/remember` command during a session to add entries.
- **Persistent:** Survives session restarts, unlike conversation context.

---

## What to Store in Memory

### Permanent Rules
Behavioral corrections that should apply to every session:
```
## ALWAYS COMPLETE THE FULL LIST (PERMANENT)
When given a numbered list of tasks, do ALL of them in sequence.
Do not stop after item 1 and ask "what's next?"
```

### Error Recovery Patterns
Lessons learned from failures that should never be repeated:
```
## ERROR RECOVERY -- NEVER FREEZE (PERMANENT)
When a tool call returns an error, DO NOT STOP.
Retry once, then pivot to alternative approach, then skip and continue.
ALWAYS communicate what happened.
```

### Key References
Pointers to important files and resources (NOT the actual secrets):
```
## CENTRAL CONFIG (PERMANENT)
All credentials and API keys are in: [YOUR_CONTEXT_DIR]/config.json
Read this FIRST before searching elsewhere.
```

### Priority Rules
Standing instructions about how to handle specific situations:
```
## SESSION-STATE IS PRIMARY (PERMANENT)
session-state.md is the MOST CURRENT source of truth on restart.
Trust what it says. Do not re-research things it documents as complete.
```

---

## What NOT to Store in Memory

- **Actual secrets** (API keys, passwords, tokens) -- store pointers to where they live, not the values
- **Temporary task state** -- use session-state.md for this
- **Information that changes frequently** -- memory is for durable knowledge
- **Large blocks of content** -- memory is loaded every session, keep it concise
- **Duplicate information** -- if it is in CLAUDE.md, it does not need to be in memory too

---

## Memory vs CLAUDE.md vs Session State

| System | Scope | Persistence | Best For |
|--------|-------|------------|----------|
| **CLAUDE.md** | Project or global | Permanent (file on disk) | Instructions, protocols, identity, frameworks |
| **MEMORY.md** | Per-project | Permanent (auto-loaded) | Behavioral corrections, key references, permanent rules |
| **session-state.md** | Per-session | Overwritten each session | Current task state, next steps, blockers |
| **Session archive** | Historical | Append-only | What happened in past sessions |

**Rule of thumb:**
- If it defines HOW to behave --> CLAUDE.md
- If it corrects a mistake you keep making --> MEMORY.md
- If it describes WHERE YOU ARE right now --> session-state.md
- If it records WHAT HAPPENED --> archive

---

## Template

See `MEMORY.md.template` for a starter template with common patterns. Customize it with your own permanent rules and references.

---

## Maintenance

- Review memory periodically -- remove entries that are no longer relevant
- Keep entries tagged with dates so you know when they were added
- Mark entries as `(PERMANENT)` if they should never be removed
- Total memory should stay under ~200 lines -- it is loaded every session
