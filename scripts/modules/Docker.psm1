# Docker.psm1 - Docker management for CaseStrainer

# Ensure errors are caught
$ErrorActionPreference = 'Stop'

# Configuration
$script:DockerConfig = @{
    # Paths
    DockerPath = "docker"
    DockerComposePath = "docker-compose"
    DockerDesktopPath = "C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"
    DockerDataPath = "$env:USERPROFILE\\.docker"
    DockerProgramDataPath = "$env:ProgramData\\Docker"
    
    # Service names
    DockerServiceName = "com.docker.service"
    
    # Timeouts (in seconds)
    DockerStartTimeout = 300  # 5 minutes
    ContainerStartTimeout = 300  # 5 minutes
    CommandTimeout = 60  # 1 minute
    
    # Retry settings
    MaxRetryAttempts = 3
    RetryDelay = 5  # seconds
    
    # WSL configuration
    WSLDistroName = "docker-desktop"
    
    # Logging
    LogDirectory = "$env:USERPROFILE\\CaseStrainer\\logs"
    MaxLogFiles = 10
    
    # Resource limits
    MaxContainers = 10
    MaxMemoryGB = 12  # 12GB or 75% of system memory, whichever is smaller
    MaxCPUPercent = 75  # 75% of available CPU
    WSLDistros = @("docker-desktop", "docker-desktop-data")
}

# Start Docker Desktop and ensure the service is running
function Start-DockerDesktop {
    [CmdletBinding()]
    param()
    
    try {
        Write-Host "=== Starting Docker Desktop ===" -ForegroundColor Cyan
        
        # 1. Check if Docker Desktop process is running
        $dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        
        if (-not $dockerProcess) {
            Write-Host "Starting Docker Desktop application..." -ForegroundColor Yellow
            Start-Process -FilePath $script:DockerConfig.DockerDesktopPath -PassThru | Out-Null
            
            # Wait for the process to start
            $maxWaitTime = 30 # seconds
            $startTime = Get-Date
            
            while (-not (Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue) -and 
                   ((Get-Date) - $startTime).TotalSeconds -lt $maxWaitTime) {
                Write-Host "." -NoNewline -ForegroundColor Yellow
                Start-Sleep -Seconds 2
            }
            
            if (-not (Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue)) {
                throw "Docker Desktop process failed to start"
            }
            
            Write-Host "`nDocker Desktop process started" -ForegroundColor Green
        } else {
            Write-Host "Docker Desktop is already running" -ForegroundColor Green
        }
        
        # 2. Ensure Docker service is running
        Write-Host "`nChecking Docker service status..." -ForegroundColor Cyan
        $service = Get-Service -Name $script:DockerConfig.DockerServiceName -ErrorAction SilentlyContinue
        
        if (-not $service) {
            throw "Docker service not found. Please reinstall Docker Desktop."
        }
        
        if ($service.Status -ne 'Running') {
            Write-Host "Starting Docker service..." -ForegroundColor Yellow
            Start-Service -Name $script:DockerConfig.DockerServiceName -ErrorAction Stop
            
            # Wait for service to start
            $service.WaitForStatus('Running', '00:00:30')
            Write-Host "Docker service started successfully" -ForegroundColor Green
        } else {
            Write-Host "Docker service is already running" -ForegroundColor Green
        }
        
        # 3. Verify Docker daemon is responding
        Write-Host "`nVerifying Docker daemon is responsive..." -ForegroundColor Cyan
        $maxRetries = 10
        $retryCount = 0
        $daemonReady = $false
        
        while ($retryCount -lt $maxRetries -and -not $daemonReady) {
            try {
                $dockerInfo = docker info 2>&1
                if ($LASTEXITCODE -eq 0) {
                    $daemonReady = $true
                    $dockerVersion = ($dockerInfo | Select-Object -First 1) -replace '^Client: Docker Engine - Community ', ''
                    Write-Host "Docker daemon is running (Version: $dockerVersion)" -ForegroundColor Green
                    break
                }
            } catch {}
            
            $retryCount++
            Write-Host "." -NoNewline -ForegroundColor Yellow
            Start-Sleep -Seconds 3
        }
        
        if (-not $daemonReady) {
            throw "Failed to communicate with Docker daemon after $maxRetries attempts. Please check Docker Desktop logs."
        }
        
        # 4. Reset WSL if needed (common issue on Windows)
        if (Get-Command wsl -ErrorAction SilentlyContinue) {
            Write-Host "`nChecking WSL status..." -ForegroundColor Cyan
            $wslStatus = wsl --status 2>&1 | Out-String
            
            if ($wslStatus -match 'The Windows Subsystem for Linux has not been enabled') {
                Write-Host "WSL is not enabled. Enabling WSL..." -ForegroundColor Yellow
                Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart -WarningAction SilentlyContinue | Out-Null
                Write-Host "WSL has been enabled. A system restart may be required." -ForegroundColor Yellow
            }
            
            # Reset WSL if Docker is configured to use it
            if ($wslStatus -match 'Default Version: 2' -or $wslStatus -match 'Default Version: 2.0') {
                Write-Host "Resetting WSL..." -ForegroundColor Yellow
                wsl --shutdown
                Start-Sleep -Seconds 5
                Write-Host "WSL has been reset" -ForegroundColor Green
            }
        }
        
        Write-Host "`n=== Docker is ready ===" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Host "`n[ERROR] Failed to start Docker: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "`nTroubleshooting steps:" -ForegroundColor Yellow
        Write-Host "1. Try restarting Docker Desktop manually" -ForegroundColor White
        Write-Host "2. Check if virtualization is enabled in BIOS" -ForegroundColor White
        Write-Host "3. Run 'wsl --update' in an administrator PowerShell" -ForegroundColor White
        Write-Host "4. Restart your computer if the issue persists" -ForegroundColor White
        
        return $false
    }
}

# Import Docker Health module
$dockerHealthModule = Join-Path $PSScriptRoot "DockerHealth.psm1"
if (Test-Path $dockerHealthModule) {
    try {
        # Import the module and get its exported commands
        $module = Import-Module $dockerHealthModule -Force -ErrorAction Stop -PassThru -WarningAction SilentlyContinue
        
        # Re-export the health check functions
        $exportedFunctions = @(
            'Test-DockerProcesses',
            'Test-DockerCLI',
            'Test-DockerDaemon',
            'Test-DockerResources',
            'Invoke-DockerHealthCheck'
        )
        
        # Export the functions in the current scope
        foreach ($func in $exportedFunctions) {
            Export-ModuleMember -Function $func -ErrorAction SilentlyContinue
        }
    } catch {
        Write-Warning "Failed to import DockerHealth module: $_"
    }
}

# Export local functions
$localFunctions = @(
    'Start-DockerDesktop',
    'Stop-DockerDesktop',
    'Test-DockerAvailability',
    'Get-DockerResourceUsage',
    'Invoke-DockerCleanup',
    'Start-DockerHealthMonitor',
    'Stop-DockerHealthMonitor'
)

# Export all functions
foreach ($func in $localFunctions) {
    Export-ModuleMember -Function $func -ErrorAction SilentlyContinue
}

# Check if Docker is available with enhanced diagnostics
function Test-DockerAvailability {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [switch]$Detailed,
        [switch]$AutoFix
    )
    
    # If DockerHealth module is available, use its comprehensive check
    if (Get-Command -Name "Invoke-DockerHealthCheck" -ErrorAction SilentlyContinue) {
        $healthResult = Invoke-DockerHealthCheck -Detailed:$Detailed -IncludeContainerTest:$false
        
        if (-not $healthResult.Overall -and $AutoFix) {
            Write-Host "`nAttempting to fix Docker issues..." -ForegroundColor Cyan
            if (Start-DockerDesktop) {
                Start-Sleep -Seconds 5
                $healthResult = Invoke-DockerHealthCheck -Detailed:$Detailed -IncludeContainerTest:$false
            }
        }
        
        return $healthResult.Overall
    }
    
    # Fallback to basic check if DockerHealth module is not available
    try {
        Write-Host "`n=== Basic Docker Health Check ===" -ForegroundColor Cyan
        $dockerInfo = docker info --format json 2>&1 | ConvertFrom-Json -ErrorAction SilentlyContinue
        
        # If JSON parsing failed, try the old way
        if (-not $dockerInfo) {
            $dockerInfo = docker info 2>&1 | Where-Object { $_ -notmatch 'WARNING' }
            if ($LASTEXITCODE -ne 0) {
                throw "Docker daemon not accessible"
            }
        }
        
        # Extract version and OS info
        $dockerVersion = if ($dockerInfo.ServerVersion) {
            $dockerInfo.ServerVersion
        } else {
            ($dockerInfo | Where-Object { $_ -match 'Server Version:' } | ForEach-Object { $_.Split(':', 2)[1].Trim() })
        }
        
        $osInfo = if ($dockerInfo.OperatingSystem) {
            $dockerInfo.OperatingSystem
        } else {
            ($dockerInfo | Where-Object { $_ -match 'Operating System:' } | ForEach-Object { $_.Split(':', 2)[1].Trim() })
        }
        
        Write-Host ("[OK] Docker Daemon is running (Version: {0}, OS: {1})" -f $dockerVersion, $osInfo) -ForegroundColor Green
        
        # Check for common issues
        $warnings = @()
        if ($dockerInfo -match 'WARNING: No blkio throttle') {
            $warnings += "Blkio throttle not supported (non-critical)"
        }
        
        if ($warnings) {
            Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
            Write-Host ($warnings -join ", ") -ForegroundColor Yellow
        }
        
        return $true
        
    } catch {
        $errorMsg = $_.Exception.Message
        
        # Check if Docker Desktop is running but daemon is not accessible
        $dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        if ($dockerProcess) {
            Write-Host "[WARNING] Docker Desktop is running but daemon is not responding" -ForegroundColor Yellow
            Write-Host "   This might indicate a Docker service issue. Try these steps:" -ForegroundColor Yellow
            Write-Host "   1. Right-click the Docker icon in the system tray"
            Write-Host "   2. Select 'Troubleshoot'"
            Write-Host "   3. Choose 'Restart' or 'Reset to factory defaults'" -ForegroundColor Yellow
            
            if ($AutoFix) {
                Write-Host "`nAttempting to restart Docker Desktop..." -ForegroundColor Cyan
                if (Start-DockerDesktop) {
                    Start-Sleep -Seconds 5
                    return Test-DockerAvailability -Detailed:$Detailed -AutoFix:$false
                }
            }
        } else {
            Write-Host "[ERROR] Docker Desktop is not running" -ForegroundColor Red
            
            if ($AutoFix) {
                Write-Host "`nAttempting to start Docker Desktop..." -ForegroundColor Cyan
                if (Start-DockerDesktop) {
                    Start-Sleep -Seconds 5
                    return Test-DockerAvailability -Detailed:$Detailed -AutoFix:$false
                }
            }
        }
        
        Write-Host ("[ERROR] Docker daemon is not accessible: {0}" -f $errorMsg) -ForegroundColor Red
        Write-Host "`nTroubleshooting steps:" -ForegroundColor Cyan
        Write-Host "1. Open Docker Desktop manually and wait for it to fully start"
        Write-Host "2. Check if Docker service is running in Windows Services (services.msc)"
        Write-Host "3. Right-click Docker Desktop icon → Troubleshoot → Restart"
        Write-Host "4. Restart your computer if the issue persists"
        
        return $false
    }
}

# Build Docker containers
function Start-DockerBuild {
    param(
        [string]$DockerComposeFile = "docker-compose.yml",
        [switch]$NoCache,
        [switch]$ForceRebuild
    )
    
    try {
        if (-not (Test-Path $DockerComposeFile)) {
            throw "Docker Compose file not found: $DockerComposeFile"
        }
        
        $buildArgs = @("-f", $DockerComposeFile, "build")
        if ($NoCache) { $buildArgs += "--no-cache" }
        if ($ForceRebuild) { $buildArgs += "--force-rm", "--pull" }
        
        Write-Host "Building Docker containers..." -ForegroundColor Cyan
        $process = Start-Process -FilePath "docker-compose" -ArgumentList $buildArgs -NoNewWindow -PassThru -Wait
        
        if ($process.ExitCode -eq 0) {
            Write-Host "Build successful" -ForegroundColor Green
            return $true
        } else {
            throw "Build failed with code $($process.ExitCode)"
        }
    } catch {
        Write-Host "Build error: $_" -ForegroundColor Red
        return $false
    }
}

# Get Docker system resource usage with enhanced error handling
function Get-DockerResourceUsage {
    [CmdletBinding()]
    param()
    
    $result = [PSCustomObject]@{
        Containers = @()
        ImagesSize = 0
        ImagesReclaimable = 0
        ContainersSize = 0
        VolumesSize = 0
        BuilderSize = 0
        LastChecked = Get-Date
        Errors = @()
        Warnings = @()
    }
    
    # 1. Try to get container stats with a timeout
    try {
        $stats = & {
            $job = Start-Job -ScriptBlock { docker stats --no-stream --format '{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}|{{.BlockIO}}' 2>&1 }
            if (Wait-Job $job -Timeout 10) {
                return Receive-Job $job
            } else {
                Stop-Job $job -ErrorAction SilentlyContinue
                Remove-Job $job -Force -ErrorAction SilentlyContinue
                throw 'Timeout getting container stats'
            }
        }
        
        if ($LASTEXITCODE -eq 0) {
            $result.Containers = foreach ($line in $stats) {
                $parts = $line -split '\|'
                if ($parts.Count -ge 5) {
                    [PSCustomObject]@{
                        Name = $parts[0]
                        CPU = $parts[1].Trim()
                        Memory = $parts[2].Trim()
                        Network = $parts[3].Trim()
                        Disk = $parts[4].Trim()
                    }
                }
            }
        } else {
            $result.Warnings += "Failed to get container stats: $($stats -join ' ')"
        }
    } catch {
        $result.Warnings += "Error getting container stats: $($_.Exception.Message)"
    }
    
    # 2. Try to get system disk usage with a timeout and fallback
    try {
        $dfOutput = & {
            $job = Start-Job -ScriptBlock { docker system df --format '{{json .}}' 2>&1 }
            if (Wait-Job $job -Timeout 10) {
                $output = Receive-Job $job
                if ($LASTEXITCODE -eq 0) {
                    return $output | ConvertFrom-Json -ErrorAction SilentlyContinue
                }
                return $null
            } else {
                Stop-Job $job -ErrorAction SilentlyContinue
                Remove-Job $job -Force -ErrorAction SilentlyContinue
                throw 'Timeout getting disk usage'
            }
        }
        
        if ($dfOutput) {
            $result.ImagesSize = [int]($dfOutput.Images.Size / 1MB) # MB
            $result.ImagesReclaimable = [int]($dfOutput.Images.Reclaimable / 1MB) # MB
            $result.ContainersSize = [int]($dfOutput.Containers.Size / 1MB) # MB
            $result.VolumesSize = [int]($dfOutput.Volumes.Size / 1MB) # MB
            $result.BuilderSize = [int]($dfOutput.BuildCache.Size / 1MB) # MB
        } else {
            $result.Warnings += 'Failed to parse disk usage information'
        }
    } catch {
        $result.Warnings += "Error getting disk usage: $($_.Exception.Message)"
    }
    
    # 3. Check for common issues
    try {
        # Check if Docker Desktop is running
        $dockerProcess = Get-Process -Name 'Docker Desktop' -ErrorAction SilentlyContinue
        if (-not $dockerProcess) {
            $result.Errors += 'Docker Desktop is not running'
        } else {
            # Check Docker service status
            $service = Get-Service -Name 'com.docker.service' -ErrorAction SilentlyContinue
            if ($service.Status -ne 'Running') {
                $result.Errors += 'Docker service is not running'
            }
        }
    } catch {
        $result.Warnings += "Error checking Docker status: $($_.Exception.Message)"
    }
    
    return $result
}

# Perform Docker system cleanup
function Invoke-DockerCleanup {
    [CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
    param(
        [switch]$PruneAll,
        [switch]$Force
    )
    
    if (-not $Force -and -not $PSCmdlet.ShouldContinue('This will remove unused Docker resources. Continue?', 'Docker Cleanup')) {
        return
    }
    
    try {
        Write-Host "`n=== Cleaning Up Docker System ===" -ForegroundColor Cyan
        
        # Get before state
        $before = Get-DockerResourceUsage
        
        # Remove stopped containers
        Write-Host "Removing stopped containers..." -ForegroundColor Yellow
        docker container prune -f 2>&1 | Out-Null
        
        # Remove unused networks
        Write-Host "Removing unused networks..." -ForegroundColor Yellow
        docker network prune -f 2>&1 | Out-Null
        
        # Remove unused images
        Write-Host "Removing unused images..." -ForegroundColor Yellow
        docker image prune -f 2>&1 | Out-Null
        
        # Remove build cache
        Write-Host "Removing build cache..." -ForegroundColor Yellow
        docker builder prune -f 2>&1 | Out-Null
        
        if ($PruneAll) {
            # Remove all unused images, not just dangling ones
            Write-Host "Removing all unused images (not just dangling)..." -ForegroundColor Yellow
            docker image prune -a -f 2>&1 | Out-Null
            
            # Remove unused volumes (this will delete named volumes not used by at least one container)
            Write-Host "Removing unused volumes..." -ForegroundColor Yellow
            docker volume prune -f 2>&1 | Out-Null
        }
        
        # Get after state
        $after = Get-DockerResourceUsage
        
        # Calculate reclaimed space
        $reclaimed = @{
            Images = if ($before -and $after) { $before.ImagesSize - $after.ImagesSize } else { 0 }
            Containers = if ($before -and $after) { $before.ContainersSize - $after.ContainersSize } else { 0 }
            Volumes = if ($before -and $after) { $before.VolumesSize - $after.VolumesSize } else { 0 }
            Builder = if ($before -and $after) { $before.BuilderSize - $after.BuilderSize } else { 0 }
        }
        
        $totalReclaimed = $reclaimed.Images + $reclaimed.Containers + $reclaimed.Volumes + $reclaimed.Builder
        
        Write-Host "`n=== Cleanup Results ===" -ForegroundColor Green
        Write-Host ("Reclaimed {0}MB of disk space" -f $totalReclaimed) -ForegroundColor Green
        Write-Host ("- Images: {0}MB" -f $reclaimed.Images)
        Write-Host ("- Containers: {0}MB" -f $reclaimed.Containers)
        Write-Host ("- Volumes: {0}MB" -f $reclaimed.Volumes)
        Write-Host ("- Build Cache: {0}MB" -f $reclaimed.Builder)
        
        return [PSCustomObject]@{
            Success = $true
            ReclaimedMB = $totalReclaimed
            Details = $reclaimed
        }
    }
    catch {
        Write-Error "Failed to clean up Docker system: $_"
        return [PSCustomObject]@{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

# Monitor Docker containers and log issues
function Start-DockerHealthMonitor {
    [CmdletBinding()]
    param(
        [int]$IntervalSeconds = 300,  # 5 minutes
        [string]$LogFile = "docker_health.log",
        [switch]$AsJob
    )
    
    $scriptBlock = {
        param($Interval, $LogPath)
        
        function Write-HealthLog {
            param($Message, $Level = 'INFO')
            
            $logMessage = "{0} [{1}] {2}" -f 
                (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),
                $Level.PadRight(5),
                $Message
                
            Add-Content -Path $LogPath -Value $logMessage -Force
            
            # Also output to console if running interactively
            $params = @{
                Message = $logMessage
                ForegroundColor = switch ($Level) {
                    'ERROR' { 'Red' }
                    'WARN'  { 'Yellow' }
                    default { 'White' }
                }
            }
            Write-Host @params
        }
        
        try {
            Write-HealthLog "Starting Docker health monitor (interval: ${Interval}s)"
            
            while ($true) {
                $startTime = Get-Date
                
                try {
                    # Check if Docker is running
                    $dockerInfo = docker info --format '{{json .}}' 2>&1 | ConvertFrom-Json -ErrorAction SilentlyContinue
                    
                    if (-not $dockerInfo) {
                        Write-HealthLog "Docker daemon is not responding" -Level 'ERROR'
                        Start-Sleep -Seconds $Interval
                        continue
                    }
                    
                    # Check container status
                    $containers = docker ps -a --format '{{.ID}}|{{.Names}}|{{.Status}}|{{.State}}|{{.RunningFor}}|{{.Health}}' 2>&1
                    
                    foreach ($container in $containers) {
                        $parts = $container -split '\|'
                        if ($parts.Count -ge 6) {
                            $status = $parts[2]
                            $health = $parts[5]
                            $name = $parts[1]
                            
                            # Log unhealthy containers
                            if ($health -and $health -ne 'healthy') {
                                Write-HealthLog "Container '$name' is unhealthy: $status" -Level 'WARN'
                                
                                # Get container logs for unhealthy containers
                                $logs = docker logs --tail 50 $($parts[0]) 2>&1 | Select-Object -Last 5
                                if ($logs) {
                                    $logMsg = $logs -join "`n"
                                    Write-HealthLog "Container '$name' logs (last 5 lines):`n$logMsg" -Level 'DEBUG'
                                }
                            }
                        }
                    }
                    
                    # Check resource usage
                    $usage = Get-DockerResourceUsage -ErrorAction SilentlyContinue
                    if ($usage) {
                        $memoryWarnThreshold = 90  # % of host memory
                        $diskWarnThreshold = 90    # % of disk space
                        
                        # Check memory pressure
                        $memoryPct = [int](($usage.Containers | 
                            Where-Object { $_.Memory -match '(\d+\.?\d*)%' } | 
                            ForEach-Object { [double]($matches[1]) } | 
                            Measure-Object -Maximum).Maximum)
                            
                        if ($memoryPct -ge $memoryWarnThreshold) {
                            Write-HealthLog ("High memory usage detected: {0}% of host memory in use" -f $memoryPct) -Level 'WARN'
                        }
                        
                        # Check disk space
                        $diskPct = [int](($usage.ImagesSize + $usage.ContainersSize + $usage.VolumesSize) / 
                            (Get-PSDrive -Name $env:SystemDrive[0]).Free * 100)
                            
                        if ($diskPct -ge $diskWarnThreshold) {
                            Write-HealthLog ("High disk usage detected: {0}% of disk space used" -f $diskPct) -Level 'WARN'
                        }
                    }
                    
                } catch {
                    Write-HealthLog ("Error during health check: {0}" -f $_.Exception.Message) -Level 'ERROR'
                }
                
                # Calculate remaining time to sleep
                $elapsed = ((Get-Date) - $startTime).TotalSeconds
                $remaining = [math]::Max(1, $Interval - [math]::Floor($elapsed))
                Start-Sleep -Seconds $remaining
            }
            
        } catch {
            Write-HealthLog ("Fatal error in health monitor: {0}" -f $_.Exception.Message) -Level 'ERROR'
        }
    }
    
    if ($AsJob) {
        Start-Job -ScriptBlock $scriptBlock -ArgumentList $IntervalSeconds, $LogFile
    } else {
        & $scriptBlock $IntervalSeconds $LogFile
    }
}

# Start/Stop containers
function Start-DockerContainers {
    param(
        [string]$DockerComposeFile = "docker-compose.yml",
        [switch]$Detached,
        [switch]$Build
    )
    
    try {
        $composeArgs = @("-f", $DockerComposeFile, "up")
        if ($Detached) { $composeArgs += "-d" }
        if ($Build) { $composeArgs += "--build" }
        
        Write-Host "Starting containers..." -ForegroundColor Cyan
        $process = Start-Process -FilePath "docker-compose" -ArgumentList $composeArgs -NoNewWindow -PassThru -Wait
        
        if ($process.ExitCode -eq 0) {
            Write-Host "Containers started" -ForegroundColor Green
            return $true
        } else {
            throw "Start failed with code $($process.ExitCode)"
        }
    } catch {
        Write-Host "Start error: $_" -ForegroundColor Red
        return $false
    }
}

function Stop-DockerContainers {
    param(
        [string]$DockerComposeFile = "docker-compose.yml",
        [switch]$RemoveVolumes,
        [int]$Timeout = 10
    )
    
    try {
        $composeArgs = @("-f", $DockerComposeFile, "down")
        if ($RemoveVolumes) { $composeArgs += "-v" }
        $composeArgs += "--timeout", $Timeout
        
        Write-Host "Stopping containers..." -ForegroundColor Cyan
        $process = Start-Process -FilePath "docker-compose" -ArgumentList $composeArgs -NoNewWindow -PassThru -Wait
        
        if ($process.ExitCode -eq 0) {
            Write-Host "Containers stopped" -ForegroundColor Green
            return $true
        } else {
            throw "Stop failed with code $($process.ExitCode)"
        }
    } catch {
        Write-Host "Stop error: $_" -ForegroundColor Red
        return $false
    }
}

# Export public functions
Export-ModuleMember -Function * -Alias *
