# Smart Resource Manager for CaseStrainer
# Automatically manages Dify containers based on CaseStrainer resource needs

param(
    [int]$CheckInterval = 60,  # Check every 60 seconds
    [int]$MemoryThreshold = 80,  # Restart Dify if memory usage > 80%
    [int]$CPUThreshold = 70,     # Restart Dify if CPU usage > 70%
    [int]$DifyRestartDelay = 900  # 15 minutes (900 seconds) before restarting Dify
)

# Configuration
$LogFile = "logs/smart_resource_manager.log"
$StateFile = "logs/resource_manager_state.json"
$CaseStrainerContainers = @(
    "casestrainer-backend-prod",
    "casestrainer-frontend-prod",
    "casestrainer-redis-prod",
    "casestrainer-rqworker-prod",
    "casestrainer-rqworker2-prod",
    "casestrainer-rqworker3-prod",
    "casestrainer-nginx-prod"
)
$DifyContainers = @(
    "docker-nginx-1",
    "docker-api-1",
    "docker-worker-1",
    "docker-worker_beat-1",
    "docker-plugin_daemon-1",
    "docker-db-1",
    "docker-redis-1",
    "docker-web-1",
    "docker-sandbox-1",
    "docker-weaviate-1",
    "docker-ssrf_proxy-1"
)

# Ensure logs directory exists
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

function Write-Log {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logMessage -Force

}

function Get-ContainerStats {
    param($ContainerNames)

    try {
        $stats = docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>$null
        if (-not $stats) { return @{} }

        $result = @{}
        foreach ($line in $stats) {
            if ($line -match "^\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$") {
                $container = $matches[1]
                $cpu = $matches[2] -replace '%', ''
                $memUsage = $matches[3]
                $memPerc = $matches[4] -replace '%', ''

                if ($ContainerNames -contains $container) {
                    $result[$container] = @{
                        CPU = [double]$cpu
                        MemoryPercent = [double]$memPerc
                        MemoryUsage = $memUsage
                    }
                }
            }
        }
        return $result
    }
    catch {
        Write-Log "Error getting container stats: $($_.Exception.Message)" -Level "ERROR"
        return @{}
    }
}

function Get-SystemResources {
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

function Test-CaseStrainerHealth {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

function Stop-DifyContainers {
    [CmdletBinding(SupportsShouldProcess)]
    param()

    Write-Log "Stopping Dify containers to free up resources for CaseStrainer" -Level "WARN"



    try {
        $stoppedContainers = @()
        foreach ($container in $DifyContainers) {
            $containerExists = docker ps --filter "name=$container" --format "{{.Names}}" 2>$null
            if ($containerExists) {
                $null = docker stop $container 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $stoppedContainers += $container
                    Write-Log "Stopped container: $container" -Level "INFO"
                }
            }
        }

        if ($stoppedContainers.Count -gt 0) {
            $state = @{
                DifyStoppedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
                StoppedContainers = $stoppedContainers
                Reason = "Resource pressure - prioritizing CaseStrainer"
            }
            $state | ConvertTo-Json | Out-File -FilePath $StateFile -Force
            Write-Log "Stopped $($stoppedContainers.Count) Dify containers" -Level "INFO"
        }
    }
    catch {
        Write-Log "Error stopping Dify containers: $($_.Exception.Message)" -Level "ERROR"
    }
}

function Start-DifyContainers {
    [CmdletBinding(SupportsShouldProcess)]
    param()

    Write-Log "Starting Dify containers after resource pressure has eased" -Level "INFO"



    try {
        $startedContainers = @()
        foreach ($container in $DifyContainers) {
            $containerExists = docker ps -a --filter "name=$container" --format "{{.Names}}" 2>$null
            if ($containerExists) {
                $null = docker start $container 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $startedContainers += $container
                    Write-Log "Started container: $container" -Level "INFO"
                }
            }
        }

        if ($startedContainers.Count -gt 0) {
            if (Test-Path $StateFile) {
                Remove-Item $StateFile -Force
            }
            Write-Log "Started $($startedContainers.Count) Dify containers" -Level "INFO"
        }
    }
    catch {
        Write-Log "Error starting Dify containers: $($_.Exception.Message)" -Level "ERROR"
    }
}

function Test-ShouldRestartDify {
    # Check if Dify was stopped and enough time has passed
    if (Test-Path $StateFile) {
        try {
            $state = Get-Content $StateFile | ConvertFrom-Json
            $stoppedAt = [DateTime]::ParseExact($state.DifyStoppedAt, "yyyy-MM-dd HH:mm:ss", $null)
            $timeSinceStopped = (Get-Date) - $stoppedAt

            if ($timeSinceStopped.TotalSeconds -ge $DifyRestartDelay) {
                Write-Log "Dify has been stopped for $([math]::Round($timeSinceStopped.TotalMinutes, 1)) minutes - considering restart" -Level "INFO"
                return $true
            }
        }
        catch {
            Write-Log "Error reading state file: $($_.Exception.Message)" -Level "ERROR"
        }
    }
    return $false
}

function Test-ResourcePressure {
    param($SystemResources, $CaseStrainerStats)

    # Check system-wide resource pressure
    $highCPU = $SystemResources.CPU -gt $CPUThreshold
    $highMemory = $SystemResources.Memory -gt $MemoryThreshold

    # Check if CaseStrainer containers are struggling
    $caseStrainerCPU = 0
    $caseStrainerMemory = 0
    $healthyContainers = 0

    foreach ($container in $CaseStrainerContainers) {
        if ($CaseStrainerStats.ContainsKey($container)) {
            $stats = $CaseStrainerStats[$container]
            $caseStrainerCPU += $stats.CPU
            $caseStrainerMemory += $stats.MemoryPercent
            $healthyContainers++
        }
    }

    if ($healthyContainers -gt 0) {
        $avgCPU = $caseStrainerCPU / $healthyContainers
        $avgMemory = $caseStrainerMemory / $healthyContainers
    } else {
        $avgCPU = 0
        $avgMemory = 0
    }

    # Determine if there's resource pressure
    $resourcePressure = $highCPU -or $highMemory -or $avgCPU -gt 50 -or $avgMemory -gt 60

    if ($resourcePressure) {
        Write-Log "Resource pressure detected - CPU: $($SystemResources.CPU)%, Memory: $($SystemResources.Memory)%, CaseStrainer Avg CPU: $([math]::Round($avgCPU, 1))%, Avg Memory: $([math]::Round($avgMemory, 1))%" -Level "WARN"
    }

    return $resourcePressure
}

# Main monitoring loop
Write-Log "Starting Smart Resource Manager for CaseStrainer" -Level "INFO"
Write-Log "Configuration: CheckInterval=$CheckInterval, MemoryThreshold=$MemoryThreshold%, CPUThreshold=$CPUThreshold%, DifyRestartDelay=$DifyRestartDelay seconds" -Level "INFO"
Write-Log "CaseStrainer containers: $($CaseStrainerContainers -join ', ')" -Level "INFO"
Write-Log "Dify containers: $($DifyContainers -join ', ')" -Level "INFO"

try {
    while ($true) {
        # Get current resource usage
        $systemResources = Get-SystemResources
        $caseStrainerStats = Get-ContainerStats -ContainerNames $CaseStrainerContainers
        $difyStats = Get-ContainerStats -ContainerNames $DifyContainers

        # Check if Dify containers are running
        $difyRunning = $difyStats.Count -gt 0

        # Test CaseStrainer health
        $caseStrainerHealthy = Test-CaseStrainerHealth

        # Check for resource pressure
        $resourcePressure = Test-ResourcePressure -SystemResources $systemResources -CaseStrainerStats $caseStrainerStats

        # Decision logic
        if ($resourcePressure -and $difyRunning -and $caseStrainerHealthy) {
            Write-Log "Resource pressure detected while CaseStrainer is healthy - stopping Dify to prioritize CaseStrainer" -Level "WARN"
            Stop-DifyContainers
        }
        elseif ((-not $resourcePressure) -and (-not $difyRunning) -and (Test-ShouldRestartDify)) {
            Write-Log "Resource pressure has eased and enough time has passed - restarting Dify" -Level "INFO"
            Start-DifyContainers
        }



        Write-Log "Status: System CPU: $($systemResources.CPU)%, Memory: $($systemResources.Memory)%, CaseStrainer Healthy: $caseStrainerHealthy, Dify Running: $difyRunning, Resource Pressure: $resourcePressure" -Level "INFO"

        # Wait for next check
        Start-Sleep -Seconds $CheckInterval
    }
}
catch {
    Write-Log "Fatal error in resource manager: $($_.Exception.Message)" -Level "ERROR"
    throw
}
finally {
    Write-Log "Smart Resource Manager stopped" -Level "INFO"
}
