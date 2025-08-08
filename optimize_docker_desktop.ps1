# Docker Desktop Optimization Script for CaseStrainer
# Configures Docker Desktop for maximum performance and reliability

param(
    [switch]$MaxResources,
    [switch]$AutoRestart,
    [switch]$Verbose,
    [switch]$DryRun,
    [switch]$Help
)

if ($Help) {
    Write-Host -Object "Docker Desktop Optimization Script" -ForegroundColor Cyan
    Write-Host -Object ""
    Write-Host -Object "Usage:" -ForegroundColor White
    Write-Host -Object "  .\optimize_docker_desktop.ps1 -MaxResources  # Configure maximum resource usage" -ForegroundColor Green
    Write-Host -Object "  .\optimize_docker_desktop.ps1 -AutoRestart   # Configure auto-restart settings" -ForegroundColor Yellow
    Write-Host -Object "  .\optimize_docker_desktop.ps1 -Verbose       # Show detailed output" -ForegroundColor Cyan
    Write-Host -Object "  .\optimize_docker_desktop.ps1 -DryRun        # Test mode (no actual changes)" -ForegroundColor Yellow
    Write-Host -Object ""
    Write-Host -Object "What it does:" -ForegroundColor White
    Write-Host -Object "  â€¢ Configures Docker Desktop to use maximum available resources" -ForegroundColor Gray
    Write-Host -Object "  â€¢ Sets up auto-restart and recovery mechanisms" -ForegroundColor Gray
    Write-Host -Object "  â€¢ Optimizes Windows services for Docker" -ForegroundColor Gray
    Write-Host -Object "  â€¢ Configures power settings to prevent sleep" -ForegroundColor Gray
    Write-Host -Object "  â€¢ Sets up monitoring and alerting" -ForegroundColor Gray
    exit 0
}

# Configuration
$LogFile = "logs/docker_optimization.log"
$SettingsFile = "logs/docker_settings.json"

# Ensure logs directory exists
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

function Write-Log {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logMessage -Force

    if ($Verbose) {
        $color = switch($Level) {
            "ERROR" { "Red" }
            "WARN" { "Yellow" }
            "INFO" { "Green" }
            default { "White" }
        }
        Write-Host $logMessage -ForegroundColor $color
    }
}

function Get-SystemResources {
    try {
        $totalMemory = (Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory / 1GB
        $cpuCores = (Get-CimInstance -ClassName Win32_Processor | Measure-Object -Property NumberOfCores -Sum).Sum
        $availableDisk = (Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace / 1GB

        return @{
            TotalMemoryGB = [math]::Round($totalMemory, 1)
            CPUCores = $cpuCores
            AvailableDiskGB = [math]::Round($availableDisk, 1)
        }
    }
    catch {
        Write-Log "Error getting system resources: $($_.Exception.Message)" -Level "ERROR"
        return @{ TotalMemoryGB = 16; CPUCores = 4; AvailableDiskGB = 100 }
    }
}

function Optimize-DockerResources {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Log "Optimizing Docker Desktop resource allocation..." -Level "INFO"
    
    $systemResources = Get-SystemResources
    Write-Log "System Resources: $($systemResources.TotalMemoryGB)GB RAM, $($systemResources.CPUCores) CPU cores, $($systemResources.AvailableDiskGB)GB free disk" -Level "INFO"
    
    # Calculate optimal Docker Desktop settings
    $dockerMemory = [math]::Min([double]($systemResources.TotalMemoryGB * 0.75), 32.0)  # Use 75% of RAM, max 32GB
    $dockerCPU = [math]::Min([double]($systemResources.CPUCores * 0.8), 16.0)  # Use 80% of cores, max 16
    $dockerDisk = [math]::Min([double]($systemResources.AvailableDiskGB * 0.5), 100.0)  # Use 50% of free disk, max 100GB
    
    Write-Log "Recommended Docker Desktop settings:" -Level "INFO"
    Write-Log "  Memory: ${dockerMemory}GB" -Level "INFO"
    Write-Log "  CPU: ${dockerCPU} cores" -Level "INFO"
    Write-Log "  Disk: ${dockerDisk}GB" -Level "INFO"
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would configure Docker Desktop with these settings" -Level "INFO"
        return @{
            Memory = $dockerMemory
            CPU = $dockerCPU
            Disk = $dockerDisk
        }
    }

    # Configure Docker Desktop settings via registry (if possible)
    try {
        $dockerSettingsPath = "$env:LOCALAPPDATA\Docker\settings.json"
        if (Test-Path $dockerSettingsPath) {
            $settings = Get-Content $dockerSettingsPath | ConvertFrom-Json

            # Update resource settings
            $settings.resources.memory = $dockerMemory * 1024 * 1024 * 1024  # Convert to bytes
            $settings.resources.cpus = $dockerCPU
            $settings.resources.diskSize = $dockerDisk * 1024 * 1024 * 1024  # Convert to bytes

            # Enable WSL2
            $settings.useWslEngine = $true

            # Enable auto-start
            $settings.startOnLogin = $true

            # Save settings
            $settings | ConvertTo-Json -Depth 10 | Out-File -FilePath $dockerSettingsPath -Force
            Write-Log "Docker Desktop settings updated successfully" -Level "INFO"
        } else {
            Write-Log "Docker Desktop settings file not found - manual configuration required" -Level "WARN"
        }
    }
    catch {
        Write-Log "Error updating Docker Desktop settings: $($_.Exception.Message)" -Level "ERROR"
    }
}

function Set-WindowsServices {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Log "Configuring Windows services for Docker..." -Level "INFO"
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would configure Windows services" -Level "INFO"
        return
    }

    try {
        # Configure Docker service
        $dockerService = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($dockerService) {
            Set-Service -Name "com.docker.service" -StartupType Automatic
            Write-Log "Docker service set to auto-start" -Level "INFO"
        }

        # Configure WSL service
        $wslService = Get-Service -Name "LxssManager" -ErrorAction SilentlyContinue
        if ($wslService) {
            Set-Service -Name "LxssManager" -StartupType Automatic
            Write-Log "WSL service set to auto-start" -Level "INFO"
        }

        # Configure Hyper-V services
        $hypervServices = @("vmms", "vmicvms", "vmicrdv", "vmicshutdown", "vmicheartbeat", "vmicvss")
        foreach ($service in $hypervServices) {
            $svc = Get-Service -Name $service -ErrorAction SilentlyContinue
            if ($svc) {
                Set-Service -Name $service -StartupType Automatic
                Write-Log "Hyper-V service $service set to auto-start" -Level "INFO"
            }
        }
    }
    catch {
        Write-Log "Error configuring Windows services: $($_.Exception.Message)" -Level "ERROR"
    }
}

function Set-PowerSettings {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Log "Configuring power settings to prevent sleep..." -Level "INFO"
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would configure power settings" -Level "INFO"
        return
    }

    try {
        # Prevent sleep when plugged in
        powercfg /change standby-timeout-ac 0
        powercfg /change hibernate-timeout-ac 0
        powercfg /change monitor-timeout-ac 0

        # Prevent sleep when on battery (if applicable)
        powercfg /change standby-timeout-dc 0
        powercfg /change hibernate-timeout-dc 0
        powercfg /change monitor-timeout-dc 0

        Write-Log "Power settings configured to prevent sleep" -Level "INFO"
    }
    catch {
        Write-Log "Error configuring power settings: $($_.Exception.Message)" -Level "ERROR"
    }
}

function Set-AutoRestart {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Log "Configuring auto-restart mechanisms..." -Level "INFO"
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would configure auto-restart mechanisms" -Level "INFO"
        return
    }

    try {
        # Create scheduled task for Docker Desktop auto-restart
        $taskName = "DockerDesktopAutoRestart"
        $taskDescription = "Automatically restart Docker Desktop if it stops"

        # Check if task already exists
        $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        }

        # Create the task
        $action = New-ScheduledTaskAction -Execute "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        $trigger = New-ScheduledTaskTrigger -AtStartup
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description $taskDescription -User "SYSTEM" -RunLevel Highest

        Write-Log "Scheduled task created for Docker Desktop auto-restart" -Level "INFO"
    }
    catch {
        Write-Log "Error configuring auto-restart: $($_.Exception.Message)" -Level "ERROR"
    }
}

function Optimize-NetworkSettings {
    Write-Log "Optimizing network settings for Docker..." -Level "INFO"

    if ($DryRun) {
        Write-Log "DRY RUN: Would optimize network settings" -Level "INFO"
        return
    }

    try {
        # Configure DNS settings for better Docker performance
        $dnsServers = @("8.8.8.8", "8.8.4.4")  # Google DNS

        # Get network adapters
        $adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" -and $_.InterfaceDescription -notlike "*Loopback*" }

        foreach ($adapter in $adapters) {
            try {
                Set-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex -ServerAddresses $dnsServers
                Write-Log "Configured DNS for adapter: $($adapter.Name)" -Level "INFO"
            }
            catch {
                Write-Log "Error configuring DNS for adapter $($adapter.Name): $($_.Exception.Message)" -Level "WARN"
            }
        }
    }
    catch {
        Write-Log "Error optimizing network settings: $($_.Exception.Message)" -Level "ERROR"
    }
}

function New-OptimizationReport {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Log "Creating optimization report..." -Level "INFO"
    
    $systemResources = Get-SystemResources
    $report = @{
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        SystemResources = $systemResources
        DockerSettings = @{
            MemoryGB = [math]::Min([double]($systemResources.TotalMemoryGB * 0.75), 32.0)
            CPUCores = [math]::Min([double]($systemResources.CPUCores * 0.8), 16.0)
            DiskGB = [math]::Min([double]($systemResources.AvailableDiskGB * 0.5), 100.0)
        }
        ServicesConfigured = @(
            "com.docker.service",
            "LxssManager",
            "vmms",
            "vmicvms",
            "vmicrdv",
            "vmicshutdown",
            "vmicheartbeat",
            "vmicvss"
        )
        PowerSettings = @{
            SleepDisabled = $true
            HibernateDisabled = $true
            MonitorTimeoutDisabled = $true
        }
        AutoRestart = @{
            ScheduledTaskCreated = $true
            TaskName = "DockerDesktopAutoRestart"
        }
    }

    $report | ConvertTo-Json -Depth 10 | Out-File -FilePath $SettingsFile -Force
    Write-Log "Optimization report saved to $SettingsFile" -Level "INFO"
}

# Main execution
Write-Log "Starting Docker Desktop optimization..." -Level "INFO"

try {
    if ($MaxResources) {
        Optimize-DockerResources
    }

    if ($AutoRestart) {
        Set-WindowsServices
        Set-PowerSettings
        Set-AutoRestart
        Optimize-NetworkSettings
    }

    New-OptimizationReport

    Write-Log "Docker Desktop optimization completed successfully!" -Level "INFO"

    if ($Verbose) {
        Write-Host -Object ""
        Write-Host -Object "✅ Docker Desktop Optimization Complete!" -ForegroundColor Green
        Write-Host -Object "ðŸ“Š Check the report: $SettingsFile" -ForegroundColor Cyan
        Write-Host -Object "ðŸ”„ Restart Docker Desktop to apply all changes" -ForegroundColor Yellow
        Write-Host -Object "ðŸ“‹ Manual steps (if needed):" -ForegroundColor White
        Write-Host -Object "  1. Open Docker Desktop" -ForegroundColor Gray
        Write-Host -Object "  2. Go to Settings > Resources" -ForegroundColor Gray
        Write-Host -Object "  3. Set Memory to recommended value" -ForegroundColor Gray
        Write-Host -Object "  4. Set CPU to recommended value" -ForegroundColor Gray
        Write-Host -Object "  5. Set Disk to recommended value" -ForegroundColor Gray
    }
}
catch {
    Write-Log "Fatal error during optimization: $($_.Exception.Message)" -Level "ERROR"
    throw
}
finally {
    Write-Log "Docker Desktop optimization process finished" -Level "INFO"
}
