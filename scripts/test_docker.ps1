# test_docker.ps1 - Simple Docker environment test script

# Set error action preference
$ErrorActionPreference = 'Stop'

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$ForegroundColor = 'White',
        [switch]$NoNewline
    )
    
    if ($NoNewline) {
        Write-Host $Message -ForegroundColor $ForegroundColor -NoNewline
    } else {
        Write-Host $Message -ForegroundColor $ForegroundColor
    }
}

# Function to run a command and return the result
function Invoke-CommandWithOutput {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-ColorOutput "`n=== $Description ===" -ForegroundColor Cyan
    Write-ColorOutput "Command: $Command" -ForegroundColor Gray
    
    try {
        $output = Invoke-Expression $Command 2>&1 | Out-String
        Write-ColorOutput "Exit Code: $LASTEXITCODE" -ForegroundColor Green
        Write-ColorOutput "Output:" -ForegroundColor Gray
        Write-ColorOutput $output.Trim()
        return $output
    }
    catch {
        Write-ColorOutput "Error: $_" -ForegroundColor Red
        return $null
    }
}

# Main execution
Write-ColorOutput "=== Docker Environment Test ===" -ForegroundColor Yellow
Write-ColorOutput "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# 1. Check Docker installation
Write-ColorOutput "`n[1/5] Checking Docker installation..." -ForegroundColor Cyan
$dockerVersion = Invoke-CommandWithOutput -Command "docker --version" -Description "Docker Version"

# 2. Check Docker Compose installation
Write-ColorOutput "`n[2/5] Checking Docker Compose installation..." -ForegroundColor Cyan
$dockerComposeVersion = Invoke-CommandWithOutput -Command "docker-compose --version" -Description "Docker Compose Version"

# 3. Check Docker service status
Write-ColorOutput "`n[3/5] Checking Docker service status..." -ForegroundColor Cyan
$serviceStatus = Invoke-CommandWithOutput -Command "Get-Service -Name 'com.docker.service' | Select-Object Name, Status, StartType | Format-List" -Description "Docker Service Status"

# 4. Check Docker info
Write-ColorOutput "`n[4/5] Checking Docker info..." -ForegroundColor Cyan
$dockerInfo = Invoke-CommandWithOutput -Command "docker info" -Description "Docker Info"

# 5. Check Docker containers
Write-ColorOutput "`n[5/5] Checking running containers..." -ForegroundColor Cyan
$containers = Invoke-CommandWithOutput -Command "docker ps --all" -Description "Docker Containers"

# Summary
Write-ColorOutput "`n=== Test Summary ===" -ForegroundColor Yellow
if ($dockerVersion -and $dockerComposeVersion -and $dockerInfo) {
    Write-ColorOutput "✅ Docker environment appears to be properly configured" -ForegroundColor Green
} else {
    Write-ColorOutput "❌ Issues detected with Docker environment" -ForegroundColor Red
}

Write-ColorOutput "`nTest completed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
