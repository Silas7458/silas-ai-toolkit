# run-http.ps1 - obsidian-canon MCP server in HTTP mode + the ngrok tunnel in front of it.
# Launched hidden by the Scheduled Task "Obsidian Canon HTTP" at logon (S#343, 2026-09-23).
# Stays alive while BOTH children live; if either dies it kills the other and exits 1 so the
# task's restart-on-failure relaunches the pair. Manual: powershell -File run-http.ps1
# Stop:  powershell -File stop-http.ps1
$ErrorActionPreference = "Continue"
$here    = Split-Path -Parent $MyInvocation.MyCommand.Path
$stateDir = Join-Path $env:USERPROFILE ".obsidian-canon"
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

$port      = 8790
$node      = "C:\Program Files\nodejs\node.exe"
$ngrok     = "C:\Users\silas\tools\ngrok\ngrok.exe"
$domainFile = Join-Path $stateDir "ngrok-domain.txt"   # one line: the static domain, e.g. xxxx.ngrok-free.app
$urlFile   = Join-Path $stateDir "public-url.txt"      # written on every start: https://<domain>/mcp/<secret>
$secretFile = Join-Path $stateDir "http-secret"
$runLog    = Join-Path $stateDir "run-http.log"
$srvOut    = Join-Path $stateDir "server-http.out"
$srvErr    = Join-Path $stateDir "server-http.err"
$ngOut     = Join-Path $stateDir "ngrok.out"
$ngErr     = Join-Path $stateDir "ngrok.err"

function Log($msg) {
    $line = (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "  " + $msg
    Add-Content -Path $runLog -Value $line
}

if (-not (Test-Path $secretFile)) { Log "FATAL no secret file $secretFile"; exit 2 }
$secret = (Get-Content $secretFile -Raw).Trim()

# one instance only (kills a previous HTTP node + ngrok; never touches Proctor's stdio instance)
& (Join-Path $here "stop-http.ps1") | Out-Null

Log "starting server on 127.0.0.1:$port"
$env:OBSIDIAN_CANON_HTTP_PORT = "$port"
$srv = Start-Process -FilePath $node -ArgumentList @('"' + (Join-Path $here "server.js") + '"', "--http") `
    -WindowStyle Hidden -PassThru -RedirectStandardOutput $srvOut -RedirectStandardError $srvErr

$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$port/healthz" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    if ($srv.HasExited) { break }
}
if (-not $ready) { Log "FATAL server did not answer /healthz (exited=$($srv.HasExited))"; exit 1 }
Log "server ready (pid $($srv.Id))"

$ngArgs = @("http")
if (Test-Path $domainFile) {
    $domain = (Get-Content $domainFile -Raw).Trim()
    if ($domain) { $ngArgs += "--url=$domain" }
}
$ngArgs += @("$port", "--log=stdout", "--log-format=logfmt")
Log ("starting ngrok " + ($ngArgs -join " "))
$ng = Start-Process -FilePath $ngrok -ArgumentList $ngArgs -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $ngOut -RedirectStandardError $ngErr

# read the public URL back from the agent's local API and record the full connector URL
$public = ""
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $t = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 2
        foreach ($tun in $t.tunnels) { if ($tun.public_url -like "https://*") { $public = $tun.public_url } }
        if ($public) { break }
    } catch {}
    if ($ng.HasExited) { break }
}
if (-not $public) {
    Log "FATAL ngrok gave no public url (exited=$($ng.HasExited)) - see $ngOut / $ngErr"
    if (-not $srv.HasExited) { Stop-Process -Id $srv.Id -Force }
    exit 1
}
Set-Content -Path $urlFile -Value ($public + "/mcp/" + $secret) -NoNewline
Log "public url $public (connector url written to $urlFile)"

# babysit: both must live
while ($true) {
    Start-Sleep -Seconds 5
    if ($srv.HasExited -or $ng.HasExited) {
        Log "child exited (server=$($srv.HasExited) ngrok=$($ng.HasExited)) - stopping the pair"
        & (Join-Path $here "stop-http.ps1") | Out-Null
        exit 1
    }
}
