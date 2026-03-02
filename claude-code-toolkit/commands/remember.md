---
name: remember
description: "Store a learning in the CC-v3 memory system. Usage: /remember <what to remember>"
---

# Store Learning in Continuous Claude v3 Memory

Store a learning, pattern, or decision for future recall across sessions.

## Usage

```bash
cd ~/amerix-saas/tools/continuous-claude-v3/opc && PYTHONPATH=. uv run python scripts/core/store_learning.py \
  --session-id "<short-identifier>" \
  --type <TYPE> \
  --content "<what you learned>" \
  --context "<what it relates to>" \
  --tags "tag1,tag2,tag3" \
  --confidence high
```

## Learning Types

| Type | Use For |
|------|---------|
| `ARCHITECTURAL_DECISION` | Design choices, system structure |
| `WORKING_SOLUTION` | Fixes, solutions that worked |
| `CODEBASE_PATTERN` | Patterns discovered in code |
| `FAILED_APPROACH` | What didn't work |
| `ERROR_FIX` | How specific errors were resolved |
| `USER_PREFERENCE` | User's preferred approaches |
| `OPEN_THREAD` | Incomplete work to resume later |

When storing a learning, construct the appropriate command and run via Bash. Use the current session context to fill in session-id, type, and tags.
