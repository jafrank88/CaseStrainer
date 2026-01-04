# Setup Docker Recovery Tasks
# This script creates Windows Task Scheduler tasks for Docker monitoring and recovery

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Test
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
}

function Get-ScriptPath {
    param([string]$ScriptName)
    return Join-Path $PSScriptRoot $ScriptName
}

function Install-RecoveryTasks {
    Write-Log "Installing Docker Recovery Tasks..."
    
    $scriptsPath = $PSScriptRoot
    
    # Task 1: Docker Service Monitor (runs at startup)
    Write-Log "Creating Docker Service Monitor task..."
    $taskName = "Docker-Service-Monitor"
    $scriptPath = Get-ScriptPath "docker_service_monitor.ps1"
    
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Days 365)
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $Principal -Force
    Write-Log "✓ Created task: $taskName"
    
    # Task 2: Docker Health Check (runs every 5 minutes)
    Write-Log "Creating Docker Health Check task..."
    $taskName = "Docker-Health-Check"
    $scriptPath = Get-ScriptPath "docker_service_monitor.ps1"
    
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -RunOnce"
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $Principal -Force
    Write-Log "✓ Created task: $taskName"
    
    # Task 3: Docker Emergency Recovery (runs on service failure)
    Write-Log "Creating Docker Emergency Recovery task..."
    $taskName = "Docker-Emergency-Recovery"
    $scriptPath = Get-ScriptPath "docker_emergency_recovery.ps1"
    
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
    $trigger = New-ScheduledTaskTrigger -AtLogon -User "SYSTEM"
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $Principal -Force
    Write-Log "✓ Created task: $taskName"
    
    # Task 4: Docker Autostart on Boot
    Write-Log "Creating Docker Autostart task..."
    $taskName = "Docker-Autostart"
    $scriptPath = Get-ScriptPath "configure_docker_autostart.ps1"
    
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Enable"
    $trigger = New-ScheduledTaskTrigger -AtStartup -Delay (New-TimeSpan -Seconds 30)
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $Principal -Force
    Write-Log "✓ Created task: $taskName"
    
    # Task 5: Docker Service Failure Trigger
    Write-Log "Configuring service failure triggers..."
    try {
        # Configure the Docker service to trigger recovery on failure
        $serviceName = "com.docker.service"
        
        # Set service recovery actions
        sc.exe failure $serviceName reset= 86400 actions= restart/5000/run/15000/restart/30000 command= "`"$scriptsPath\docker_emergency_recovery.ps1`" -Force" 2>$null
        Write-Log "✓ Configured service recovery for $serviceName"
        
        # Set service to restart on failure
        sc.exe config $serviceName start= auto 2>$null
        Write-Log "✓ Set $serviceName to automatic start"
    }
    catch {
        Write-Log "Failed to configure service triggers: $($_.Exception.Message)" "WARN"
    }
    
    Write-Log "All Docker recovery tasks installed successfully!"
}

function Uninstall-RecoveryTasks {
    Write-Log "Uninstalling Docker Recovery Tasks..."
    
    $tasks = @(
        "Docker-Service-Monitor",
        "Docker-Health-Check",
        "Docker-Emergency-Recovery",
        "Docker-Autostart"
    )
    
    foreach ($taskName in $tasks) {
        try {
            Unregister-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            Write-Log "✓ Removed task: $taskName"
        }
        catch {
            Write-Log "Could not remove task $taskName`: $($_.Exception.Message)" "WARN"
        }
    }
    
    # Reset service recovery
    try {
        sc.exe failure "com.docker.service" reset= actions= "" 2>$null
        Write-Log "✓ Reset service recovery configuration"
    }
    catch {
        Write-Log "Could not reset service recovery: $($_.Exception.Message)" "WARN"
    }
    
    Write-Log "All Docker recovery tasks uninstalled!"
}

function Test-RecoveryTasks {
    Write-Log "Testing Docker Recovery Tasks..."
    
    $tasks = @(
        "Docker-Service-Monitor",
        "Docker-Health-Check",
        "Docker-Emergency-Recovery",
        "Docker-Autostart"
    )
    
    Write-Log "Checking task status:"
    foreach ($taskName in $tasks) {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task) {
            Write-Log "✓ $taskName - Status: $($task.State)"
        }
        else {
            Write-Log "✗ $taskName - Not found"
        }
    }
    
    # Test emergency recovery script
    Write-Log "`nTesting emergency recovery script (dry run)..."
    $scriptPath = Get-ScriptPath "docker_emergency_recovery.ps1"
    try {
        & PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptPath -Diagnostics
        Write-Log "✓ Emergency recovery script executed successfully"
    }
    catch {
        Write-Log "✗ Emergency recovery script failed: $($_.Exception.Message)" "ERROR"
    }
    
    # Check service configuration
    Write-Log "`nChecking service configuration:"
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($service) {
            Write-Log "✓ com.docker.service - Status: $($service.Status), StartType: $($service.StartType)"
        }
        else {
            Write-Log "✗ com.docker.service - Not found"
        }
    }
    catch {
        Write-Log "✗ Could not check service: $($_.Exception.Message)" "ERROR"
    }
    
    Write-Log "`nTest completed!"
}

# Main execution
if ($Install) {
    # Check admin privileges
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Log "This script requires administrator privileges. Please run as Administrator." "ERROR"
        exit 1
    }
    
    Install-RecoveryTasks
}
elseif ($Uninstall) {
    # Check admin privileges
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Log "This script requires administrator privileges. Please run as Administrator." "ERROR"
        exit 1
    }
    
    Uninstall-RecoveryTasks
}
elseif ($Test) {
    Test-RecoveryTasks
}
else {
    Write-Host "Usage:"
    Write-Host "  .\setup_docker_recovery_tasks.ps1 -Install  # Install all recovery tasks"
    Write-Host "  .\setup_docker_recovery_tasks.ps1 -Uninstall # Remove all recovery tasks"
    Write-Host "  .\setup_docker_recovery_tasks.ps1 -Test     # Test task configuration"
    Write-Host ""
    Write-Host "Note: Install/Uninstall require administrator privileges"
}
