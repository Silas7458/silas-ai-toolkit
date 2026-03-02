# claude-config-guard.ps1
# Watches claude_desktop_config.json and creates timestamped backups
# Keeps rolling 10 backups, purges oldest beyond that
# Can be run manually or as a scheduled task

$configPath = "{{HOME_DIR}}\AppData\Roaming\Claude\claude_desktop_config.json"
$backupDir = "{{HOME_DIR}}\AppData\Roaming\Claude\profiles"
$maxBackups = 10

function Backup-ClaudeConfig {
    if (-not (Test-Path $configPath)) {
        Write-Host "ERROR: Config file not found at $configPath" -ForegroundColor Red
        return $false
    }

    # Validate JSON before backing up
    try {
        $content = Get-Content $configPath -Raw
        $null = $content | ConvertFrom-Json
    } catch {
        Write-Host "WARNING: Current config is INVALID JSON - not backing up corrupt file" -ForegroundColor Yellow
        Write-Host "Error: $_" -ForegroundColor Yellow
        return $false
    }

    # Check if content actually changed from most recent backup
    $latestBackup = Get-ChildItem "$backupDir\config-backup-*.json" -ErrorAction SilentlyContinue | 
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    if ($latestBackup) {
        $currentHash = (Get-FileHash $configPath -Algorithm MD5).Hash
        $backupHash = (Get-FileHash $latestBackup.FullName -Algorithm MD5).Hash
        if ($currentHash -eq $backupHash) {
            Write-Host "Config unchanged from latest backup - skipping" -ForegroundColor Cyan
            return $true
        }
    }

    # Create timestamped backup
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupFile = Join-Path $backupDir "config-backup-$timestamp.json"
    Copy-Item $configPath $backupFile
    Write-Host "Backup created: $backupFile" -ForegroundColor Green

    # Purge old backups beyond max
    $backups = Get-ChildItem "$backupDir\config-backup-*.json" | Sort-Object LastWriteTime -Descending
    if ($backups.Count -gt $maxBackups) {
        $toDelete = $backups | Select-Object -Skip $maxBackups
        foreach ($old in $toDelete) {
            Remove-Item $old.FullName
            Write-Host "Purged old backup: $($old.Name)" -ForegroundColor DarkGray
        }
    }

    return $true
}

function Restore-ClaudeConfig {
    param([string]$BackupName)
    
    $backups = Get-ChildItem "$backupDir\config-backup-*.json" | Sort-Object LastWriteTime -Descending
    
    if (-not $BackupName) {
        Write-Host "`nAvailable backups:" -ForegroundColor Cyan
        $i = 1
        foreach ($b in $backups) {
            $size = [math]::Round($b.Length / 1KB, 1)
            Write-Host "  [$i] $($b.Name) ($size KB) - $($b.LastWriteTime)" -ForegroundColor White
            $i++
        }
        Write-Host "`nUsage: Restore-ClaudeConfig -BackupName 'config-backup-20260223-115500.json'" -ForegroundColor Yellow
        return
    }

    $restoreFile = Join-Path $backupDir $BackupName
    if (-not (Test-Path $restoreFile)) {
        Write-Host "Backup not found: $restoreFile" -ForegroundColor Red
        return
    }

    # Validate the backup JSON
    try {
        $null = Get-Content $restoreFile -Raw | ConvertFrom-Json
    } catch {
        Write-Host "ERROR: Backup file contains invalid JSON!" -ForegroundColor Red
        return
    }

    # Backup current (even if broken) before overwriting
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    Copy-Item $configPath "$backupDir\config-pre-restore-$timestamp.json" -ErrorAction SilentlyContinue

    Copy-Item $restoreFile $configPath
    Write-Host "Config restored from: $BackupName" -ForegroundColor Green
    Write-Host "Restart Claude Desktop to apply changes." -ForegroundColor Yellow
}

function Validate-ClaudeConfig {
    if (-not (Test-Path $configPath)) {
        Write-Host "Config file missing!" -ForegroundColor Red
        return $false
    }
    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        $servers = $config.mcpServers.PSObject.Properties.Name
        Write-Host "Config is valid JSON" -ForegroundColor Green
        Write-Host "MCP Servers configured: $($servers -join ', ')" -ForegroundColor Cyan
        return $true
    } catch {
        Write-Host "INVALID JSON in config!" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Yellow
        return $false
    }
}

# If run directly (not dot-sourced), perform a backup
if ($MyInvocation.InvocationName -ne '.') {
    Backup-ClaudeConfig
}
