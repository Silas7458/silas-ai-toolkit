# GSD Statusline (v3)

Pacing-aware Claude Code statusline with rate-limit window awareness.

## What it shows

```
Opus 4.7 (1M context) │ █░░░░░░░░░ 15% 152K tok │ $4.33 │ 5h:6% 3h38m left  7d:27% 3d3h left
```

Left to right:
- **Model name** (dim)
- **Context bar** — 10-block bar + percentage, colored by absolute usage
- **Token meter** — total tokens used this session (input + output + cache create/read)
- **Session cost** — cumulative USD, colored by amount
- **Rate limits** — 5h and 7d window usage %, plus time-remaining until reset

## The key innovation — pacing-aware rate-limit colors

Previous statuslines colored rate-limit % by absolute thresholds (`<50% green, <75% yellow, ...`).
That tells you nothing useful. **A raw `7d:27%` is meaningless without knowing how far into the window you are.**

- 27% used at **10%** elapsed → burning fast. BAD. Should be RED.
- 27% used at **90%** elapsed → coasting. GREAT. Should be GREEN.

This statusline reads `rate_limits.{five_hour,seven_day}.resets_at` (unix timestamps provided by
Claude Code) to compute elapsed%, then colors based on **pacing ratio = used% / elapsed%**:

| Ratio       | Meaning                        | Color  |
|-------------|--------------------------------|--------|
| < 0.9       | Underpacing, plenty of headroom| Green  |
| 0.9 – 1.1   | On pace                        | Yellow |
| 1.1 – 1.5   | Overpacing, will exhaust early | Orange |
| > 1.5       | Burning fast                   | Red    |

In the first 5% of a window (pacing ratio is noisy when elapsed is tiny), it falls back
to absolute-usage coloring.

## Why node, not bun

Statuslines run **per TUI render** — can be many times per second while typing. Runtime cold-start
cost directly causes input lag.

| Runtime | Cold-start (Windows) |
|---------|---------------------|
| bun     | ~144ms (127–176ms)  |
| node    | ~46ms (41–54ms)     |

3.1× speedup. The shebang is `#!/usr/bin/env node` and the settings.json command must be `node`
(not `bun`), otherwise you get the cold-start penalty on every keystroke.

## Install

1. Copy `gsd-statusline.js` to `~/.claude/hooks/gsd-statusline.js` (any path works — match step 2).
2. Add to `~/.claude/settings.json`:
   ```json
   "statusLine": {
     "type": "command",
     "command": "node \"C:/Users/silas/.claude/hooks/gsd-statusline.js\""
   }
   ```
3. Restart Claude Code (or just start a new turn — it picks up live).

## Troubleshooting

**Input lag.** Check that the settings.json command is `node`, not `bun`. If you see `bun` and typing
is laggy, that's the cause — bun cold-start on Windows is ~150ms per render.

**Rate-limit section missing.** The `rate_limits` field is only present once you've made enough
calls in the current 5h/7d windows for the API to return quota. On a fresh account or fresh window
it will be absent — the statusline silently omits that section.

**"X left" not showing.** Means `rate_limits.five_hour.resets_at` was null in the input — older
Claude Code versions may not have it. The percentage still shows with fallback absolute coloring.

## JSON input reference

The statusline receives this on stdin each render (trimmed to relevant fields):

```json
{
  "model": { "display_name": "Opus 4.7 (1M context)" },
  "context_window": {
    "used_percentage": 15,
    "current_usage": {
      "input_tokens": 1,
      "output_tokens": 82,
      "cache_creation_input_tokens": 319,
      "cache_read_input_tokens": 141950
    }
  },
  "cost": { "total_cost_usd": 4.33 },
  "rate_limits": {
    "five_hour":  { "used_percentage": 6,  "resets_at": 1776711600 },
    "seven_day":  { "used_percentage": 27, "resets_at": 1776970800 }
  }
}
```

## History

- **v1** — model + task + dir + context usage (original)
- **v2** — 1M-context-aware context bar + accurate token/cost meter, replaced v1
- **v3** (2026-04-20) — pacing-aware rate-limit colors + window time-remaining, node runtime
