# Protocols

Protocols are formalized procedures for recurring operational patterns. Unlike playbooks (which document domain-specific knowledge), protocols define **how Claude Code operates** -- session lifecycle, agent coordination, communication, and decision-making.

---

## Protocols in This Toolkit

### agent-delegation.md
The decision framework for when to spin up a sub-agent vs do the work yourself. Includes a flowchart, concrete thresholds (500 tokens, 80 lines, 3+ tool calls), and the "agent type selection matrix" for choosing the right kind of agent.

### session-management.md
The startup and shutdown lifecycle. How to preserve state across sessions so every new session picks up exactly where the last one left off. Includes the startup checklist, shutdown checklist, session-state file format, and archive patterns.

### multi-agent-coordination.md
How to run multiple Claude Code instances that coordinate with each other. Covers communication channels (Discord, file inboxes), role definition, handoff protocols, and window management for instances that need to monitor each other.

### notification-system.md
A push-based notification queue that ensures agents notice messages from teammates. Supplements inbox-based communication with a lightweight "check this FIRST every response" mechanism.

---

## How to Adopt Protocols

1. **Start with session-management.md** -- this is the foundation. Without session state, every session starts from zero.
2. **Add agent-delegation.md** -- the second highest-impact protocol. Doubles effective session length.
3. **Add multi-agent-coordination.md** only if you run multiple Claude instances.
4. **Add notification-system.md** only if you have multi-agent coordination and need push notifications.

You do not need all protocols. Adopt them incrementally based on your workflow complexity.
