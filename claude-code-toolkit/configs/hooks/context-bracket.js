#!/usr/bin/env node
/**
 * Context Bracket Hook — inspired by CARL's bracket system
 *
 * Reads the current session's JSONL to calculate context window usage,
 * then injects bracket-specific guidance ONLY when it matters:
 *   FRESH (60-100%):    No injection — save tokens
 *   MODERATE (40-60%):  One-line status reminder
 *   DEPLETED (25-40%):  Wrap-up guidance
 *   CRITICAL (<25%):    Urgent stop-and-compact warning
 */

const fs = require('fs');
const path = require('path');

const MAX_CONTEXT = 200000;

function readStdin() {
  return fs.readFileSync(0, 'utf-8');
}

/**
 * Convert a CWD path to Claude's project directory name.
 * Windows: C:\Users\silas -> C--Users-silas
 * Unix:    /home/user/project -> -home-user-project
 */
function cwdToProjectDir(cwd) {
  if (!cwd) return null;

  // Windows path
  if (cwd.includes('\\') || (cwd.length >= 2 && cwd[1] === ':')) {
    // Normalize to backslashes first
    const normalized = cwd.replace(/\//g, '\\');
    // C:\ -> C-- then \ -> -
    return normalized.replace(/:\\/g, '--').replace(/\\/g, '-');
  }

  // Unix path: /home/user -> -home-user
  return cwd.replace(/\//g, '-');
}

/**
 * Find the session JSONL file by walking up directory tree.
 */
function findSessionFile(sessionId, cwd) {
  const home = process.env.USERPROFILE || process.env.HOME || '';
  if (!home || !sessionId) return null;

  const projectsDir = path.join(home, '.claude', 'projects');

  // Try the cwd and parent directories
  let searchPath = cwd.replace(/\//g, '\\'); // normalize

  for (let i = 0; i < 10; i++) {
    const dirName = cwdToProjectDir(searchPath);
    if (!dirName) break;

    const candidate = path.join(projectsDir, dirName, `${sessionId}.jsonl`);
    if (fs.existsSync(candidate)) {
      return candidate;
    }

    // Try parent
    const parent = path.dirname(searchPath);
    if (parent === searchPath) break;
    searchPath = parent;
  }

  return null;
}

/**
 * Scan file in chunks from the end to find the latest usage data.
 * Starts with 64KB, doubles up to 512KB if no usage found.
 * This handles sessions where the tail of the file is non-assistant entries.
 */
function getLatestUsage(filePath) {
  try {
    const stat = fs.statSync(filePath);
    const fd = fs.openSync(filePath, 'r');

    // Try progressively larger chunks from the end
    const chunkSizes = [64 * 1024, 256 * 1024, 512 * 1024];

    for (const maxRead of chunkSizes) {
      const readSize = Math.min(stat.size, maxRead);
      const buffer = Buffer.alloc(readSize);
      fs.readSync(fd, buffer, 0, readSize, stat.size - readSize);

      const content = buffer.toString('utf-8');
      const lines = content.split('\n').filter(l => l.trim());

      // Walk backwards to find the latest usage entry
      for (let i = lines.length - 1; i >= 0; i--) {
        try {
          const entry = JSON.parse(lines[i]);
          const usage = entry?.message?.usage;
          if (usage && (usage.input_tokens !== undefined)) {
            const inputTokens = usage.input_tokens || 0;
            const cacheCreation = usage.cache_creation_input_tokens || 0;
            const cacheRead = usage.cache_read_input_tokens || 0;
            const total = inputTokens + cacheCreation + cacheRead;
            if (total > 0) {
              fs.closeSync(fd);
              return total;
            }
          }
        } catch {
          // Skip unparseable lines
        }
      }

      // If we already read the whole file, stop
      if (readSize >= stat.size) break;
    }

    fs.closeSync(fd);
  } catch {
    // File read error — session just started or path issue
  }

  return null;
}

function getBracket(remaining) {
  if (remaining >= 60) return 'FRESH';
  if (remaining >= 40) return 'MODERATE';
  if (remaining >= 25) return 'DEPLETED';
  return 'CRITICAL';
}

function formatGuidance(bracket, remaining) {
  switch (bracket) {
    case 'FRESH':
      // No injection — save tokens when everything is fine
      return null;

    case 'MODERATE':
      return `CONTEXT: ${remaining}% remaining [MODERATE] — Stay focused, batch operations, avoid unnecessary file reads.`;

    case 'DEPLETED':
      return [
        `⚠️ CONTEXT: ${remaining}% remaining [DEPLETED]`,
        '- Complete current task, then recommend wrapping up',
        '- Summarize progress before switching tasks',
        '- Recommend /compact or fresh session for new work',
        '- Keep responses concise — every token counts now'
      ].join('\n');

    case 'CRITICAL':
      return [
        `🚨 CONTEXT CRITICAL: ${remaining}% remaining`,
        '- STOP accepting new tasks — finish current operation only',
        '- Recommend: /compact or start a fresh session NOW',
        '- If mid-code, complete the current file then stop',
        '- Write session handoff summary if user needs to continue elsewhere'
      ].join('\n');

    default:
      return null;
  }
}

function main() {
  let input;
  try {
    input = JSON.parse(readStdin());
  } catch {
    return;
  }

  // Don't run for subagents — they have their own context
  if (process.env.CLAUDE_AGENT_ID) return;

  const sessionId = input.sessionId || input.session_id || '';
  const cwd = input.cwd || '';

  if (!sessionId || !cwd) return;

  const sessionFile = findSessionFile(sessionId, cwd);
  if (!sessionFile) return; // Fresh session, no file yet

  const totalTokens = getLatestUsage(sessionFile);
  if (!totalTokens) return; // No usage data yet

  const remaining = Math.max(0, 100 - (totalTokens * 100 / MAX_CONTEXT));
  const bracket = getBracket(remaining);
  const guidance = formatGuidance(bracket, Math.round(remaining));

  // FRESH = no injection (save tokens)
  if (!guidance) return;

  console.log(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext: guidance
    }
  }));
}

main();
