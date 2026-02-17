# Create-DockerService.ps1 - Creates Docker as a proper Windows service for unattended operation
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Creating Docker Auto-Restart Service" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check admin privileges
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[ERROR] Must run as Administrator!" -ForegroundColor Red
    exit 1
}

# Create a PowerShell script that will be our service
$serviceScript = @"
# Docker Monitor Service Script
`$serviceLog = "D:\dev\casestrainer\logs\docker-service.log"
`$restartCount = 0
`$maxRestarts = 10
`$lastRestart = Get-Date

function Write-ServiceLog {
    param([string]`$Message)
    `$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    `$logEntry = "[`$timestamp] `$Message"
    Add-Content -Path `$serviceLog -Value `$logEntry
}

function Restart-DockerIfNeeded {
    # Check if Docker is responding
    `$null = docker info 2>`$null
    if (`$LASTEXITCODE -ne 0) {
        Write-ServiceLog "Docker not responding - attempting restart"
        
        # Check restart rate limiting
        `$now = Get-Date
        `$hoursSinceLastRestart = (`$now - `$lastRestart).TotalHours
        
        if (`$hoursSinceLastRestart -lt 1) {
            `$restartCount++
            if (`$restartCount -gt `$maxRestarts) {
                Write-ServiceLog "Max restarts reached - waiting"
                return
            }
        } else {
            `$restartCount = 1
        }
        
        # Stop Docker Desktop
        Get-Process "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
        
        # Start Docker Desktop with GPU disabled (prevents crashes in VM environments)
        Start-Process "`${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe" -ArgumentList "--disable-gpu" -WindowStyle Minimized
        
        `$lastRestart = `$now
        Write-ServiceLog "Docker restart initiated"
        
        # Wait for Docker to be ready
        `$waitTime = 0
        while (`$waitTime -lt 300) {
            `$null = docker info 2>`$null
            if (`$LASTEXITCODE -eq 0) {
                Write-ServiceLog "Docker is ready"
                
                # Start containers
                Push-Location "D:\dev\casestrainer"
                docker-compose -f docker-compose.prod.yml up -d
                Pop-Location
                
                break
            }
            Start-Sleep -Seconds 10
            `$waitTime += 10
        }
    }
}

# Main monitoring loop
Write-ServiceLog "Docker monitor service started"
while (`$true) {
    Restart-DockerIfNeeded
    Start-Sleep -Seconds 60
}
"@

# Save the service script
$serviceScriptPath = "D:\dev\casestrainer\scripts\docker-monitor-service.ps1"
$serviceScript | Out-File -FilePath $serviceScriptPath -Encoding UTF8 -Force

Write-Host "[OK] Service script created: $serviceScriptPath" -ForegroundColor Green

# Create the scheduled task with proper settings
$taskName = "CaseStrainer-Docker-Service"
$taskDescription = "Monitors and restarts Docker as a service"

Write-Host "`n[CONFIG] Creating service task: $taskName" -ForegroundColor Yellow

# Remove existing task
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Create action
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$serviceScriptPath`""

# Create trigger - run at startup and every 5 minutes for recovery
$triggers = @()
$startupTrigger = New-ScheduledTaskTrigger -AtStartup
$startupTrigger.StartBoundary = (Get-Date).AddMinutes(2).ToString("yyyy-MM-dd'T'HH:mm:ss")
$triggers += $startupTrigger

$recoveryTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
$triggers += $recoveryTrigger

# Create settings for unattended operation
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -WakeToRun `
    -RunOnlyIfNetworkAvailable `
    -DontStopOnIdleEnd `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# Create principal
$principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Settings $settings -Principal $principal -Description $taskDescription -Force | Out-Null

Write-Host "[SUCCESS] Service task created!" -ForegroundColor Green

# Verify
$task = Get-ScheduledTask -TaskName $taskName
Write-Host "`nTask Details:" -ForegroundColor Gray
Write-Host "  Name: $($task.TaskName)" -ForegroundColor Gray
Write-Host "  State: $($task.State)" -ForegroundColor Gray
Write-Host "  Principal: $($task.Principal.UserId)" -ForegroundColor Gray
Write-Host "  Triggers: $($task.Triggers.Count) configured" -ForegroundColor Gray

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "[SUCCESS] Docker service configured!" -ForegroundColor Green
Write-Host "`nThe system will now:" -ForegroundColor Gray
Write-Host "  1. Start monitoring 2 minutes after boot" -ForegroundColor Gray
Write-Host "  2. Run as SYSTEM service (no login required)" -ForegroundColor Gray
Write-Host "  3. Check Docker every 60 seconds" -ForegroundColor Gray
Write-Host "  4. Auto-restart if Docker crashes" -ForegroundColor Gray
Write-Host "  5. Self-recover every 5 minutes if needed" -ForegroundColor Gray
Write-Host "`nTo test: Restart the computer" -ForegroundColor Yellow
Write-Host "Docker should start automatically within 3-4 minutes" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan
