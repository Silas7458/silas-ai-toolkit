# Playbook: Context Conservation — Agent-First Protocol

Established 2/27/2026. Refined same day after Silas requested formalization.

**Purpose:** Maximize useful context lifespan by delegating heavy work to agents. Every tool result dumps permanently into Brother's context. An agent does the same work in its own context and returns a compact summary. This is the single biggest lever for longer, more productive sessions.

---

## The Math

| Action | Context cost (Brother) | Context cost (Agent) |
|--------|----------------------|---------------------|
| Read a 500-line file | ~500 lines in your window forever | ~100-word summary returned |
| 3 web searches | ~3000 tokens of search results | ~200-word synthesis returned |
| Build a .docx (script + run + fix) | ~2000 tokens of code + output + errors | Agent handles loop, returns "done, file at X" |
| Grep across 50 files | ~1000 tokens of matches | Agent returns "found in 3 files, here's what matters" |

**Rule of thumb:** If the raw output would be >500 tokens and you only need a summary/answer, agent it.

---

## When to AGENT

1. **File reads >80 lines** when you need answers, not exact content for editing
2. **Web research** — any task requiring 2+ searches
3. **Multi-file exploration** — "find how X works", "where is Y used across the codebase"
4. **Document building** (.docx, .xlsx) — the entire write-script-execute-fix loop
5. **Code review** of large diffs or multi-file changes
6. **Any task requiring 3+ search/read cycles** to complete
7. **Parallel research tracks** — fire 3-5 agents at once for independent domains
8. **File analysis** — reading logs, configs, data files to extract specific info
9. **Codebase mapping** — understanding architecture, dependencies, patterns

## When to DO IT YOURSELF

1. **File reads <80 lines** that you're about to edit (need exact content)
2. **Single targeted grep/glob** where you know the exact target
3. **File edits, writes, git operations** — these are small and necessary
4. **Discord sends, session-state updates** — lightweight coordination
5. **Conversations/decisions with Silas** — can't delegate judgment
6. **Quick single-shot commands** — git status, npm install, etc.
7. **Anything where 30s agent startup exceeds the work itself**

---

## WRITE DELEGATION RULE (Added 2026-02-28)

The agent-first protocol originally focused on READS (file reads, research, exploration). But WRITES can burn just as much context when you're producing multiple similar files.

**The rule:** If you're about to write 3+ similar files (templates, configs, docs, test files, components), write ONE as the example/pattern, then delegate the rest to an agent.

**Why:** Writing 10 agent prompt templates directly consumed ~35% of context in a single session. Writing 1 template + agenting the other 9 would have saved ~30%.

**How to apply:**
1. Write the first file yourself — establish the format, voice, and quality bar
2. Spec the remaining files clearly: "Follow the exact format of template #1. Here are the specifics for each..."
3. Dispatch one agent with all remaining files, or parallel agents if they're independent
4. Review the agent's summary, spot-check 1-2 files

**Decision test:** "Am I about to write 3+ files that follow the same pattern?" → Write 1, agent the rest.

**Examples:**
- 10 agent prompt templates → write template #1, agent templates 2-10
- 5 standing order files → write the first role, agent the rest with role-specific specs
- 8 test files → write the pattern test, agent the rest with case-specific inputs
- 3 config templates → probably just do it yourself (only 3, and configs are tricky)

---

## BROWSER SCRAPING RULE (Added 2026-03-01)

**ALL multi-step browser interactions (Playwright) must be delegated to an agent.** Every page snapshot dumps 2-5KB of DOM tree YAML into your context — navigation bars, footers, dialogs, dropdowns — most of it irrelevant. A 6-step scrape can burn 30KB+ of context for data that compresses to 2KB of actual results.

**The incident:** Scraping Texas hospice rates from Palmetto GBA required: accept license dialog → select rate period → select quality data → select state → extract table. Six Playwright snapshots consumed ~30KB of context. An agent would have returned a clean JSON blob in ~3KB.

**How to apply:**
1. **Fire a `general-purpose` agent** with the full scraping instructions: URL, what to click, what to extract, what format to return
2. The agent handles all the DOM snapshots in its own context
3. You get back a compact result — just the data you need

**Decision test:** "Am I about to interact with a webpage that requires 2+ page loads/clicks?" → Agent it. One-shot `WebFetch` for a simple page is fine to do yourself.

**Examples:**
- Scraping a rate table through dropdown forms → AGENT (6+ snapshots)
- Fetching a single API docs page → DO IT YOURSELF (1 WebFetch)
- Filling out a multi-page form to get a result → AGENT
- Taking one screenshot to verify a deployment → DO IT YOURSELF

---

## Decision Flowchart

```
Is the task a file EDIT or WRITE? → DO IT YOURSELF
                                     ↓ no
Does it involve 2+ browser clicks/pages? → AGENT IT
                                            ↓ no
Will raw output exceed ~500 tokens? → AGENT IT
                                     ↓ no
Do I need exact content for a decision? → DO IT YOURSELF
                                          ↓ no
Does it require 3+ tool calls? → AGENT IT
                                  ↓ no
→ DO IT YOURSELF (not worth agent overhead)
```

**Decision rule:**
- "Will the raw output be >500 tokens and do I only need a summary?" → Agent
- "Do I need the exact content to make an edit or decision?" → Myself
- "Am I about to write 3+ similar files?" → Write 1, agent the rest

**When in doubt → AGENT.** The 30-second startup cost is almost always worth the context savings.

---

## Agent Types — When to Use Which

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
Fire simultaneously when Silas asks for research across multiple domains:
```
Agent 1: "Research X — focus on pricing data"
Agent 2: "Research Y — focus on market size"
Agent 3: "Research Z — focus on competitive landscape"
```
Each returns a summary. Brother synthesizes.

### Document Build (1 agent, full loop)
Single agent handles: write Python script → execute → check output → fix errors → confirm file exists.
Brother just gets "done, deliverable at path."

### Codebase Understanding (1-2 Explore agents)
Use `Explore` type for "how does X work in this codebase" questions. They're read-only but fast and thorough.

---

## Anti-Patterns (What NOT to Do)

1. **Reading a 300-line file inline to answer one question** — Agent should read and answer
2. **Running 5 web searches in sequence in your context** — Fire an agent per search domain
3. **Building a .docx by writing Python, running it, reading errors, fixing, re-running** — That entire loop is agent work
4. **Grepping across the entire codebase yourself** — Explore agent does this without context cost
5. **Reading multiple files to "understand the current state"** — Agent reads and summarizes
6. **Doing work yourself that you already delegated to an agent** — Trust the agent's output

---

## Context Budget Awareness

- Brother's context window is finite. Every token consumed is permanent for the session.
- A typical session burns ~60% of context on tool results, ~20% on system prompts, ~20% on actual conversation.
- By agenting the tool-result-heavy work, we can shift that to ~20% tool results, ~20% system, ~60% useful conversation.
- **Goal:** Double the useful work per session by halving the context wasted on raw tool output.

---

*Created: 2026-02-27 | Author: Brother + Silas | Status: ACTIVE*
