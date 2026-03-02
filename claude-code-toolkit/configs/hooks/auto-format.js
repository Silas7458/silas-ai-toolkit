#!/usr/bin/env node
// Auto-format hook: runs prettier on files after Write/Edit if project has prettier configured
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

try {
  const input = JSON.parse(fs.readFileSync('/dev/stdin', 'utf8'));
  const filePath = input.tool_input?.file_path;
  if (!filePath) process.exit(0);

  // Only format code files
  const ext = path.extname(filePath).toLowerCase();
  const formatExts = ['.js', '.jsx', '.ts', '.tsx', '.css', '.json', '.html', '.vue', '.svelte'];
  if (!formatExts.includes(ext)) process.exit(0);

  // Check if prettier is available in the project
  const dir = path.dirname(filePath);
  try {
    execSync(`npx prettier --check "${filePath}" 2>/dev/null`, { cwd: dir, timeout: 5000, stdio: 'pipe' });
  } catch {
    // File needs formatting — format it
    try {
      execSync(`npx prettier --write "${filePath}" 2>/dev/null`, { cwd: dir, timeout: 5000, stdio: 'pipe' });
    } catch { /* prettier not available or failed — skip silently */ }
  }
} catch { /* skip on any error */ }
