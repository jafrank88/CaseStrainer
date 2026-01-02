# enhanced_docker_monitor.ps1 - Advanced Docker monitoring with self-healing capabilities
# Addresses recurring 24-48 hour Docker crashes with comprehensive monitoring

param(
    [int]$CheckInterval = 60,           # Health check interval in seconds
    [int]$DockerTimeout = 15,           # Docker response timeout
    [int]$MemoryThreshold = 85,         # Memory usage warning threshold (%)
    [int]$CpuThreshold = 90,            # CPU usage warning threshold (%)
    [int]$DiskThreshold = 90,           # Disk usage warning threshold (%)
    [switch]$EnableAutoRecovery,        # Enable automatic recovery actions
    [switch]$EnableResourceMonitoring,  # Enable resource monitoring
    [string]$LogPath = "logs\enhanced_monitor.log"
)

# Setup logging
$ErrorActionPreference = "Continue"
$script:LogPath = Join-Path $PSScriptRoot $LogPath
$script:StartTime = Get-Date
$script:LastDockerRestart = $null
$script:ConsecutiveFailures = 0
$script:MaxConsecutiveFailures = 5

# Ensure logs directory exists
$logDir = Split-Path $script:LogPath -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-EnhancedLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [switch]$NoConsole
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $uptime = "{0:hh\:mm\:ss}" - (Get-Date - $script:StartTime)
    $logEntry = "[$timestamp] [Uptime: $uptime] [$Level] $Message"
    
    # Write to log file
    Add-Content -Path $script:LogPath -Value $logEntry
    
    # Write to console if not disabled
    if (-not $NoConsole) {
        switch ($Level) {
            "ERROR" { Write-Host $logEntry -ForegroundColor Red }
            "WARN"  { Write-Host $logEntry -ForegroundColor Yellow }
            "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
            "CRITICAL" { Write-Host $logEntry -ForegroundColor Magenta }
            default { Write-Host $logEntry }
        }
    }
}

function Test-DockerComprehensive {
    <#
    .SYNOPSIS
    Comprehensive Docker health check with multiple test points
    #>
    
    $health = @{
        DockerInfo = $false
        DockerPs = $false
        DockerVersion = $false
        ContainerHealth = $false
        RedisConnection = $false
        ResponseTime = 0
        Overall = $false
    }
    
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        
        # Test 1: Docker info
        $infoJob = Start-Job -ScriptBlock { docker info 2>&1 }
        if (Wait-Job $infoJob -Timeout $DockerTimeout) {
            $infoOutput = Receive-Job $infoJob
            Remove-Job $infoJob -Force
            $health.DockerInfo = ($LASTEXITCODE -eq 0)
        } else {
            Stop-Job $infoJob -ErrorAction SilentlyContinue
            Remove-Job $infoJob -Force -ErrorAction SilentlyContinue
        }
        
        # Test 2: Docker ps
        $psJob = Start-Job -ScriptBlock { docker ps --format "table {{.Names}}\t{{.Status}}" 2>&1 }
        if (Wait-Job $psJob -Timeout $DockerTimeout) {
            $psOutput = Receive-Job $psJob
            Remove-Job $psJob -Force
            $health.DockerPs = ($LASTEXITCODE -eq 0)
        } else {
            Stop-Job $psJob -ErrorAction SilentlyContinue
            Remove-Job $psJob -Force -ErrorAction SilentlyContinue
        }
        
        # Test 3: Docker version
        if ($health.DockerInfo) {
            $versionJob = Start-Job -ScriptBlock { docker --version 2>&1 }
            if (Wait-Job $versionJob -Timeout 10) {
                $versionOutput = Receive-Job $versionJob
                Remove-Job $versionJob -Force
                $health.DockerVersion = ($LASTEXITCODE -eq 0)
            } else {
                Stop-Job $versionJob -ErrorAction SilentlyContinue
                Remove-Job $versionJob -Force -ErrorAction SilentlyContinue
            }
        }
        
        # Test 4: Container health (if Docker is responsive)
        if ($health.DockerPs) {
            try {
                $containers = docker ps --format "{{.Names}}" --filter "status=running" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $runningContainers = @($containers -split "`n" | Where-Object { $_.Trim() })
                    $health.ContainerHealth = ($runningContainers.Count -gt 0)
                    
                    # Test Redis connection specifically
                    if ($runningContainers -contains "casestrainer-redis-prod") {
                        $redisTest = docker exec casestrainer-redis-prod redis-cli ping 2>$null
                        $health.RedisConnection = ($redisTest -eq "PONG")
                    }
                }
            } catch {
                $health.ContainerHealth = $false
            }
        }
        
        $stopwatch.Stop()
        $health.ResponseTime = $stopwatch.ElapsedMilliseconds
        
        # Overall health
        $health.Overall = $health.DockerInfo -and $health.DockerPs -and $health.DockerVersion
        
    } catch {
        Write-EnhancedLog "Comprehensive health check failed: $($_.Exception.Message)" "ERROR"
    }
    
    return $health
}

function Get-DockerResourceUsage {
    <#
    .SYNOPSIS
    Monitor Docker Desktop resource usage
    #>
    
    $resources = @{
        MemoryUsage = 0
        MemoryLimit = 0
        MemoryPercent = 0
        CpuUsage = 0
        DiskUsage = 0
        ContainerCount = 0
        HighMemoryContainers = @()
        HighCpuContainers = @()
    }
    
    try {
        # Get Docker Desktop process stats
        $dockerProcesses = Get-Process "*Docker*" -ErrorAction SilentlyContinue
        foreach ($process in $dockerProcesses) {
            $resources.MemoryUsage += $process.WorkingSet64
            $resources.CpuUsage += $process.CPU
        }
        
        # Get container stats
        if ((Test-DockerComprehensive).DockerPs) {
            try {
                $containerStats = docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.CPUPerc}}" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $lines = $containerStats -split "`n" | Select-Object -Skip 1
                    $resources.ContainerCount = $lines.Count
                    
                    foreach ($line in $lines) {
                        if ($line.Trim()) {
                            $parts = $line -split "\s+" | Where-Object { $_ }
                            if ($parts.Count -ge 3) {
                                $containerName = $parts[0]
                                $memUsage = $parts[1]
                                $cpuUsage = $parts[2]
                                
                                # Parse memory usage (e.g., "1.2GiB / 2GiB")
                                if ($memUsage -match "([\d.]+)(\w+)\s*/\s*([\d.]+)(\w+)") {
                                    $used = [double]$matches[1]
                                    $limit = [double]$matches[3]
                                    $unit = $matches[2]
                                    
                                    if ($unit -eq "GiB") {
                                        $usedMB = $used * 1024
                                        $limitMB = $limit * 1024
                                    } elseif ($unit -eq "MiB") {
                                        $usedMB = $used
                                        $limitMB = $limit
                                    } else {
                                        continue
                                    }
                                    
                                    $memPercent = ($usedMB / $limitMB) * 100
                                    if ($memPercent -gt $MemoryThreshold) {
                                        $resources.HighMemoryContainers += @{
                                            Name = $containerName
                                            MemoryPercent = [math]::Round($memPercent, 1)
                                            MemoryUsage = $memUsage
                                        }
                                    }
                                }
                                
                                # Parse CPU usage (e.g., "15.25%")
                                if ($cpuUsage -match "([\d.]+)%") {
                                    $cpuPercent = [double]$matches[1]
                                    if ($cpuPercent -gt $CpuThreshold) {
                                        $resources.HighCpuContainers += @{
                                            Name = $containerName
                                            CpuPercent = [math]::Round($cpuPercent, 1)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } catch {
                Write-EnhancedLog "Failed to get container stats: $($_.Exception.Message)" "WARN"
            }
        }
        
        # Calculate system memory percentage
        $totalMemory = (Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory
        if ($totalMemory -gt 0) {
            $resources.MemoryPercent = [math]::Round(($resources.MemoryUsage / $totalMemory) * 100, 2)
        }
        
        # Convert to MB for readability
        $resources.MemoryUsage = [math]::Round($resources.MemoryUsage / 1MB, 2)
        
    } catch {
        Write-EnhancedLog "Resource monitoring failed: $($_.Exception.Message)" "ERROR"
    }
    
    return $resources
}

function Test-DockerResourceLimits {
    <#
    .SYNOPSIS
    Check if Docker is approaching resource limits
    #>
    
    $limits = @{
        MemoryWarning = $false
        MemoryCritical = $false
        CpuWarning = $false
        CpuCritical = $false
        DiskWarning = $false
        DiskCritical = $false
        ContainerIssues = $false
    }
    
    try {
        # Check system memory
        $os = Get-CimInstance -ClassName Win32_OperatingSystem
        $totalMemory = $os.TotalVisibleMemorySize
        $freeMemory = $os.FreePhysicalMemory
        $usedMemory = $totalMemory - $freeMemory
        $memoryPercent = ($usedMemory / $totalMemory) * 100
        
        $limits.MemoryWarning = $memoryPercent -gt $MemoryThreshold
        $limits.MemoryCritical = $memoryPercent -gt 95
        
        # Check disk space
        $systemDrive = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='C:'"
        $diskPercent = (($systemDrive.Size - $systemDrive.FreeSpace) / $systemDrive.Size) * 100
        $limits.DiskWarning = $diskPercent -gt $DiskThreshold
        $limits.DiskCritical = $diskPercent -gt 95
        
        # Check Docker-specific issues
        $resources = Get-DockerResourceUsage
        $limits.ContainerIssues = ($resources.HighMemoryContainers.Count -gt 0) -or ($resources.HighCpuContainers.Count -gt 0)
        
    } catch {
        Write-EnhancedLog "Resource limit check failed: $($_.Exception.Message)" "ERROR"
    }
    
    return $limits
}

function Invoke-EnhancedDockerRestart {
    <#
    .SYNOPSIS
    Enhanced Docker restart with multiple fallback methods
    #>
    
    param([string]$Reason = "Enhanced auto-recovery")
    
    Write-EnhancedLog "=== ENHANCED DOCKER RESTART INITIATED ===" "CRITICAL"
    Write-EnhancedLog "Reason: $Reason" "CRITICAL"
    
    $restartSuccess = $false
    $attempt = 1
    $maxAttempts = 3
    
    while (-not $restartSuccess -and $attempt -le $maxAttempts) {
        Write-EnhancedLog "Restart attempt $attempt of $maxAttempts" "WARN"
        
        try {
            # Method 1: Gentle restart (stop and start)
            Write-EnhancedLog "Attempting gentle restart (stop/start)..." "INFO"
            
            # Stop Docker Desktop
            Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
            Stop-Process -Name "com.docker.backend" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 5
            
            # Start Docker Desktop
            $dockerDesktop = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
            if (-not (Test-Path $dockerDesktop)) {
                $dockerDesktop = "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
            }
            
            if (Test-Path $dockerDesktop) {
                Start-Process -FilePath $dockerDesktop -WindowStyle Minimized
                Write-EnhancedLog "Docker Desktop started, waiting for readiness..." "INFO"
                
                # Wait for Docker to be ready (extended timeout)
                $ready = $false
                $maxWait = 180  # 3 minutes
                $waited = 0
                
                while (-not $ready -and $waited -lt $maxWait) {
                    Start-Sleep -Seconds 10
                    $waited += 10
                    
                    try {
                        $testJob = Start-Job -ScriptBlock { docker info 2>&1 }
                        if (Wait-Job $testJob -Timeout 15) {
                            $output = Receive-Job $testJob
                            Remove-Job $testJob -Force
                            $ready = ($LASTEXITCODE -eq 0)
                        } else {
                            Stop-Job $testJob -ErrorAction SilentlyContinue
                            Remove-Job $testJob -Force -ErrorAction SilentlyContinue
                        }
                    } catch {
                        $ready = $false
                    }
                    
                    if ($waited % 30 -eq 0) {
                        Write-EnhancedLog "Still waiting for Docker... (${waited}s elapsed)" "INFO"
                    }
                }
                
                if ($ready) {
                    $restartSuccess = $true
                    Write-EnhancedLog "=== ENHANCED DOCKER RESTART SUCCESSFUL ===" "SUCCESS"
                    Write-EnhancedLog "Docker ready after ${waited} seconds" "SUCCESS"
                } else {
                    Write-EnhancedLog "Docker did not become ready within ${maxWait} seconds" "ERROR"
                }
            } else {
                Write-EnhancedLog "Docker Desktop executable not found" "ERROR"
            }
            
        } catch {
            Write-EnhancedLog "Restart attempt $attempt failed: $($_.Exception.Message)" "ERROR"
        }
        
        $attempt++
        
        if (-not $restartSuccess -and $attempt -le $maxAttempts) {
            Write-EnhancedLog "Waiting 30 seconds before next attempt..." "WARN"
            Start-Sleep -Seconds 30
        }
    }
    
    if (-not $restartSuccess) {
        Write-EnhancedLog "=== ENHANCED DOCKER RESTART FAILED ===" "CRITICAL"
        Write-EnhancedLog "All $maxAttempts restart attempts failed" "CRITICAL"
    }
    
    return $restartSuccess
}

function Start-EnhancedMonitoring {
    <#
    .SYNOPSIS
    Start the enhanced Docker monitoring loop
    #>
    
    Write-EnhancedLog "=== ENHANCED DOCKER MONITORING STARTED ===" "SUCCESS"
    Write-EnhancedLog "Check interval: ${CheckInterval}s" "INFO"
    Write-EnhancedLog "Docker timeout: ${DockerTimeout}s" "INFO"
    Write-EnhancedLog "Memory threshold: ${MemoryThreshold}%" "INFO"
    Write-EnhancedLog "CPU threshold: ${CpuThreshold}%" "INFO"
    Write-EnhancedLog "Auto-recovery: $(if ($EnableAutoRecovery) { 'ENABLED' } else { 'DISABLED' })" "INFO"
    Write-EnhancedLog "Resource monitoring: $(if ($EnableResourceMonitoring) { 'ENABLED' } else { 'DISABLED' })" "INFO"
    
    $lastResourceCheck = Get-Date
    $resourceCheckInterval = 300  # Check resources every 5 minutes
    
    while ($true) {
        try {
            $timestamp = Get-Date -Format "HH:mm:ss"
            
            # Comprehensive health check
            $health = Test-DockerComprehensive
            
            if ($health.Overall) {
                if ($script:ConsecutiveFailures -gt 0) {
                    Write-EnhancedLog "Docker recovered after $script:ConsecutiveFailures consecutive failures" "SUCCESS"
                    $script:ConsecutiveFailures = 0
                }
                
                # Log periodic status
                $checkCount = (Get-Date).Minute % 10
                if ($checkCount -eq 0) {
                    Write-EnhancedLog "Health check: OK (Response: $($health.ResponseTime)ms, Containers: $($health.ContainerHealth), Redis: $($health.RedisConnection))" "INFO"
                }
            } else {
                $script:ConsecutiveFailures++
                Write-EnhancedLog "Health check FAILED (attempt $script:ConsecutiveFailures)" "ERROR"
                Write-EnhancedLog "  DockerInfo: $($health.DockerInfo), DockerPs: $($health.DockerPs), Version: $($health.DockerVersion)" "ERROR"
                Write-EnhancedLog "  Response time: $($health.ResponseTime)ms" "ERROR"
                
                # Auto-recovery if enabled
                if ($EnableAutoRecovery -and $script:ConsecutiveFailures -ge $script:MaxConsecutiveFailures) {
                    Write-EnhancedLog "Triggering auto-recovery after $script:ConsecutiveFailures consecutive failures" "CRITICAL"
                    
                    $restartSuccess = Invoke-EnhancedDockerRestart -Reason "Auto-recovery after $script:ConsecutiveFailures health check failures"
                    
                    if ($restartSuccess) {
                        $script:ConsecutiveFailures = 0
                        $script:LastDockerRestart = Get-Date
                        Write-EnhancedLog "Auto-recovery successful" "SUCCESS"
                        
                        # Wait for stabilization
                        Start-Sleep -Seconds 30
                    } else {
                        Write-EnhancedLog "Auto-recovery failed - manual intervention required" "CRITICAL"
                    }
                }
            }
            
            # Resource monitoring (if enabled)
            if ($EnableResourceMonitoring -and ((Get-Date) - $lastResourceCheck).TotalSeconds -ge $resourceCheckInterval) {
                $limits = Test-DockerResourceLimits
                $resources = Get-DockerResourceUsage
                
                $warnings = @()
                if ($limits.MemoryWarning) { $warnings += "Memory usage high" }
                if ($limits.CpuWarning) { $warnings += "CPU usage high" }
                if ($limits.DiskWarning) { $warnings += "Disk space low" }
                if ($limits.ContainerIssues) { $warnings += "Container resource issues" }
                
                if ($warnings.Count -gt 0) {
                    Write-EnhancedLog "Resource warnings: $($warnings -join ', ')" "WARN"
                    Write-EnhancedLog "  Memory: $($resources.MemoryPercent)% (Used: $($resources.MemoryUsage)MB)" "INFO"
                    
                    if ($resources.HighMemoryContainers.Count -gt 0) {
                        Write-EnhancedLog "  High memory containers:" "WARN"
                        foreach ($container in $resources.HighMemoryContainers) {
                            Write-EnhancedLog "    - $($container.Name): $($container.MemoryPercent)% ($($container.MemoryUsage))" "WARN"
                        }
                    }
                }
                
                $lastResourceCheck = Get-Date
            }
            
        } catch {
            Write-EnhancedLog "Monitoring loop error: $($_.Exception.Message)" "ERROR"
        }
        
        Start-Sleep -Seconds $CheckInterval
    }
}

# Start monitoring
Write-EnhancedLog "Enhanced Docker Monitor v2.0 starting..." "INFO"
Start-EnhancedMonitoring
