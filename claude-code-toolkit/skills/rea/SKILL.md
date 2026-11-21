---
name: rea
description: REA (Reverse Engineer Anything, morluto/rea, npm rea-agents) CLI - static and runtime reverse engineering of shipped software from the terminal. Use when a question depends on a shipped artifact rather than available source - a JavaScript/Electron app or ASAR, a web page's bundle, a Windows/PE, Go, PyInstaller, Deno or .NET binary, an APK, firmware, a Windows .lnk, a browser or Electron scenario capture, or comparing two versions of an app. Trigger on "REA", "reverse engineer", "how does this app work inside", "decompile", "what's in this exe / asar / apk", "compare these two versions", "what endpoints does this site call". Do NOT use for ordinary analysis of a source repo you already have (read the code instead).
---

# REA CLI (Reverse Engineer Anything)

Installed S#406 (2026-11-21). Upstream: https://github.com/morluto/rea (MIT). Version 6.10.1.
Lookalike repos exist (e.g. NabilRFG12/Reverse-Engineer-anything copies the description) - only
use morluto/rea and the npm package `rea-agents`.

## How it is installed (do not "fix" this)

- `rea` on PATH: `%USERPROFILE%\bin\rea.cmd` (cmd/PowerShell) and `%USERPROFILE%\bin\rea` (Git Bash).
- Runs on a PRIVATE Node 22.23.5 at `%USERPROFILE%\tools\node-22.23.5\` because REA needs
  Node >=22.23.4 and the system Node is 22.19.0. The wrapper puts that Node first on PATH for
  REA's process only. Never upgrade the system Node for REA.
- Package: `%USERPROFILE%\tools\rea\node_modules\rea-agents\` (npm --prefix install).
- NO MCP server is registered (the CLI-first rule). Do NOT run `rea setup` - it writes
  `mcpServers.rea` into `~/.claude.json` and a 48 KB skill into `~/.claude/skills`. Ask the owner first.

## Use

```bash
rea --help                        # all commands
rea <command> --help              # options for one command
rea guidance                      # REA's own workflow guidance (search or read)
rea doctor                        # readiness; "healthy: false" is EXPECTED - no native engine installed
```

Common commands:
- `rea analyze-javascript-application <dir-or-.asar> --format json` - static reconstruction of a
  JS/Electron app (modules, imports, routes, IPC, source maps). Tested: a 2-file app in 8 s.
- `rea inspect-artifact <path>` / `rea analyze <path>` - overview of any artifact plus next probes.
- `rea audit-release-exposure <path>` - what static analysis can recover from a shipped build.
- `rea analyze-web-bundle` / `rea capture-browser-scenario` - NETWORK: fetches the live site.
- `rea compare-application-versions`, `rea compare-artifacts` - diff two versions.
- `rea extract-artifact`, `rea extract-firmware` - safe extraction.

Big targets - scope them or they crawl: a 3,400-file folder with node_modules ran 7+ minutes
and was stopped. Use `--source-path <file>` (repeatable) or `--source-paths-json <file>`, and for
large output `--detail summary --evidence_output <new-file>` then `rea inspect-analysis-view`.
Output is NDJSON progress lines then one result line; take the LAST line as the result.
Default format is TOON; pass `--format json` for parsing. Close stdin (`< /dev/null`) in scripts.

## Engines (none installed - each is a separate install, ask the owner first)

Native decompile (`decompile`, `function`, `decompile-all`) needs one of Hopper, Ghidra 12.2+
(`GHIDRA_INSTALL_DIR`; check Ghidra's own JDK requirement - recent Ghidra releases need a newer
JDK than the Corretto 17 on this machine, INFERRED, not checked), IDA or Kuna.
APKs need the jadx-headless-mcp 0.7.1 JAR (`REA_JADX_MCP_JAR`). Static JS, Go, PyInstaller, Deno,
LNK and artifact inspection need nothing extra. `rea setup` can offer to install Hopper - do not.

## Rules

- Only targets the owner owns or is authorized to analyze. Never point it at patient data or client
  systems without explicit permission.
- Everything runs locally except the web/browser capture commands, which contact the target site.
- Tag findings VERIFIED (from REA Evidence) vs INFERRED.

## Upgrade

```bash
export PATH="$HOME/tools/node-22.23.5:$PATH"
npm install -g --prefix "~/tools/rea" rea-agents@<version> --no-fund --no-audit
rea --version && rea doctor
```
Check the new version's `engines.node`; if it needs a newer Node, download the portable zip from
nodejs.org, verify it against SHASUMS256.txt, and update both wrappers. Log it in the debt ledger first.
