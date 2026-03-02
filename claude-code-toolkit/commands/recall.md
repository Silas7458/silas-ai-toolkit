---
name: recall
description: "Recall learnings from the CC-v3 memory system. Usage: /recall <search query>"
---

# Recall Learnings from Continuous Claude v3 Memory

Search the persistent memory system for relevant learnings from past sessions.

## Usage

```bash
cd ~/amerix-saas/tools/continuous-claude-v3/opc && PYTHONPATH=. uv run python scripts/core/recall_learnings.py --query "$ARGUMENTS" --k 5 --text-only
```

## Options

```bash
# Default hybrid search (recommended)
cd ~/amerix-saas/tools/continuous-claude-v3/opc && PYTHONPATH=. uv run python scripts/core/recall_learnings.py --query "$ARGUMENTS"

# More results
cd ~/amerix-saas/tools/continuous-claude-v3/opc && PYTHONPATH=. uv run python scripts/core/recall_learnings.py --query "$ARGUMENTS" --k 10

# Pure vector search
cd ~/amerix-saas/tools/continuous-claude-v3/opc && PYTHONPATH=. uv run python scripts/core/recall_learnings.py --query "$ARGUMENTS" --vector-only

# Text-only (fast, no embeddings)
cd ~/amerix-saas/tools/continuous-claude-v3/opc && PYTHONPATH=. uv run python scripts/core/recall_learnings.py --query "$ARGUMENTS" --text-only
```

When the user asks to recall or remember something, run the appropriate command via Bash.
