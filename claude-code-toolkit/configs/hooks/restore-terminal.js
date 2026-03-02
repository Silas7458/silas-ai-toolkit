// PostToolUse hook: restores Windows Terminal window if minimized
// Fires after any mcp__windows-mcp__ tool call to prevent team blindness
// Uses Python ctypes (Win32 API) — PowerShell .NET interop is unreliable in Claude Code
// Created 2026-02-15 — PERMANENT FIX for Brother minimizing his terminal

const { execFileSync } = require('child_process');

const pyScript = [
  'import ctypes',
  'u = ctypes.windll.user32',
  'h = u.FindWindowW("CASCADIA_HOSTING_WINDOW_CLASS", None)',
  'if h and u.IsIconic(h): u.ShowWindow(h, 9)'
].join('\n');

try {
  execFileSync('python', ['-c', pyScript], {
    timeout: 3000,
    stdio: 'ignore',
    windowsHide: true
  });
} catch (e) {
  // Silent fail — never break the session over a window restore
}
