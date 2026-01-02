# Setup Docker Monitoring and Auto-Recovery
# Configures Docker daemon monitoring and Windows service auto-restart

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Status
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Docker Monitoring Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

if ($Status) {
    Write-Host "=== Current Status ===" -ForegroundColor Cyan
    
    # Check Docker service configuration
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($service) {
            Write-Host "Docker Service:" -ForegroundColor Yellow
            Write-Host "  Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq 'Running') { 'Green' } else { 'Red' })
            Write-Host "  Startup Type: $($service.StartType)" -ForegroundColor Gray
            
            # Check failure actions
            $failureActions = sc.exe qfailure "com.docker.service" 2>&1
            Write-Host "  Failure Actions:" -ForegroundColor Gray
            Write-Host "    $failureActions" -ForegroundColor Gray
        } else {
            Write-Host "Docker Service: Not found" -ForegroundColor Red
        }
    } catch {
        Write-Host "Docker Service: Error checking - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Check scheduled task
    try {
        $task = Get-ScheduledTask -TaskName "DockerDaemonMonitor" -ErrorAction SilentlyContinue
        if ($task) {
            Write-Host "`nDocker Daemon Monitor Task:" -ForegroundColor Yellow
            Write-Host "  Status: $($task.State)" -ForegroundColor $(if ($task.State -eq 'Ready') { 'Green' } else { 'Yellow' })
            Write-Host "  Last Run: $($task.LastRunTime)" -ForegroundColor Gray
            Write-Host "  Next Run: $($task.NextRunTime)" -ForegroundColor Gray
        } else {
            Write-Host "`nDocker Daemon Monitor Task: Not installed" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "`nDocker Daemon Monitor Task: Error checking" -ForegroundColor Red
    }
    
    # Check if monitor script exists
    $monitorScript = Join-Path $PSScriptRoot "docker_daemon_monitor.ps1"
    if (Test-Path $monitorScript) {
        Write-Host "`nMonitor Script: Found at $monitorScript" -ForegroundColor Green
    } else {
        Write-Host "`nMonitor Script: Not found" -ForegroundColor Red
    }
    
    exit 0
}

if ($Uninstall) {
    Write-Host "Uninstalling Docker monitoring..." -ForegroundColor Yellow
    
    # Remove scheduled task
    try {
        $task = Get-ScheduledTask -TaskName "DockerDaemonMonitor" -ErrorAction SilentlyContinue
        if ($task) {
            Unregister-ScheduledTask -TaskName "DockerDaemonMonitor" -Confirm:$false
            Write-Host "[OK] Removed scheduled task" -ForegroundColor Green
        }
    } catch {
        Write-Host "[WARN] Could not remove scheduled task: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # Stop any running monitor jobs
    try {
        $jobs = Get-Job -Name "DockerDaemonMonitor" -ErrorAction SilentlyContinue
        if ($jobs) {
            $jobs | Stop-Job
            $jobs | Remove-Job -Force
            Write-Host "[OK] Stopped running monitor jobs" -ForegroundColor Green
        }
    } catch {
        # Ignore
    }
    
    Write-Host "`n[SUCCESS] Docker monitoring uninstalled" -ForegroundColor Green
    exit 0
}

if ($Install) {
    Write-Host "Installing Docker monitoring and auto-recovery..." -ForegroundColor Cyan
    
    # Step 1: Configure Docker service auto-restart
    Write-Host "`n[1/3] Configuring Docker service auto-restart..." -ForegroundColor Yellow
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($service) {
            # Set startup type to automatic
            Set-Service -Name "com.docker.service" -StartupType Automatic -ErrorAction Stop
            Write-Host "  [OK] Set Docker service to Automatic startup" -ForegroundColor Green
            
            # Configure failure actions: restart after 5s, 10s, 30s
            $result = sc.exe failure "com.docker.service" reset= 86400 actions= restart/5000/restart/10000/restart/30000 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [OK] Configured service failure actions (restart on failure)" -ForegroundColor Green
            } else {
                Write-Host "  [WARN] Could not configure failure actions: $result" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  [WARN] Docker service not found - may not be installed" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [ERROR] Failed to configure Docker service: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Step 2: Create scheduled task for Docker daemon monitor
    Write-Host "`n[2/3] Creating scheduled task for Docker daemon monitor..." -ForegroundColor Yellow
    try {
        $monitorScript = Join-Path $PSScriptRoot "docker_daemon_monitor.ps1"
        if (-not (Test-Path $monitorScript)) {
            Write-Host "  [ERROR] Monitor script not found at: $monitorScript" -ForegroundColor Red
            Write-Host "  Please ensure docker_daemon_monitor.ps1 exists in the scripts directory" -ForegroundColor Yellow
        } else {
            # Remove existing task if it exists
            $existingTask = Get-ScheduledTask -TaskName "DockerDaemonMonitor" -ErrorAction SilentlyContinue
            if ($existingTask) {
                Unregister-ScheduledTask -TaskName "DockerDaemonMonitor" -Confirm:$false -ErrorAction SilentlyContinue
            }
            
            # Create the action
            $action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
                -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$monitorScript`" -AsJob" `
                -WorkingDirectory $PSScriptRoot
            
            # Create trigger (at system startup with 5 minute delay)
            $trigger = New-ScheduledTaskTrigger -AtStartup
            $trigger.Delay = "PT5M"  # Wait 5 minutes after boot
            
            # Create principal (run as current user with highest privileges)
            $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
                -LogonType Interactive `
                -RunLevel Highest
            
            # Create settings
            $settings = New-ScheduledTaskSettingsSet `
                -AllowStartIfOnBatteries `
                -DontStopIfGoingOnBatteries `
                -StartWhenAvailable `
                -RestartCount 3 `
                -RestartInterval (New-TimeSpan -Minutes 5) `
                -ExecutionTimeLimit (New-TimeSpan -Hours 0)  # No time limit
            
            # Register the task
            Register-ScheduledTask -TaskName "DockerDaemonMonitor" `
                -Action $action `
                -Trigger $trigger `
                -Principal $principal `
                -Settings $settings `
                -Description "Monitors Docker daemon health and automatically restarts if frozen" | Out-Null
            
            Write-Host "  [OK] Created scheduled task 'DockerDaemonMonitor'" -ForegroundColor Green
            Write-Host "       Task will start 5 minutes after system boot" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  [ERROR] Failed to create scheduled task: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Step 3: Start monitor immediately (optional)
    Write-Host "`n[3/3] Starting Docker daemon monitor..." -ForegroundColor Yellow
    try {
        $monitorScript = Join-Path $PSScriptRoot "docker_daemon_monitor.ps1"
        if (Test-Path $monitorScript) {
            Write-Host "  To start monitor now, run:" -ForegroundColor Cyan
            Write-Host "    .\scripts\docker_daemon_monitor.ps1 -AsJob" -ForegroundColor Yellow
            Write-Host "`n  Or start it interactively:" -ForegroundColor Cyan
            Write-Host "    .\scripts\docker_daemon_monitor.ps1" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [WARN] Could not start monitor: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host "`n[SUCCESS] Docker monitoring setup complete!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Check status: .\scripts\setup_docker_monitoring.ps1 -Status" -ForegroundColor Yellow
    Write-Host "  2. Start monitor: .\scripts\docker_daemon_monitor.ps1 -AsJob" -ForegroundColor Yellow
    Write-Host "  3. View logs: Get-Content logs\docker_daemon_monitor.log -Tail 50 -Wait" -ForegroundColor Yellow
    
    exit 0
}

# Default: show usage
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  .\setup_docker_monitoring.ps1 -Install    # Install monitoring" -ForegroundColor Yellow
Write-Host "  .\setup_docker_monitoring.ps1 -Uninstall  # Remove monitoring" -ForegroundColor Yellow
Write-Host "  .\setup_docker_monitoring.ps1 -Status     # Check current status" -ForegroundColor Yellow
Write-Host "`nThis script must be run as Administrator" -ForegroundColor Gray










