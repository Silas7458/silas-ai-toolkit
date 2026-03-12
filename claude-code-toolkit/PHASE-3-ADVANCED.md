# Phase 3 — Advanced: Multi-Agent Coordination, Automation & Protocols
# Tandem Team Bootstrap — After completing Phase 2 (Infrastructure & MCP Servers)
#
# PREREQUISITE: You completed Phase 2 and have all infrastructure working:
#   Brother identity, session state, MCP servers, Docker, n8n, Discord.
#   This guide adds the coordination layer that turns individual tools into a team.
#
# HOW TO USE: Work through each section IN ORDER. Each section has:
#   - What it is and why you need it
#   - Setup steps (copy-paste ready)
#   - Verification step (confirm it works before moving on)
#   - Troubleshooting if it fails
#
# ESTIMATED TIME: 2-3 hours for the full stack. You can stop after any section
# and pick up later — each section is independent once prerequisites are met.
# ===============================================================================

---

## Prerequisites Check

Before starting Phase 3, confirm these Phase 2 components are working:

```bash
# Discord MCP — can Brother read/write messages?
# Start Claude Code and ask: "Read the last 5 messages from #handoffs"

# n8n — is the API responding?
curl -s http://localhost:5678/api/v1/workflows -H "X-N8N-API-KEY: YOUR_KEY" | head -5

# Docker — is Postgres running?
docker exec postgres-dev psql -U dev -d main -c "SELECT 1;"

# Session state — does the file exist?
cat {YOUR_HOME}/Documents/claude-context/session-state.md
```

If any of these fail, go back to Phase 2 and fix them first. Phase 3 builds on all of them.

---

## Section 1: Proctor Setup — Strategic Coordinator (20 min)

### What Proctor IS

Proctor is your second Claude agent. While Brother (Claude Code CLI) handles engineering — code, builds, infrastructure — Proctor (Claude Desktop Chat tab) handles strategic coordination: research, planning, task assignment, and oversight.

**The key distinction:** Proctor coordinates. Brother builds. Their responsibilities do not overlap.

| | Brother (Engineer) | Proctor (Coordinator) |
|--|---|---|
| **Interface** | Claude Code CLI (terminal) | Claude Desktop Chat tab |
| **Does** | Code, git, Docker, builds, infrastructure | Research, planning, task assignment, monitoring |
| **Does NOT** | Strategic decisions, business documents | Direct code edits, terminal commands |
| **Tool budget** | Unlimited tool calls | 3 tool calls per response (stay lean) |
| **Personality** | Direct, technical, action-oriented | Measured, strategic, delegation-focused |

Proctor's 3-tool-call limit is deliberate. A coordinator who digs into implementation details stops coordinating. Proctor reads just enough to make decisions, then delegates the work to Brother.

### Step 1: Create Standing Orders

Standing orders are role-specific instruction files that each agent reads on startup. They define identity, capabilities, and protocols for each role.

```bash
mkdir -p {YOUR_HOME}/Documents/claude-family/standing-orders
```

Create Brother's standing orders:

```bash
cat > {YOUR_HOME}/Documents/claude-family/standing-orders/brother.md << 'ORDERS'
# Standing Orders — Brother (Chief Engineer)

## Identity
You are Brother — the Chief Engineer. You operate in Claude Code (CLI terminal).
You are the engineering powerhouse. If it needs a terminal, code, infrastructure,
or technical problem-solving — it is yours.

## Responsibilities
- Code: write, debug, refactor, review
- Infrastructure: Docker, databases, CI/CD, environment setup
- Terminal operations: git, npm, pip, system administration
- Build and deploy: deployments, container management
- Agent coordination: spawn sub-agents for parallel work

## Communication
- Post to Discord #brother-log on session start/end
- Post handoffs to #handoffs when completing work for Proctor
- Check #handoffs on startup for messages from Proctor
- Prefix all Discord messages with **[Brother]**

## What You Do NOT Do
- Make strategic business decisions unilaterally — ask {YOUR_NAME}
- Skip verification — always confirm code works before declaring done
- Generate documents without being asked
- Add features beyond what was requested
ORDERS
```

Create Proctor's standing orders:

```bash
cat > {YOUR_HOME}/Documents/claude-family/standing-orders/proctor.md << 'ORDERS'
# Standing Orders — Proctor (Strategic Coordinator)

## Identity
You are Proctor — the Strategic Coordinator. You operate in Claude Desktop Chat.
You are the planning brain. You research, decide priorities, assign tasks, and
monitor progress. You stay lean — 3 tool calls max per response.

## Responsibilities
- Strategic decisions: priorities, roadmap, task ordering
- Research: market analysis, competitive intelligence, compliance questions
- Task assignment: break work into pieces, assign to Brother
- Oversight: check Brother's progress, review deliverables
- Documentation: high-level docs, reports, summaries (delegate formatting to Brother)

## Communication
- Post to Discord #proctor-log on session start/end
- Post task assignments to #handoffs for Brother
- Check #handoffs on startup for messages from Brother
- Prefix all Discord messages with **[Proctor]**

## 3-Tool-Call Limit
You stay lean. Maximum 3 tool calls per response. If you need more:
- Delegate the deep work to Brother via #handoffs
- Ask {YOUR_NAME} to relay to Brother
- Focus on the decision, not the implementation

## What You Do NOT Do
- Write code or run terminal commands
- Dig into implementation details (delegate to Brother)
- Use more than 3 tool calls per response
- Make infrastructure changes directly
ORDERS
```

### Step 2: Create Proctor's Custom Instructions

Claude Desktop uses Project Custom Instructions to inject Proctor's identity. Create this file and paste its contents into Claude Desktop:

```bash
cat > {YOUR_HOME}/Documents/claude-family/proctor-custom-instructions.txt << 'PROCTOR'
# Identity
You are Proctor — the Strategic Coordinator of {YOUR_NAME}'s Tandem Team.
You operate in Claude Desktop Chat. You coordinate, research, and plan.
You do NOT write code or run terminal commands — that is Brother's job.

# Startup
On every new conversation, read these files:
1. {YOUR_HOME}/Documents/claude-context/session-state.md
2. {YOUR_HOME}/Documents/claude-context/next-session-prompt.md
3. {YOUR_HOME}/Documents/claude-family/inbox-proctor.md
4. {YOUR_HOME}/Documents/claude-context/notifications/proctor-queue.md

# Communication
- Post to Discord #handoffs for cross-agent messages (prefix: **[Proctor]**)
- Write to inbox-brother.md when Discord is unavailable
- Post to #proctor-log on session start/end

# Standing Orders
Read: {YOUR_HOME}/Documents/claude-family/standing-orders/proctor.md
PROCTOR
```

**To activate Proctor:**
1. Open Claude Desktop
2. Create a new Project (or open your existing one)
3. Go to Project Settings (gear icon)
4. Under "Custom Instructions", paste the contents of `proctor-custom-instructions.txt`
5. Start a new conversation in that project — Proctor is now active

### Step 3: Create File-Based Inboxes

These are the fallback communication channel when Discord MCP is unavailable:

```bash
cat > {YOUR_HOME}/Documents/claude-family/inbox-proctor.md << 'INBOX'
# Proctor Inbox
<!-- Messages from teammates when Discord is unavailable -->

No pending messages.
INBOX

cat > {YOUR_HOME}/Documents/claude-family/inbox-brother.md << 'INBOX'
# Brother Inbox
<!-- Messages from teammates when Discord is unavailable -->

No pending messages.
INBOX
```

**Message format for file inboxes:**
```markdown
## [YYYY-MM-DD HH:MM] | [Sender] --> [Recipient] | [Subject]

[Message content. Keep concise but complete.]

**Files created/modified:** [list]
**Status:** [Complete / In Progress / Blocked]
**Next steps:** [what happens next]
```

### Step 4: Update CLAUDE.md for Identity Detection

Add this block to your CLAUDE.md so each agent knows which role it is:

```markdown
## Identity Detection

Determine your role based on your environment:

| Signal | You Are | Standing Orders |
|--------|---------|-----------------|
| Claude Code CLI (terminal) | Brother (Engineer) | standing-orders/brother.md |
| Claude Desktop Chat tab | Proctor (Coordinator) | standing-orders/proctor.md |

Read your standing orders IMMEDIATELY on session start.
```

### Verify:
1. Start Claude Code — Brother should identify itself as Brother (Engineer)
2. Open Claude Desktop with the project — Proctor should identify itself as Proctor (Coordinator)
3. Have Proctor write a message to `inbox-brother.md`
4. Have Brother read `inbox-brother.md` and confirm the message is there

### Troubleshooting:
- Proctor acts like Brother: Custom Instructions were not pasted correctly. Re-paste into Project Settings.
- Brother does not read standing orders: Check that the file path in CLAUDE.md matches the actual file location.
- Inboxes not created: Run the `cat >` commands above from Git Bash.

---

## Section 2: Cross-Agent Communication (15 min)

### The Dual-Write Protocol

Every cross-agent handoff goes to BOTH Discord #handoffs AND the file inbox. This is non-negotiable.

**Why dual-write:**
- Discord MCP goes down for one agent -- the file inbox catches the message
- File inbox gets auto-cleaned -- Discord retains the full history
- At least one channel always has the message
- Zero dead zones in team communication

### Message Format

Every Discord message is prefixed with the sender's role:

```
**[Brother]** Completed API refactoring. Files modified: src/api/users.ts, src/api/auth.ts.
Tests passing: 47/47. Ready for Proctor review.

**[Proctor]** Market analysis complete. Deliverable at deliverables/2026-03-10-market-analysis.xlsx.
Brother: please incorporate findings into the dashboard data model.
```

### Channel Purpose Map

These channels were created in Phase 2. Here is how they are used in multi-agent operation:

| Channel | Purpose | Who Posts Here |
|---------|---------|---------------|
| **#handoffs** | Cross-agent task handoffs (DEFAULT inbox) | Both — this is the primary channel |
| **#brother-log** | Brother session logs, build completions | Brother only |
| **#proctor-log** | Proctor session logs, decisions | Proctor only |
| **#alerts** | Infrastructure alerts, failures | Both + automated (n8n) |
| **#session-archive** | End-of-session summaries | Both |

**"Check your messages"** = Read Discord #handoffs RIGHT NOW. Fresh read, not from memory. No clarification needed, no asking which channel. #handoffs is the default inbox.

### Notification Queue System

The notification queue adds a push layer on top of pull-based inboxes. Every agent checks their queue FIRST on every response.

```bash
mkdir -p {YOUR_HOME}/Documents/claude-context/notifications
```

Create queue files:

```bash
cat > {YOUR_HOME}/Documents/claude-context/notifications/brother-queue.md << 'QUEUE'
# Brother Notification Queue
<!-- Check this file FIRST before every response. Process and clear after reading. -->

No pending notifications.
QUEUE

cat > {YOUR_HOME}/Documents/claude-context/notifications/proctor-queue.md << 'QUEUE'
# Proctor Notification Queue
<!-- Check this file FIRST before every response. Process and clear after reading. -->

No pending notifications.
QUEUE
```

**Notification format (appended to queue files):**
```markdown
## [YYYY-MM-DD HH:MM] From: [SENDER] | Priority: [HIGH/NORMAL/LOW]
**Subject:** [brief subject line]
**Message:** [content or pointer to full message]
**Action Required:** [YES/NO] -- [what is needed, if YES]
---
```

**Priority levels:**

| Priority | Meaning | Response Expectation |
|----------|---------|---------------------|
| **HIGH** | Blocking or urgent | Address before any other work |
| **NORMAL** | Review when you can | Non-blocking but important |
| **LOW** | FYI only | No response expected |

Create the protocol reference file:

```bash
cat > {YOUR_HOME}/Documents/claude-context/notifications/PROTOCOL.md << 'PROTO'
# Notification Protocol

## Rules
1. SEND RULE: When sending a message to another agent, ALSO append a notification
   to their queue file. Every message gets a notification.
2. CHECK RULE: First action on every response — read your queue file. If notifications
   exist, acknowledge them before proceeding. Clear after processing.
3. CLEAR RULE: After processing, reset the queue to "No pending notifications."
4. RESPONSE RULE: If a notification requires a response, send the reply AND append
   a notification to the original sender's queue confirming the reply.
PROTO
```

### Sending a Handoff (Complete Flow)

When Brother finishes work that Proctor needs:

1. Write output to deliverables directory
2. Post to Discord #handoffs: `**[Brother]** Completed X. Files at [path]. For Proctor: [next step].`
3. Write same message to `inbox-proctor.md`
4. Append notification to `proctor-queue.md`

That is three writes for every handoff. It sounds like overhead, but it guarantees zero lost messages.

### Add to CLAUDE.md:

```markdown
## Cross-Agent Communication

### Dual-Write Rule
Every handoff goes to BOTH Discord #handoffs AND the recipient's file inbox.
If one fails, note the failure in the other.

### Notification Protocol
Check {YOUR_HOME}/Documents/claude-context/notifications/{your-role}-queue.md
FIRST ACTION every response. Process and clear.

### "Check your messages"
= Fresh Discord #handoffs read. Not memory. Not recall. Read it NOW.
```

### Verify:
1. In Claude Code (Brother), send a message to Discord #handoffs AND write to inbox-proctor.md
2. In Claude Desktop (Proctor), read both Discord #handoffs and inbox-proctor.md — both should have the message
3. Brother appends a notification to proctor-queue.md — Proctor should process it on next response

### Troubleshooting:
- Discord messages not appearing: Check bot permissions (Section 5 of Phase 2)
- File inbox empty after write: Check path — must be `{YOUR_HOME}/Documents/claude-family/`, not `{YOUR_HOME}/claude-family/`
- Notifications not processed: Confirm CLAUDE.md instructs checking the queue on every response

---

## Section 3: Automated Workflows — n8n Council Engine (30 min)

### What the Council IS

The Council is n8n acting as the fourth team member. While Brother builds and Proctor coordinates, the Council handles everything that should happen on a schedule or in response to events — no human or agent intervention required.

Think of it as the operations backbone: it cleans up old files, monitors system health, relays notifications, and runs scheduled tasks. Once configured, it runs 24/7 in Docker.

### n8n API Reminder

When calling the n8n API directly (not through MCP), always use:
```
Header: X-N8N-API-KEY: your-api-key
```
NOT `Authorization: Bearer` — that returns 401 on n8n.

### Workflow 1: Inbox Auto-Archive (Cron every 12h)

Clears processed inbox messages so file inboxes stay small.

**Create in n8n UI (http://localhost:5678):**

1. New Workflow -> Name: "Inbox Auto-Archive"
2. Add **Schedule Trigger** node:
   - Rule: Every 12 hours
3. Add **Execute Command** node:
   ```bash
   # Archive inbox contents if they have messages, then reset
   INBOX_DIR="{YOUR_HOME}/Documents/claude-family"
   ARCHIVE_DIR="{YOUR_HOME}/Documents/claude-family/inbox-archive"
   mkdir -p "$ARCHIVE_DIR"
   TIMESTAMP=$(date +%Y-%m-%dT%H-%M)

   for INBOX in "$INBOX_DIR"/inbox-*.md; do
     BASENAME=$(basename "$INBOX")
     # Only archive if there are actual messages (more than 3 lines)
     LINES=$(wc -l < "$INBOX")
     if [ "$LINES" -gt 4 ]; then
       cp "$INBOX" "$ARCHIVE_DIR/${TIMESTAMP}-${BASENAME}"
       # Reset to empty state
       ROLE=$(echo "$BASENAME" | sed 's/inbox-//;s/\.md//')
       printf "# %s Inbox\n<!-- Messages from teammates when Discord is unavailable -->\n\nNo pending messages.\n" "$(echo $ROLE | sed 's/./\U&/')" > "$INBOX"
       echo "Archived $BASENAME ($LINES lines)"
     else
       echo "Skipped $BASENAME (no messages)"
     fi
   done
   ```
4. Save and Activate

### Workflow 2: Session Snapshot Archiver (Cron daily)

Moves old session snapshots to the archive folder, keeping only the 10 most recent per agent.

**Create in n8n UI:**

1. New Workflow -> Name: "Snapshot Archiver"
2. Add **Schedule Trigger** node:
   - Rule: Daily at 03:00
3. Add **Execute Command** node:
   ```bash
   SNAP_DIR="{YOUR_HOME}/Documents/claude-context/session-snapshots"
   ARCHIVE_DIR="$SNAP_DIR/archive"
   mkdir -p "$ARCHIVE_DIR"

   for AGENT in brother proctor; do
     # List snapshots for this agent, sorted newest first
     FILES=$(ls -1t "$SNAP_DIR"/*-${AGENT}-session-*.md 2>/dev/null)
     COUNT=$(echo "$FILES" | grep -c . 2>/dev/null || echo 0)

     if [ "$COUNT" -gt 10 ]; then
       # Move everything after the 10th to archive
       echo "$FILES" | tail -n +11 | while read FILE; do
         mv "$FILE" "$ARCHIVE_DIR/"
         echo "Archived: $(basename $FILE)"
       done
     else
       echo "$AGENT: $COUNT snapshots (under limit)"
     fi
   done
   ```
4. Save and Activate

### Workflow 3: Health Check Ping (Cron hourly)

Pings all services and posts to #alerts if any are down.

**Create in n8n UI:**

1. New Workflow -> Name: "Health Check"
2. Add **Schedule Trigger** node:
   - Rule: Every hour
3. Add **Execute Command** node:
   ```bash
   FAILURES=""

   # Check Docker
   if ! docker ps > /dev/null 2>&1; then
     FAILURES="$FAILURES\n- Docker is not responding"
   fi

   # Check n8n API
   STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/api/v1/workflows -H "X-N8N-API-KEY: {YOUR_N8N_API_KEY}")
   if [ "$STATUS" != "200" ]; then
     FAILURES="$FAILURES\n- n8n API returned $STATUS"
   fi

   # Check Postgres
   if ! docker exec postgres-dev psql -U dev -d main -c "SELECT 1;" > /dev/null 2>&1; then
     FAILURES="$FAILURES\n- PostgreSQL is not responding"
   fi

   # Check Discord bot (optional — test a read)
   # Add your own check here based on your Discord setup

   if [ -n "$FAILURES" ]; then
     echo "FAILURES:$FAILURES"
   else
     echo "ALL_HEALTHY"
   fi
   ```
4. Add **IF** node:
   - Condition: `{{ $json.stdout }}` contains "FAILURES"
5. On TRUE branch, add **Discord Send Message** node (or HTTP Request to Discord webhook):
   - Channel: #alerts (use channel ID)
   - Message: `**[Council]** Health check failed:\n{{ $json.stdout }}`
6. Save and Activate

### Workflow 4: Notification Relay (Webhook trigger)

Receives a JSON payload and writes a notification to the specified agent's queue file.

**Create in n8n UI:**

1. New Workflow -> Name: "Notification Relay"
2. Add **Webhook** node:
   - HTTP Method: POST
   - Path: `notification-relay`
   - Note the full URL (e.g., `http://localhost:5678/webhook/notification-relay`)
3. Add **Execute Command** node:
   ```bash
   RECIPIENT="{{ $json.body.recipient }}"
   SENDER="{{ $json.body.sender }}"
   PRIORITY="{{ $json.body.priority }}"
   SUBJECT="{{ $json.body.subject }}"
   MESSAGE="{{ $json.body.message }}"
   ACTION="{{ $json.body.action_required }}"
   TIMESTAMP=$(date +"%Y-%m-%d %H:%M")

   QUEUE_FILE="{YOUR_HOME}/Documents/claude-context/notifications/${RECIPIENT}-queue.md"

   # Append notification
   cat >> "$QUEUE_FILE" << NOTIF

   ## $TIMESTAMP From: $SENDER | Priority: $PRIORITY
   **Subject:** $SUBJECT
   **Message:** $MESSAGE
   **Action Required:** $ACTION
   ---
   NOTIF

   echo "Notification written to $QUEUE_FILE"
   ```
4. Save and Activate

**Trigger from Brother:**
```bash
curl -X POST http://localhost:5678/webhook/notification-relay \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "proctor",
    "sender": "Brother",
    "priority": "NORMAL",
    "subject": "Build complete",
    "message": "API refactoring done. Tests passing.",
    "action_required": "YES -- review deliverable"
  }'
```

### Workflow 5: Knowledge Ingest (Webhook trigger)

Receives session files and stores them in the knowledge base. This connects to the Knowledge Layer in Section 4.

**Create in n8n UI:**

1. New Workflow -> Name: "Knowledge Ingest"
2. Add **Webhook** node:
   - HTTP Method: POST
   - Path: `knowledge-ingest`
3. Add **Execute Command** node:
   ```bash
   STORE="{{ $json.body.store }}"
   CONTENT="{{ $json.body.content }}"
   SOURCE="{{ $json.body.source }}"

   # Store to knowledge base (connects to Section 4 — Knowledge Layer)
   # This is a placeholder — replace with your actual storage command
   # once the Knowledge Layer is configured
   echo "$CONTENT" >> "{YOUR_HOME}/Documents/claude-context/knowledge-ingest.log"
   echo "Ingested from $SOURCE into store: $STORE"
   ```
4. Save and Activate

### Verify:
```bash
# List all workflows
curl -s http://localhost:5678/api/v1/workflows \
  -H "X-N8N-API-KEY: YOUR_KEY" | python3 -m json.tool | head -30

# Manually trigger the health check (if using webhook version)
# Or activate it and wait for the next cron run, then check #alerts

# Test the notification relay
curl -X POST http://localhost:5678/webhook/notification-relay \
  -H "Content-Type: application/json" \
  -d '{"recipient":"brother","sender":"Council","priority":"LOW","subject":"Test","message":"Notification relay working.","action_required":"NO"}'

# Check that the notification was written
cat {YOUR_HOME}/Documents/claude-context/notifications/brother-queue.md
```

### Troubleshooting:
- Workflow not triggering: Check that it is set to "Active" (toggle in top right of workflow editor)
- Execute Command fails: n8n runs commands inside the Docker container — paths must be accessible from inside the container. Mount your Documents folder as a volume if needed.
- Webhook returns 404: Workflow must be active AND saved. The webhook URL is only live when the workflow is active.
- n8n cannot reach Discord: If using the Discord node, configure Discord credentials in n8n Settings -> Credentials.

---

## Section 4: Knowledge Layer — Dual-Source Memory (25 min)

### Architecture

The Knowledge Layer gives your agents persistent memory across sessions. It has two sources:

| Source | Type | Speed | Best For |
|--------|------|-------|----------|
| **pgvector** | Local PostgreSQL + vector embeddings | Fast (local) | Semantic search, code patterns, exact recall |
| **Gemini** | Google Cloud AI batch store | Medium (API) | Broader context, long-term knowledge, cross-project recall |

Both sources are queried on recall and return ranked results. Using two sources means you get both precise local search and broad cloud-backed recall.

### Part A: pgvector Setup

pgvector is a PostgreSQL extension that enables vector similarity search — storing and querying text embeddings directly in your database.

#### Step 1: Create the Database

```bash
# If you already have a Postgres container from Phase 2, add pgvector:
docker exec -it postgres-dev psql -U dev -d main -c "CREATE EXTENSION IF NOT EXISTS vector;"

# If you need a new container with pgvector built in:
docker run -d \
  --name postgres-knowledge \
  -e POSTGRES_USER=claude \
  -e POSTGRES_PASSWORD=claude_dev \
  -e POSTGRES_DB=continuous_claude \
  -p 5433:5432 \
  pgvector/pgvector:pg16

# Wait for startup
sleep 5

# Verify pgvector extension
docker exec postgres-knowledge psql -U claude -d continuous_claude \
  -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extversion FROM pg_extension WHERE extname='vector';"
```

#### Step 2: Create the Learnings Table

```bash
docker exec postgres-knowledge psql -U claude -d continuous_claude << 'SQL'
CREATE TABLE IF NOT EXISTS learnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    learning_type TEXT NOT NULL,
    content TEXT NOT NULL,
    context TEXT,
    tags TEXT[],
    confidence TEXT DEFAULT 'medium',
    embedding vector(1536),
    superseded_by UUID REFERENCES learnings(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_learnings_type ON learnings(learning_type);
CREATE INDEX IF NOT EXISTS idx_learnings_tags ON learnings USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_learnings_embedding ON learnings USING ivfflat (embedding vector_cosine_ops);
SQL
```

**Note on `superseded_by`:** This field enables soft-deprecation of outdated memories. When a learning is replaced by a newer, more accurate version, set `superseded_by` to the new record's UUID. Recall queries should filter out superseded records (WHERE superseded_by IS NULL) to avoid returning stale information.

#### Step 3: Install Dependencies

The recall and store scripts use Python with `uv` (fast Python package manager):

```bash
# Install uv if not already installed
pip install uv

# Create the scripts directory
mkdir -p {YOUR_HOME}/.claude/scripts/core

# Install Python dependencies
cd {YOUR_HOME}/.claude/scripts/core
uv pip install asyncpg pgvector openai
```

#### Step 4: Create the Recall Script

```bash
cat > {YOUR_HOME}/.claude/scripts/core/recall_learnings.py << 'RECALL'
#!/usr/bin/env python3
"""Recall learnings from the persistent memory system."""
import argparse
import asyncio
import json
import os
import sys

import asyncpg

DB_URL = os.environ.get('CONTINUOUS_CLAUDE_DB_URL',
    'postgresql://claude:claude_dev@localhost:5433/continuous_claude')

async def search_text(conn, query, k=5):
    """Text-based search using ILIKE matching."""
    terms = query.split()
    conditions = " AND ".join([f"content ILIKE '%' || ${i+1} || '%'" for i in range(len(terms))])
    rows = await conn.fetch(f"""
        SELECT id, session_id, learning_type, content, context, tags, confidence, created_at
        FROM learnings
        WHERE {conditions}
        ORDER BY created_at DESC
        LIMIT ${ len(terms) + 1 }
    """, *terms, k)
    return [dict(r) for r in rows]

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', required=True, help='Search query')
    parser.add_argument('--k', type=int, default=5, help='Number of results')
    parser.add_argument('--text-only', action='store_true', help='Text search only (fast)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    conn = await asyncpg.connect(DB_URL)
    try:
        results = await search_text(conn, args.query, args.k)
        if args.json:
            output = {"results": []}
            for r in results:
                output["results"].append({
                    "id": str(r["id"]),
                    "type": r["learning_type"],
                    "content": r["content"],
                    "context": r.get("context", ""),
                    "score": 1.0
                })
            print(json.dumps(output))
        else:
            if not results:
                print(f"No learnings found for: {args.query}")
                return
            for i, r in enumerate(results, 1):
                print(f"\n--- Result {i} ---")
                print(f"Type: {r['learning_type']}")
                print(f"Content: {r['content']}")
                if r.get('context'):
                    print(f"Context: {r['context']}")
                print(f"Session: {r['session_id']}")
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
RECALL
```

#### Step 5: Create the Store Script

```bash
cat > {YOUR_HOME}/.claude/scripts/core/store_learning.py << 'STORE'
#!/usr/bin/env python3
"""Store a learning in the persistent memory system."""
import argparse
import asyncio
import os

import asyncpg

DB_URL = os.environ.get('CONTINUOUS_CLAUDE_DB_URL',
    'postgresql://claude:claude_dev@localhost:5433/continuous_claude')

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session-id', required=True)
    parser.add_argument('--type', required=True,
        choices=['ARCHITECTURAL_DECISION', 'WORKING_SOLUTION', 'CODEBASE_PATTERN',
                 'FAILED_APPROACH', 'ERROR_FIX', 'USER_PREFERENCE', 'OPEN_THREAD'])
    parser.add_argument('--content', required=True)
    parser.add_argument('--context', default='')
    parser.add_argument('--tags', default='')
    parser.add_argument('--confidence', default='medium', choices=['high', 'medium', 'low'])
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(',') if t.strip()] if args.tags else []

    conn = await asyncpg.connect(DB_URL)
    try:
        await conn.execute("""
            INSERT INTO learnings (session_id, learning_type, content, context, tags, confidence)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, args.session_id, args.type, args.content, args.context, tags, args.confidence)
        print(f"Stored [{args.type}]: {args.content[:80]}...")
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
STORE
```

### Part B: Gemini Recall Setup

Gemini provides a cloud-backed memory layer with named stores for organizing knowledge by domain.

#### Step 1: Get a Gemini API Key

1. Go to https://makersuite.google.com/app/apikey (Google AI Studio)
2. Create an API key
3. Add it to your credential vault:

```bash
# Read existing config first, then add gemini key
# (edit council-config.json manually to add this block)
```

Add this to your `council-config.json`:
```json
"gemini": {
  "api_key": "YOUR_GEMINI_API_KEY"
}
```

#### Step 2: Create the Gemini Recall Script

```bash
cat > {YOUR_HOME}/scripts/gemini-recall-v2.py << 'GEMINI'
#!/usr/bin/env python3
"""Query and store knowledge using Gemini's context caching."""
import argparse
import json
import os
import sys
from pathlib import Path

# Store data locally as JSON files organized by store name
STORES_DIR = Path.home() / "Documents" / "claude-context" / "knowledge-stores"

def ensure_store(store_name):
    store_path = STORES_DIR / store_name
    store_path.mkdir(parents=True, exist_ok=True)
    return store_path

def store_knowledge(store_name, content, source="manual"):
    """Store a piece of knowledge in a named store."""
    store_path = ensure_store(store_name)
    import time
    entry = {
        "content": content,
        "source": source,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "id": f"k-{int(time.time())}"
    }
    entry_file = store_path / f"{entry['id']}.json"
    entry_file.write_text(json.dumps(entry, indent=2))
    print(f"Stored in {store_name}: {content[:80]}...")

def recall_knowledge(store_name, query, k=5):
    """Search a named store for relevant knowledge."""
    store_path = ensure_store(store_name)
    results = []
    query_lower = query.lower()
    query_terms = query_lower.split()

    for entry_file in store_path.glob("*.json"):
        entry = json.loads(entry_file.read_text())
        content_lower = entry["content"].lower()
        # Simple relevance scoring: count matching terms
        score = sum(1 for term in query_terms if term in content_lower)
        if score > 0:
            entry["score"] = score / len(query_terms)
            results.append(entry)

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:k]

    if not results:
        print(f"No results in {store_name} for: {query}")
        return

    for i, r in enumerate(results, 1):
        print(f"\n--- Result {i} (score: {r['score']:.2f}) ---")
        print(f"Content: {r['content']}")
        print(f"Source: {r['source']}")
        print(f"Stored: {r['timestamp']}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--store', required=True, help='Named store (e.g., tandem_ops)')
    parser.add_argument('--query', help='Search query')
    parser.add_argument('--add', help='Content to store')
    parser.add_argument('--source', default='manual', help='Source label')
    parser.add_argument('--k', type=int, default=5, help='Number of results')
    args = parser.parse_args()

    if args.add:
        store_knowledge(args.store, args.add, args.source)
    elif args.query:
        recall_knowledge(args.store, args.query, args.k)
    else:
        print("Specify --query to search or --add to store")

if __name__ == '__main__':
    main()
GEMINI

mkdir -p {YOUR_HOME}/scripts
mkdir -p {YOUR_HOME}/Documents/claude-context/knowledge-stores
```

### Part C: Using the Knowledge Layer

**Store names convention:**
- `tandem_ops` — Operational knowledge (session learnings, team coordination patterns)
- `codebase` — Code patterns, architecture decisions, working solutions
- `domain` — Business/domain-specific knowledge (your industry, your clients)

**When to use recall:**
- Session startup — check for relevant context about the current task
- Investigation tasks — before digging in, check if this was solved before
- Before building something — check if a similar thing was built in a past session

**Recall card format (what you get back):**
```
--- Result 1 ---
Type: WORKING_SOLUTION
Content: pgvector requires CREATE EXTENSION vector before any embedding operations...
Context: Session 45, Postgres setup
Session: session-45
```

### Verify:

```bash
# Store a test learning
cd {YOUR_HOME}/.claude/scripts/core
uv run python store_learning.py \
  --session-id "test-session" \
  --type WORKING_SOLUTION \
  --content "Test learning: the Knowledge Layer is working correctly" \
  --context "Phase 3 setup verification" \
  --tags "test,setup" \
  --confidence high

# Recall the test learning
uv run python recall_learnings.py --query "Knowledge Layer working" --text-only

# Test Gemini store
python {YOUR_HOME}/scripts/gemini-recall-v2.py \
  --store tandem_ops \
  --add "Test: Knowledge Layer dual-source memory is configured" \
  --source "phase-3-setup"

# Query Gemini store
python {YOUR_HOME}/scripts/gemini-recall-v2.py \
  --store tandem_ops \
  --query "Knowledge Layer"
```

Both should return the test learnings you stored.

### Troubleshooting:
- asyncpg connection refused: Check Postgres container is running and port matches (5432 vs 5433)
- pgvector extension not found: Run `docker exec postgres-knowledge psql -U claude -d continuous_claude -c "CREATE EXTENSION vector;"`
- uv not found: `pip install uv`
- Gemini store empty: Check the knowledge-stores directory was created at the right path

### Memory Architecture Notes (Lessons Learned)

These are operational insights from running the Knowledge Layer in production:

- **Recency weighting in recall queries.** When relevance scores are equal, newer memories should rank higher. Add `ORDER BY created_at DESC` as a tiebreaker in your recall queries. Stale context from 50 sessions ago is rarely more useful than last week's.
- **SQLite fallback.** If Postgres is unreachable (container down, port conflict), memory operations should not block the session. Consider a lightweight SQLite fallback that stores learnings locally and syncs to Postgres when it comes back up.
- **Memory audit baseline.** An early audit scored the system at 6.2/10. Main gaps: low record count (69 records — too few for meaningful semantic search), empty Postgres tables (16 of 18 tables had zero rows). The fix is discipline — store learnings consistently, not just when you remember to.
- **MEMORY.md consolidation.** As your auto-memory file (MEMORY.md) grows, complex rules should get their own detail files (e.g., `memory/skill-zero-details.md`, `memory/agent-verb-rules.md`). MEMORY.md holds pointers only — one line per rule with a file reference. This prevents MEMORY.md from becoming a context bomb on every session.

---

## Section 5: Advanced Hooks (15 min)

### What Hooks ARE

Hooks are shell commands that fire automatically on Claude Code events. They run in the background and inject context, enforce rules, or perform side effects. Think of them as event listeners for your AI agent.

**Hook types:**

| Hook Type | Fires When | Use For |
|-----------|-----------|---------|
| **PreToolUse** | Before a tool call executes | Block dangerous operations, inject warnings |
| **PostToolUse** | After a tool call completes | Auto-format code, restore window state, log actions |
| **UserPromptSubmit** | When the user sends a message | Inject memory context, track context usage |

### Hooks Already in the Toolkit

The `configs/hooks/` directory contains these ready-to-use hooks:

#### 1. auto-format.js (PostToolUse)

Runs Prettier on code files after every Write or Edit. Only formats if the project has Prettier configured.

**What it does:** Intercepts Edit/Write tool calls, checks the file extension, runs `npx prettier --write` if applicable.

**Supported extensions:** .js, .jsx, .ts, .tsx, .css, .json, .html, .vue, .svelte

#### 2. restore-terminal.js (PostToolUse)

Restores the Windows Terminal window if it gets minimized. Fires after any windows-mcp tool call.

**What it does:** Uses Python ctypes to find the Windows Terminal window and restore it if minimized. Prevents the agent from "going blind" after desktop automation.

**Windows only.** Skip this on macOS/Linux.

#### 3. context-bracket.js (UserPromptSubmit)

Monitors context window usage and injects guidance when context is running low.

**What it does:** Reads the session JSONL file to calculate token usage, then injects bracket-specific guidance:

| Bracket | Remaining | Guidance Injected |
|---------|-----------|-------------------|
| FRESH | 60-100% | Nothing (saves tokens) |
| MODERATE | 40-60% | One-line status reminder |
| DEPLETED | 25-40% | Wrap-up guidance |
| CRITICAL | <25% | Urgent stop-and-save warning |

#### 4. session-register.mjs (UserPromptSubmit)

Registers the current session in a PostgreSQL table on startup. Enables multi-session awareness — each session can see what other sessions are working on.

**What it does:**
- Generates a unique session ID
- Registers it in a `sessions` table with project and timestamp
- Queries for other active sessions on the same project
- Injects a system reminder listing peer sessions (if any)

**Requires:** PostgreSQL with the sessions table (created automatically on first run).

#### 5. memory-awareness.mjs (UserPromptSubmit)

Automatically searches the Knowledge Layer when you send a prompt and injects relevant past learnings.

**What it does:**
- Extracts the intent from your prompt (strips meta-phrases like "can you" and "please")
- Runs a fast text search against pgvector
- If relevant learnings are found, injects them as context hints
- Suggests `/recall` for full content

**Requires:** pgvector Knowledge Layer (Section 4).

#### 6. file-claims.mjs (PreToolUse)

Tracks which session is editing which files. When two sessions try to edit the same file, the second session gets a conflict warning.

**What it does:**
- Fires before every Edit tool call
- Checks a `file_claims` table in PostgreSQL
- If another session has claimed the file, injects a warning
- If unclaimed, registers the claim

**Requires:** PostgreSQL with the file_claims table (created automatically on first run).

### Installing Hooks

Hooks are configured in `~/.claude/settings.json` under the `hooks` key. Add the hooks you want:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "node {YOUR_HOME}/.claude/hooks/file-claims.mjs"
      }
    ],
    "PostToolUse": [
      {
        "type": "command",
        "command": "node {YOUR_HOME}/.claude/hooks/auto-format.js"
      },
      {
        "type": "command",
        "command": "node {YOUR_HOME}/.claude/hooks/restore-terminal.js"
      }
    ],
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "node {YOUR_HOME}/.claude/hooks/context-bracket.js"
      },
      {
        "type": "command",
        "command": "node {YOUR_HOME}/.claude/hooks/session-register.mjs"
      },
      {
        "type": "command",
        "command": "node {YOUR_HOME}/.claude/hooks/memory-awareness.mjs"
      }
    ]
  }
}
```

Copy the hook files to your Claude config:

```bash
mkdir -p {YOUR_HOME}/.claude/hooks

# Copy from the toolkit
cp silas-ai-toolkit/claude-code-toolkit/configs/hooks/auto-format.js {YOUR_HOME}/.claude/hooks/
cp silas-ai-toolkit/claude-code-toolkit/configs/hooks/restore-terminal.js {YOUR_HOME}/.claude/hooks/
cp silas-ai-toolkit/claude-code-toolkit/configs/hooks/context-bracket.js {YOUR_HOME}/.claude/hooks/
cp silas-ai-toolkit/claude-code-toolkit/configs/hooks/dist/session-register.mjs {YOUR_HOME}/.claude/hooks/
cp silas-ai-toolkit/claude-code-toolkit/configs/hooks/dist/memory-awareness.mjs {YOUR_HOME}/.claude/hooks/
cp silas-ai-toolkit/claude-code-toolkit/configs/hooks/dist/file-claims.mjs {YOUR_HOME}/.claude/hooks/
```

### Creating a Custom Hook

Hooks receive JSON on stdin with details about the event. Here is a minimal PostToolUse hook:

```javascript
#!/usr/bin/env node
// Custom hook: log every file edit to a tracking file
const fs = require('fs');

try {
  const input = JSON.parse(fs.readFileSync('/dev/stdin', 'utf8'));
  const filePath = input.tool_input?.file_path;

  if (filePath && (input.tool_name === 'Edit' || input.tool_name === 'Write')) {
    const logLine = `${new Date().toISOString()} | ${input.tool_name} | ${filePath}\n`;
    fs.appendFileSync(
      process.env.HOME + '/Documents/claude-context/edit-log.txt',
      logLine
    );
  }
} catch { /* silent fail — never break the session */ }
```

**Key rules for hooks:**
1. Always wrap in try/catch — a crashing hook breaks the session
2. Keep execution under 5 seconds — hooks that hang freeze Claude Code
3. Use `process.exit(0)` for early exits — do not throw
4. Read from stdin for event data — the JSON structure varies by hook type
5. Write to stdout (JSON) to inject context back into the conversation

### Verify:

```bash
# Confirm hooks are in settings.json
node -e "const s=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.claude/settings.json','utf8')); console.log('Hooks configured:', Object.keys(s.hooks || {}).join(', '))"

# Start Claude Code and make a file edit — check that auto-format runs
# (you will see Prettier output if the project has Prettier configured)

# Send a prompt and check if memory-awareness injects context
# (you will see "MEMORY MATCH" in the system context if learnings are found)
```

### Troubleshooting:
- Hook not firing: Check the path in settings.json matches the actual file location. Use absolute paths.
- Hook crashing: Run the hook manually with test input: `echo '{"tool_name":"Edit","tool_input":{"file_path":"test.js"}}' | node {YOUR_HOME}/.claude/hooks/auto-format.js`
- session-register fails: PostgreSQL must be running and accessible.
- memory-awareness returns nothing: Knowledge Layer must be set up (Section 4) with at least one stored learning.

---

## Section 6: Swarm-First Planning — Skill Zero (10 min)

### Why This Is the Most Important Protocol

Without this protocol, every task starts the same way: the agent reads the request and immediately starts working solo. This burns expensive context on work that sub-agents could handle in parallel at near-zero context cost.

Skill Zero forces a 30-second planning pause before every task. It calculates whether solo execution or agent delegation is more efficient, then enforces the decision. The result: 2-3x more useful work per session before hitting context limits.

**The math:**
- A solo file read costs ~50-100 lines permanently in your context
- A solo web search costs ~200-500 lines permanently in your context
- An agent returns a 3-5 line summary for the same work

When a task requires 5+ tool calls, agents save 80%+ of context compared to solo execution.

### Teams > Swarms — The Proven Architecture (Session #129)

**Use Teams (TeamCreate) for 2+ agent multi-agent work, NOT agent swarms.** This is the single biggest architecture decision for context efficiency.

**The problem with swarms:** When you spawn 3 agents via the Agent tool, each returns a summary to Brother's main context. If one agent produces a 500-line report and returns a 5-line summary, great. But if you need those agents' outputs **synthesized** (combined, compared, merged), Brother has to read all 3 output files, synthesize them, and that synthesis burns 200K+ tokens in Brother's main context.

**The Teams solution:** TeamCreate spawns teammates that share a separate context. Worker teammates produce output, a synthesizer teammate reads and combines it — all within the team's context, NOT Brother's. Brother only receives the final 10-line summary.

**Measured results (Session #129):**
| Metric | Swarms | Teams | Savings |
|--------|--------|-------|---------|
| Brother context | 200K+ tokens | 32K tokens | **70%+** |
| Context window used | 85%+ | 49% | **36 percentage points** |
| Agent work quality | Same | Same | — |

**Pattern:**
```
TeamCreate → parallel worker teammates → synthesizer teammate → 10-line summary to Brother
```

**When to use what:**
- **2+ agents needing synthesis:** USE TEAMS (TeamCreate)
- **Single-agent tasks:** Use Agent tool directly (no team overhead)
- **Solo tasks (1 subtask, mechanical):** Do it yourself, max 4 tool calls

**Requires:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in settings.json env block (already in the template).

### The Cost-Based Gate Check

Before every non-trivial task, run this 6-line analysis:

```
1. TASK: [one sentence description]
2. SOLO ESTIMATE: [N tool calls] x [avg ~75 lines each] = [total lines into context]
   -- DAISY-CHAIN MULTIPLIER: investigate/diagnose = 3x, build/fix = 2x, simple edit = 1x
   -- CORRECTION FACTOR: Multiply estimate by 1.5x (historical underestimation)
3. AGENT ESTIMATE: [N agents] x [3-line summary] = [total lines into context]
4. SAVINGS: [solo context] - [agent context] = [lines saved] ([X%] reduction)
5. VERB CHECK: [list verbs] -- Mandatory agent verbs present? [YES/NO]
6. DECISION: AGENTS if savings >30% OR any mandatory verb. SOLO only if <30% savings
   AND no mandatory verbs AND corrected estimate is 4 tool calls or fewer.
```

### Mandatory Agent Verbs

If the task contains ANY of these verbs, agents are required regardless of other factors:

> investigate, audit, research, diagnose, analyze, evaluate, compare, assess, explore, review

These verbs inherently require multiple perspectives and deep exploration — exactly the work that burns context fastest when done solo.

### Operation-Type Classification

This is the primary trigger, harder to game than verb matching:

| Operation Type | Solo Eligible? | Rationale |
|----------------|----------------|-----------|
| **Read-only** (search, list, read single file) | Yes | Low context cost |
| **Single-file write** (one edit, one config change) | Yes | Mechanical, low cost |
| **Multi-file write** (2+ files to modify) | No — agents mandatory | Coordination risk + context cost |
| **External service** (API calls, Discord, webhooks) | No — agents mandatory | Error loops burn context |
| **Unknown scope** (cannot define all steps upfront) | No — agents mandatory | Scope creep is the #1 context killer |

### Solo Hard Cap

If you declare SOLO on the gate check, you are committing to a maximum of 4 tool calls. If you hit call 4 and are not done, STOP. The gate check was wrong. Re-plan with agents.

### PreToolUse Enforcement Hook

Skill Zero is no longer honor-system only. A **PreToolUse hook** counts tool calls and enforces the gate check:

- The hook fires before every tool call and checks whether Skill Zero output is visible in the conversation
- At 4+ tool calls without a visible gate check, the hook injects a **warning** into the conversation
- This prevents the most common failure mode: the agent deciding "this task is simple enough to skip planning" and then burning 20+ tool calls solo

To install the hook, add it to your `settings.json` PreToolUse array (see Section 5 for hook installation).

### Mid-Task Scope Check

At tool call 3 on any solo task, pause and answer: "SCOPE CHECK: same or expanded?"

If the task has grown beyond the original estimate (new files discovered, deeper problem found, additional fixes needed), re-run the gate check. If it now says AGENTS, pivot immediately.

### Phase Transition Re-Check

**One Skill Zero pass does NOT authorize all subsequent phases.** When the nature of work shifts — for example, from analysis to implementation, or from research to build — re-run the 6-line cost check. Each phase has different tool call profiles and context costs. A task that started as "read 2 files" can expand into "refactor 8 files" after the analysis phase reveals the scope.

### Creating the Skill File

Create the Skill Zero command so it can be invoked as `/swarm-first-planning`:

```bash
mkdir -p .claude/commands

cat > .claude/commands/swarm-first-planning.md << 'SKILL'
---
name: swarm-first-planning
description: "Mandatory planning gate check before any task execution. Determines solo vs agent delegation."
---

# Skill Zero — Swarm-First Planning Gate Check

Before executing ANY task, complete this cost-based analysis.

## Gate Check Template

Fill in ALL 6 lines before your first tool call:

```
1. TASK: [one sentence description of what you are about to do]
2. SOLO ESTIMATE: [N tool calls] x [~75 lines each] = [total lines]
   DAISY-CHAIN MULTIPLIER: investigate = 3x, build = 2x, simple edit = 1x
   CORRECTION FACTOR: Multiply by 1.5x (you historically underestimate by 40-60%)
3. AGENT ESTIMATE: [N agents] x [3-line summary each] = [total lines]
4. SAVINGS: [solo] - [agent] = [lines saved] ([X%] reduction)
5. VERB CHECK: [list task verbs] -- Mandatory agent verbs? [YES/NO]
   Mandatory verbs: investigate, audit, research, diagnose, analyze, evaluate, compare, assess, explore, review
6. DECISION: [AGENTS / SOLO] -- Justification: [one sentence]
```

## Decision Rules
- AGENTS if savings >30% OR any mandatory verb is present
- SOLO only if savings <30% AND no mandatory verbs AND corrected estimate <=4 tool calls
- Solo = max 4 tool calls hard cap
- At tool call 3, do a scope check: if task has expanded, re-run this gate check

## After the Gate Check
- If AGENTS: Define agent prompts, spawn them, wait for summaries
- If SOLO: Proceed. But if you hit tool call 4 and are not done, STOP and re-plan with agents.
SKILL
```

### Example Gate Check

**Task: "Investigate why the API is returning 500 errors on the /users endpoint."**

```
1. TASK: Investigate API 500 errors on /users endpoint
2. SOLO ESTIMATE: 8 tool calls x 75 lines = 600 lines
   DAISY-CHAIN: investigate = 3x -> 8 x 3 = 24 effective calls -> 1800 lines
   CORRECTION: 1800 x 1.5 = 2700 lines
3. AGENT ESTIMATE: 3 agents x 5 lines = 15 lines
4. SAVINGS: 2700 - 15 = 2685 lines saved (99% reduction)
5. VERB CHECK: [investigate] -- Mandatory agent verb? YES
6. DECISION: AGENTS -- mandatory verb "investigate" + 99% context savings
```

Result: Use TeamCreate — 3 worker teammates (logs reader, route tracer, DB query checker) + 1 synthesizer teammate. The synthesizer combines all findings within the team context. Brother gets a 10-line summary. Zero synthesis cost in main context.

### Agent Reliability — What We Learned

Early testing suggested a 23% agent failure rate. After investigation, the **actual failure rate is ~5%.** The root cause was Write tool sequencing — agents tried to Read nonexistent files before Writing new ones, which triggered errors.

**The fix (baked into agent base rules):**
1. **If Write fails, return content inline.** The agent should never silently fail — if it cannot write the deliverable file, it returns the full content in its summary so the main context can capture it.
2. **New files: Write directly, do not Read first.** The Write tool requires a prior Read on *existing* files, but for *new* files the agent should Write directly without a Read.
3. **Write early, research second.** Agents should create their output file first (even with placeholder content), then fill it in. This prevents the failure mode where an agent does 10 minutes of research and then fails on the final Write.

**Prompt quality matters more than anything else.** Prescriptive prompts (specific files, exact output format, clear success criteria) succeed ~99% of the time. Open-ended prompts ("investigate this and tell me what you find") risk budget burn and vague results. Every agent prompt should include:
- Exact file paths to read/write
- Output format (e.g., "Write a table with columns X, Y, Z")
- A 3-line summary format for the return value
- Credentials/endpoints if the agent needs external access

### Verify:
1. Start a new Claude Code session
2. Give it a task
3. Confirm the gate check template appears BEFORE the first tool call
4. Confirm the decision (AGENTS or SOLO) matches the rules above

---

## Section 7: Custom Skill Library (10 min)

### What Skills ARE

Skills are `.md` files in `.claude/commands/` that become `/slash-commands` in Claude Code. When you type `/skill-name`, Claude Code reads the file and follows its instructions. Skills turn recurring workflows into one-command invocations.

### Anatomy of a Skill File

```markdown
---
name: skill-name
description: "When this skill should be used. Shown in /slash-command list."
---

# Skill Title

Instructions for Claude Code to follow when this skill is invoked.

You can include:
- Step-by-step procedures
- Code templates with $ARGUMENTS placeholder (replaced with user input)
- Decision trees
- Output format requirements
```

The `$ARGUMENTS` variable contains whatever the user typed after the slash command.
Example: `/recall database errors` sets `$ARGUMENTS` to `database errors`.

### Essential Starter Skills

#### /session-start — Automated Startup (Agent-Powered)

The startup skill launches **2 lightweight agents in parallel** to gather state and messages simultaneously. This replaced the old sequential approach (which read 16+ individual snapshot files) and cut startup token cost from ~114K to ~50K.

**Architecture:**

| Agent | Reads | Writes |
|-------|-------|--------|
| **State Reader** | session-state.md, inbox-brother.md, trajectory.md | deliverables/startup-state-digest.md |
| **Discord Reader** | #handoffs channel (last 15 messages) | deliverables/startup-discord-digest.md |

Both agents return 3-line summaries. Brother synthesizes into a briefing for the user.

**Key design decisions:**
- **trajectory.md replaces snapshot globbing.** Instead of reading 16+ individual session snapshots, the State Reader reads a single rolling history table. See Section 8 for details.
- **Recall is ON-DEMAND ONLY.** Generic startup recall (`/recall` on every boot) was removed — it produced low-value results at ~26K token cost. Use `/recall <query>` when a specific task needs prior context.
- **Agent output goes to files, not inline.** Each agent writes its full report to a deliverables file and returns only a 3-line summary. This prevents agent output from bloating the main context.

```bash
cat > .claude/commands/session-start.md << 'SKILL'
---
name: session-start
description: "Run on every session startup. Launches 2 agents to read state + Discord, presents briefing."
---

# Session Startup — Agent-Powered

Launch 2 agents IN PARALLEL. Do not read state files yourself — the agents do it.

## Agent 1: State Reader
Spawn a sub-agent with this prompt:
> Read these 3 files and write a consolidated digest to
> {YOUR_HOME}/Documents/claude-context/deliverables/startup-state-digest.md:
> 1. {YOUR_HOME}/Documents/claude-context/session-state.md (current status + priorities)
> 2. {YOUR_HOME}/Documents/claude-family/inbox-{role}.md (pending messages)
> 3. {YOUR_HOME}/Documents/claude-context/trajectory.md (recent session history)
> Return ONLY: (1) status, (2) top priority, (3) file path.

## Agent 2: Discord Reader
Spawn a sub-agent with this prompt:
> Read the last 15 messages from Discord #handoffs (channel ID: YOUR_HANDOFFS_ID).
> Write digest to {YOUR_HOME}/Documents/claude-context/deliverables/startup-discord-digest.md.
> Return ONLY: (1) message count, (2) anything needing immediate action, (3) file path.

## After Both Return
Read the two digest files. Synthesize into a briefing for the user covering:
- Current status and priorities
- Pending inbox messages or handoffs
- What needs immediate attention vs. what can wait
- Blockers or decisions needed

Do NOT proceed with any other work until this briefing is presented.
SKILL
```

#### /session-end — Automated Shutdown (Agent-Powered)

The shutdown skill launches **4 agents in parallel**, completing in ~30 seconds (down from ~161 seconds with sequential execution).

**Architecture:**

| Agent | Writes | Notes |
|-------|--------|-------|
| **Archive Agent** | session-state.md, claude-archive.md | Overwrites state, appends to archive |
| **Snapshot Agent** | session snapshot, handoff prompt, next-session-prompt.md | Handoff prompt goes to `handoff-prompts/` folder |
| **Discord Agent** | Posts to #session-archive and #brother-log (or #proctor-log) | Brief summary of session |
| **Knowledge Ingest Agent** | POSTs to knowledge-ingest webhook | Fire-and-forget — do not wait for response |

**Key design decisions:**
- **Handoff prompts go to a folder** (`handoff-prompts/`) with Skill Zero prepend on the first line. The folder provides audit trail and gap detection — if the next session sees session N-2 as the latest prompt, they know N-1 failed to hand off.
- **Knowledge ingest is fire-and-forget.** The webhook call does not block shutdown. If it fails, it fails silently.
- **All 4 agents run simultaneously.** No dependencies between them — each has all the context it needs from the main session.

```bash
cat > .claude/commands/session-end.md << 'SKILL'
---
name: session-end
description: "Run at end of every session. Launches 4 agents in parallel for fast shutdown (~30s)."
---

# Session Shutdown — Agent-Powered (4 Parallel Agents)

Launch ALL 4 agents simultaneously. Each agent gets the session context it needs inline.

## Agent 1: Archive Agent
> Update session-state.md with current status, next tasks, blockers, files modified.
> Append a dated session entry to claude-archive.md.

## Agent 2: Snapshot Agent
> Write session snapshot to session-snapshots/{YYYY-MM-DD}T{HH-MM}-{role}-session-{N}.md.
> Write handoff prompt to handoff-prompts/{YYYY-MM-DD}T{HH-MM}-session-{N}.md.
> FIRST LINE of handoff prompt MUST be the Skill Zero prepend.
> Also write to next-session-prompt.md as backwards-compatible fallback.
> Prune: if >10 snapshots exist, move oldest to archive/.

## Agent 3: Discord Agent
> Post to Discord #session-archive: brief summary of what was accomplished, decisions, next steps.
> Post to your role's log channel (#brother-log or #proctor-log): session end notice.

## Agent 4: Knowledge Ingest Agent
> POST to http://localhost:5678/webhook/knowledge-ingest with session files.
> Fire-and-forget — do NOT wait for response. If it fails, exit cleanly.

## After All Return
Notify the user that state is saved, handoff is written, and the next session can pick up cleanly.
Show the handoff prompt content so the user can paste it into the next session if needed.
SKILL
```

#### /recall — Query Knowledge Layer

```bash
cat > .claude/commands/recall.md << 'SKILL'
---
name: recall
description: "Recall learnings from the memory system. Usage: /recall <search query>"
---

# Recall Learnings

Search the persistent memory system for relevant learnings from past sessions.

```bash
cd {YOUR_HOME}/.claude/scripts/core && uv run python recall_learnings.py --query "$ARGUMENTS" --k 5 --text-only
```

Run the command above via Bash. Present the results to the user.
SKILL
```

#### /remember — Store to Knowledge Layer

```bash
cat > .claude/commands/remember.md << 'SKILL'
---
name: remember
description: "Store a learning in the memory system. Usage: /remember <what to remember>"
---

# Store Learning

Store a learning, pattern, or decision for future recall.

```bash
cd {YOUR_HOME}/.claude/scripts/core && uv run python store_learning.py \
  --session-id "$(date +%Y%m%d)" \
  --type WORKING_SOLUTION \
  --content "$ARGUMENTS" \
  --context "stored via /remember command" \
  --tags "manual" \
  --confidence high
```

Run the command above via Bash. Confirm storage to the user.

**Available types:** ARCHITECTURAL_DECISION, WORKING_SOLUTION, CODEBASE_PATTERN, FAILED_APPROACH, ERROR_FIX, USER_PREFERENCE, OPEN_THREAD
SKILL
```

#### /commit — Standardized Git Commit

```bash
cat > .claude/commands/commit.md << 'SKILL'
---
name: commit
description: "Standardized git commit workflow with status check and meaningful message."
---

# Git Commit Workflow

1. Run `git status` to see all changes
2. Run `git diff --staged` to see what is staged (if anything)
3. If nothing is staged, ask the user what to stage
4. Analyze the changes and draft a commit message:
   - Summarize the nature of the change (feat, fix, refactor, docs, etc.)
   - Keep the first line under 72 characters
   - Add a body if the change is non-trivial
5. Create the commit
6. Run `git status` to confirm
7. Report: commit hash, files changed, message used
SKILL
```

### Skill-First Protocol

Add this rule to your CLAUDE.md:

```markdown
## Skill-First Protocol
Before starting ANY task, check your available skills list (/slash commands).
If a skill matches the task, USE IT. Do not manually replicate what a skill automates.
```

This prevents the agent from doing manually what a skill already handles. Over time, as you add more skills, the agent becomes increasingly automated.

### How to Add New Skills

1. Identify a recurring workflow (you have done it manually 3+ times)
2. Create a `.md` file in `.claude/commands/`
3. Give it a clear `name` and `description` in the frontmatter
4. Write step-by-step instructions that Claude Code can follow
5. Test it: type `/your-skill-name` in Claude Code

**Good candidates for skills:**
- Any multi-step process you repeat regularly
- Deployment workflows
- Data processing pipelines
- Report generation
- Environment setup procedures

### Verify:
```bash
# List all skill files
ls -la .claude/commands/

# Start Claude Code and type / — your skills should appear in the list
```

Start Claude Code, type `/session-start`, and confirm it runs through the startup sequence.

---

## Section 8: trajectory.md — Rolling Session History (5 min)

### What It Is

`trajectory.md` is a single file that replaces reading 16+ individual session snapshots on startup. Instead of globbing for snapshot files and reading each one, the State Reader agent reads this one table and gets the full session history at a glance.

**Location:** `{YOUR_HOME}/Documents/claude-context/trajectory.md`

### Format

The file is a Markdown table with these columns:

```markdown
# Session Trajectory

| Session | Agent | Date | Time | Summary |
|---------|-------|------|------|---------|
| 122 | Brother | 2026-03-11 | 14:30 | Optimized startup skill — 3 agents to 2, removed boot recall |
| 121 | Proctor | 2026-03-11 | 10:15 | Market analysis for Texas expansion — delegated deep dive to Brother |
| 120 | Brother | 2026-03-10 | 22:00 | Fixed n8n webhook routing — 3 workflows updated |
```

### Rules

- **Updated at end of each session** by the shutdown skill (Snapshot Agent appends a row)
- **Parallel sessions on the same date** should be noted — if two rows share a date, the reader should flag potential overlap
- **Keep it rolling** — prune entries older than 30 days to keep the file compact
- **This is what startup reads instead of snapshots.** The State Reader agent reads trajectory.md, not individual snapshot files. Individual snapshots still exist for detailed drill-down but are not part of the boot path.

### Setup

```bash
cat > {YOUR_HOME}/Documents/claude-context/trajectory.md << 'TRAJ'
# Session Trajectory

| Session | Agent | Date | Time | Summary |
|---------|-------|------|------|---------|
TRAJ
```

The shutdown skill populates this automatically. You do not need to maintain it by hand.

---

## Post-Install Checklist

Run through this to confirm all Phase 3 components are working:

```
[ ] Standing orders created for Brother and Proctor
[ ] Proctor custom instructions pasted into Claude Desktop project
[ ] File inboxes created (inbox-brother.md, inbox-proctor.md)
[ ] Proctor identifies correctly in Claude Desktop
[ ] Brother identifies correctly in Claude Code

[ ] Discord dual-write: handoff appears in BOTH #handoffs AND file inbox
[ ] Notification queues created (brother-queue.md, proctor-queue.md)
[ ] PROTOCOL.md created in notifications directory
[ ] "Check your messages" triggers a fresh Discord read

[ ] n8n Inbox Auto-Archive workflow active
[ ] n8n Snapshot Archiver workflow active
[ ] n8n Health Check workflow active and posting to #alerts
[ ] n8n Notification Relay webhook accepting POSTs
[ ] n8n Knowledge Ingest webhook accepting POSTs

[ ] pgvector extension installed in PostgreSQL
[ ] Learnings table created
[ ] recall_learnings.py returns test results
[ ] store_learning.py stores and confirms
[ ] Gemini recall script stores and queries successfully
[ ] Knowledge stores directory created

[ ] Hooks copied to ~/.claude/hooks/
[ ] settings.json hooks section configured
[ ] auto-format hook fires on file edits (if Prettier is in project)
[ ] context-bracket hook injects guidance at moderate/depleted levels
[ ] memory-awareness hook injects relevant learnings on prompts

[ ] swarm-first-planning.md created in .claude/commands/
[ ] Gate check template appears before first tool call on new tasks
[ ] Solo hard cap (4 tool calls) is respected
[ ] PreToolUse enforcement hook installed and warning at 4+ calls without gate check
[ ] Phase transitions trigger re-check (analysis -> implementation = new Skill Zero pass)
[ ] Teams (TeamCreate) used for 2+ agent tasks — CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 set
[ ] LSP plugins enabled (ENABLE_LSP_TOOL=1 + 11 plugins in settings.json)
[ ] Language servers installed (typescript-language-server, pyright, vscode-langservers-extracted)
[ ] ast-grep installed for structural code search (pip install ast-grep-cli)
[ ] CLAUDE.md includes "LSP FIRST, ast-grep SECOND" priority rule

[ ] trajectory.md created in claude-context/
[ ] Shutdown skill appends rows to trajectory.md

[ ] /session-start skill launches 2 agents and presents briefing (~50K tokens)
[ ] /session-end skill launches 4 agents and completes in ~30 seconds
[ ] /recall and /remember skills work with Knowledge Layer
[ ] /commit skill runs standardized git workflow
```

---

## What's Next — Phase 4

Once multi-agent coordination, automation, and protocols are stable, Phase 4 covers:

- **Custom domain skills** — Build skills tailored to your specific industry or workflow (e.g., compliance audits, data pipelines, client onboarding sequences)
- **Agent prompt templates** — Pre-built agent personas (researcher, deployer, QA tester, doc builder, strategist) ready to spawn for any task
- **Production hardening** — Health monitoring dashboards, automatic recovery workflows, credential rotation, backup verification
- **CI/CD integration** — Connect Brother to your deployment pipeline so code changes flow from commit to production automatically
- **Team scaling beyond 2 agents** — Adding specialized agents (Reviewer, QA, Domain Expert), managing 3+ simultaneous sessions, conflict resolution at scale

Phase 4 will be pushed to this repo when you are ready. Pull and check the toolkit for updates.

---

# END OF PHASE 3
#
# At this point you have:
# - Two coordinated agents (Brother + Proctor) with clear roles
# - Dual-write communication that never drops messages
# - Automated workflows handling maintenance and monitoring
# - Persistent memory across sessions via dual-source Knowledge Layer
# - Event-driven hooks for auto-formatting, context tracking, and conflict prevention
# - Mandatory planning protocol that prevents context blowouts
# - Teams architecture (TeamCreate) for 70%+ context savings on multi-agent work
# - LSP code intelligence (11 language servers, 9 operations, 250x token savings vs grep)
# - A growing skill library that automates recurring work
#
# The system is designed to compound: every skill you add, every learning you store,
# every workflow you automate makes every future session more productive.
#
# Questions? Have Brother read this file and ask — he understands the context.
