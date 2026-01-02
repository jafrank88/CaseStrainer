# system_recovery_logger.ps1 - System reboot detection and recovery logging
# Tracks system reboots, Docker crashes, and recovery patterns to identify recurring issues

param(
    [string]$LogPath = "logs\system_recovery.log",
    [string]$StateFile = "logs\system_state.json",
    [int]$CheckInterval = 300  # Check every 5 minutes
)

# Setup logging and state tracking
$ErrorActionPreference = "Continue"
$script:LogPath = Join-Path $PSScriptRoot $LogPath
$script:StateFile = Join-Path $PSScriptRoot $StateFile
$script:StartTime = Get-Date

# Ensure logs directory exists
$logDir = Split-Path $script:LogPath -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-RecoveryLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [hashtable]$Metadata = @{}
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = @{
        timestamp = $timestamp
        level = $Level
        message = $Message
        metadata = $Metadata
    }
    
    # Write as JSON for structured logging
    $jsonEntry = $logEntry | ConvertTo-Json -Compress
    Add-Content -Path $script:LogPath -Value $jsonEntry
    
    # Also write human-readable format
    $humanEntry = "[$timestamp] [$Level] $Message"
    if ($Metadata.Count -gt 0) {
        $humanEntry += " | " + ($Metadata.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ", "
    }
    
    switch ($Level) {
        "ERROR" { Write-Host $humanEntry -ForegroundColor Red }
        "WARN"  { Write-Host $humanEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $humanEntry -ForegroundColor Green }
        "CRITICAL" { Write-Host $humanEntry -ForegroundColor Magenta }
        default { Write-Host $humanEntry }
    }
}

function Get-SystemState {
    <#
    .SYNOPSIS
    Get current system state for comparison
    #>
    
    $state = @{
        timestamp = Get-Date
        bootTime = $null
        uptime = 0
        dockerRunning = $false
        dockerProcesses = @()
        containerCount = 0
        memoryUsage = 0
        systemLoad = 0
        activeConnections = 0
    }
    
    try {
        # Get system boot time
        $os = Get-CimInstance -ClassName Win32_OperatingSystem
        $state.bootTime = $os.LastBootUpTime
        $state.uptime = (Get-Date) - $state.bootTime
        
        # Check Docker status
        $dockerProcesses = Get-Process "*Docker*" -ErrorAction SilentlyContinue
        $state.dockerProcesses = $dockerProcesses | ForEach-Object {
            @{
                Name = $_.ProcessName
                Id = $_.Id
                StartTime = $_.StartTime
                WorkingSet = $_.WorkingSet64
            }
        }
        $state.dockerRunning = ($dockerProcesses.Count -gt 0)
        
        # Get container count if Docker is running
        if ($state.dockerRunning) {
            try {
                $containers = docker ps --format "{{.Names}}" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $state.containerCount = ($containers -split "`n" | Where-Object { $_.Trim() }).Count
                }
            } catch {
                $state.containerCount = 0
            }
        }
        
        # Get memory usage
        $totalMemory = (Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory
        $freeMemory = (Get-CimInstance -ClassName Win32_OperatingSystem).FreePhysicalMemory
        $state.memoryUsage = [math]::Round((($totalMemory - $freeMemory) / $totalMemory) * 100, 2)
        
        # Get system load (simplified for Windows)
        $cpu = Get-CimInstance -ClassName Win32_Processor | Measure-Object -Property LoadPercentage -Average
        $state.systemLoad = if ($cpu.LoadPercentage) { $cpu.LoadPercentage } else { 0 }
        
        # Get active network connections (simplified)
        $connections = Get-NetTCPConnection | Where-Object { $_.State -eq "Established" }
        $state.activeConnections = $connections.Count
        
    } catch {
        Write-RecoveryLog "Failed to get system state: $($_.Exception.Message)" "ERROR"
    }
    
    return $state
}

function Get-PreviousState {
    <#
    .SYNOPSIS
    Load previous system state from file
    #>
    
    if (Test-Path $script:StateFile) {
        try {
            $json = Get-Content $script:StateFile -Raw
            return $json | ConvertFrom-Json
        } catch {
            Write-RecoveryLog "Failed to load previous state: $($_.Exception.Message)" "ERROR"
            return $null
        }
    }
    
    return $null
}

function Save-SystemState {
    <#
    .SYNOPSIS
    Save current system state to file
    #>
    
    param([hashtable]$State)
    
    try {
        $State | ConvertTo-Json -Depth 10 | Out-File -FilePath $script:StateFile -Encoding UTF8
    } catch {
        Write-RecoveryLog "Failed to save system state: $($_.Exception.Message)" "ERROR"
    }
}

function Test-SystemReboot {
    <#
    .SYNOPSIS
    Detect if system has rebooted since last check
    #>
    
    $currentState = Get-SystemState
    $previousState = Get-PreviousState
    
    if ($null -eq $previousState) {
        Write-RecoveryLog "No previous state found - initializing" "INFO"
        Save-SystemState $currentState
        return @{
            Rebooted = $false
            Reason = "Initial state"
            CurrentState = $currentState
        }
    }
    
    # Check boot time
    $bootTimeChanged = $currentState.bootTime -ne $previousState.bootTime
    $uptimeReset = $currentState.uptime.TotalMinutes -lt 10  # System uptime less than 10 minutes
    
    if ($bootTimeChanged -or $uptimeReset) {
        $downtime = if ($previousState.timestamp) {
            (Get-Date) - [datetime]$previousState.timestamp
        } else {
            [TimeSpan]::Zero
        }
        
        Write-RecoveryLog "SYSTEM REBOOT DETECTED" "CRITICAL" @{
            previous_boot = $previousState.bootTime
            current_boot = $currentState.bootTime
            estimated_downtime_minutes = [math]::Round($downtime.TotalMinutes, 1)
            uptime_minutes = [math]::Round($currentState.uptime.TotalMinutes, 1)
        }
        
        return @{
            Rebooted = $true
            Reason = "Boot time changed or uptime reset"
            CurrentState = $currentState
            PreviousState = $previousState
            Downtime = $downtime
        }
    }
    
    return @{
        Rebooted = $false
        Reason = "No reboot detected"
        CurrentState = $currentState
        PreviousState = $previousState
    }
}

function Test-DockerRecovery {
    <#
    .SYNOPSIS
    Detect Docker recovery or crash patterns
    #>
    
    $currentState = Get-SystemState
    $previousState = Get-PreviousState
    
    if ($null -eq $previousState) {
        return @{
            Status = "Unknown"
            Reason = "No previous state"
        }
    }
    
    # Check Docker status changes
    $dockerWasRunning = $previousState.dockerRunning
    $dockerIsRunning = $currentState.dockerRunning
    
    if (-not $dockerWasRunning -and $dockerIsRunning) {
        # Docker recovered
        $recovery = @{
            Status = "Recovered"
            Reason = "Docker started running"
            CurrentProcesses = $currentState.dockerProcesses.Count
            ContainerCount = $currentState.containerCount
        }
        
        Write-RecoveryLog "Docker recovery detected" "SUCCESS" $recovery
        return $recovery
    }
    
    if ($dockerWasRunning -and -not $dockerIsRunning) {
        # Docker crashed
        $crash = @{
            Status = "Crashed"
            Reason = "Docker stopped running"
            PreviousProcesses = $previousState.dockerProcesses.Count
            PreviousContainers = $previousState.containerCount
        }
        
        Write-RecoveryLog "Docker crash detected" "CRITICAL" $crash
        return $crash
    }
    
    # Check for significant changes
    $processChange = $currentState.dockerProcesses.Count - $previousState.dockerProcesses.Count
    $containerChange = $currentState.containerCount - $previousState.containerCount
    
    if ([math]::Abs($processChange) -gt 2) {
        Write-RecoveryLog "Significant Docker process change detected" "WARN" @{
            previous_count = $previousState.dockerProcesses.Count
            current_count = $currentState.dockerProcesses.Count
            change = $processChange
        }
    }
    
    if ([math]::Abs($containerChange) -gt 5) {
        Write-RecoveryLog "Significant container count change detected" "WARN" @{
            previous_count = $previousState.containerCount
            current_count = $currentState.containerCount
            change = $containerChange
        }
    }
    
    return @{
        Status = "Stable"
        Reason = "No significant changes"
    }
}

function Analyze-RecoveryPatterns {
    <#
    .SYNOPSIS
    Analyze historical recovery patterns to identify issues
    #>
    
    if (-not (Test-Path $script:LogPath)) {
        return @{
            Pattern = "No data"
            Recommendation = "Monitor for patterns"
        }
    }
    
    try {
        $logs = Get-Content $script:LogPath | ForEach-Object { $_ | ConvertFrom-Json }
        $recentLogs = $logs | Where-Object { 
            [datetime]::Parse($_.timestamp) -gt (Get-Date).AddDays(-7) 
        }
        
        $reboots = $recentLogs | Where-Object { $_.message -match "SYSTEM REBOOT DETECTED" }
        $dockerCrashes = $recentLogs | Where-Object { $_.message -match "Docker crash detected" }
        $dockerRecoveries = $recentLogs | Where-Object { $_.message -match "Docker recovery detected" }
        
        $analysis = @{
            RebootCount = $reboots.Count
            DockerCrashCount = $dockerCrashes.Count
            DockerRecoveryCount = $dockerRecoveries.Count
            Pattern = "Unknown"
            Recommendation = "Continue monitoring"
        }
        
        # Identify patterns
        if ($analysis.DockerCrashCount -ge 3) {
            $analysis.Pattern = "Frequent Docker crashes"
            $analysis.Recommendation = "Investigate Docker resource limits and system stability"
        } elseif ($analysis.RebootCount -ge 2) {
            $analysis.Pattern = "Frequent system reboots"
            $analysis.Recommendation = "Check for hardware issues, Windows updates, or scheduled reboots"
        } elseif ($analysis.DockerCrashCount -gt $analysis.DockerRecoveryCount) {
            $analysis.Pattern = "Docker crashes without recovery"
            $analysis.Recommendation = "Manual intervention required for Docker recovery"
        } else {
            $analysis.Pattern = "Stable"
            $analysis.Recommendation = "System appears stable"
        }
        
        Write-RecoveryLog "Recovery pattern analysis completed" "INFO" $analysis
        return $analysis
        
    } catch {
        Write-RecoveryLog "Failed to analyze recovery patterns: $($_.Exception.Message)" "ERROR"
        return @{
            Pattern = "Analysis failed"
            Recommendation = "Check log file integrity"
        }
    }
}

function Start-SystemRecoveryMonitoring {
    <#
    .SYNOPSIS
    Start the system recovery monitoring loop
    #>
    
    Write-RecoveryLog "=== SYSTEM RECOVERY MONITORING STARTED ===" "SUCCESS"
    Write-RecoveryLog "Check interval: ${CheckInterval}s" "INFO"
    Write-RecoveryLog "Log file: $script:LogPath" "INFO"
    Write-RecoveryLog "State file: $script:StateFile" "INFO"
    
    # Initial state
    $initialState = Get-SystemState
    Save-SystemState $initialState
    
    Write-RecoveryLog "Initial system state captured" "INFO" @{
        boot_time = $initialState.bootTime
        uptime_minutes = [math]::Round($initialState.uptime.TotalMinutes, 1)
        docker_running = $initialState.dockerRunning
        container_count = $initialState.containerCount
        memory_usage_percent = $initialState.memoryUsage
    }
    
    # Analyze historical patterns
    $pattern = Analyze-RecoveryPatterns
    Write-RecoveryLog "Historical pattern: $($pattern.Pattern)" "INFO"
    Write-RecoveryLog "Recommendation: $($pattern.Recommendation)" "INFO"
    
    while ($true) {
        try {
            # Check for system reboot
            $rebootTest = Test-SystemReboot
            
            if ($rebootTest.Rebooted) {
                Write-RecoveryLog "Processing system reboot event..." "INFO"
                
                # Log reboot details
                if ($rebootTest.PreviousState) {
                    $downtime = $rebootTest.Downtime
                    Write-RecoveryLog "System downtime estimated: $($downtime.TotalDays.ToString('F2')) days" "INFO"
                }
                
                # Check if Docker auto-recovered after reboot
                Start-Sleep -Seconds 30  # Give Docker time to start
                $dockerTest = Test-DockerRecovery
                
                if ($dockerTest.Status -eq "Recovered") {
                    Write-RecoveryLog "Docker auto-recovered after system reboot" "SUCCESS"
                } else {
                    Write-RecoveryLog "Docker did not auto-recover after system reboot" "WARN"
                    Write-RecoveryLog "Manual Docker restart may be required" "WARN"
                }
            }
            
            # Check for Docker recovery/crash patterns
            $dockerTest = Test-DockerRecovery
            
            # Update state
            $currentState = Get-SystemState
            Save-SystemState $currentState
            
            # Periodic status logging
            $checkCount = (Get-Date).Minute % 20
            if ($checkCount -eq 0) {
                Write-RecoveryLog "System status check" "INFO" @{
                    uptime_hours = [math]::Round($currentState.uptime.TotalHours, 1)
                    docker_running = $currentState.dockerRunning
                    container_count = $currentState.containerCount
                    memory_usage_percent = $currentState.memoryUsage
                    system_load_percent = $currentState.systemLoad
                }
            }
            
        } catch {
            Write-RecoveryLog "System recovery monitoring error: $($_.Exception.Message)" "ERROR"
        }
        
        Start-Sleep -Seconds $CheckInterval
    }
}

# Start system recovery monitoring
Write-RecoveryLog "System Recovery Logger v1.0 starting..." "INFO"
Start-SystemRecoveryMonitoring
