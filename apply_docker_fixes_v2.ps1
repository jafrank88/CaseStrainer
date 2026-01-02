# Apply Docker monitoring fixes to cslaunch.ps1 (version 2)

Write-Host "=== Applying Docker Monitoring Fixes (v2) ===" -ForegroundColor Cyan

# Read the script
$content = Get-Content ".\cslaunch.ps1" -Raw

# Define the helper functions to add
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

# Insert helper functions after the parameter block
$insertPoint = $content.IndexOf("# Setup crash logging")
if ($insertPoint -gt 0) {
    $content = $content.Substring(0, $insertPoint) + $helperFunctions + "`n" + $content.Substring($insertPoint)
    Write-Host "[OK] Added helper functions" -ForegroundColor Green
}

# Add event monitoring to Start-BackgroundMonitoring function
$pattern = '(Write-Host "\[INFO\] Starting background Docker daemon monitoring\.\.\." -ForegroundColor Cyan\s+)(\s+# Check if running as administrator)'
if ($content -match $pattern) {
    $eventMonitoringCode = @'
    # Start Docker event monitoring
    Write-Host "[INFO] Starting Docker event monitoring..." -ForegroundColor Cyan
    $eventJob = Start-DockerEventMonitoring
'@
    $content = $content -replace $pattern, "`$1$eventMonitoringCode`n`$2"
    Write-Host "[OK] Added event monitoring call" -ForegroundColor Green
}

# Write the updated script
Set-Content -Path ".\cslaunch.ps1" -Value $content -Encoding UTF8

Write-Host "`n[SUCCESS] Docker monitoring fixes applied!" -ForegroundColor Green
Write-Host "`nTo test: .\cslaunch.ps1 -Monitor" -ForegroundColor Gray
