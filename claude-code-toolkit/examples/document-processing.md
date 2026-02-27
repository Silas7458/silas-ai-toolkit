# Examples: Document Processing Patterns

Patterns for processing large documents, generating deliverables, and handling file-heavy workflows without burning your main context.

---

## Pattern 1: Large File Summary

**Situation:** You need to understand a 300+ line file but do not need to edit it.

**Wrong approach (context-heavy):**
```
Read the entire 300-line file --> 300 lines permanently in context
Answer the question --> maybe 50 words of actual value
Context cost: ~300 lines for ~50 words of useful output
```

**Right approach (agent-delegated):**
```
Agent reads the file --> agent's context (disposable)
Agent returns summary --> ~100 words in your context
Context cost: ~100 words for ~100 words of useful output
```

**Agent prompt:**
```
Read [path/to/file]. I need to understand:
1. What is the primary purpose of this file?
2. What are the key functions/classes and what do they do?
3. Are there any obvious issues or areas that need attention?
Return a concise summary (under 200 words).
```

---

## Pattern 2: Multi-File Analysis

**Situation:** You need to understand how a feature works across 5-10 files.

**Agent prompt (Explore type):**
```
Trace the data flow for [feature X] across this codebase. Starting from
[entry point], follow the imports and function calls through all related files.
For each file in the chain, note: file path, key function, what it does,
and what it passes to the next step. Return the complete flow as a numbered list.
```

**Result:** A compact architectural trace instead of 1000+ lines of raw file content.

---

## Pattern 3: Excel/Word Document Generation

**Situation:** User requests a formatted document (.xlsx, .docx).

**Why agent:** Document generation involves a write-run-debug loop:
1. Write a Python script using openpyxl/python-docx
2. Execute it
3. Read error output if it fails
4. Fix the script
5. Re-execute
6. Verify the output file

This loop typically takes 2-5 iterations and generates 1000-2000 tokens of code + output.

**Agent prompt:**
```
Create a Python script that generates an Excel file at [path] with the
following specifications:

Columns: [list columns]
Data: [describe data or provide it]
Formatting:
- Header row: bold, light blue background
- Currency columns: $#,##0.00 format
- Date columns: YYYY-MM-DD format
- Auto-fit column widths

Execute the script. If it fails, fix and retry. Confirm the file exists
and report: row count, column count, file size.
```

**What you receive:** "Done. File at [path], 47 rows, 8 columns, 12KB."

---

## Pattern 4: Log File Analysis

**Situation:** You need to analyze a large log file (1000+ lines) for patterns.

**Agent prompt:**
```
Read the log file at [path] (last [N] lines). Analyze for:
1. Top 5 most frequent error types with counts
2. Time distribution -- are errors clustered at specific hours?
3. Any correlation between error types (do they occur together?)
4. The single most actionable finding -- what should be fixed first?

Return a concise analysis (under 300 words) with specific line numbers
for the most critical entries.
```

---

## Pattern 5: Configuration Audit

**Situation:** You need to review multiple config files for consistency or issues.

**Agent prompt (Explore type):**
```
Read all configuration files in [directory]:
- [list known config files, or "all .json/.yaml/.toml files"]

Check for:
1. Inconsistencies between environments (dev vs prod vs staging)
2. Hardcoded values that should be environment variables
3. Missing required fields (compare against [reference config])
4. Security issues (exposed credentials, overly permissive settings)

Return a findings report grouped by severity (critical, warning, info).
```

---

## Pattern 6: Batch File Processing

**Situation:** You need to process many files (rename, convert, extract data from each).

**Agent prompt:**
```
Process all [file type] files in [directory]:

For each file:
1. Read the file
2. Extract [specific data]
3. [Transform/convert as needed]
4. Write result to [output location]

After processing all files, report:
- Total files processed
- Any files that failed (with reasons)
- Summary of extracted data
```

---

## Pattern 7: Eisenhower Matrix for Task Prioritization

**Situation:** You have a backlog of 15 tasks and need to decide what to work on.

This is not document processing per se, but it is a "large input processing" pattern that benefits from agent delegation.

**Agent prompt:**
```
Read the task list at [path/to/backlog.md]. For each task, evaluate:
- Is it URGENT? (blocking something, time-sensitive, user-requested)
- Is it IMPORTANT? (affects core functionality, infrastructure, revenue)

Categorize each task into the Eisenhower Matrix:
- DO FIRST (urgent + important): [list]
- SCHEDULE (important, not urgent): [list]
- DELEGATE/MINIMIZE (urgent, not important): [list]
- ELIMINATE (neither): [list]

For the DO FIRST category, recommend an execution order with brief rationale.
```

---

## General Tips

### Prompt Structure for Document Tasks
```
1. WHAT to create (file type, location)
2. CONTENT specification (columns, data, structure)
3. FORMATTING requirements (styles, number formats)
4. VERIFICATION step (confirm file exists, report stats)
```

### Error Handling in Agent Prompts
Always include: "If the script fails, fix and retry" -- this lets the agent handle the debug loop autonomously instead of reporting the error back to you.

### File Size Awareness
Before deciding whether to agent or self-read:
```bash
wc -l file.txt    # Check line count
```
- Under 80 lines and you need to edit --> read it yourself
- Over 80 lines and you only need info --> agent it

### Deliverable Naming Convention
Use a consistent naming pattern for generated files:
```
{YYYY-MM-DD}-{topic}.{ext}
```
Examples:
- `2026-02-26-market-analysis.xlsx`
- `2026-02-26-api-documentation.docx`
- `2026-02-26-competitor-matrix.xlsx`

---

*These patterns cover the most common document and file processing scenarios. The core principle is always the same: if the raw content exceeds ~500 tokens and you only need a summary or derived output, delegate to an agent.*
