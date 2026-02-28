# Agent Prompt Templates — Index

Reusable prompt templates for dispatching agents with consistent quality guardrails.
All agents inherit from `_base-rules.md` (10 mandatory quality rules).

## Templates

| # | Template | File | When to Use |
|---|----------|------|-------------|
| — | **Base Rules** | `_base-rules.md` | Shared quality rules applied to ALL agents. Contains copy-paste condensed block. |
| 1 | **Video Analyzer** | `01-video-analyzer.md` | Analyzing processed TikTok/YouTube videos (keyframes + transcript + visual correlation) |
| 2 | **Stack Evaluator** | `02-stack-evaluator.md` | Evaluating a tool/repo/skill against our installed stack — verdict: install/skip/replace/revisit |
| 3 | **Deep Comparison** | `03-deep-comparison.md` | Merging multiple source analyses of the same topic into one non-redundant brief |
| 4 | **Research Synthesizer** | `04-research-synthesizer.md` | Consolidating parallel research agent outputs into a single decision-ready document |
| 5 | **Code Builder** | `05-code-builder.md` | Building code deliverables that must be verified working before reporting complete |
| 6 | **Document Builder** | `06-document-builder.md` | Creating professional .docx/.xlsx deliverables with proper formatting standards |
| 7 | **Codebase Explorer** | `07-codebase-explorer.md` | Mapping unfamiliar codebase architecture, patterns, and structure before taking action |
| 8 | **Web Researcher** | `08-web-researcher.md` | Multi-source web research with cross-validation, source tiering, and gap identification |
| 9 | **Audit / Reviewer** | `09-audit-reviewer.md` | Thorough code/security/PR/architecture review — checks EVERYTHING, severity-rated findings |
| 10 | **Deliverable QA** | `10-deliverable-qa.md` | Final quality gate before presenting any deliverable to Silas |

## How to Use

1. Pick the template that matches your task
2. Open the template file and copy the prompt block (between the ``` markers)
3. Replace all `{{PLACEHOLDER}}` values with specifics
4. Dispatch via Agent tool with the filled prompt
5. For final deliverables, always run template #10 (Deliverable QA) before presenting to Silas

## Combining Templates

Templates can be chained:
- **Research pipeline:** #8 (Web Researcher) x3-5 agents in parallel → #4 (Research Synthesizer) → #6 (Document Builder) → #10 (Deliverable QA)
- **Video analysis pipeline:** #1 (Video Analyzer) per video → #3 (Deep Comparison) if overlap → #2 (Stack Evaluator) per tool found
- **Code project:** #7 (Codebase Explorer) → #5 (Code Builder) → #9 (Audit/Reviewer) → #10 (Deliverable QA)

## Folder
`~/Documents\claude-family\agent-prompts\`

*Created: 2026-02-28 | Brother Session 35*
