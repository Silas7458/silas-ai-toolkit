#!/usr/bin/env node
// Claude Code Statusline v3 — Pacing-aware rate-limit colors + window time-remaining
//
// Shows: model │ context-bar tokens │ cost │ 5h-usage timeLeft  7d-usage timeLeft
//
// KEY INSIGHT: rate-limit colors are based on pacing (used% vs elapsed%), not absolute used%.
// A raw "7d:27%" is meaningless without knowing how far into the window you are.
//   - If 27% used at 10% elapsed → you're burning fast (RED)
//   - If 27% used at 90% elapsed → you're coasting (GREEN)
//
// Runtime: node (NOT bun). Bun cold-start on Windows is ~150ms; node is ~45ms.
// Statusline runs per TUI render, so cold-start directly causes typing lag at scale.
// See debt-ledger 2026-04-20 [S204] for the bun→node swap rationale.
//
// Install:
//   1. Copy this file to ~/.claude/hooks/gsd-statusline.js
//   2. Add to ~/.claude/settings.json:
//        "statusLine": { "type": "command", "command": "node \"<path>/gsd-statusline.js\"" }
//   3. Restart Claude Code (or it may pick up live on next render).

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const model = data.model?.display_name || 'Claude';

    // Context bar — use Claude Code's own used_percentage directly (no scaling)
    let ctx = '';
    const used = data.context_window?.used_percentage;
    if (used != null) {
      const filled = Math.floor(used / 10);
      const bar = '\u2588'.repeat(filled) + '\u2591'.repeat(10 - filled);

      if (used < 50)       ctx = ` \x1b[32m${bar} ${used}%\x1b[0m`;
      else if (used < 70)  ctx = ` \x1b[33m${bar} ${used}%\x1b[0m`;
      else if (used < 90)  ctx = ` \x1b[38;5;208m${bar} ${used}%\x1b[0m`;
      else                 ctx = ` \x1b[5;31m\ud83d\udc80 ${bar} ${used}%\x1b[0m`;
    }

    // Token meter — use current_usage which has the REAL numbers (including cache)
    let tokenMeter = '';
    const cu = data.context_window?.current_usage;
    if (cu) {
      const totalTokens = (cu.input_tokens || 0)
        + (cu.output_tokens || 0)
        + (cu.cache_creation_input_tokens || 0)
        + (cu.cache_read_input_tokens || 0);
      const totalK = Math.round(totalTokens / 1000);
      tokenMeter = ` \x1b[34m${totalK}K tok\x1b[0m`;
    }

    // Session cost — from cost.total_cost_usd
    let costMeter = '';
    const cost = data.cost?.total_cost_usd;
    if (cost != null) {
      const formatted = cost < 10 ? cost.toFixed(2) : cost.toFixed(1);
      // Color by cost: green < $2, yellow < $5, orange < $10, red >= $10
      if (cost < 2)       costMeter = ` \x1b[32m$${formatted}\x1b[0m`;
      else if (cost < 5)  costMeter = ` \x1b[33m$${formatted}\x1b[0m`;
      else if (cost < 10) costMeter = ` \x1b[38;5;208m$${formatted}\x1b[0m`;
      else                costMeter = ` \x1b[31m$${formatted}\x1b[0m`;
    }

    // Rate limits — pacing-aware color + time-remaining in window
    // Color is based on used% vs elapsed% of the window, not absolute used%.
    //   ratio = used_pct / elapsed_pct
    //   < 0.9: green   (underpacing — plenty of headroom)
    //   0.9–1.1: yellow (on pace)
    //   1.1–1.5: orange (overpacing — will exhaust window early)
    //   > 1.5: red     (burning fast)
    // Early in the window (<5% elapsed) pacing is noisy, so fall back to absolute.
    function formatWindow(label, win, durationSec) {
      if (win?.used_percentage == null) return null;
      const pct = Math.round(win.used_percentage);
      const resetAt = win.resets_at;
      const nowSec = Math.floor(Date.now() / 1000);

      let color;
      let rem = '';
      if (resetAt != null) {
        const remainSec = Math.max(0, resetAt - nowSec);
        const elapsedSec = Math.max(0, durationSec - remainSec);
        const pctElapsed = (elapsedSec / durationSec) * 100;

        if (pctElapsed < 5) {
          color = pct < 10 ? '32' : pct < 25 ? '33' : pct < 50 ? '38;5;208' : '31';
        } else {
          const ratio = pct / pctElapsed;
          if (ratio < 0.9) color = '32';
          else if (ratio < 1.1) color = '33';
          else if (ratio < 1.5) color = '38;5;208';
          else color = '31';
        }

        // Format remaining: 5h window → "Nh Mm"; 7d window → "Nd Nh" (or "Nh" if <1d)
        if (durationSec <= 24 * 3600) {
          const h = Math.floor(remainSec / 3600);
          const m = Math.floor((remainSec % 3600) / 60);
          rem = ` \x1b[2m${h}h${m}m left\x1b[0m`;
        } else {
          const d = Math.floor(remainSec / 86400);
          const h = Math.floor((remainSec % 86400) / 3600);
          rem = ` \x1b[2m${d > 0 ? `${d}d${h}h` : `${h}h`} left\x1b[0m`;
        }
      } else {
        // Fallback: no reset timestamp → absolute-usage coloring
        color = pct < 50 ? '32' : pct < 75 ? '33' : pct < 90 ? '38;5;208' : '31';
      }

      return `\x1b[${color}m${label}:${pct}%\x1b[0m${rem}`;
    }

    let rateMeter = '';
    const rl = data.rate_limits;
    if (rl?.five_hour || rl?.seven_day) {
      const parts = [];
      const p5 = formatWindow('5h', rl.five_hour, 5 * 3600);
      const p7 = formatWindow('7d', rl.seven_day, 7 * 86400);
      if (p5) parts.push(p5);
      if (p7) parts.push(p7);
      if (parts.length) rateMeter = ` \u2502 ${parts.join('  ')}`;
    }

    process.stdout.write(`\x1b[2m${model}\x1b[0m \u2502${ctx}${tokenMeter} \u2502${costMeter}${rateMeter}`);
  } catch { /* silent */ }
});
