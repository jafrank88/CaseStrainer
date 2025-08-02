# DockerDiagnostics.ps1 - Diagnostic functions for Docker issues

function Get-DockerStatus {
    [CmdletBinding()]
    param(
        [switch]$Detailed
    )
    
    $status = @{
        DockerInstalled = $false
        DockerRunning = $false
        DockerComposeAvailable = $false
        DockerDaemonAccessible = $false
        DockerVersion = $null
        DockerInfo = $null
        DockerProcesses = $null
        DockerServiceStatus = $null
        WSLStatus = $null
        DockerDaemonError = $null
        DockerSystemInfo = $null
        DockerImages = $null
        DockerContainers = $null
        DockerNetworks = $null
        DockerVolumes = $null
    }
    
    # Check if Docker CLI is installed and get version
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $status.DockerInstalled = $true
            $status.DockerVersion = $dockerVersion.Trim()
        }
    } catch {
        $status.DockerDaemonError = "Docker CLI not found: $($_.Exception.Message)"
        return [PSCustomObject]$status
    }
    
    # Check if Docker Desktop processes are running
    $dockerProcesses = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if ($dockerProcesses) {
        $status.DockerRunning = $true
        $status.DockerProcesses = $dockerProcesses | Select-Object Id, StartTime, CPU, PM
    } else {
        $status.DockerDaemonError = "Docker Desktop is not running"
        return [PSCustomObject]$status
    }
    
    # Check Docker service status
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction Stop
        $status.DockerServiceStatus = @{
            Name = $service.Name
            Status = $service.Status
            StartType = $service.StartType
        }
        
        if ($service.Status -ne 'Running') {
            $status.DockerDaemonError = "Docker service is not running (Status: $($service.Status))"
            return [PSCustomObject]$status
        }
    } catch {
        $status.DockerServiceStatus = "Service not found or error: $($_.Exception.Message)"
        $status.DockerDaemonError = "Error checking Docker service: $($_.Exception.Message)"
        return [PSCustomObject]$status
    }
    
    # Try to get Docker info with detailed error handling
    try {
        $dockerInfo = docker info --format json 2>&1 | ConvertFrom-Json -ErrorAction SilentlyContinue
        if (-not $dockerInfo) {
            $dockerInfo = docker info 2>&1
            if ($LASTEXITCODE -eq 0) {
                $status.DockerDaemonAccessible = $true
                $status.DockerInfo = $dockerInfo | Where-Object { $_ -match '^(Server Version|Operating System|Kernel Version|OSType|Architecture|Total Memory|CPUs|Name|Docker Root Dir|Debug Mode|HTTP Proxy|HTTPS Proxy|Registry|Experimental Build|Insecure Registries|Live Restore Enabled|Product License|WARNING)' }
            } else {
                $status.DockerDaemonError = "Docker daemon returned error: $dockerInfo"
                $status.DockerInfo = $dockerInfo
            }
        } else {
            $status.DockerDaemonAccessible = $true
            $status.DockerInfo = $dockerInfo
        }
    } catch {
        $status.DockerDaemonError = "Error accessing Docker daemon: $($_.Exception.Message)"
        $status.DockerInfo = $dockerInfo
    }
    
    # Check WSL status
    try {
        $wslStatus = wsl --status 2>&1
        $status.WSLStatus = $wslStatus
        
        # Check if WSL is running the correct version
        $wslVersion = wsl --version 2>&1
        if ($wslVersion -like "*0x80070057*" -or $wslVersion -like "*incorrect parameter*") {
            $wslVersion = wsl -l -v 2>&1
        }
        $status.WSLVersion = $wslVersion
    } catch {
        $status.WSLStatus = "Error checking WSL status: $($_.Exception.Message)"
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $status.DockerComposeAvailable = $true
            $status.DockerComposeVersion = $composeVersion.Trim()
        } else {
            # Try with docker compose (v2)
            $composeVersion = docker compose version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $status.DockerComposeAvailable = $true
                $status.DockerComposeVersion = $composeVersion | Select-Object -First 1
            }
        }
    } catch {
        $status.DockerComposeAvailable = $false
        $status.DockerDaemonError = "Error checking Docker Compose: $($_.Exception.Message)"
    }
    
    # Get additional Docker system information if requested
    if ($Detailed) {
        try {
            $status.DockerSystemInfo = docker system info --format json 2>&1 | ConvertFrom-Json -ErrorAction SilentlyContinue
            if (-not $status.DockerSystemInfo) {
                $status.DockerSystemInfo = docker system info 2>&1
            }
        } catch {}
        
        try {
            $status.DockerImages = docker images --format "{{.ID}}\t{{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>&1
        } catch {}
        
        try {
            $status.DockerContainers = docker ps -a --format "{{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}" 2>&1
        } catch {}
        
        try {
            $status.DockerNetworks = docker network ls --format "{{.ID}}\t{{.Name}}\t{{.Driver}}\t{{.Scope}}" 2>&1
        } catch {}
        
        try {
            $status.DockerVolumes = docker volume ls --format "{{.Name}}\t{{.Driver}}\t{{.Mountpoint}}" 2>&1
        } catch {}
    }
    
    return [PSCustomObject]$status
}

function Reset-Docker {
    [CmdletBinding()]
    param()
    
    $status = @{
        DockerInstalled = $false
        DockerRunning = $false
        DockerComposeAvailable = $false
        DockerDaemonAccessible = $false
        DockerVersion = $null
        DockerInfo = $null
        DockerProcesses = $null
        DockerServiceStatus = $null
        WSLStatus = $null
    }
    
    try {
        # Check if Docker CLI is installed
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $status.DockerInstalled = $true
            $status.DockerVersion = $dockerVersion.Trim()
        }
    } catch {
        Write-Verbose "Docker CLI not found"
    }
    
    # Check if Docker Desktop process is running
    $dockerProcesses = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if ($dockerProcesses) {
        $status.DockerRunning = $true
        $status.DockerProcesses = $dockerProcesses | Select-Object Id, StartTime, CPU, PM
    }
    
    # Check Docker service status
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction Stop
        $status.DockerServiceStatus = @{
            Name = $service.Name
            Status = $service.Status
            StartType = $service.StartType
        }
    } catch {
        $status.DockerServiceStatus = "Service not found or error: $($_.Exception.Message)"
    }
    
    # Check Docker daemon accessibility
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            $status.DockerDaemonAccessible = $true
            $status.DockerInfo = $dockerInfo | Where-Object { $_ -match '^(Server Version|Operating System|Kernel Version|OSType|Architecture|Total Memory|CPUs|Name|Docker Root Dir|Debug Mode|HTTP Proxy|HTTPS Proxy|Registry|Experimental Build|Insecure Registries|Live Restore Enabled|Product License|WARNING)' }
        }
    } catch {
        $status.DockerDaemonAccessible = $false
        $status.DockerInfo = "Error accessing Docker daemon: $($_.Exception.Message)"
    }
    
    # Check WSL status
    try {
        $wslStatus = wsl --status 2>&1
        $status.WSLStatus = $wslStatus
    } catch {
        $status.WSLStatus = "Error checking WSL status: $($_.Exception.Message)"
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $status.DockerComposeAvailable = $true
        } else {
            # Try with docker compose (v2)
            $composeVersion = docker compose version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $status.DockerComposeAvailable = $true
            }
        }
    } catch {
        $status.DockerComposeAvailable = $false
    }
    
    return [PSCustomObject]$status
}

function Reset-Docker {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    if (-not $PSCmdlet.ShouldProcess("Docker", "Reset Docker to factory defaults")) {
        return
    }
    
    try {
        Write-Host "Stopping Docker Desktop..." -ForegroundColor Yellow
        Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
        
        # Wait for processes to exit
        Start-Sleep -Seconds 5
        
        # Reset Docker to factory defaults
        Write-Host "Resetting Docker..." -ForegroundColor Yellow
        & "C:\Program Files\Docker\Docker\Docker Desktop.exe" --uninstall-service
        Start-Sleep -Seconds 2
        & "C:\Program Files\Docker\Docker\Docker Desktop.exe" --install-service
        
        # Start Docker Desktop
        Write-Host "Starting Docker Desktop..." -ForegroundColor Yellow
        Start-Process -FilePath "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        
        # Wait for Docker to start
        $timeout = 120
        $startTime = Get-Date
        $dockerReady = $false
        
        while (((Get-Date) - $startTime).TotalSeconds -lt $timeout) {
            try {
                $info = docker info 2>&1
                if ($LASTEXITCODE -eq 0) {
                    $dockerReady = $true
                    break
                }
            } catch {}
            Write-Progress -Activity "Waiting for Docker to start" -Status "Please wait..." -SecondsRemaining ($timeout - ((Get-Date) - $startTime).TotalSeconds)
            Start-Sleep -Seconds 5
        }
        
        if ($dockerReady) {
            Write-Host "Docker has been reset and is now running" -ForegroundColor Green
            return $true
        } else {
            Write-Host "Timed out waiting for Docker to start" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "Error resetting Docker: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Module exports are handled by the module manifest
