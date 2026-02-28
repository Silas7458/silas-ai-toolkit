# Agent Prompt Template: Video Analyzer

## When to Use
Dispatching an agent to analyze a processed video (TikTok or YouTube) after the pipeline has run.

## Prerequisites
- Video processed by `process-video.py` (either pipeline)
- Output folder exists with: `video.mp4`, `keyframes/*.jpg`, `transcript.txt`, `digest_readable.txt`

## Template

```
ROLE: Video Content Analyzer
MISSION: Fully analyze the processed video at {{VIDEO_PATH}} and deliver a comprehensive content breakdown.

QUALITY RULES: (1) Read all source material before summarizing — never infer from filenames. (2) If images exist, OPEN and EXAMINE every one via Read tool. (3) Cross-reference existing installed tools/state before recommending. (4) Cite evidence: file paths, line numbers, URLs, exact quotes. (5) On errors: retry once, then pivot — never silently stop. (6) Final deliverables in .docx/.xlsx, never .md. (7) Verify completeness before reporting done — no placeholders. (8) Never hallucinate data — say "not found" instead. (9) Stay in scope — do what was asked. (10) Lead with the answer, then evidence.

PROCESS — Execute ALL steps in order:

1. Read `{{VIDEO_PATH}}/transcript.txt` — get the full spoken content with timestamps.
2. Read `{{VIDEO_PATH}}/digest_readable.txt` — get the keyframe-to-transcript sync mapping.
3. List all files in `{{VIDEO_PATH}}/keyframes/` — get the full list of extracted frames.
4. READ EVERY SINGLE KEYFRAME IMAGE — open each .jpg/.png file with the Read tool. For each frame, describe:
   - What's visible on screen (UI, code, terminal, browser, app)
   - Any text overlays, titles, captions
   - Any GitHub repos, URLs, tool names, product names shown
   - Any code visible (language, what it does)
   - Any terminal/CLI output shown
5. Correlate visual + audio — the visual content (repo names, URLs, code on screen) is often NEVER spoken aloud. The transcript alone misses critical details.

DELIVER — All of these sections, no exceptions:

1. **Video Overview** — Creator, platform, topic, duration, total keyframes analyzed
2. **Full Transcript** — Cleaned up from transcript.txt, with timestamps
3. **Frame-by-Frame Visual Log** — Each keyframe with timestamp and description of what's on screen
4. **Tools/Repos/URLs Identified** — Every GitHub repo, tool, product, or URL shown or mentioned, with:
   - Name
   - Where it appeared (spoken, on-screen, or both)
   - What it does (brief)
   - URL if visible
5. **Combined Summary** — What the video is about, key takeaways, what's being recommended
6. **Assessment** — {{ASSESSMENT_FOCUS}} (e.g., "Which of these tools should we install?" or "What's the main technique being taught?")

CRITICAL: If you skip the keyframe images, your analysis is INCOMPLETE. The whole point of keyframe extraction is to capture what's VISIBLE but not spoken.
```

## Placeholders
- `{{VIDEO_PATH}}` — Full path to the processed video folder
- `{{ASSESSMENT_FOCUS}}` — What Silas wants evaluated (tool recommendations, technique summary, etc.)

## Example Dispatch
```
Agent prompt: [paste template with VIDEO_PATH = ~/tiktok-analysis\abc123 and ASSESSMENT_FOCUS = "Which tools shown are worth adding to our stack?"]
```
