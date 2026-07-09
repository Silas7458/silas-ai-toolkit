# stage-out.ps1
# One-command offline migration staging: mirrors this laptop's data onto the
# encrypted MIGRATION drive as a browsable category tree, captures non-file
# system state, writes SHA-256 manifests, and verifies every copied file
# against its source hash.
#
# Usage:  pwsh -File stage-out.ps1            (full run + verify)
#         pwsh -File stage-out.ps1 -SkipVerify (copy only, no hash pass)
# Re-runs are incremental (robocopy /MIR keeps the drive a true mirror).

param(
    [string]$DriveLetter = '',
    [switch]$SkipVerify
)

$ErrorActionPreference = 'Continue'
$HOME_DIR = 'C:\Users\silas'
# Stable path (NOT session scratchpad) so scheduled/future runs can always write it
$statusFile = 'C:\Users\silas\scripts\migration\last-run-status.txt'
$startTime = Get-Date

# ---------------------------------------------------------------- target
if (-not $DriveLetter) {
    $vol = Get-Volume | Where-Object { $_.FileSystemLabel -eq 'MIGRATION' -and $_.DriveLetter }
    if (-not $vol) { Set-Content $statusFile 'FAILED: no volume labeled MIGRATION found'; exit 1 }
    $DriveLetter = $vol.DriveLetter
}
$ROOT = "${DriveLetter}:\MIGRATION"
$LOGDIR = Join-Path $ROOT ('00-RUNBOOK\logs\' + (Get-Date -Format 'yyyy-MM-dd_HHmm'))
$MANDIR = Join-Path $ROOT '00-RUNBOOK\manifests'
New-Item -ItemType Directory -Force -Path $LOGDIR, $MANDIR | Out-Null

function Log([string]$msg) {
    $line = ('[{0}] {1}' -f (Get-Date -Format 'HH:mm:ss'), $msg)
    Write-Host $line
    Add-Content -Path (Join-Path $LOGDIR 'stage-out.log') -Value $line
}

# Junk excluded EVERYWHERE (regenerable build/dependency caches). This is the
# only deliberate omission in the whole tree - documented in RESTORE.md.
$JUNK_DIRS = @('node_modules', '__pycache__', '.venv', '.next', '.turbo', '$RECYCLE.BIN', 'System Volume Information')

# ---------------------------------------------------------------- job list
# Each job: DestRel (folder on drive) + Src (folder on laptop). Verify pass
# maps dest files back to Src by relative path.
$jobs = New-Object System.Collections.ArrayList

function Add-Job([string]$destRel, [string]$src) {
    if (Test-Path -LiteralPath $src) {
        [void]$jobs.Add(@{ DestRel = $destRel; Src = $src })
    } else {
        Log ("SKIP (missing): " + $src)
    }
}

# 01-USER : personal file trees, structure preserved exactly
foreach ($d in @('Documents','Desktop','Downloads','Pictures','Videos','Music','Favorites','Contacts','Saved Games')) {
    Add-Job ("01-USER\" + $d) (Join-Path $HOME_DIR $d)
}

# 02-REPOS : every top-level git repo (enumerated live, never hardcoded)
Get-ChildItem -LiteralPath $HOME_DIR -Directory | Where-Object {
    Test-Path (Join-Path $_.FullName '.git')
} | ForEach-Object {
    Add-Job ("02-REPOS\" + $_.Name) $_.FullName
}

# 03-SCRIPTS : automation + tools (includes the KanTime worker + its creds)
foreach ($d in @('scripts','tools','bin')) {
    Add-Job ("03-SCRIPTS\" + $d) (Join-Path $HOME_DIR $d)
}

# 09-ONEDRIVE : full OneDrive tree. Silas plans to DELETE OneDrive, so this
# content does NOT survive via cloud. Note: shell-Documents (where Word/Excel
# save dialogs point) is KFM-redirected to OneDrive\Documents - it is the real
# "Documents" for GUI apps, separate from the literal C:\Users\silas\Documents.
Add-Job '09-ONEDRIVE' (Join-Path $HOME_DIR 'OneDrive')

# 04-CONFIGS : every dot-directory in the profile except regenerable caches
$DOT_EXCLUDE = @('.cache','.npm','.nuget','.gradle','.docker','.ollama','.rustup','.cargo','.vscode','.android','.conda','.lmstudio')
Get-ChildItem -LiteralPath $HOME_DIR -Directory -Force | Where-Object {
    $_.Name -like '.*'
} | ForEach-Object {
    if ($DOT_EXCLUDE -contains $_.Name) { Log ("SKIP (regenerable cache): " + $_.Name) }
    else { Add-Job ("04-CONFIGS\" + $_.Name) $_.FullName }
}

# 07-APPDATA : selective app state worth keeping (caches excluded)
Add-Job '07-APPDATA\Code'          (Join-Path $HOME_DIR 'AppData\Roaming\Code')
Add-Job '07-APPDATA\Chrome'        (Join-Path $HOME_DIR 'AppData\Local\Google\Chrome\User Data')
Add-Job '07-APPDATA\Edge'          (Join-Path $HOME_DIR 'AppData\Local\Microsoft\Edge\User Data')
Add-Job '07-APPDATA\Mozilla'       (Join-Path $HOME_DIR 'AppData\Roaming\Mozilla')
Add-Job '07-APPDATA\Obsidian'      (Join-Path $HOME_DIR 'AppData\Roaming\obsidian')

# 08-OTHER : any top-level folder not already covered (completeness net)
$covered = @('AppData','Application Data','OneDrive','Searches','Links','3D Objects',
             'Documents','Desktop','Downloads','Pictures','Videos','Music','Favorites','Contacts','Saved Games',
             'scripts','tools','bin')
Get-ChildItem -LiteralPath $HOME_DIR -Directory | Where-Object {
    ($covered -notcontains $_.Name) -and
    ($_.Name -notlike '.*') -and
    (-not (Test-Path (Join-Path $_.FullName '.git')))
} | ForEach-Object {
    Add-Job ("08-OTHER\" + $_.Name) $_.FullName
}

# ---------------------------------------------------------------- robocopy
$APPDATA_CACHE_XD = @('*Cache*','GPUCache','Code Cache','CachedData','ShaderCache','DawnCache','Crashpad','logs','CachedExtensions','component_crx_cache')
$failedJobs = @()
$jobNum = 0
foreach ($j in $jobs) {
    $jobNum++
    $dest = Join-Path $ROOT $j.DestRel
    $logf = Join-Path $LOGDIR (($j.DestRel -replace '[\\:]', '_') + '.log')
    $args = @($j.Src, $dest, '/MIR', '/COPY:DAT', '/DCOPY:DAT', '/XJ', '/R:1', '/W:1', '/MT:16',
              '/NFL', '/NDL', '/NP', ('/LOG+:' + $logf), '/XF', 'NTUSER.DAT*', 'ntuser*', '.849C9593*')
    $xd = @($JUNK_DIRS)
    if ($j.DestRel -like '07-APPDATA*') {
        $xd += $APPDATA_CACHE_XD
        # live-browser lock markers: always locked while the browser runs, zero data value
        $args += @('parent.lock', 'lockfile', 'LOCK', '.parentlock')
    }
    $args += '/XD'; $args += $xd
    Log ("[{0}/{1}] robocopy {2} -> {3}" -f $jobNum, $jobs.Count, $j.Src, $j.DestRel)
    & robocopy @args | Out-Null
    if ($LASTEXITCODE -ge 8) {
        Log ("  FAILED (exit {0}) - see {1}" -f $LASTEXITCODE, $logf)
        $failedJobs += $j.DestRel
    }
}

# Loose top-level files in the profile root
$looseDest = Join-Path $ROOT '08-OTHER\_profile-root-files'
New-Item -ItemType Directory -Force -Path $looseDest | Out-Null
Get-ChildItem -LiteralPath $HOME_DIR -File -Force | Where-Object {
    $_.Name -notlike 'NTUSER*' -and $_.Name -notlike 'ntuser*' -and $_.Name -ne '.brother-session.lock'
} | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $looseDest -Force -ErrorAction SilentlyContinue
}

# ---------------------------------------------------------------- 06-SYSTEM-STATE
Log 'Capturing system state (non-file machine state)...'
$SYS = Join-Path $ROOT '06-SYSTEM-STATE'
New-Item -ItemType Directory -Force -Path $SYS, (Join-Path $SYS 'scheduled-tasks'), (Join-Path $SYS 'wifi-profiles') | Out-Null

try { winget export -o (Join-Path $SYS 'winget-packages.json') --accept-source-agreements 2>&1 | Out-Null; Log '  winget export OK' } catch { Log ('  winget export FAILED: ' + $_.Exception.Message) }
try { npm ls -g --depth=0 2>$null | Out-File (Join-Path $SYS 'npm-globals.txt'); Log '  npm globals OK' } catch { Log '  npm globals FAILED' }
try { & py -m pip list --format=freeze 2>$null | Out-File (Join-Path $SYS 'pip-freeze.txt'); Log '  pip freeze OK' } catch { Log '  pip freeze FAILED' }
try { git config --global --list 2>$null | Out-File (Join-Path $SYS 'git-global-config.txt') } catch {}
Get-ChildItem Env: | ForEach-Object { ($_.Name + '=' + $_.Value) } | Out-File (Join-Path $SYS 'env-vars.txt')
try { Copy-Item 'C:\Windows\System32\drivers\etc\hosts' (Join-Path $SYS 'hosts.txt') -ErrorAction SilentlyContinue } catch {}
try {
    Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
                     'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
                     'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName } | Sort-Object DisplayName |
        Select-Object DisplayName, DisplayVersion, Publisher |
        Out-File (Join-Path $SYS 'installed-programs.txt')
} catch {}

$taskFail = 0
Get-ScheduledTask | Where-Object { $_.TaskPath -eq '\' -and $_.Author -notlike 'Microsoft*' } | ForEach-Object {
    try {
        Export-ScheduledTask -TaskName $_.TaskName -TaskPath $_.TaskPath |
            Out-File (Join-Path $SYS ('scheduled-tasks\' + ($_.TaskName -replace '[^A-Za-z0-9 ._-]','_') + '.xml'))
    } catch { $taskFail++ }
}
Log ("  scheduled tasks exported (failures: {0})" -f $taskFail)

try {
    netsh wlan export profile key=clear folder=(Join-Path $SYS 'wifi-profiles') 2>&1 | Out-Null
    Log '  wifi profiles exported (with keys if permitted)'
} catch { Log '  wifi profile export FAILED (may need admin for key=clear)' }

# 05-SECRETS : pointer file for the things Windows will not export by script
$SEC = Join-Path $ROOT '05-SECRETS'
New-Item -ItemType Directory -Force -Path $SEC | Out-Null
$secLines = @(
    'SECRETS - MANUAL EXPORT CHECKLIST',
    '=================================',
    'Most credentials already travel inside other categories:',
    '  - council-config.json      -> 01-USER\Documents\claude-context\',
    '  - repo .env files          -> 02-REPOS\<repo>\',
    '  - KanTime worker creds     -> 03-SCRIPTS\scripts\kantime\',
    '  - gws / gws-azalea auth    -> 04-CONFIGS\.config\',
    '  - SSH keys                 -> 04-CONFIGS\.ssh\',
    '',
    'CANNOT be exported by script - do these by hand before destroying the laptop:',
    '  1. Browser saved passwords: Chrome/Edge -> Settings -> Passwords -> Export -> save CSV into this folder.',
    '  2. Windows Credential Manager: no plaintext export exists. Run cmdkey /list, note entries, re-create on the new machine.',
    '  3. Any authenticator apps / hardware tokens are outside this drive''s scope.',
    '',
    'Wi-Fi profiles (with keys) attempted automatically -> 06-SYSTEM-STATE\wifi-profiles\'
)
Set-Content -Path (Join-Path $SEC 'SECRETS-README.txt') -Value $secLines

# ---------------------------------------------------------------- RESTORE.md
$restore = @'
# RESTORE RUNBOOK - new laptop

REBUILDING BROTHER (Claude Code)? Start with BROTHER-REVIVAL.md in this folder.
It is the full resurrection procedure (identity, programs, Docker, tasks,
re-auth, verification). This file is the raw file-mapping reference behind it.

Unlock this drive with the BitLocker password (recovery key is the backup).

Order of operations:
1. Install programs:  winget import 06-SYSTEM-STATE\winget-packages.json
   (cross-check 06-SYSTEM-STATE\installed-programs.txt for anything winget missed)
2. Copy categories home (paths mirror the old machine, C:\Users\silas):
   01-USER\*      -> C:\Users\<you>\<same folder name>
   02-REPOS\*     -> C:\Users\<you>\<repo name>   then run npm install / pip install per repo
   03-SCRIPTS\*   -> C:\Users\<you>\scripts|tools|bin
   04-CONFIGS\*   -> C:\Users\<you>\<same dot-folder name>
   07-APPDATA\Code    -> AppData\Roaming\Code
   07-APPDATA\Chrome  -> AppData\Local\Google\Chrome\User Data
   07-APPDATA\Edge    -> AppData\Local\Microsoft\Edge\User Data
   07-APPDATA\Mozilla -> AppData\Roaming\Mozilla
   07-APPDATA\Obsidian-> AppData\Roaming\obsidian
   08-OTHER\*     -> C:\Users\<you>\<same name> (loose profile-root files in _profile-root-files)
   09-ONEDRIVE\Documents -> merge into C:\Users\<you>\Documents (on the old machine this was
                            OneDrive shell-Documents, where GUI apps saved by default)
3. Global packages: re-install from 06-SYSTEM-STATE\npm-globals.txt and pip-freeze.txt
4. Scheduled tasks: for each XML in 06-SYSTEM-STATE\scheduled-tasks\:
   Register-ScheduledTask -TaskName <name> -Xml (Get-Content <file> -Raw)
   (fix any hardcoded paths/user SIDs inside the XML first)
5. Wi-Fi: netsh wlan add profile filename=<xml>  for each file in 06-SYSTEM-STATE\wifi-profiles
6. Secrets: work through 05-SECRETS\SECRETS-README.txt
7. Re-auth cloud services (they were never on this drive): GitHub/GitLab, Vercel, Neon,
   Google (gws + gws-azalea), NotebookLM, Discord bot, Anthropic/Claude Code.
8. Verify integrity: manifests in 00-RUNBOOK\manifests are SHA-256 over every staged file.

Deliberate omissions (regenerable): node_modules, __pycache__, .venv, .next, .turbo,
dependency caches (.npm/.nuget/.cargo/...), browser caches,
AppData beyond the five folders above. Databases live in Neon (cloud) - not on this drive.
'@
Set-Content -Path (Join-Path $ROOT '00-RUNBOOK\RESTORE.md') -Value $restore

# Brother revival runbook: canonical copy lives next to this script; refresh
# the drive copy every run so the launch codes are always current.
$revivalSrc = Join-Path $PSScriptRoot 'BROTHER-REVIVAL.md'
if (Test-Path -LiteralPath $revivalSrc) {
    Copy-Item -LiteralPath $revivalSrc -Destination (Join-Path $ROOT '00-RUNBOOK\BROTHER-REVIVAL.md') -Force
    Log 'BROTHER-REVIVAL.md refreshed on drive'
} else {
    Log 'WARN: BROTHER-REVIVAL.md not found next to stage-out.ps1 - drive copy not refreshed'
}

# ---------------------------------------------------------------- manifest + verify
$totalFiles = 0; $totalBytes = 0; $mismatches = @(); $hashErrors = 0
if (-not $SkipVerify) {
    Log 'Hashing destination + verifying against source (this is the long part)...'
    foreach ($j in $jobs) {
        $dest = Join-Path $ROOT $j.DestRel
        if (-not (Test-Path -LiteralPath $dest)) { continue }
        $manifest = Join-Path $MANDIR (($j.DestRel -replace '[\\:]', '_') + '.sha256')
        $sw = New-Object System.IO.StreamWriter($manifest, $false)
        Get-ChildItem -LiteralPath $dest -Recurse -File -Force -ErrorAction SilentlyContinue | ForEach-Object {
            $rel = $_.FullName.Substring($dest.Length + 1)
            try {
                $dh = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
                $sw.WriteLine($dh + '  ' + $rel)
                $totalFiles++; $totalBytes += $_.Length
                $srcFile = Join-Path $j.Src $rel
                if (Test-Path -LiteralPath $srcFile) {
                    $sh = (Get-FileHash -LiteralPath $srcFile -Algorithm SHA256 -ErrorAction Stop).Hash
                    if ($sh -ne $dh) { $mismatches += ($j.DestRel + '\' + $rel) }
                }
                # source file gone since copy = fine (it changed after snapshot)
            } catch { $hashErrors++ }
        }
        $sw.Close()
        Log ("  verified {0}" -f $j.DestRel)
    }
}

# ---------------------------------------------------------------- summary
$mins = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
$gb = [math]::Round($totalBytes / 1GB, 2)
$summary = @(
    ('Stage-out finished: ' + (Get-Date -Format s)),
    ('Duration: ' + $mins + ' min'),
    ('Jobs: ' + $jobs.Count + '  robocopy failures: ' + $failedJobs.Count),
    ('Files hashed: ' + $totalFiles + ' (' + $gb + ' GB)  hash errors: ' + $hashErrors),
    ('Hash mismatches vs source: ' + $mismatches.Count)
)
if ($failedJobs.Count -gt 0) { $summary += ('Failed jobs: ' + ($failedJobs -join ', ')) }
if ($mismatches.Count -gt 0) { $summary += ('Mismatched files: ' + (($mismatches | Select-Object -First 20) -join '; ')) }
$summary | ForEach-Object { Log $_ }
Set-Content -Path (Join-Path $ROOT '00-RUNBOOK\STAGING-REPORT.txt') -Value $summary

if ($failedJobs.Count -eq 0 -and $mismatches.Count -eq 0) {
    Set-Content $statusFile ('SUCCESS files=' + $totalFiles + ' gb=' + $gb + ' mins=' + $mins + ' hashErrors=' + $hashErrors)
} else {
    Set-Content $statusFile ('PARTIAL failures=' + $failedJobs.Count + ' mismatches=' + $mismatches.Count + ' files=' + $totalFiles + ' gb=' + $gb + ' mins=' + $mins)
}
