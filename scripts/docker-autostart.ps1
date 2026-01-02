# CaseStrainer Auto-Start Script
# This script starts Docker Desktop, waits for it to be ready, then starts containers

$ErrorActionPreference = "SilentlyContinue"
$ProjectPath = "D:\dev\casestrainer"
$ComposeFile = Join-Path $ProjectPath "docker-compose.prod.yml"
$LogFile = Join-Path $ProjectPath "logs\autostart.log"

# Create logs directory if it doesn't exist
$LogDir = Split-Path $LogFile
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] $Message"
    Add-Content -Path $LogFile -Value $LogMessage
}

Write-Log "=== CaseStrainer Auto-Start ==="

# Start Docker Desktop if not running
$dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
if (-not (Test-Path $dockerDesktopPath)) {
    $dockerDesktopPath = "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
}

$dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
if (-not $dockerProcess) {
    Write-Log "Starting Docker Desktop..."
    if (Test-Path $dockerDesktopPath) {
        Start-Process -FilePath $dockerDesktopPath -WindowStyle Minimized
        Write-Log "Docker Desktop process started"
    } else {
        Write-Log "[WARN] Docker Desktop not found at expected path"
    }
} else {
    Write-Log "Docker Desktop already running"
}

Write-Log "Waiting for Docker to be ready..."

# Wait for Docker daemon (max 5 minutes)
$MaxWait = 300
$Waited = 0
$DockerReady = $false

while ($Waited -lt $MaxWait) {
    $DockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        $DockerReady = $true
        Write-Log "Docker is ready!"
        break
    }
    Start-Sleep -Seconds 10
    $Waited += 10
    Write-Log "Still waiting for Docker... ($Waited seconds)"
}

if (-not $DockerReady) {
    Write-Log "[ERROR] Docker did not become ready within $MaxWait seconds"
    exit 1
}

# Additional wait for Docker Desktop to fully initialize
Write-Log "Waiting for Docker Desktop to fully initialize..."
Start-Sleep -Seconds 30

# Start containers
Write-Log "Starting CaseStrainer containers..."
Push-Location $ProjectPath
docker-compose -f $ComposeFile up -d 2>&1 | Tee-Object -FilePath (Join-Path $ProjectPath "logs\docker-startup.log")

if ($LASTEXITCODE -eq 0) {
    Write-Log "[SUCCESS] Containers started successfully"
} else {
    Write-Log "[ERROR] Failed to start containers (exit code: $LASTEXITCODE)"
    exit 1
}

Pop-Location
Write-Log "=== Auto-Start Complete ==="
