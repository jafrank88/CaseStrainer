# Docker Engine Manager for CaseStrainer
# Comprehensive Docker service management with enhanced diagnostics and recovery

param(
    [ValidateSet('start', 'stop', 'restart', 'status', 'diagnose', 'repair')]
    [string]$Action = 'status',
    
    [switch]$Force,
    [switch]$Verbose,
    [int]$Timeout = 30
)

# Configuration
$LogFile = "logs/docker_engine.log"
$StateFile = "logs/docker_state.json"
$ServiceName = "com.docker.service"
$DockerDesktopPath = "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"

# Ensure logs directory exists
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

# Initialize state if it doesn't exist
if (!(Test-Path $StateFile)) {
    @{
        LastStartAttempt = $null
        LastStopAttempt = $null
        StartCount = 0
        StopCount = 0
        LastError = $null
        StatusHistory = @()
    } | ConvertTo-Json | Out-File -FilePath $StateFile -Force
}

# Load state
$state = Get-Content $StateFile -Raw | ConvertFrom-Json

function Write-Log {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logMessage -Force
    
    if ($Verbose -or $Level -in @("ERROR", "WARN")) {
        $color = switch($Level) { 
            "ERROR" { "Red" } 
            "WARN" { "Yellow" } 
            "INFO" { "Green" } 
            "DEBUG" { "Gray" }
            default { "White" } 
        }
        Write-Host $logMessage -ForegroundColor $color
    }
}

function Test-DockerRunning {
    try {
        $dockerPs = docker ps 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Test-DockerServiceRunning {
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        return $service -and $service.Status -eq 'Running'
    } catch {
        return $false
    }
}

function Start-DockerEngine {
    param($Reason = "Manual start requested")
    
    Write-Log "Starting Docker Engine... Reason: $Reason"
    
    # Start Docker Desktop if not running
    if (!(Test-DockerServiceRunning)) {
        try {
            Write-Log "Starting Docker Desktop service..."
            Start-Process -FilePath $DockerDesktopPath
            $state.LastStartAttempt = Get-Date -Format "o"
            $state.StartCount++
            $state | ConvertTo-Json | Out-File -FilePath $StateFile -Force
            
            # Wait for Docker to start
            $timeout = New-TimeSpan -Seconds $Timeout
            $startTime = Get-Date
            
            while (((Get-Date) - $startTime) -lt $timeout) {
                if (Test-DockerRunning) {
                    Write-Log "Docker Engine started successfully"
                    return $true
                }
                Start-Sleep -Seconds 2
            }
            
            Write-Log "Timed out waiting for Docker to start" -Level "WARN"
            return $false
            
        } catch {
            $errorMsg = $_.Exception.Message
            Write-Log "Failed to start Docker Desktop: $errorMsg" -Level "ERROR"
            $state.LastError = $errorMsg
            $state | ConvertTo-Json | Out-File -FilePath $StateFile -Force
            return $false
        }
    } else {
        Write-Log "Docker Desktop service is already running"
        return $true
    }
}

function Stop-DockerEngine {
    param($Reason = "Manual stop requested")
    
    Write-Log "Stopping Docker Engine... Reason: $Reason"
    
    try {
        # Stop all running containers first
        $containers = docker ps -q
        if ($containers) {
            Write-Log "Stopping $($containers.Count) running containers..."
            docker stop $containers 2>&1 | Out-Null
        }
        
        # Stop Docker Desktop
        if (Test-DockerServiceRunning) {
            Write-Log "Stopping Docker Desktop service..."
            Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
            $state.LastStopAttempt = Get-Date -Format "o"
            $state.StopCount++
            $state | ConvertTo-Json | Out-File -FilePath $StateFile -Force
        }
        
        # Verify Docker is stopped
        $timeout = New-TimeSpan -Seconds $Timeout
        $startTime = Get-Date
        
        while (((Get-Date) - $startTime) -lt $timeout) {
            if (!(Test-DockerRunning)) {
                Write-Log "Docker Engine stopped successfully"
                return $true
            }
            Start-Sleep -Seconds 2
        }
        
        Write-Log "Timed out waiting for Docker to stop" -Level "WARN"
        return $false
        
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Log "Failed to stop Docker Engine: $errorMsg" -Level "ERROR"
        $state.LastError = $errorMsg
        $state | ConvertTo-Json | Out-File -FilePath $StateFile -Force
        return $false
    }
}

function Get-DockerStatus {
    $status = @{
        DockerInstalled = Test-Path $DockerDesktopPath
        ServiceRunning = Test-DockerServiceRunning
        DockerRunning = Test-DockerRunning
        LastError = $state.LastError
        LastStartAttempt = $state.LastStartAttempt
        LastStopAttempt = $state.LastStopAttempt
        StartCount = $state.StartCount
        StopCount = $state.StopCount
    }
    
    return $status
}

function Invoke-DockerDiagnostics {
    Write-Log "Running Docker diagnostics..."
    
    $diagnostics = @{
        Timestamp = Get-Date -Format "o"
        DockerInstalled = Test-Path $DockerDesktopPath
        ServiceRunning = Test-DockerServiceRunning
        DockerRunning = Test-DockerRunning
        DockerVersion = docker --version 2>&1
        DockerComposeVersion = docker-compose --version 2>&1
        DockerInfo = docker info 2>&1
        DockerPs = docker ps -a 2>&1
        DockerImages = docker images 2>&1
        DockerNetworks = docker network ls 2>&1
        DockerVolumes = docker volume ls 2>&1
        SystemInfo = systeminfo 2>&1
        WslStatus = wsl --status 2>&1
        WslList = wsl --list --verbose 2>&1
    }
    
    $diagnostics | ConvertTo-Json -Depth 5 | Out-File "logs/docker_diagnostics_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    Write-Log "Diagnostics saved to logs/docker_diagnostics_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    
    return $diagnostics
}

function Repair-DockerInstallation {
    Write-Log "Attempting to repair Docker installation..."
    
    try {
        # 1. Stop Docker if running
        if (Test-DockerServiceRunning) {
            Write-Log "Stopping Docker service..."
            Stop-DockerEngine -Reason "Repair operation requested"
        }
        
        # 2. Reset Docker data (WARNING: This will remove all containers and images)
        if ($Force) {
            Write-Log "Resetting Docker data (force mode)..."
            wsl --unregister docker-desktop 2>&1 | Out-Null
            wsl --unregister docker-desktop-data 2>&1 | Out-Null
        } else {
            Write-Log "Skipping data reset (use -Force to reset Docker data)" -Level "WARN"
        }
        
        # 3. Restart Docker Desktop
        Write-Log "Restarting Docker Desktop..."
        Start-DockerEngine -Reason "After repair operation"
        
        # 4. Run diagnostics
        $diagnostics = Invoke-DockerDiagnostics
        
        if ($diagnostics.DockerRunning) {
            Write-Log "Docker repair completed successfully" -Level "INFO"
            return $true
        } else {
            Write-Log "Docker repair completed but Docker is not running" -Level "WARN"
            return $false
        }
        
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Log "Failed to repair Docker: $errorMsg" -Level "ERROR"
        return $false
    }
}

# Main execution
switch ($Action.ToLower()) {
    'start' {
        $result = Start-DockerEngine -Reason "Manual start requested"
        exit $(if ($result) { 0 } else { 1 })
    }
    
    'stop' {
        $result = Stop-DockerEngine -Reason "Manual stop requested"
        exit $(if ($result) { 0 } else { 1 })
    }
    
    'restart' {
        $stopResult = Stop-DockerEngine -Reason "Restart requested"
        if ($stopResult) {
            $startResult = Start-DockerEngine -Reason "After restart"
            exit $(if ($startResult) { 0 } else { 1 })
        } else {
            exit 1
        }
    }
    
    'status' {
        $status = Get-DockerStatus
        $status | Format-List | Out-String | Write-Host
        exit 0
    }
    
    'diagnose' {
        $diagnostics = Invoke-DockerDiagnostics
        $diagnostics | Format-List | Out-String | Write-Host
        exit 0
    }
    
    'repair' {
        $result = Repair-DockerInstallation
        exit $(if ($result) { 0 } else { 1 })
    }
    
    default {
        Write-Host "Invalid action. Use start, stop, restart, status, diagnose, or repair."
        exit 1
    }
}
