---
name: pg-query
description: "Query the Amerix PostgreSQL database (read-only). Usage: /pg-query <sql or action>"
---

# PostgreSQL Read-Only Query Tool

Execute safe, read-only queries against the Amerix development database using the postgres skill at `~/amerix-saas/tools/ai-skills/skills/postgres/`.

## Available Commands

```bash
# List configured databases
python3 ~/amerix-saas/tools/ai-skills/skills/postgres/scripts/query.py --list

# List all tables
python3 ~/amerix-saas/tools/ai-skills/skills/postgres/scripts/query.py --db amerix_dev --tables

# Show full schema
python3 ~/amerix-saas/tools/ai-skills/skills/postgres/scripts/query.py --db amerix_dev --schema

# Run a SELECT query
python3 ~/amerix-saas/tools/ai-skills/skills/postgres/scripts/query.py --db amerix_dev --query "YOUR SQL HERE" --limit 100
```

## Safety
- Read-only mode enforced at database level
- Only SELECT, SHOW, EXPLAIN, WITH queries allowed
- 30-second timeout, max 10,000 rows
- Credentials never shown in output

When the user asks to query the database, use the appropriate command above via Bash.
