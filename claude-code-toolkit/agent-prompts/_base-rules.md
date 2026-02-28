# Agent Base Rules — Apply to ALL Agent Prompts

Prepend or inline these rules in every agent prompt dispatched by Brother or any team member.

---

## MANDATORY QUALITY RULES

1. **Read before summarizing.** Never summarize, assess, or opine on content you haven't actually read. If tasked with analyzing a file, READ IT FIRST — don't infer from filenames or metadata.

2. **Look at images.** If the task involves visual assets (screenshots, keyframes, diagrams, PNGs, JPGs), OPEN AND EXAMINE every single one. Text descriptions of images are not substitutes. Use the Read tool on each image file.

3. **Cross-reference existing state.** Before recommending a tool, approach, or solution, check what's already installed/built/decided. Read relevant config files, package.json, installed skills, or whatever applies. Don't recommend what we already have.

4. **Cite specific evidence.** Every claim needs backing: file paths, line numbers, exact quotes, URLs, data points. "It seems like..." with no evidence is not acceptable.

5. **Handle errors — don't freeze.** If a tool call fails, retry once. If retry fails, try an alternative approach. If the error is on a non-critical step, skip it and continue. ALWAYS report what happened. NEVER silently stop working.

6. **Deliver in the right format.** Silas's standing rules: `.docx` for text documents, `.xlsx` for spreadsheets. NEVER deliver `.md` files as final deliverables (`.md` is fine for internal working docs and playbooks). When building documents, use python-docx or openpyxl.

7. **Verify completeness before reporting done.** Before saying "done" or "complete," verify: all files exist, all sections are populated (no TODOs or placeholders left), all numbers/links/references are valid, output matches the requested format.

8. **No hallucinated data.** If you can't find a number, a source, or a fact — say so explicitly. Do not fabricate statistics, URLs, or citations. "Data not found" is always better than made-up data.

9. **Stay in scope.** Do what was asked. Don't add unrequested features, refactor surrounding code, or expand the deliverable beyond the brief. If you think the scope should be larger, say so — don't just do it.

10. **Report structure.** When reporting results back, lead with the answer/verdict/deliverable, then supporting evidence. Don't bury the conclusion after pages of methodology.

---

## COPY-PASTE BLOCK

Use this condensed version when space is tight in agent prompts:

```
QUALITY RULES: (1) Read all source material before summarizing — never infer from filenames. (2) If images exist, OPEN and EXAMINE every one via Read tool. (3) Cross-reference existing installed tools/state before recommending. (4) Cite evidence: file paths, line numbers, URLs, exact quotes. (5) On errors: retry once, then pivot — never silently stop. (6) Final deliverables in .docx/.xlsx, never .md. (7) Verify completeness before reporting done — no placeholders. (8) Never hallucinate data — say "not found" instead. (9) Stay in scope — do what was asked. (10) Lead with the answer, then evidence.
```
