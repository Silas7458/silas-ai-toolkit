@echo off
rem REA (Reverse Engineer Anything) CLI - morluto/rea, npm rea-agents.
rem Runs on a private Node 22.23.5 (REA needs >=22.23.4; system Node stays 22.19.0).
rem Installed S#406 2026-11-21. Upgrade: see ~/.claude/skills/rea/SKILL.md
setlocal
set "PATH=%USERPROFILE%\tools\node-22.23.5;%PATH%"
"%USERPROFILE%\tools\node-22.23.5\node.exe" "%USERPROFILE%\tools\rea\node_modules\rea-agents\scripts\rea.mjs" %*
exit /b %ERRORLEVEL%
