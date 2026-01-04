# Docker Emergency Recovery Script
# This script performs emergency recovery when Docker Desktop fails to start

param(
    [switch]$Force,
    [switch]$Cleanup,
    [switch]$Diagnostics
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    
    # Also write to main log
    $logFile = Join-Path $PSScriptRoot "..\logs\docker_emergency_recovery.log"
    $logDir = Split-Path $logFile -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    Add-Content -Path $logFile -Value $logEntry
}

function Stop-AllDockerProcesses {
    Write-Log "Stopping all Docker processes..."
    
    $processes = @(
        "Docker Desktop",
        "com.docker.backend",
        "com.docker.proxy",
        "com.docker.cli",
        "dockerd",
        "docker",
        "VpnService",
        "com.docker.vmnetd"
    )
    
    foreach ($procName in $processes) {
        $processes = Get-Process -Name $procName -ErrorAction SilentlyContinue
        if ($processes) {
            Write-Log "Stopping process: $procName"
            $processes | Stop-Process -Force -ErrorAction SilentlyContinue
        }
    }
    
    # Stop Docker service
    try {
        Stop-Service -Name "com.docker.service" -Force -ErrorAction SilentlyContinue
        Write-Log "Stopped com.docker.service"
    }
    catch {
        Write-Log "Could not stop com.docker.service: $($_.Exception.Message)" "WARN"
    }
    
    Start-Sleep -Seconds 5
}

function Clear-DockerData {
    param([bool]$FullCleanup = $false)
    
    Write-Log "Clearing Docker data..."
    
    # Clear temporary files
    $tempPaths = @(
        "$env:LOCALAPPDATA\Docker\temp",
        "$env:APPDATA\Docker\logs",
        "$env:LOCALAPPDATA\Docker\log",
        "$env:LOCALAPPDATA\Docker\vm"
    )
    
    foreach ($path in $tempPaths) {
        if (Test-Path $path) {
            Write-Log "Cleaning: $path"
            try {
                Remove-Item "$path\*" -Recurse -Force -ErrorAction SilentlyContinue
            }
            catch {
                Write-Log "Could not clean $path`: $($_.Exception.Message)" "WARN"
            }
        }
    }
    
    if ($FullCleanup) {
        Write-Log "Performing full cleanup - this will remove all containers and images!"
        
        # Remove container data
        $containerPaths = @(
            "$env:LOCALAPPDATA\Docker\containers",
            "$env:LOCALAPPDATA\Docker\image",
            "$env:LOCALAPPDATA\Docker\volumes",
            "$env:LOCALAPPDATA\Docker\buildkit"
        )
        
        foreach ($path in $containerPaths) {
            if (Test-Path $path) {
                Write-Log "Removing: $path"
                try {
                    Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue
                }
                catch {
                    Write-Log "Could not remove $path`: $($_.Exception.Message)" "WARN"
                }
            }
        }
    }
}

function Repair-DockerInstallation {
    Write-Log "Repairing Docker installation..."
    
    # Reset WSL
    try {
        Write-Log "Resetting WSL..."
        wsl --shutdown
        Start-Sleep -Seconds 3
    }
    catch {
        Write-Log "WSL not available or error occurred: $($_.Exception.Message)" "WARN"
    }
    
    # Reset network adapters
    try {
        Write-Log "Resetting Docker network adapters..."
        Get-NetAdapter | Where-Object { $_.Name -like "*Docker*" -or $_.InterfaceDescription -like "*Docker*" } | Restart-NetAdapter
    }
    catch {
        Write-Log "Could not reset network adapters: $($_.Exception.Message)" "WARN"
    }
    
    # Clear DNS cache
    try {
        Write-Log "Clearing DNS cache..."
        Clear-DnsClientCache
    }
    catch {
        Write-Log "Could not clear DNS cache: $($_.Exception.Message)" "WARN"
    }
}

function Start-DockerDesktop {
    Write-Log "Starting Docker Desktop..."
    
    $dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
    
    if (-not (Test-Path $dockerDesktopPath)) {
        Write-Log "Docker Desktop not found at: $dockerDesktopPath" "ERROR"
        return $false
    }
    
    # Start with clean state
    Start-Process -FilePath $dockerDesktopPath -ArgumentList "--reset" -WindowStyle Minimized
    
    # Wait for startup
    $maxWait = 180
    $waited = 0
    $isHealthy = $false
    
    while ($waited -lt $maxWait -and -not $isHealthy) {
        Start-Sleep -Seconds 5
        $waited += 5
        
        # Check if process is running
        $process = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        if (-not $process) {
            Write-Log "Docker Desktop process not running" "WARN"
            continue
        }
        
        # Check if service is running
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if (-not $service -or $service.Status -ne "Running") {
            Write-Log "Docker service not running (waited $waited seconds)" "WARN"
            continue
        }
        
        # Check if daemon responds
        try {
            $result = & docker.exe info 2>$null
            if ($LASTEXITCODE -eq 0) {
                $isHealthy = $true
                Write-Log "Docker Desktop is healthy and ready"
            }
            else {
                Write-Log "Docker daemon not responding (waited $waited seconds)" "WARN"
            }
        }
        catch {
            Write-Log "Docker daemon not accessible (waited $waited seconds)" "WARN"
        }
    }
    
    if ($isHealthy) {
        Write-Log "Docker Desktop started successfully in $waited seconds"
        
        # Start CaseStrainer if configured
        $composeFile = Join-Path $PSScriptRoot "..\docker-compose.prod.yml"
        if (Test-Path $composeFile) {
            Write-Log "Starting CaseStrainer containers..."
            Set-Location (Split-Path $composeFile -Parent)
            & docker-compose -f docker-compose.prod.yml up -d
            Write-Log "CaseStrainer containers started"
        }
        
        return $true
    }
    else {
        Write-Log "Failed to start Docker Desktop within timeout" "ERROR"
        return $false
    }
}

function Run-Diagnostics {
    Write-Log "Running Docker diagnostics..."
    
    $diagFile = Join-Path $PSScriptRoot "..\logs\docker_diagnostics_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    
    "=== Docker Diagnostics ===" | Out-File $diagFile
    "Generated: $(Get-Date)" | Out-File $diagFile -Append
    "" | Out-File $diagFile -Append
    
    # System info
    "=== System Information ===" | Out-File $diagFile -Append
    Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, TotalPhysicalMemory | Out-File $diagFile -Append
    "" | Out-File $diagFile -Append
    
    # Docker service status
    "=== Docker Service Status ===" | Out-File $diagFile -Append
    Get-Service -Name "*docker*" | Out-File $diagFile -Append
    "" | Out-File $diagFile -Append
    
    # Docker processes
    "=== Docker Processes ===" | Out-File $diagFile -Append
    Get-Process | Where-Object { $_.ProcessName -like "*docker*" } | Select-Object ProcessName, Id, CPU, WorkingSet | Out-File $diagFile -Append
    "" | Out-File $diagFile -Append
    
    # Network adapters
    "=== Network Adapters ===" | Out-File $diagFile -Append
    Get-NetAdapter | Where-Object { $_.Name -like "*Docker*" -or $_.InterfaceDescription -like "*Docker*" } | Out-File $diagFile -Append
    "" | Out-File $diagFile -Append
    
    # WSL info
    "=== WSL Information ===" | Out-File $diagFile -Append
    try {
        wsl --list --verbose | Out-File $diagFile -Append
    }
    catch {
        "WSL not available" | Out-File $diagFile -Append
    }
    "" | Out-File $diagFile -Append
    
    # Recent Docker logs
    "=== Recent Docker Events ===" | Out-File $diagFile -Append
    try {
        docker events --since 1h --format "{{.Time}} {{.Status}} {{.Action}} {{.Type}} {{.Actor.Attributes.name}}" 2>$null | Select-Object -First 50 | Out-File $diagFile -Append
    }
    catch {
        "Docker not accessible" | Out-File $diagFile -Append
    }
    
    Write-Log "Diagnostics saved to: $diagFile"
    return $diagFile
}

# Main execution
Write-Log "=== Docker Emergency Recovery Started ==="

if ($Diagnostics) {
    Run-Diagnostics
    exit
}

if ($Force -or $Cleanup) {
    Stop-AllDockerProcesses
    Clear-DockerData -FullCleanup:$Cleanup
    Repair-DockerInstallation
}

if (Start-DockerDesktop) {
    Write-Log "=== Recovery Successful ==="
    exit 0
}
else {
    Write-Log "=== Recovery Failed ===" "ERROR"
    Write-Log "Run with -Diagnostics to gather more information" "ERROR"
    exit 1
}
