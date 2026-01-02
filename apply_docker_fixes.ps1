# Simple script to apply Docker monitoring fixes to cslaunch.ps1

Write-Host "=== Applying Docker Monitoring Fixes ===" -ForegroundColor Cyan

# Read cslaunch.ps1
$scriptPath = ".\cslaunch.ps1"
$backupPath = ".\cslaunch.ps1.backup"

# Create backup
Write-Host "[INFO] Creating backup..." -ForegroundColor Gray
Copy-Item $scriptPath $backupPath -Force

# Read the content
$content = Get-Content $scriptPath -Raw

# Fix 1: Add helper functions after parameter block
$helperFunctions = @'

# Helper function to test admin privileges
function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Function to implement exponential backoff for restart attempts
function Get-BackoffDelay {
    param(
        [int]$AttemptNumber,
        [int]$BaseDelay = 30,
        [int]$MaxDelay = 300
    )
    
    $delay = [math]::Min($BaseDelay * [math]::Pow(2, $AttemptNumber - 1), $MaxDelay)
    return $delay
}

# Enhanced function to capture Docker events
function Start-DockerEventMonitoring {
    $eventLogPath = Join-Path $PSScriptRoot "logs\docker_events.log"
    
    $eventScriptBlock = {
        param($LogPath)
        
        function Write-DockerEventLog {
            param([string]$Message)
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logEntry = "[$timestamp] $Message"
            Add-Content -Path $LogPath -Value $logEntry
        }
        
        try {
            Write-DockerEventLog "=== DOCKER EVENT MONITORING STARTED ==="
            docker events --format 'Type={{.Type}} Action={{.Action}} Object={{.Object}} Time={{.Time}} Status={{.Status}}' 2>&1 | ForEach-Object {
                if ($_ -and $_.Trim()) {
                    Write-DockerEventLog $_
                }
            }
        } catch {
            Write-DockerEventLog "ERROR: Docker event monitoring failed: $($_.Exception.Message)"
        }
    }
    
    $eventJob = Start-Job -Name "Docker-Event-Monitor" -ScriptBlock $eventScriptBlock -ArgumentList $eventLogPath
    
    Write-Host "[EVENTS] Docker event monitoring started (job ID: $($eventJob.Id))" -ForegroundColor Cyan
    Write-Host "  - Event log: $eventLogPath" -ForegroundColor Gray
    
    return $eventJob
}
'@

# Insert helper functions
$insertPoint = $content.IndexOf("# Setup crash logging")
if ($insertPoint -gt 0) {
    $content = $content.Substring(0, $insertPoint) + $helperFunctions + "`n" + $content.Substring($insertPoint)
    Write-Host "[FIXED] Added helper functions" -ForegroundColor Green
}

# Fix 2: Add event monitoring to Start-BackgroundMonitoring
$eventMonitoringCode = @'
    # Start Docker event monitoring
    Write-Host "[INFO] Starting Docker event monitoring..." -ForegroundColor Cyan
    $eventJob = Start-DockerEventMonitoring
'@

$pattern = '(Write-Host "\[INFO\] Starting background Docker daemon monitoring\.\.\." -ForegroundColor Cyan)'
if ($content -match $pattern) {
    $content = $content -replace $pattern, "$matches[0]`n$eventMonitoringCode"
    Write-Host "[FIXED] Added event monitoring call" -ForegroundColor Green
}

# Fix 3: Update monitoring loop with exponential backoff
$oldDelay = 'Start-Sleep -Seconds $actualDelay'
$newDelay = @'
# Use exponential backoff
$backoffDelay = Get-BackoffDelay -AttemptNumber ([math]::Min($dockerDaemonFailures, 10))
Write-DaemonLog "Using exponential backoff: waiting ${backoffDelay}s (attempt $dockerDaemonFailures)" "INFO"
Start-Sleep -Seconds $backoffDelay
'@

$content = $content -replace $oldDelay, $newDelay
Write-Host "[FIXED] Added exponential backoff" -ForegroundColor Green

# Write the updated script
Set-Content -Path $scriptPath -Value $content -Encoding UTF8

Write-Host "[SUCCESS] Docker monitoring fixes applied!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Run: .\cslaunch.ps1 -Monitor" -ForegroundColor Gray
Write-Host "2. Check logs\docker_events.log for events" -ForegroundColor Gray
Write-Host "3. Monitor logs\docker_daemon_monitor.log for improved diagnostics" -ForegroundColor Gray
