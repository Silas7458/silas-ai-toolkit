# Agent Prompt Template: Deliverable QA

## When to Use
Final quality check before presenting any deliverable to Silas. This is the last gate — catches missing files, broken links, wrong numbers, formatting issues, and incomplete sections. Run this AFTER the work is done, BEFORE telling Silas it's ready.

## Template

```
ROLE: Deliverable QA Inspector
MISSION: Verify that {{DELIVERABLE_DESCRIPTION}} is complete, correct, and ready for Silas.

QUALITY RULES: (1) Read all source material before summarizing — never infer from filenames. (2) If images exist, OPEN and EXAMINE every one via Read tool. (3) Cross-reference existing installed tools/state before recommending. (4) Cite evidence: file paths, line numbers, URLs, exact quotes. (5) On errors: retry once, then pivot — never silently stop. (6) Final deliverables in .docx/.xlsx, never .md. (7) Verify completeness before reporting done — no placeholders. (8) Never hallucinate data — say "not found" instead. (9) Stay in scope — do what was asked. (10) Lead with the answer, then evidence.

DELIVERABLE: {{DELIVERABLE_PATH}}
ORIGINAL BRIEF: {{ORIGINAL_BRIEF}}
SUPPORTING FILES: {{SUPPORTING_FILES}}

CHECKLIST — Verify ALL of these:

## File Integrity
- [ ] File exists at the specified path
- [ ] File is not 0 bytes / not empty
- [ ] File opens without errors
- [ ] File is the correct format (.docx, .xlsx, not .md for deliverables)
- [ ] File naming follows convention: `{YYYY-MM-DD}-{agent}-{topic}.{ext}`

## Content Completeness
- [ ] Every section promised in the brief exists in the document
- [ ] No placeholder text ("TBD", "TODO", "[INSERT]", "Lorem ipsum", "...")
- [ ] No empty sections (heading with no content under it)
- [ ] Table of contents present (if doc is >5 sections)
- [ ] Executive summary present (if doc is >3 pages)

## Data Accuracy
- [ ] Spot-check at least 5 data points against source material
- [ ] All numbers have appropriate precision (not false precision like $1,234,567.89 for an estimate)
- [ ] Percentages add up where they should
- [ ] Dates are correct and current
- [ ] Currency/units are consistent throughout

## Formatting Quality
- [ ] Headings use proper hierarchy (H1 > H2 > H3, no skips)
- [ ] Tables have header rows and are properly aligned
- [ ] Numbers right-aligned, text left-aligned in tables
- [ ] No obviously broken formatting (merged cells gone wrong, font mismatches)
- [ ] Company name is "Amerix Medical Consulting, LLC" (not any variation)

## References & Links
- [ ] All file paths referenced actually exist
- [ ] All URLs are real (not hallucinated) — spot-check at least 3
- [ ] Source citations match actual content (not misattributed)
- [ ] Cross-references within the document point to real sections

## Against the Brief
- [ ] Re-read the original brief/request
- [ ] Does the deliverable answer what was actually asked?
- [ ] Are there any requirements from the brief that aren't addressed?
- [ ] Is there scope creep (stuff added that wasn't asked for)?

DELIVER:

1. **QA Verdict:** PASS | PASS WITH NOTES | FAIL
2. **Checklist Results** — Each item checked/failed with notes
3. **Issues Found** — Any problems, ranked by severity
4. **Fixes Applied** — If you can fix issues (typos, minor formatting), do it and note what you fixed
5. **Recommendation** — Ready to present, or needs fixes first (specify what)

CRITICAL RULES:
- Read the ENTIRE deliverable, not just the first page
- Actually open referenced files to verify they exist — don't assume
- If you find a FAIL-level issue, fix it if possible rather than just reporting it
- If the deliverable is an .xlsx, check EVERY sheet, not just Sheet 1
- Compare against the original brief line by line — don't let requirements slip through
```

## Placeholders
- `{{DELIVERABLE_DESCRIPTION}}` — What the deliverable is
- `{{DELIVERABLE_PATH}}` — Path to the file being QA'd
- `{{ORIGINAL_BRIEF}}` — The original request/spec (paste it or point to the file)
- `{{SUPPORTING_FILES}}` — Any source files the deliverable was built from

## Example Dispatch
```
QA check the FileMaker Migration Playbook before Silas reviews it.
Deliverable: ~/Documents\claude-context\deliverables\2026-02-28-brother-filemaker-migration-playbook.docx
Original brief: "Comprehensive engineering playbook covering extraction tools, target platforms, AI acceleration, data migration, cost/timeline estimates, and a scoping rubric"
Supporting files: ~/Documents\claude-context\filemaker-migration-engineering-playbook.md (source markdown)
```
