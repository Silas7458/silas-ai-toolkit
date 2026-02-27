# Playbook: Context Conservation -- Agent-First Protocol

**Purpose:** Maximize useful context lifespan by delegating heavy work to agents. Every tool result dumps permanently into your main context. An agent does the same work in its own context and returns a compact summary. This is the single biggest lever for longer, more productive sessions.

---

## The Math

| Action | Context cost (main) | Context cost (agent) |
|--------|---------------------|----------------------|
| Read a 500-line file | ~500 lines in your window forever | ~100-word summary returned |
| 3 web searches | ~3000 tokens of search results | ~200-word synthesis returned |
| Build a .docx (script + run + fix) | ~2000 tokens of code + output + errors | Agent handles loop, returns "done, file at X" |
| Grep across 50 files | ~1000 tokens of matches | Agent returns "found in 3 files, here is what matters" |

**Rule of thumb:** If the raw output would be >500 tokens and you only need a summary/answer, agent it.

---

## When to AGENT

1. **File reads >80 lines** when you need answers, not exact content for editing
2. **Web research** -- any task requiring 2+ searches
3. **Multi-file exploration** -- "find how X works", "where is Y used across the codebase"
4. **Document building** (.docx, .xlsx) -- the entire write-script-execute-fix loop
5. **Code review** of large diffs or multi-file changes
6. **Any task requiring 3+ search/read cycles** to complete
7. **Parallel research tracks** -- fire 3-5 agents at once for independent domains
8. **File analysis** -- reading logs, configs, data files to extract specific info
9. **Codebase mapping** -- understanding architecture, dependencies, patterns

## When to DO IT YOURSELF

1. **File reads <80 lines** that you are about to edit (need exact content)
2. **Single targeted grep/glob** where you know the exact target
3. **File edits, writes, git operations** -- these are small and necessary
4. **Communication sends, session-state updates** -- lightweight coordination
5. **Conversations/decisions with the user** -- cannot delegate judgment
6. **Quick single-shot commands** -- git status, npm install, etc.
7. **Anything where 30s agent startup exceeds the work itself**

---

## Decision Flowchart

```
Is the task a file EDIT or WRITE? --> DO IT YOURSELF
                                      | no
Will raw output exceed ~500 tokens? --> AGENT IT
                                        | no
Do I need exact content for a decision? --> DO IT YOURSELF
                                            | no
Does it require 3+ tool calls? --> AGENT IT
                                    | no
--> DO IT YOURSELF (not worth agent overhead)
```

**When in doubt --> AGENT.** The 30-second startup cost is almost always worth the context savings.

---

## Agent Types -- When to Use Which

| Agent Type | Best For | Tools Available |
|------------|----------|-----------------|
| `general-purpose` | Research, file ops, multi-step tasks, document building | Everything |
| `Explore` | Codebase exploration, finding files/patterns | Read-only (Glob, Grep, Read) |
| `Plan` | Architecture design, implementation planning | Read-only |
| `feature-dev:code-architect` | Feature design with implementation blueprint | Read-only + web |
| `feature-dev:code-reviewer` | Code review with confidence-based filtering | Read-only |
| `code-simplifier:code-simplifier` | Post-implementation cleanup | Everything |

**Key distinction:** Explore/Plan agents CANNOT edit files. Use `general-purpose` for anything that requires writing, building, or executing.

---

## Parallel Agent Patterns

### Research Sprint (3-5 agents, different tracks)
Fire simultaneously when research spans multiple domains:
```
Agent 1: "Research X -- focus on pricing data"
Agent 2: "Research Y -- focus on market size"
Agent 3: "Research Z -- focus on competitive landscape"
```
Each returns a summary. You synthesize.

### Document Build (1 agent, full loop)
Single agent handles: write Python script --> execute --> check output --> fix errors --> confirm file exists.
You just get "done, deliverable at path."

### Codebase Understanding (1-2 Explore agents)
Use `Explore` type for "how does X work in this codebase" questions. They are read-only but fast and thorough.

---

## Anti-Patterns (What NOT to Do)

1. **Reading a 300-line file inline to answer one question** -- Agent should read and answer
2. **Running 5 web searches in sequence in your context** -- Fire an agent per search domain
3. **Building a .docx by writing Python, running it, reading errors, fixing, re-running** -- That entire loop is agent work
4. **Grepping across the entire codebase yourself** -- Explore agent does this without context cost
5. **Reading multiple files to "understand the current state"** -- Agent reads and summarizes
6. **Doing work yourself that you already delegated to an agent** -- Trust the agent's output

---

## Context Budget Awareness

- Your context window is finite. Every token consumed is permanent for the session.
- A typical session burns ~60% of context on tool results, ~20% on system prompts, ~20% on actual conversation.
- By agenting the tool-result-heavy work, you can shift that to ~20% tool results, ~20% system, ~60% useful conversation.
- **Goal:** Double the useful work per session by halving the context wasted on raw tool output.

---

*This playbook is universal. It applies to any Claude Code instance regardless of specific tools, projects, or domains.*
