# Protocol: Agent Delegation

## Purpose

Claude Code can spin up sub-agents that execute tasks in their own context windows. This protocol defines when to delegate to agents vs do the work yourself, and how to choose the right agent type.

The core insight: **every tool result is permanently written into your context**. An agent does the same work in its own disposable context and returns only the summary. This is the single biggest lever for longer, more productive sessions.

---

## Decision Flowchart

```
START: You have a task to complete.
  |
  v
Is the task a file EDIT or WRITE?
  |-- YES --> DO IT YOURSELF (you need to produce the output)
  |-- NO
  v
Will the raw output exceed ~500 tokens?
  |-- YES --> AGENT IT
  |-- NO
  v
Do you need the EXACT content to make an edit or decision?
  |-- YES --> DO IT YOURSELF
  |-- NO
  v
Does it require 3 or more tool calls?
  |-- YES --> AGENT IT
  |-- NO
  v
DO IT YOURSELF (not worth the 30-second agent startup)
```

**Default when uncertain: AGENT.** The 30-second startup cost is almost always worth the context savings.

---

## Thresholds

| Signal | Action |
|--------|--------|
| File read >80 lines and you only need a summary | Agent |
| File read <80 lines and you are about to edit it | Yourself |
| 2+ web searches needed | Agent |
| Single targeted grep with known target | Yourself |
| Document building (.docx, .xlsx) | Agent (handles the write-run-fix loop) |
| Git operations (commit, push, status) | Yourself |
| Code review of >100 lines changed | Agent |
| Session state updates, communication | Yourself |

---

## Agent Type Selection

| Agent Type | Best For | Capabilities |
|------------|----------|-------------|
| **general-purpose** | Research, file ops, multi-step tasks, document building | Full tool access (read, write, execute, web) |
| **Explore** | Codebase exploration, finding patterns | Read-only (Glob, Grep, Read) |
| **Plan** | Architecture design, implementation planning | Read-only |
| **code-architect** | Feature design with implementation blueprint | Read-only + web |
| **code-reviewer** | Code review with confidence-based filtering | Read-only |
| **code-simplifier** | Post-implementation cleanup and refactoring | Full tool access |

**Key rule:** Explore/Plan agents CANNOT edit files. Use `general-purpose` for anything requiring writes or execution.

---

## Parallel Agent Patterns

### Research Sprint
Fire 3-5 agents simultaneously for independent research tracks:
```
Agent 1: "Research competitor A -- pricing, features, market position"
Agent 2: "Research competitor B -- pricing, features, market position"
Agent 3: "Research market trends in sector X -- growth rates, forecasts"
```
Each returns a focused summary. You synthesize across all results.

### Document Build
Single agent handles the entire build loop:
```
Agent: "Create a Python script that generates an Excel file with columns [X, Y, Z],
        populate it with [data description], save to [path]. Execute the script
        and confirm the file exists."
```
You receive: "Done. File at [path], 47 rows, 3 columns."

### Codebase Understanding
Use read-only Explore agents for architecture questions:
```
Agent: "Map the authentication flow in this codebase. Which files handle login,
        session management, and token refresh? Trace the request path."
```
You receive a concise architectural summary without reading 20 files yourself.

---

## Anti-Patterns

| Bad Pattern | Why It Is Bad | Better Approach |
|-------------|--------------|-----------------|
| Reading a 300-line file to answer one question | 300 lines permanently in context | Agent reads and answers the question |
| Running 5 web searches in sequence | ~3000 tokens of search results in context | Agent per search domain, or one agent for all |
| Building a document inline (write script, run, fix errors, re-run) | Entire debugging loop in context | Single agent handles the full loop |
| Grepping across 50 files yourself | ~1000 tokens of matches in context | Explore agent does this at zero context cost |
| Re-reading files an agent already summarized | Duplicates context for no gain | Trust the agent's summary |

---

## Context Budget Awareness

- A typical session burns ~60% of context on tool results, ~20% on system prompts, ~20% on conversation.
- With aggressive agent delegation, this shifts to ~20% tool results, ~20% system, ~60% useful conversation.
- **Practical impact:** 2-3x more useful work per session before hitting context limits.
- Monitor your context usage. When it climbs past ~50%, shift to agent-heavy mode for remaining work.

---

*This protocol is the foundation of the context conservation strategy. Combine with the [context-conservation playbook](../playbooks/context-conservation.md) for the complete picture.*
