# docker_engine.ps1 - Enhanced Docker Engine Management for CaseStrainer
# 
# This script provides robust Docker environment management, including:
# - Automatic PATH configuration for Docker and Docker Compose
# - Docker Desktop service management
# - Health checks and recovery
# - WSL integration
# - Comprehensive logging

# Set strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Configuration
$Script:Config = @{
    # Paths
    DockerPaths = @(
        "C:\Program Files\Docker\Docker\resources\bin"
        "C:\Program Files\Docker\Docker\resources"
        "$env:ProgramFiles\Docker\Docker\resources\bin"
        "$env:ProgramFiles\Docker\Docker\resources"
    )
    
    # Service names
    DockerServiceName = "com.docker.service"
    
    # Timeouts (in seconds)
    DockerStartTimeout = 300  # 5 minutes
    HealthCheckTimeout = 30    # 30 seconds
    
    # Logging
    LogFile = Join-Path $PSScriptRoot "..\logs\docker_engine_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
    
    # WSL Configuration
    WSLDistroName = "Ubuntu"
}

# Initialize logging
function Initialize-Logging {
    [CmdletBinding()]
    param()
    
    try {
        # Create logs directory if it doesn't exist
        $logDir = Split-Path -Parent $Script:Config.LogFile
        if (-not (Test-Path $logDir)) {
            Write-Host "Creating log directory: $logDir" -ForegroundColor Cyan
            New-Item -ItemType Directory -Path $logDir -Force -ErrorAction Stop | Out-Null
        }
        
        # Ensure we can write to the log file
        $testLogPath = Join-Path $logDir "test_$([System.IO.Path]::GetRandomFileName())"
        try {
            "Test log entry" | Out-File -FilePath $testLogPath -Force -ErrorAction Stop
            if (Test-Path $testLogPath) {
                Remove-Item -Path $testLogPath -Force -ErrorAction SilentlyContinue
            }
            
            # Start a new log file
            "=== Docker Engine Management - $(Get-Date) ===" | Out-File -FilePath $Script:Config.LogFile -Force -ErrorAction Stop
            Write-Host "Logging initialized. Log file: $($Script:Config.LogFile)" -ForegroundColor Green
        }
        catch {
            # If we can't write to the log file, use a temporary file
            $tempLogFile = [System.IO.Path]::GetTempFileName()
            $Script:Config.LogFile = $tempLogFile
            "=== Docker Engine Management - $(Get-Date) ===" | Out-File -FilePath $tempLogFile -Force
            Write-Host "WARNING: Could not write to log file. Using temporary file: $tempLogFile" -ForegroundColor Yellow
        }
    }
    catch {
        # If all else fails, write to a file in the temp directory
        $tempLogFile = [System.IO.Path]::GetTempFileName()
        $Script:Config.LogFile = $tempLogFile
        "=== Docker Engine Management - $(Get-Date) ===" | Out-File -FilePath $tempLogFile -Force
        Write-Host "WARNING: Could not initialize logging. Using temporary file: $tempLogFile" -ForegroundColor Yellow
    }
}

# Write log message
function Write-Log {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [ValidateSet('DEBUG', 'INFO', 'WARNING', 'ERROR', 'SUCCESS')]
        [string]$Level = 'INFO',
        
        [switch]$NoConsoleOutput
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Always write to console first to ensure we see the output
    try {
        # Color output based on level
        switch ($Level) {
            'ERROR'   { Write-Host $logMessage -ForegroundColor Red }
            'WARNING' { Write-Host $logMessage -ForegroundColor Yellow }
            'SUCCESS' { Write-Host $logMessage -ForegroundColor Green }
            'DEBUG'   { if ($Script:Config.Debug) { Write-Host $logMessage -ForegroundColor Gray } }
            default   { Write-Host $logMessage -ForegroundColor Cyan }
        }
    }
    catch {
        # If Write-Host fails, try another method
        try { [Console]::WriteLine($logMessage) } catch {}
    }
    
    # Then try to write to log file if possible
    try {
        # Ensure the log directory exists
        $logDir = Split-Path -Parent $Script:Config.LogFile -ErrorAction Stop
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir -Force -ErrorAction Stop | Out-Null
        }
        
        # Append to log file
        $logMessage | Out-File -FilePath $Script:Config.LogFile -Append -Force -ErrorAction Stop
    }
    catch {
        # If writing to log file fails, try a temporary location
        try {
            $tempLogPath = [System.IO.Path]::GetTempFileName()
            $logMessage | Out-File -FilePath $tempLogPath -Append -Force -ErrorAction Stop
            Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [WARNING] Could not write to log file. Using temporary file: $tempLogPath" -ForegroundColor Yellow
        }
        catch {
            # If all else fails, just write to error stream
            Write-Error "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [ERROR] Failed to write to log: $_"
        }
    }
}

# Configure system PATH to include Docker and Docker Compose
function Initialize-DockerPath {
    [CmdletBinding()]
    param()
    
    Write-Log "Configuring Docker and Docker Compose in PATH..."
    
    $pathModified = $false
    $currentPath = [System.Environment]::GetEnvironmentVariable('Path', 'Process')
    
    foreach ($dockerPath in $Script:Config.DockerPaths) {
        if (Test-Path $dockerPath) {
            if ($currentPath -notlike "*$dockerPath*") {
                Write-Log "Adding to PATH: $dockerPath" -Level DEBUG
                $env:Path = "$dockerPath;$env:Path"
                $pathModified = $true
            }
        }
    }
    
    if ($pathModified) {
        Write-Log "PATH updated to include Docker and Docker Compose"
    } else {
        Write-Log "Docker and Docker Compose already in PATH" -Level DEBUG
    }
    
    # Verify Docker CLI is accessible
    if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
        throw "Docker CLI not found in PATH. Please ensure Docker Desktop is installed."
    }
    
    # Verify Docker Compose is accessible
    if (-not (Get-Command "docker-compose" -ErrorAction SilentlyContinue)) {
        Write-Log "Docker Compose not found in PATH. Some features may be limited." -Level WARNING
    }
}

# Check if Docker Desktop is installed
function Test-DockerDesktopInstalled {
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    
    Write-Log "Checking if Docker Desktop is installed..." -Level DEBUG
    
    try {
        # First, check if docker command is available
        $dockerExe = Get-Command "docker" -ErrorAction SilentlyContinue
        if ($dockerExe) {
            Write-Log "Docker CLI found at: $($dockerExe.Source)" -Level DEBUG
            
            # Verify the docker command works
            $dockerVersion = & docker --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Docker CLI is working: $dockerVersion" -Level DEBUG
                return $true
            } else {
                Write-Log "Docker CLI found but command failed: $dockerVersion" -Level WARNING
            }
        } else {
            Write-Log "Docker CLI not found in PATH" -Level DEBUG
        }
        
        # Check common installation paths
        $dockerPaths = @(
            "C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"
            "${env:ProgramFiles}\\Docker\\Docker\\Docker Desktop.exe"
        )
        
        Write-Log "Checking Docker Desktop installation paths..." -Level DEBUG
        $foundPath = $false
        
        foreach ($path in $dockerPaths) {
            Write-Log "Checking path: $path" -Level DEBUG
            if (Test-Path $path) {
                Write-Log "Docker Desktop found at: $path" -Level DEBUG
                $foundPath = $true
                
                # Check if the Docker service is running
                $service = Get-Service -Name $Script:Config.DockerServiceName -ErrorAction SilentlyContinue
                if ($service) {
                    Write-Log "Docker service status: $($service.Status)" -Level DEBUG
                    if ($service.Status -ne 'Running') {
                        Write-Log "Docker service is not running. Attempting to start..." -Level WARNING
                        try {
                            Start-Service -Name $Script:Config.DockerServiceName -ErrorAction Stop
                            $service.WaitForStatus('Running', (New-TimeSpan -Seconds 30))
                            Write-Log "Docker service started successfully" -Level INFO
                        } catch {
                            Write-Log "Failed to start Docker service: $_" -Level ERROR
                        }
                    }
                } else {
                    Write-Log "Docker service not found. Docker Desktop may not be properly installed." -Level WARNING
                }
                
                return $true
            }
        }
        
        if (-not $foundPath) {
            Write-Log "Docker Desktop not found in standard installation paths" -Level DEBUG
        }
        
        return $false
    }
    catch {
        Write-Log "Error checking Docker Desktop installation: $_" -Level ERROR
        return $false
    }
}

# Start Docker Desktop
function Start-DockerDesktop {
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    
    Write-Log "Starting Docker Desktop..."
    
    # Check if Docker Desktop is already running
    $dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if ($dockerProcess) {
        Write-Log "Docker Desktop is already running" -Level DEBUG
        return $true
    }
    
    # Try to start Docker Desktop
    try {
        # Try to start via service first
        $service = Get-Service -Name $Script:Config.DockerServiceName -ErrorAction SilentlyContinue
        if ($service -and $service.Status -ne 'Running') {
            Write-Log "Starting Docker service..." -Level DEBUG
            Start-Service -Name $Script:Config.DockerServiceName -ErrorAction Stop
            
            # Wait for service to start
            $service.WaitForStatus('Running', (New-TimeSpan -Seconds $Script:Config.DockerStartTimeout))
        }
        
        # Start Docker Desktop application
        $dockerDesktopPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $dockerDesktopPath) {
            Write-Log "Launching Docker Desktop application..." -Level DEBUG
            Start-Process -FilePath $dockerDesktopPath -ErrorAction Stop
        }
        
        # Wait for Docker daemon to be ready
        return Wait-DockerReady -Timeout $Script:Config.DockerStartTimeout
    }
    catch {
        Write-Log "Failed to start Docker Desktop: $_" -Level ERROR
        return $false
    }
}

# Wait for Docker daemon to be ready
function Wait-DockerReady {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [int]$Timeout = 300  # 5 minutes default
    )
    
    Write-Log "Waiting for Docker daemon to be ready (timeout: ${Timeout}s)..."
    
    $startTime = Get-Date
    $timeoutTime = $startTime.AddSeconds($Timeout)
    $isReady = $false
    
    while ((Get-Date) -lt $timeoutTime) {
        try {
            $dockerInfo = docker info --format '{{json .}}' 2>&1 | ConvertFrom-Json -ErrorAction Stop
            if ($dockerInfo -and $dockerInfo.ServerVersion) {
                $isReady = $true
                Write-Log "Docker daemon is ready (Version: $($dockerInfo.ServerVersion))"
                break
            }
        }
        catch {
            # Ignore errors while waiting
        }
        
        # Show progress every 5 seconds
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        if (($elapsed % 5) -eq 0) {
            Write-Log "Still waiting for Docker daemon... (${elapsed}s elapsed)" -Level DEBUG
        }
        
        Start-Sleep -Seconds 1
    }
    
    if (-not $isReady) {
        Write-Log "Timed out waiting for Docker daemon to be ready" -Level ERROR
        return $false
    }
    
    return $true
}

# Check Docker health
function Test-DockerHealth {
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param()
    
    $result = @{
        DockerInstalled = $false
        DockerRunning = $false
        DockerComposeAvailable = $false
        WSLIntegration = $false
        Issues = @()
    }
    
    # Check if Docker is installed
    $result.DockerInstalled = Test-DockerDesktopInstalled
    if (-not $result.DockerInstalled) {
        $result.Issues += "Docker Desktop is not installed"
        return [PSCustomObject]$result
    }
    
    # Check Docker CLI
    try {
        $dockerVersion = & docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $result.DockerRunning = $true
            Write-Log "Docker CLI is working: $dockerVersion" -Level DEBUG
            
            # Check Docker daemon
            try {
                $dockerInfo = docker info 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Log "Docker daemon is running" -Level DEBUG
                } else {
                    $result.DockerRunning = $false
                    $result.Issues += "Docker daemon is not running: $dockerInfo"
                }
            }
            catch {
                $result.DockerRunning = $false
                $result.Issues += "Error checking Docker daemon: $_"
            }
        } else {
            $result.Issues += "Docker CLI returned error: $dockerVersion"
        }
    }
    catch {
        $result.Issues += "Docker CLI is not working: $_"
    }
    
    # Check Docker Compose
    try {
        $composeVersion = & docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $result.DockerComposeAvailable = $true
            Write-Log "Docker Compose is available: $composeVersion" -Level DEBUG
        } else {
            $result.Issues += "Docker Compose returned error: $composeVersion"
        }
    }
    catch {
        $result.Issues += "Docker Compose is not available: $_"
    }
    
    # Check WSL integration
    if (Get-Command "wsl" -ErrorAction SilentlyContinue) {
        try {
            $wslList = wsl --list --verbose 2>&1
            if ($LASTEXITCODE -eq 0) {
                $result.WSLIntegration = $true
                Write-Log "WSL is available and integrated with Docker" -Level DEBUG
            } else {
                $result.Issues += "WSL is installed but not properly configured: $wslList"
            }
        }
        catch {
            $result.Issues += "Error checking WSL integration: $_"
        }
    } else {
        $result.Issues += "WSL is not installed"
    }
    
    return [PSCustomObject]$result
}

# Main function to ensure Docker is ready
function Initialize-DockerEnvironment {
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    
    try {
        Write-Log "Initializing Docker environment..." -Level DEBUG
        
        # Initialize logging
        Initialize-Logging
        
        # Check if Docker is installed
        Write-Log "Checking if Docker Desktop is installed..." -Level DEBUG
        if (-not (Test-DockerDesktopInstalled)) {
            throw "Docker Desktop is not installed. Please install Docker Desktop from https://www.docker.com/products/docker-desktop/"
        }
        Write-Log "Docker Desktop is installed" -Level DEBUG
        
        # Configure PATH
        Write-Log "Configuring Docker PATH..." -Level DEBUG
        Initialize-DockerPath
        
        # Check Docker health
        Write-Log "Checking Docker health..." -Level DEBUG
        $health = Test-DockerHealth -ErrorAction Stop
        
        # Log health status
        Write-Log "Docker health check completed. Docker running: $($health.DockerRunning), Issues: $($health.Issues.Count)" -Level DEBUG
        
        # Try to fix issues if any
        if ($health.Issues.Count -gt 0) {
            Write-Log "Found $($health.Issues.Count) issue(s) with Docker environment:" -Level WARNING
            foreach ($issue in $health.Issues) {
                Write-Log "  - $issue" -Level WARNING
            }
            
            # Try to start Docker Desktop if not running
            if (-not $health.DockerRunning) {
                Write-Log "Docker is not running. Attempting to start Docker Desktop..." -Level WARNING
                if (-not (Start-DockerDesktop)) {
                    $errorMsg = "Failed to start Docker Desktop. Please start it manually and try again."
                    Write-Log $errorMsg -Level ERROR
                    throw $errorMsg
                }
                
                # Re-check health after starting
                Write-Log "Re-checking Docker health after starting Docker Desktop..." -Level DEBUG
                $health = Test-DockerHealth -ErrorAction Stop
                Write-Log "Docker health after start attempt - Running: $($health.DockerRunning), Issues: $($health.Issues.Count)" -Level DEBUG
            }
            
            # If still issues after trying to fix
            if ($health.Issues.Count -gt 0) {
                $issuesList = $health.Issues -join "`n  - "
                Write-Log "The following issues could not be automatically resolved:`n  - $issuesList" -Level WARNING
                
                if (-not $health.DockerRunning) {
                    $errorMsg = "Docker is still not running after start attempt. Please check Docker Desktop and try again."
                    Write-Log $errorMsg -Level ERROR
                    throw $errorMsg
                }
            }
        }
        
        # Final check
        if (-not $health.DockerRunning) {
            $errorMsg = "Docker is not running. Please ensure Docker Desktop is started and try again."
            Write-Log $errorMsg -Level ERROR
            throw $errorMsg
        }
        
        # Verify Docker CLI is working
        try {
            $dockerVersion = & docker --version 2>&1
            if ($LASTEXITCODE -ne 0) {
                throw "Docker CLI returned error: $dockerVersion"
            }
            Write-Log "Docker CLI is working: $dockerVersion" -Level INFO
            
            # Verify Docker daemon is accessible
            $dockerInfo = & docker info 2>&1
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to get Docker info: $dockerInfo"
            }
            Write-Log "Docker daemon is accessible" -Level INFO
        }
        catch {
            $errorMsg = "Docker CLI verification failed: $_"
            Write-Log $errorMsg -Level ERROR
            throw $errorMsg
        }
        
        Write-Log "Docker environment is ready" -Level INFO
        return $true
    }
    catch {
        $errorMsg = "Failed to initialize Docker environment: $_"
        Write-Log $errorMsg -Level ERROR
        
        # Additional troubleshooting steps
        Write-Log "`nTroubleshooting steps:" -Level WARNING
        Write-Log "1. Make sure Docker Desktop is installed and running" -Level WARNING
        Write-Log "2. Open Docker Desktop and check for any error messages" -Level WARNING
        Write-Log "3. Try restarting Docker Desktop" -Level WARNING
        Write-Log "4. Check if virtualization is enabled in your BIOS" -Level WARNING
        Write-Log "5. Run 'docker --version' in a new PowerShell window to verify Docker CLI is accessible" -Level WARNING
        
        return $false
    }
}

# If script is run directly, initialize the Docker environment
if ($MyInvocation.InvocationName -ne '.') {
    if (Initialize-DockerEnvironment) {
        Write-Log "Docker environment is ready to use!" -Level INFO
        exit 0
    } else {
        Write-Log "Failed to initialize Docker environment. Check the logs for details." -Level ERROR
        exit 1
    }
}
