---
name: craft-anything-cli
description: Craft Anything (storytold/craft-anything) CLI - 323 inspection and build tools for understanding how a piece of software works and crafting your own version - native PE/ELF/Mach-O, JavaScript, browser pages, Android, Java, .NET, file formats, runtime tracing. Use when the owner says "Craft Anything", "craft-anything-cli", "study this app and build my own", "clean-room rebuild", or wants a target opened and inspected with Craft's tools. For pure static reverse engineering of an artifact, REA (skill `rea`) is the other option; pick the one the owner names.
---

# Craft Anything CLI

Installed S#406 (2026-11-21). Upstream: https://github.com/storytold/craft-anything (MIT / Apache-2.0).
Version 0.6.1, Windows x64 portable build. Lookalikes exist (e.g. auraecosystem/CRaft-Anything-cli,
0 stars) - only use storytold/craft-anything releases.

## How it is installed

- `craft-anything-cli` on PATH: `%USERPROFILE%\bin\craft-anything-cli.cmd` (cmd/PowerShell) and
  `%USERPROFILE%\bin\craft-anything-cli` (Git Bash).
- Files: `%USERPROFILE%\tools\craft-anything\craft-anything-0.6.1-windows-x64-portable\`
  (`craft-anything-cli.exe`, plus `craft-anything.exe`, the desktop app). Portable: settings live
  next to the app. SHA256 matched SHA256SUMS.txt, GPG signature good, both exes Authenticode-signed
  by Learning Machines Inc.
- NOT registered with any agent (the CLI-first rule). Do NOT run `craft-anything-cli setup` -
  it registers an MCP server and a skill in Claude Code / Claude Desktop / Codex / Gemini etc.
  ask the owner first.

## Use

```bash
craft-anything-cli commands                  # JSON list of every tool (command, toolset, summary)
craft-anything-cli <tool> --help             # options for one tool
craft-anything-cli doctor                    # install, engines, MCP self-test (healthy: true at install)
craft-anything-cli --deep core-target-open --path "C:/path/to/target.exe" --output-format text
```

- **Clean room is the default and refuses to look inside a target** ("This looks inside the
  original ... which Clean room never does"). Pass `--deep` (before the tool name) to inspect.
  Clean room is for rebuilding without reading the original's code; Deep is for studying it.
- Output: `--output-format json|jsonl|md|text` (a tool's own `--format` is a different option).
- Toolsets: core 37, native 55, formats 36, projects 29, adb 24, browser 22, setup 20,
  application 17, runtime 14, apple 14, android 14, javascript 11, frida 9, managed 8, build 6,
  java 6, database 1.
- Tested: `--deep core-target-open` on whoami.exe returned kind pe, sha256, target id.

## Engines found / missing at install

Found: Chrome (browser tools), Java 17 (Corretto). Missing (all optional): Ghidra, adb, JADX,
Apktool, Frida, GDB, mitmproxy, Binwalk, Unblob, ILSpy, tshark, objdump, Rizin, Vineflower.
No AI backend configured (`craft-anything-cli ai detect` / `ai add`) - not needed for the tools.
Each engine is a separate install: ask the owner first.

## Builder mode (the desktop app's Study -> Build -> Check -> Ready)

The desktop app runs the local `claude` binary headless (`claude -p ... --mcp-config`) on the owner's
own Claude sign-in and usage, with its own approval tool. Builders can run `npm install` etc. in the
project folder. Only start a build when the owner asks; tell the owner it bills their Claude usage.

## Rules

- Only targets the owner owns or is authorized to study (your own software, or written permission). No patient data or client
  systems without explicit permission.
- Browser tools contact the target site; native/format tools are local.
- Tag findings VERIFIED (tool output) vs INFERRED.

## Upgrade

Download the new `craft-anything-<ver>-windows-x64-portable.zip` + `SHA256SUMS.txt` with
`gh release download v<ver> -R storytold/craft-anything`, verify the hash, extract to
`%USERPROFILE%\tools\craft-anything\`, update the path in both wrappers, run `doctor`.
Log it in the debt ledger first.
