# last-roman-canon - canon-mirror tooling (Brother, S#327-S#328)

Tools that keep a Google-Docs story corpus consistent after every author ruling. Paths and Doc ids inside are
Silas's live corpus; adapt them.

- `lint.py` - canon lint, run after every mirror pull. Harvests every quoted phrase in the corpus's DEAD lists plus a
  hand-kept REGISTRY of retired wordings and searches every live doc; skips record lines (DEAD / SUPERSEDED / [Was: /
  changelog / a bracket citing the superseding ruling). Since S#328 a LONG line (>500 chars - a per-episode dossier, a
  character-file paragraph) is judged per hit in a window around it instead of being skipped whole: that is how
  "the son watching the father" hid for three weeks behind a DEAD word 1,500 characters away on the same line.
  Also flags duplicate / out-of-order version lines, a footer that disagrees with its header, unclosed "[Was:".
- `pull.py` - the one-way Drive -> mirror -> git pull; since S#328 it runs `lint.py` itself after every real pull, so the
  MCP's canon_pull / canon_fold (which call this script, not the batch file) print the same straggler count.
- `push_doc_text.py` - replace a Google Doc's whole body from a marked-up text file (delete range -> ~6K UTF-16
  insertText chunks in reverse -> reset styles -> headings/bold -> re-fetch and diff; exit 1 on mismatch).
- `cascade_helper_00W2.py` - the shared exact-string cascade helper: replace_all (dry count against the mirror first,
  then ONE batchUpdate per Doc with occurrencesChanged verification), find-by-name, changelog bump.
- `cascade_00W16_R177_sweep.py` - the exemplar wave: 45 exact-string edits across 9 Docs plus two whole-paragraph
  replacements by index range (get -> find the paragraph by prefix -> deleteContentRange + insertText).

Rules the tools encode: dry = live; a grep cascade is not a verification (full-read every touched doc); strip Docs list
numbers/bullets from anchors; straight vs curly quotes are literal; re-pull if "0 updated" within 30 s of an edit.
