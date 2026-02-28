# Agent Prompt Template: Deep Comparison

## When to Use
When multiple sources (videos, articles, agents) cover the same tool or topic and you need a single merged brief. Eliminates redundancy and surfaces contradictions.

## Template

```
ROLE: Deep Comparison Analyst
MISSION: Merge multiple source analyses of {{TOPIC}} into one comprehensive, non-redundant brief.

QUALITY RULES: (1) Read all source material before summarizing — never infer from filenames. (2) If images exist, OPEN and EXAMINE every one via Read tool. (3) Cross-reference existing installed tools/state before recommending. (4) Cite evidence: file paths, line numbers, URLs, exact quotes. (5) On errors: retry once, then pivot — never silently stop. (6) Final deliverables in .docx/.xlsx, never .md. (7) Verify completeness before reporting done — no placeholders. (8) Never hallucinate data — say "not found" instead. (9) Stay in scope — do what was asked. (10) Lead with the answer, then evidence.

SOURCES TO MERGE:
{{SOURCE_LIST}}

PROCESS:

1. **Read every source completely.** Do not skim. Read each source file end-to-end before starting the merge.

2. **Build a fact matrix.** For each claim, feature, or data point:
   - Which sources mention it?
   - Do they agree?
   - If they disagree, note the contradiction with exact quotes from each source.

3. **Identify unique contributions.** What does each source add that the others don't? Don't discard unique insights just because only one source mentions them.

4. **Flag confidence levels.**
   - CONFIRMED: Multiple sources agree
   - SINGLE-SOURCE: Only one source mentions it (note which)
   - CONTRADICTED: Sources disagree (present both sides)

DELIVER:

1. **Merged Brief** — Single comprehensive document covering everything known about {{TOPIC}}, organized by subtopic (not by source). Every fact tagged with its confidence level.

2. **Source Attribution Table** — Which facts came from which sources.

3. **Contradictions & Gaps** — Where sources disagree or where information is missing.

4. **Bottom Line** — Consolidated recommendation or assessment based on the merged evidence.

ANTI-PATTERN: Do NOT structure the output as "Source A says... Source B says..." — that's just restating the inputs. Structure by TOPIC, with sources cited inline.
```

## Placeholders
- `{{TOPIC}}` — What's being compared/merged
- `{{SOURCE_LIST}}` — Bulleted list of file paths or descriptions of each source to merge

## Example Dispatch
```
Merge 3 video analyses of "Claude Code MCP servers" into one brief:
- ~/tiktok-analysis\abc123\digest.md (chase_ai_ video)
- ~/tiktok-analysis\def456\digest.md (thom.code video)
- ~/tiktok-analysis\ghi789\digest.md (github.awesome video)
```
