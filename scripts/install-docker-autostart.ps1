#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Configures Docker and CaseStrainer containers to start automatically on Windows boot.

.DESCRIPTION
    This script sets up automatic startup for:
    1. Docker Desktop service
    2. CaseStrainer containers via docker-compose
    3. Windows Task Scheduler task to ensure containers start after Docker is ready

.PARAMETER ProjectPath
    Path to the CaseStrainer project directory (default: current directory)

.EXAMPLE
    .\scripts\install-docker-autostart.ps1
#>

param(
    [string]$ProjectPath = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Docker Auto-Start Configuration" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get the project root (parent of scripts directory)
if ($ProjectPath -eq $PSScriptRoot) {
    $ProjectPath = Split-Path -Parent $ProjectPath
}

$composeFile = Join-Path $ProjectPath "docker-compose.prod.yml"
if (-not (Test-Path $composeFile)) {
    Write-Host "[ERROR] Could not find docker-compose.prod.yml at: $composeFile" -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Configuring Docker Desktop to start on boot..." -ForegroundColor Yellow

# Check if Docker Desktop is installed
$dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
if (-not (Test-Path $dockerDesktopPath)) {
    $dockerDesktopPath = "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
}

if (-not (Test-Path $dockerDesktopPath)) {
    Write-Host "[WARN] Docker Desktop not found. Please install Docker Desktop first." -ForegroundColor Yellow
    Write-Host "       Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Gray
} else {
    # Create startup shortcut for Docker Desktop
    $startupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
    $shortcutPath = Join-Path $startupFolder "Docker Desktop.lnk"
    
    if (-not (Test-Path $shortcutPath)) {
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut($shortcutPath)
        $Shortcut.TargetPath = $dockerDesktopPath
        $Shortcut.WorkingDirectory = Split-Path $dockerDesktopPath
        $Shortcut.Save()
        Write-Host "  [OK] Created Docker Desktop startup shortcut" -ForegroundColor Green
    } else {
        Write-Host "  [OK] Docker Desktop startup shortcut already exists" -ForegroundColor Green
    }
}

Write-Host "`n[2/4] Creating startup script..." -ForegroundColor Yellow

# Create startup script that waits for Docker and starts containers
$startupScript = @"
# CaseStrainer Auto-Start Script
# This script waits for Docker to be ready, then starts containers

`$ErrorActionPreference = "SilentlyContinue"
`$ProjectPath = "$ProjectPath"
`$ComposeFile = Join-Path `$ProjectPath "docker-compose.prod.yml"
`$LogFile = Join-Path `$ProjectPath "logs\autostart.log"

# Create logs directory if it doesn't exist
`$LogDir = Split-Path `$LogFile
if (-not (Test-Path `$LogDir)) {
    New-Item -ItemType Directory -Path `$LogDir -Force | Out-Null
}

function Write-Log {
    param([string]`$Message)
    `$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    `$LogMessage = "[`$Timestamp] `$Message"
    Add-Content -Path `$LogFile -Value `$LogMessage
    Write-Host `$LogMessage
}

Write-Log "=== CaseStrainer Auto-Start ==="
Write-Log "Waiting for Docker to be ready..."

# Wait for Docker daemon (max 5 minutes)
`$MaxWait = 300
`$Waited = 0
`$DockerReady = `$false

while (`$Waited -lt `$MaxWait) {
    `$DockerInfo = docker info 2>&1
    if (`$LASTEXITCODE -eq 0) {
        `$DockerReady = `$true
        Write-Log "Docker is ready!"
        break
    }
    Start-Sleep -Seconds 10
    `$Waited += 10
    Write-Log "Still waiting for Docker... (`$Waited seconds)"
}

if (-not `$DockerReady) {
    Write-Log "[ERROR] Docker did not become ready within `$MaxWait seconds"
    exit 1
}

# Additional wait for Docker Desktop to fully initialize
Write-Log "Waiting for Docker Desktop to fully initialize..."
Start-Sleep -Seconds 30

# Start containers
Write-Log "Starting CaseStrainer containers..."
Push-Location `$ProjectPath
docker-compose -f `$ComposeFile up -d 2>&1 | Tee-Object -FilePath (Join-Path `$ProjectPath "logs\docker-startup.log")

if (`$LASTEXITCODE -eq 0) {
    Write-Log "[SUCCESS] Containers started successfully"
} else {
    Write-Log "[ERROR] Failed to start containers (exit code: `$LASTEXITCODE)"
    exit 1
}

Pop-Location
Write-Log "=== Auto-Start Complete ==="
"@

$startupScriptPath = Join-Path $ProjectPath "scripts\docker-autostart.ps1"
$startupScript | Out-File -FilePath $startupScriptPath -Encoding UTF8
Write-Host "  [OK] Created startup script: $startupScriptPath" -ForegroundColor Green

Write-Host "`n[3/4] Creating Windows Task Scheduler task..." -ForegroundColor Yellow

# Create scheduled task that runs on system startup
$TaskName = "CaseStrainer-Docker-AutoStart"
$TaskDescription = "Automatically starts CaseStrainer Docker containers on system boot"

# Remove existing task if it exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "  [INFO] Removed existing task" -ForegroundColor Gray
}

# Create the action (run PowerShell script)
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$startupScriptPath`"" `
    -WorkingDirectory $ProjectPath

# Create the trigger (on system startup, with delay)
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Trigger.Delay = "PT2M"  # Wait 2 minutes after boot for system to stabilize

# Create the principal (run as current user, highest privileges)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# Register the task
try {
    Register-ScheduledTask -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Principal $Principal `
        -Settings $Settings `
        -Description $TaskDescription | Out-Null
    
    Write-Host "  [OK] Created scheduled task: $TaskName" -ForegroundColor Green
    Write-Host "       Task will run 2 minutes after system boot" -ForegroundColor Gray
} catch {
    Write-Host "  [ERROR] Failed to create scheduled task: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "          You may need to run this script as Administrator" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n[4/4] Verifying configuration..." -ForegroundColor Yellow

# Verify Docker Desktop shortcut
if (Test-Path $shortcutPath) {
    Write-Host "  [OK] Docker Desktop startup shortcut exists" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Docker Desktop startup shortcut not found" -ForegroundColor Yellow
}

# Verify startup script
if (Test-Path $startupScriptPath) {
    Write-Host "  [OK] Startup script exists" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Startup script not found" -ForegroundColor Red
    exit 1
}

# Verify scheduled task
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($Task) {
    Write-Host "  [OK] Scheduled task registered" -ForegroundColor Green
    Write-Host "       Task State: $($Task.State)" -ForegroundColor Gray
} else {
    Write-Host "  [ERROR] Scheduled task not found" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Configuration Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  ✓ Docker Desktop will start on boot" -ForegroundColor Green
Write-Host "  ✓ CaseStrainer containers will start 2 minutes after boot" -ForegroundColor Green
Write-Host "  ✓ Task will retry up to 3 times if startup fails" -ForegroundColor Green
Write-Host ""
Write-Host "To test the configuration:" -ForegroundColor Yellow
Write-Host "  1. Restart your computer" -ForegroundColor Gray
Write-Host "  2. Wait 3-5 minutes after boot" -ForegroundColor Gray
Write-Host "  3. Check logs: logs\autostart.log" -ForegroundColor Gray
Write-Host "  4. Verify containers: docker ps" -ForegroundColor Gray
Write-Host ""
Write-Host "To manually trigger the startup script:" -ForegroundColor Yellow
Write-Host "  .\scripts\docker-autostart.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "To remove auto-start configuration:" -ForegroundColor Yellow
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
Write-Host ""












