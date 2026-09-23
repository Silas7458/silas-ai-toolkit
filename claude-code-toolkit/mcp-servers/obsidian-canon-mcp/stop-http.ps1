# stop-http.ps1 - kills the HTTP-mode obsidian-canon server (node ... server.js --http) and the ngrok
# agent from tools\ngrok, whole process trees. Never touches Proctor's stdio instance (no --http).
$ErrorActionPreference = "Continue"
$procs = Get-CimInstance Win32_Process | Where-Object {
    ($_.Name -eq "node.exe" -and $_.CommandLine -like "*obsidian-canon-mcp*server.js*--http*") -or
    ($_.Name -eq "ngrok.exe" -and $_.CommandLine -like "*ngrok*http*")
}
foreach ($p in $procs) {
    Write-Output ("stopping " + $p.Name + " pid " + $p.ProcessId)
    & taskkill /PID $p.ProcessId /T /F 2>$null | Out-Null
}
if (-not $procs) { Write-Output "nothing running" }
