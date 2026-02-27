# Protocol: Push Notification System

## Purpose

In a multi-agent setup, file inboxes are "pull" based -- an agent only sees messages when it checks. This notification protocol adds a "push" layer: a lightweight queue that every agent checks FIRST on every response. It ensures no message goes unnoticed.

---

## Architecture

```
Layer 1: Inboxes (pull)     -- Full messages with context, checked on startup
Layer 2: Notification Queue (push) -- Lightweight pointers, checked EVERY response
```

The notification queue does not replace inboxes. It ensures you notice that an inbox message (or any other action requiring attention) exists.

---

## Queue Files

Each agent has a queue file at a known location:

```
[YOUR_CONTEXT_DIR]/notifications/engineer-queue.md
[YOUR_CONTEXT_DIR]/notifications/coordinator-queue.md
[YOUR_CONTEXT_DIR]/notifications/reviewer-queue.md
```

---

## Notification Format

When appending a notification to any queue file:

```markdown
## [YYYY-MM-DD HH:MM] From: [SENDER] | Priority: [HIGH/NORMAL/LOW]
**Subject:** [brief subject line]
**Message:** [content or pointer to full message]
**Action Required:** [YES/NO] -- [what is needed, if YES]
---
```

### Priority Levels

| Priority | Meaning | Response Expectation |
|----------|---------|---------------------|
| **HIGH** | Blocking or urgent | Address before proceeding with other work |
| **NORMAL** | Review when you can | Non-blocking but important |
| **LOW** | FYI only | No response expected |

---

## Rules

### 1. Send Rule (MANDATORY)
When ANY agent sends a message to another agent -- whether by inbox, chat, or any other means -- they MUST ALSO append a notification to that agent's queue file. No silent drops. Every message gets a notification.

### 2. Stacking
Notifications stack. Multiple notifications can be pending. New notifications are appended below existing ones.

### 3. Check Rule (MANDATORY)
Every agent's FIRST ACTION on EVERY response must be:
1. Read their own queue file
2. If notifications exist, acknowledge them before proceeding
3. Clear processed notifications

### 4. Clearing
After processing all pending notifications, reset the queue to:
```markdown
# [Agent] Notification Queue
<!-- Check this file FIRST before every response. Process and clear after reading. -->

No pending notifications.
```

### 5. Response Rule
If a notification requires a response:
1. Send the reply (via inbox, chat, or direct file)
2. Append a notification to the original sender's queue confirming the reply

---

## Example Flow

**Coordinator finishes a research summary and sends it to Engineer:**

1. Coordinator writes the summary to `deliverables/2026-02-26-market-analysis.md`
2. Coordinator posts to #handoffs: "Market analysis complete, file at [path]"
3. Coordinator appends to `engineer-queue.md`:
   ```markdown
   ## 2026-02-26 14:30 From: Coordinator | Priority: NORMAL
   **Subject:** Market analysis deliverable ready
   **Message:** See #handoffs and deliverables/2026-02-26-market-analysis.md
   **Action Required:** YES -- Review and incorporate into the dashboard
   ---
   ```

**Engineer's next response:**
1. Reads `engineer-queue.md` -- sees the notification
2. Acknowledges: "Notification from Coordinator -- market analysis ready for review. Will incorporate."
3. Clears the queue
4. Proceeds with work, including the review task

---

## When to Use This Protocol

- **Multi-agent setups** where agents run in separate windows/sessions
- **Async workflows** where an agent might not check chat for a while
- **Critical handoffs** where a missed message causes delays

**Not needed for:**
- Single-agent setups (no one to notify)
- Real-time chat-only workflows where all agents monitor chat continuously

---

*This protocol adds minimal overhead (one file read per response, one file write per notification sent) but prevents the costly failure mode of missed messages causing duplicate work or stalled tasks.*
