# Enhanced Docker Engine Manager for CaseStrainer
# Comprehensive Docker service management with improved diagnostics and recovery

param(
    [ValidateSet('start', 'stop', 'restart', 'status', 'diagnose', 'repair', 'clean', 'switch-mode')]
    [string]$Action = 'status',
    [string]$Mode = '',  # 'windows' or 'linux' for switch-mode
    [switch]$Force,
    [switch]$Verbose,
    [int]$Timeout = 30
)

# Configuration
$LogFile = "logs/docker_engine_enhanced.log"
$StateFile = "logs/docker_state_enhanced.json"
# Updated Docker Desktop path
$DockerDesktopPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
$DockerConfigPath = "$env:ProgramData\Docker\config\daemon.json"

# Ensure logs directory exists
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

# Initialize state if it doesn't exist
if (!(Test-Path $StateFile) -or (Get-Item $StateFile).Length -eq 0) {
    @{
        LastStartAttempt = $null
        LastStopAttempt = $null
        StartCount = 0
        StopCount = 0
        LastError = $null
        CurrentMode = ""
        StatusHistory = @()
    } | ConvertTo-Json -Depth 5 | Out-File -FilePath $StateFile -Force -Encoding utf8
}

# Load state
$state = Get-Content $StateFile -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json -ErrorAction SilentlyContinue
if ($null -eq $state) {
    Write-Host "Warning: Could not load state file. Creating a new one." -ForegroundColor Yellow
    $state = @{
        LastStartAttempt = $null
        LastStopAttempt = $null
        StartCount = 0
        StopCount = 0
        LastError = $null
        CurrentMode = ""
        StatusHistory = @()
    } | ConvertTo-Json -Depth 5 | ConvertFrom-Json
}

function Write-Log {
    param($Message, $Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    try {
        Add-Content -Path $LogFile -Value $logMessage -Force -ErrorAction Stop
    } catch {
        Write-Host "Failed to write to log file: $_" -ForegroundColor Red
    }
    
    if ($Verbose -or $Level -in @("ERROR", "WARN")) {
        $color = switch($Level) { 
            "ERROR" { "Red" } 
            "WARN"  { "Yellow" } 
            "INFO"  { "Green" } 
            "DEBUG" { "Gray" }
            default { "White" }
        }
        Write-Host $logMessage -ForegroundColor $color
    }
}

function Get-DockerStatus {
    try {
        $dockerInfo = docker info --format '{{json .}}' 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerInfoObj = $dockerInfo | ConvertFrom-Json -ErrorAction SilentlyContinue
            $mode = if ($dockerInfoObj.OSType -eq "linux") { "linux" } else { "windows" }
            
            # Update state with current mode
            $state.CurrentMode = $mode
            
            return @{
                Status = "running"
                Mode = $mode
                Info = $dockerInfoObj
                RawOutput = $dockerInfo
            }
        } else {
            return @{
                Status = "error"
                Error = $dockerInfo
                RawOutput = $dockerInfo
            }
        }
    } catch {
        return @{
            Status = "error"
            Error = $_.Exception.Message
            RawOutput = $_.Exception.Message
        }
    }
}

function Start-DockerEngine {
    param($Reason = "Manual start requested")
    
    Write-Log "Starting Docker Engine... Reason: $Reason"
    
    # Check if already running
    $status = Get-DockerStatus
    if ($status.Status -eq "running") {
        Write-Log "Docker Engine is already running in $($status.Mode) mode"
        return $true
    }
    
    try {
        # Start Docker Desktop
        if (Test-Path $DockerDesktopPath) {
            Start-Process -FilePath $DockerDesktopPath -PassThru
            Write-Log "Launched Docker Desktop"
        } else {
            Write-Log "Docker Desktop not found at $DockerDesktopPath" "ERROR"
            return $false
        }
        
        # Wait for Docker to be ready
        $startTime = Get-Date
        $timeout = New-TimeSpan -Seconds $Timeout
        $dockerReady = $false
        
        while (((Get-Date) - $startTime) -lt $timeout) {
            $status = Get-DockerStatus
            if ($status.Status -eq "running") {
                $dockerReady = $true
                break
            }
            Start-Sleep -Seconds 2
        }
        
        if ($dockerReady) {
            Write-Log "Docker Engine started successfully in $($status.Mode) mode"
            $state.LastStartAttempt = Get-Date -Format "o"
            $state.StartCount++
            $state.LastError = $null
            $state.StatusHistory += @{
                Timestamp = Get-Date -Format "o"
                Status = "started"
                Mode = $status.Mode
                Reason = $Reason
            }
            return $true
        } else {
            $errorMsg = "Failed to start Docker Engine within timeout period"
            Write-Log $errorMsg "ERROR"
            $state.LastError = $errorMsg
            return $false
        }
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Log "Error starting Docker Engine: $errorMsg" "ERROR"
        $state.LastError = $errorMsg
        return $false
    } finally {
        # Save state
        $state | ConvertTo-Json -Depth 5 | Out-File -FilePath $StateFile -Force -Encoding utf8
    }
}

function Stop-DockerEngine {
    param($Reason = "Manual stop requested")
    
    Write-Log "Stopping Docker Engine... Reason: $Reason"
    
    # Check if already stopped
    $status = Get-DockerStatus
    if ($status.Status -ne "running") {
        Write-Log "Docker Engine is not running"
        return $true
    }
    
    try {
        # Stop Docker Desktop gracefully first
        if (Test-Path $DockerDesktopPath) {
            & "$DockerDesktopPath" -Quit
            Write-Log "Sent quit command to Docker Desktop"
            
            # Wait for Docker to stop
            $startTime = Get-Date
            $timeout = New-TimeSpan -Seconds $Timeout
            $dockerStopped = $false
            
            while (((Get-Date) - $startTime) -lt $timeout) {
                $status = Get-DockerStatus
                if ($status.Status -ne "running") {
                    $dockerStopped = $true
                    break
                }
                Start-Sleep -Seconds 2
            }
            
            if (-not $dockerStopped) {
                Write-Log "Graceful stop timed out, forcing stop" "WARN"
                # Force stop if graceful stop failed
                Get-Process "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
                Get-Process "com.docker.*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
                Write-Log "Forcibly stopped Docker processes" "WARN"
            }
        } else {
            # Fallback to stopping processes directly
            Get-Process "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
            Get-Process "com.docker.*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
            Write-Log "Stopped Docker processes directly (Docker Desktop not found)" "WARN"
        }
        
        # Verify Docker is stopped
        $status = Get-DockerStatus
        if ($status.Status -ne "running") {
            Write-Log "Docker Engine stopped successfully"
            $state.LastStopAttempt = Get-Date -Format "o"
            $state.StopCount++
            $state.LastError = $null
            $state.StatusHistory += @{
                Timestamp = Get-Date -Format "o"
                Status = "stopped"
                Reason = $Reason
            }
            return $true
        } else {
            $errorMsg = "Failed to stop Docker Engine"
            Write-Log $errorMsg "ERROR"
            $state.LastError = $errorMsg
            return $false
        }
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Log "Error stopping Docker Engine: $errorMsg" "ERROR"
        $state.LastError = $errorMsg
        return $false
    } finally {
        # Save state
        $state | ConvertTo-Json -Depth 5 | Out-File -FilePath $StateFile -Force -Encoding utf8
    }
}

function Switch-DockerMode {
    param(
        [ValidateSet('windows', 'linux')]
        [string]$TargetMode
    )
    
    $currentStatus = Get-DockerStatus
    $currentMode = $currentStatus.Mode
    
    if ($currentMode -eq $TargetMode) {
        Write-Log "Docker is already in $TargetMode mode"
        return $true
    }
    
    Write-Log "Switching Docker from $currentMode to $TargetMode mode..."
    
    # Stop Docker if running
    if ($currentStatus.Status -eq "running") {
        if (-not (Stop-DockerEngine -Reason "Switching to $TargetMode mode")) {
            Write-Log "Failed to stop Docker Engine for mode switch" "ERROR"
            return $false
        }
    }
    
    try {
        # Switch mode using Docker CLI if available
        $switchCmd = "& '$DockerDesktopPath' -SwitchDaemon"
        if ($TargetMode -eq "windows") {
            $switchCmd += " -WindowsContainers"
        } else {
            $switchCmd += " -LinuxContainers"
        }
        
        Invoke-Expression $switchCmd
        
        # Start Docker with new mode
        if (Start-DockerEngine -Reason "Starting in $TargetMode mode") {
            $newStatus = Get-DockerStatus
            if ($newStatus.Mode -eq $TargetMode) {
                Write-Log "Successfully switched Docker to $TargetMode mode"
                return $true
            } else {
                $errorMsg = "Docker started but in wrong mode (expected: $TargetMode, actual: $($newStatus.Mode))"
                Write-Log $errorMsg "ERROR"
                $state.LastError = $errorMsg
                return $false
            }
        } else {
            $errorMsg = "Failed to start Docker in $TargetMode mode"
            Write-Log $errorMsg "ERROR"
            $state.LastError = $errorMsg
            return $false
        }
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Log "Error switching Docker mode: $errorMsg" "ERROR"
        $state.LastError = $errorMsg
        return $false
    } finally {
        # Save state
        $state | ConvertTo-Json -Depth 5 | Out-File -FilePath $StateFile -Force -Encoding utf8
    }
}

function Repair-DockerInstallation {
    Write-Log "Attempting to repair Docker installation..."
    
    try {
        # Stop any running Docker processes
        Stop-DockerEngine -Reason "Repairing Docker installation" | Out-Null
        
        # Reset Docker to factory defaults
        Write-Log "Resetting Docker to factory defaults..."
        if (Test-Path $DockerDesktopPath) {
            & "$DockerDesktopPath" -Reset
            Start-Sleep -Seconds 10  # Give it time to reset
        }
        
        # Clean up Docker data
        Write-Log "Cleaning up Docker data..."
        Remove-Item -Path "$env:USERPROFILE\.docker\*" -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -Path "$env:ProgramData\Docker\*" -Recurse -Force -ErrorAction SilentlyContinue
        
        # Recreate Docker config with default settings
        $defaultConfig = @{
            "registry-mirrors" = @()
            "insecure-registries" = @()
            "debug" = $false
            "experimental" = $false
            "features" = @{
                "buildkit" = $true
            }
        }
        
        $configDir = [System.IO.Path]::GetDirectoryName($DockerConfigPath)
        if (-not (Test-Path $configDir)) {
            New-Item -ItemType Directory -Path $configDir -Force | Out-Null
        }
        
        $defaultConfig | ConvertTo-Json -Depth 5 | Out-File -FilePath $DockerConfigPath -Force -Encoding utf8
        
        # Start Docker
        if (Start-DockerEngine -Reason "After repair") {
            Write-Log "Docker repair completed successfully"
            return $true
        } else {
            $errorMsg = "Docker repair completed but failed to start"
            Write-Log $errorMsg "ERROR"
            $state.LastError = $errorMsg
            return $false
        }
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Log "Error repairing Docker: $errorMsg" "ERROR"
        $state.LastError = $errorMsg
        return $false
    } finally {
        # Save state
        $state | ConvertTo-Json -Depth 5 | Out-File -FilePath $StateFile -Force -Encoding utf8
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
        $stopResult = Stop-DockerEngine -Reason "Manual restart requested"
        if ($stopResult) {
            $startResult = Start-DockerEngine -Reason "After manual restart"
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
        $diagnostics = @{
            Timestamp = Get-Date -Format "o"
            DockerStatus = Get-DockerStatus
            DockerProcesses = Get-Process "*docker*" -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime
            DockerDesktopProcesses = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime
            DockerService = Get-Service "com.docker.service" -ErrorAction SilentlyContinue | Select-Object Name, Status, StartType
            DockerConfig = if (Test-Path $DockerConfigPath) { Get-Content $DockerConfigPath -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue } else { $null }
            State = $state
        }
        
        $diagnostics | ConvertTo-Json -Depth 5 | Out-File "logs/docker_diagnostic_$(Get-Date -Format 'yyyyMMdd_HHmmss').json" -Force -Encoding utf8
        $diagnostics | Format-List | Out-String | Write-Host
        exit 0
    }
    'repair' {
        $result = Repair-DockerInstallation
        exit $(if ($result) { 0 } else { 1 })
    }
    'clean' {
        Write-Log "Cleaning Docker system..."
        docker system prune -a --volumes --force
        exit $LASTEXITCODE
    }
    'switch-mode' {
        if ($Mode -notin @('windows', 'linux')) {
            Write-Log "Please specify target mode: -Mode 'windows' or -Mode 'linux'" "ERROR"
            exit 1
        }
        $result = Switch-DockerMode -TargetMode $Mode
        exit $(if ($result) { 0 } else { 1 })
    }
    default {
        Write-Log "Unknown action: $Action" "ERROR"
        exit 1
    }
}
