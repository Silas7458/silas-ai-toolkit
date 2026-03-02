# compile-proctor-briefing.ps1
# Compiles last 5 Proctor session snapshots into briefing-proctor.md
# Runs as scheduled task — replaces the old "morning brief" concept

$snapshotDir = "{{DOCS_DIR}}\claude-context\session-snapshots"
$outputFile = "{{DOCS_DIR}}\claude-context\briefings\briefing-proctor.md"

# Get last 5 Proctor snapshots (newest first)
$snapshots = Get-ChildItem -Path $snapshotDir -Filter "*-proctor-session-*.md" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 5

$timestamp = Get-Date -Format "yyyy-MM-dd h:mm tt"

if ($snapshots.Count -eq 0) {
    # No snapshots yet — write a minimal placeholder
    @"
# Proctor Session Trajectory
*Compiled: $timestamp — No snapshots found yet.*

Proctor has not written any session snapshots. On shutdown, Proctor should write a snapshot to:
``session-snapshots/{YYYY-MM-DD}T{HH-MM}-proctor-session-{N}.md``

Once snapshots exist, this file will auto-populate with the last 5 sessions.
"@ | Set-Content -Path $outputFile -Encoding UTF8
    exit 0
}

# Build the compiled briefing
$header = @"
# Proctor Session Trajectory — Last 5 Sessions
*Auto-compiled: $timestamp | $($snapshots.Count) snapshots*

Use this for trajectory context on startup. Session-state.md is the primary source of truth for current status.

---

"@

$body = ""
foreach ($snap in $snapshots) {
    $content = Get-Content -Path $snap.FullName -Raw
    $body += $content.TrimEnd() + "`n`n---`n`n"
}

($header + $body.TrimEnd()) | Set-Content -Path $outputFile -Encoding UTF8
