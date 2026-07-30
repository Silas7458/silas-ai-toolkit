# nano-banana

Direct Nano Banana (Gemini image API) pipeline - generate and iterate character/concept art from the CLI, bypassing the gemini.google.com web UI.

## Setup

Needs GEMINI_API_KEY in the environment or in `~/.gemini/.env` (paid-tier Gemini API key).

## Usage

```
# Generate
node nano-banana.mjs "a weathered Roman centurion, cinematic film still" --name marcus --ar 2:3

# Iterate with character consistency (pass previous renders / references)
node nano-banana.mjs "same man, now smiling, closer crop" --ref out/marcus-1.jpg --name marcus-v2
```

Options: --ref (repeatable, up to 14 on Pro), --model (default gemini-3-pro-image; fast: gemini-3.1-flash-image), --out, --name, --ar (1:1 2:3 16:9 ...), --size (1K/2K/4K, Pro), --timeout <s>, --retries <n>, --no-open.

## Gotchas

- The API sometimes holds a connection open indefinitely; every attempt has a hard timeout + retry.
- Claude Code Bash sandbox HANGS (not errors) node fs writes under C:/Users/<user>/Pictures - default output is tool-local `out/`, use Documents for project art.
