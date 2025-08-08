# Docker Auto-Recovery System for CaseStrainer
# Monitors Docker Desktop health and automatically restarts when needed

param(
    [int]$CheckInterval = 30,  # Check every 30 seconds
    [int]$MaxRestartAttempts = 3,  # Maximum restart attempts per hour
    [switch]$EnableAutoRestart = $true,
    [switch]$Verbose,
    [switch]$DryRun
)

# Configuration
$LogFile = "logs/docker_auto_recovery.log"
$StateFile = "logs/docker_recovery_state.json"
$RestartHistoryFile = "logs/docker_restart_history.json"

# Ensure logs directory exists
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

# Initialize restart history if it doesn't exist
if (!(Test-Path $RestartHistoryFile)) {
    @{
        RestartCount = 0
        LastRestartTime = $null
        RestartHistory = @()
    } | ConvertTo-Json | Out-File -FilePath $RestartHistoryFile -Force
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

function Test-DockerHealth {
    param(
        [int]$TimeoutSeconds = 30
    )
    
    try {
        Write-Log "Testing Docker daemon communication with timeout protection..." -Level "INFO"
        
        # Test Docker version with timeout
        $versionJob = Start-Job -ScriptBlock { docker --version 2>$null }
        $versionResult = Wait-Job -Job $versionJob -Timeout $TimeoutSeconds
        
        if (-not $versionResult) {
            Stop-Job -Job $versionJob
            Remove-Job -Job $versionJob
            Write-Log "Docker version check timed out" -Level "ERROR"
            return $false
        }
        
        $dockerVersion = Receive-Job -Job $versionJob
        Remove-Job -Job $versionJob
        
        if (-not $dockerVersion) {
            Write-Log "Docker command not responding" -Level "ERROR"
            return $false
        }
        
        Write-Log "Docker version: $dockerVersion" -Level "INFO"
        
        # Test Docker daemon with timeout
        $infoJob = Start-Job -ScriptBlock { docker info 2>$null }
        $infoResult = Wait-Job -Job $infoJob -Timeout $TimeoutSeconds
        
        if (-not $infoResult) {
            Stop-Job -Job $infoJob
            Remove-Job -Job $infoJob
            Write-Log "Docker daemon info check timed out" -Level "ERROR"
            return $false
        }
        
        $dockerInfo = Receive-Job -Job $infoJob
        Remove-Job -Job $infoJob
        
        if (-not $dockerInfo) {
            Write-Log "Docker daemon not responding" -Level "ERROR"
            return $false
        }
        
        Write-Log "Docker daemon is responsive" -Level "INFO"
        
        # Test container listing with timeout
        $containersJob = Start-Job -ScriptBlock { docker ps 2>$null }
        $containersResult = Wait-Job -Job $containersJob -Timeout $TimeoutSeconds
        
        if (-not $containersResult) {
            Stop-Job -Job $containersJob
            Remove-Job -Job $containersJob
            Write-Log "Container listing timed out" -Level "ERROR"
            return $false
        }
        
        $containers = Receive-Job -Job $containersJob
        Remove-Job -Job $containersJob
        
        if (-not $containers) {
            Write-Log "Cannot list containers (or no containers running)" -Level "WARN"
            # This might be OK - just no containers
            return $true
        }
        
        Write-Log "Container listing successful" -Level "INFO"
        return $true
        
    }
    catch {
        Write-Log "Docker health check failed: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Test-DockerService {
    param(
        [int]$TimeoutSeconds = 30
    )
    
    try {
        Write-Log "Testing Docker service status..." -Level "INFO"
        
        # First check if Docker is working with timeout
        $dockerJob = Start-Job -ScriptBlock { docker --version 2>$null }
        $dockerResult = Wait-Job -Job $dockerJob -Timeout $TimeoutSeconds
        
        if ($dockerResult) {
            $dockerVersion = Receive-Job -Job $dockerJob
            Remove-Job -Job $dockerJob -Force
            
            if ($dockerVersion) {
                Write-Log "Docker command is working: $dockerVersion" -Level "INFO"
                return $true
            }
        } else {
            Stop-Job -Job $dockerJob -Force
            Remove-Job -Job $dockerJob -Force
        }

        # If Docker command doesn't work, check the service
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if (-not $service) {
            Write-Log "Docker service not found" -Level "ERROR"
            return $false
        }

        Write-Log "Docker service status: $($service.Status)" -Level "INFO"
        return $service.Status -eq "Running"
        
    }
    catch {
        Write-Log "Docker service check failed: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Test-CaseStrainerContainers {
    try {
        $caseStrainerContainers = @(
            "casestrainer-backend-prod",
            "casestrainer-frontend-prod",
            "casestrainer-redis-prod",
            "casestrainer-nginx-prod"
        )
        
        $runningContainers = docker ps --filter "name=casestrainer" --format "{{.Names}}" 2>$null
        $runningCount = ($runningContainers | Measure-Object).Count
        
        if ($runningCount -lt 4) {
            Write-Log "Only $runningCount CaseStrainer containers running (expected 4+)" -Level "WARN"
            return $false
        }
        
        return $true
    }
    catch {
        Write-Log "Error checking CaseStrainer containers: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Get-RestartHistory {
    try {
        if (Test-Path $RestartHistoryFile) {
            $history = Get-Content $RestartHistoryFile | ConvertFrom-Json
if (-not $history.RestartHistory) { $history.RestartHistory = @() }
            return $history
        }
        return @{
            RestartCount = 0
            LastRestartTime = $null
            RestartHistory = @()
        }
    }
    catch {
        Write-Log "Error reading restart history: $($_.Exception.Message)" -Level "ERROR"
        return @{
            RestartCount = 0
            LastRestartTime = $null
            RestartHistory = @()
        }
    }
}

function Update-RestartHistory {
    param($Reason)
    
    try {
        $history = Get-RestartHistory
        $now = Get-Date
        
        # Add to restart history
        $restartRecord = @{
            Time = $now.ToString("yyyy-MM-dd HH:mm:ss")
            Reason = $Reason
        }
        
        $history.RestartHistory += $restartRecord
        
        # Keep only last 24 hours of history
        $cutoffTime = $now.AddHours(-24)
        $history.RestartHistory = $history.RestartHistory | Where-Object {
            [DateTime]::ParseExact($_.Time, "yyyy-MM-dd HH:mm:ss", $null) -gt $cutoffTime
        }
        
        # Update restart count for last hour
        $lastHourRestarts = $history.RestartHistory | Where-Object {
            [DateTime]::ParseExact($_.Time, "yyyy-MM-dd HH:mm:ss", $null) -gt $now.AddHours(-1)
        }
        $history.RestartCount = $lastHourRestarts.Count
        $history.LastRestartTime = $now.ToString("yyyy-MM-dd HH:mm:ss")
        
        $history | ConvertTo-Json -Depth 10 | Out-File -FilePath $RestartHistoryFile -Force
    }
    catch {
        Write-Log "Error updating restart history: $($_.Exception.Message)" -Level "ERROR"
    }
}

function Test-ShouldRestart {
    $history = Get-RestartHistory
    
    # Check if we've restarted too many times recently
    if ($history.RestartCount -ge $MaxRestartAttempts) {
        Write-Log "Too many restart attempts ($($history.RestartCount)) in the last hour - skipping restart" -Level "WARN"
        return $false
    }
    
    # Check if last restart was too recent (minimum 5 minutes between restarts)
    if ($history.LastRestartTime) {
        $lastRestart = [DateTime]::ParseExact($history.LastRestartTime, "yyyy-MM-dd HH:mm:ss", $null)
        $timeSinceLastRestart = (Get-Date) - $lastRestart
        
        if ($timeSinceLastRestart.TotalMinutes -lt 5) {
            Write-Log "Last restart was $([math]::Round($timeSinceLastRestart.TotalMinutes, 1)) minutes ago - waiting before next restart" -Level "INFO"
            return $false
        }
    }
    
    return $true
}

function Restart-DockerDesktop {
    param($Reason)
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would restart Docker Desktop - Reason: $Reason" -Level "INFO"
        return $true
    }
    
    if (-not $EnableAutoRestart) {
        Write-Log "Auto-restart disabled - Docker Desktop needs manual restart" -Level "WARN"
        return $false
    }
    
    if (-not (Test-ShouldRestart)) {
        return $false
    }
    
    Write-Log "Restarting Docker Desktop - Reason: $Reason" -Level "WARN"
    
    try {
        # Stop Docker processes
        $processes = @("Docker Desktop", "com.docker.backend", "com.docker.build")
        foreach ($proc in $processes) {
            $runningProcs = Get-Process -Name $proc -ErrorAction SilentlyContinue
            if ($runningProcs) {
                Write-Log "Stopping $proc processes..." -Level "INFO"
                $runningProcs | Stop-Process -Force -ErrorAction SilentlyContinue
            }
        }
        
        # Wait for processes to stop
        Start-Sleep -Seconds 10
        
        # Start Docker Desktop
        Write-Log "Starting Docker Desktop..." -Level "INFO"
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Minimized
        
        # Wait for Docker to initialize
        Start-Sleep -Seconds 30
        
        # Update restart history
        Update-RestartHistory -Reason $Reason
        
        Write-Log "Docker Desktop restart completed" -Level "INFO"
        return $true
    }
    catch {
        Write-Log "Error restarting Docker Desktop: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Test-SystemResources {
    try {
        $cpu = (Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples[0].CookedValue
        $memory = (Get-Counter "\Memory\% Committed Bytes In Use").CounterSamples[0].CookedValue
        
        return @{
            CPU = [math]::Round($cpu, 2)
            Memory = [math]::Round($memory, 2)
        }
    }
    catch {
        Write-Log "Error getting system resources: $($_.Exception.Message)" -Level "ERROR"
        return @{ CPU = 0; Memory = 0 }
    }
}

# Main monitoring loop
if ($DryRun) {
    Write-Log "DryRun mode: skipping health checks to avoid hanging" -Level "INFO"
    Write-Log "DryRun complete, exiting" -Level "INFO"
    exit 0
}

Write-Log "Starting Docker Auto-Recovery System" -Level "INFO"
Write-Log "Configuration: CheckInterval=$CheckInterval, MaxRestartAttempts=$MaxRestartAttempts, AutoRestart=$EnableAutoRestart" -Level "INFO"

try {
    while ($true) {
        $issues = @()
        
        # Check Docker health with timeout
        $dockerHealthy = Test-DockerHealth -TimeoutSeconds 30
        if (-not $dockerHealthy) {
            $issues += "Docker daemon communication failure"
        }
        
        # Check Docker service with timeout
        $serviceHealthy = Test-DockerService -TimeoutSeconds 30
        if (-not $serviceHealthy) {
            $issues += "Docker service not running"
        }
        
        # Check CaseStrainer containers
        if (-not (Test-CaseStrainerContainers)) {
            $issues += "CaseStrainer containers not running properly"
        }
        
        # Get system resources
        $systemResources = Test-SystemResources
        
        # Log status
        $statusMessage = "Status: CPU: $($systemResources.CPU)%, Memory: $($systemResources.Memory)%, Issues: $($issues.Count)"
        Write-Log $statusMessage -Level "INFO"
        
        # Take action if issues detected
        if ($issues.Count -gt 0) {
            $reason = $issues -join "; "
            Write-Log "Issues detected: $reason" -Level "WARN"
            
            if (Test-ShouldRestart) {
                Restart-DockerDesktop -Reason $reason
            } else {
                Write-Log "Skipping restart due to restart limits" -Level "WARN"
            }
        } else {
            Write-Log "All systems healthy" -Level "INFO"
        }
        
        # Wait for next check
        Start-Sleep -Seconds $CheckInterval
    }
}
catch {
    Write-Log "Fatal error in auto-recovery system: $($_.Exception.Message)" -Level "ERROR"
    throw
}
finally {
    Write-Log "Docker Auto-Recovery System stopped" -Level "INFO"
}
