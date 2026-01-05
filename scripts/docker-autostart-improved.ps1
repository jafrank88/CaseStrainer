# docker-autostart.ps1 - Improved version for unattended operation
# This script waits for Docker to be ready, then starts containers

param(
    [switch]$Force,
    [switch]$Test
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Configuration
$ProjectPath = "D:\dev\casestrainer"
$ComposeFile = Join-Path $ProjectPath "docker-compose.prod.yml"
$LogFile = Join-Path $ProjectPath "logs\autostart.log"
$DockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"

# Create logs directory if it doesn't exist
$LogDir = Split-Path $LogFile
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $LogMessage
    
    # Also output to console for immediate feedback
    switch ($Level) {
        "ERROR" { Write-Host $Message -ForegroundColor Red }
        "WARN"  { Write-Host $Message -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $Message -ForegroundColor Green }
        default { Write-Host $Message -ForegroundColor Gray }
    }
}

function Start-DockerDesktop {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
    param()
    
    Write-Log "Starting Docker Desktop..." "INFO"
    
    if (-not (Test-Path $DockerDesktopPath)) {
        # Try x86 path
        $DockerDesktopPath = "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
    }
    
    if (-not (Test-Path $DockerDesktopPath)) {
        Write-Log "Docker Desktop not found!" "ERROR"
        return $false
    }
    
    if ($PSCmdlet.ShouldProcess("Docker Desktop", "Start")) {
        try {
            # Check if Docker Desktop is already running
            $dockerProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
            if ($dockerProcess) {
                Write-Log "Docker Desktop is already running" "INFO"
                return $true
            }
            
            # Start Docker Desktop
            Start-Process -FilePath $DockerDesktopPath -WindowStyle Minimized
            Write-Log "Docker Desktop started" "SUCCESS"
            
            # Wait a bit for it to initialize
            Start-Sleep -Seconds 10
            
            return $true
        } catch {
            Write-Log "Failed to start Docker Desktop: $($_.Exception.Message)" "ERROR"
            return $false
        }
    }
}

function Test-DockerReady {
    param([int]$MaxWait = 300)
    
    Write-Log "Testing Docker connectivity..." "INFO"
    $Waited = 0
    $DockerReady = $false
    
    while ($Waited -lt $MaxWait) {
        try {
            $null = docker info 2>&1
            if ($LASTEXITCODE -eq 0) {
                $DockerReady = $true
                Write-Log "Docker daemon is ready!" "SUCCESS"
                break
            }
        } catch {
            # Docker command not available yet
            Write-Log "Docker command failed: $($_.Exception.Message)" "WARN"
        }
        
        $Waited += 5
        if ($Waited % 15 -eq 0) {
            Write-Log "Still waiting for Docker... ($Waited seconds)" "INFO"
        }
        Start-Sleep -Seconds 5
    }
    
    if (-not $DockerReady) {
        Write-Log "Docker did not become ready within $MaxWait seconds" "ERROR"
        return $false
    }
    
    return $true
}

function Start-Containers {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
    param()
    
    Write-Log "Starting CaseStrainer containers..." "INFO"
    
    if ($PSCmdlet.ShouldProcess("CaseStrainer containers", "Start")) {
        try {
            Push-Location $ProjectPath
            
            # Check if compose file exists
            if (-not (Test-Path $ComposeFile)) {
                Write-Log "Compose file not found: $ComposeFile" "ERROR"
                return $false
            }
            
            # Stop existing containers if any
            Write-Log "Stopping any existing containers..." "INFO"
            docker-compose -f $ComposeFile down 2>&1 | Out-Null
            
            # Start containers
            Write-Log "Running: docker-compose -f $ComposeFile up -d" "INFO"
            $output = docker-compose -f $ComposeFile up -d 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Containers started successfully!" "SUCCESS"
                
                # Wait a bit and check status
                Start-Sleep -Seconds 10
                $running = docker ps --filter name=casestrainer --format "{{.Names}}" | Measure-Object | Select-Object -ExpandProperty Count
                Write-Log "Found $running CaseStrainer containers running" "INFO"
                
                return $true
            } else {
                Write-Log "Failed to start containers: $output" "ERROR"
                return $false
            }
        } catch {
            Write-Log "Error starting containers: $($_.Exception.Message)" "ERROR"
            return $false
        } finally {
            Pop-Location
        }
    }
}

# Main execution
Write-Log "=== CaseStrainer Auto-Start Started ===" "INFO"
Write-Log "Running as: $env:USERDOMAIN\$env:USERNAME" "INFO"
Write-Log "Force mode: $Force" "INFO"

try {
    # Step 1: Start Docker Desktop
    if (-not (Start-DockerDesktop)) {
        Write-Log "Failed to start Docker Desktop, aborting" "ERROR"
        exit 1
    }
    
    # Step 2: Wait for Docker daemon
    if (-not (Test-DockerReady)) {
        Write-Log "Docker daemon not ready, attempting restart..." "WARN"
        
        # Try to restart Docker Desktop
        Get-Process "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
        
        if (-not (Start-DockerDesktop)) {
            Write-Log "Failed to restart Docker Desktop" "ERROR"
            exit 1
        }
        
        if (-not (Test-DockerReady -MaxWait 600)) {
            Write-Log "Docker still not ready after restart, giving up" "ERROR"
            exit 1
        }
    }
    
    # Step 3: Start containers
    if (-not (Start-Containers)) {
        Write-Log "Failed to start containers" "ERROR"
        exit 1
    }
    
    Write-Log "=== Auto-Start Completed Successfully ===" "SUCCESS"
    
    # Health check
    if ($Test) {
        Write-Log "Performing health check..." "INFO"
        $healthUrl = "http://localhost:5000/api/health"
        try {
            $response = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 30
            Write-Log "Health check passed: $($response.status)" "SUCCESS"
        } catch {
            Write-Log "Health check failed: $($_.Exception.Message)" "WARN"
        }
    }
    
    exit 0
    
} catch {
    Write-Log "Fatal error in auto-start: $($_.Exception.Message)" "ERROR"
    exit 1
}
