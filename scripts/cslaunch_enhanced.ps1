# cslaunch_enhanced.ps1 - Enhanced CaseStrainer Launcher
# 
# This script provides a robust way to launch CaseStrainer with proper Docker environment setup

# Set strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Import the enhanced Docker engine module
$dockerEnginePath = Join-Path $PSScriptRoot "docker_engine.ps1"
if (-not (Test-Path $dockerEnginePath)) {
    Write-Host "[ERROR] docker_engine.ps1 not found at $dockerEnginePath" -ForegroundColor Red
    exit 1
}

# Import the module
. $dockerEnginePath

# Configure logging
$logDir = Join-Path $PSScriptRoot "..\logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('INFO', 'WARNING', 'ERROR', 'DEBUG')]
        [string]$Level = 'INFO'
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Write to console with appropriate color
    switch ($Level) {
        'ERROR'   { Write-Host $logMessage -ForegroundColor Red }
        'WARNING' { Write-Host $logMessage -ForegroundColor Yellow }
        'INFO'    { Write-Host $logMessage -ForegroundColor Cyan }
        'DEBUG'   { Write-Host $logMessage -ForegroundColor Gray }
    }
}

# Main execution
try {
    Write-Log "Starting enhanced CaseStrainer launcher..."
    
    # 1. Initialize Docker environment
    Write-Log "Initializing Docker environment..."
    if (-not (Initialize-DockerEnvironment)) {
        throw "Failed to initialize Docker environment. Please check the logs and try again."
    }
    
    # 2. Check Docker health
    $health = Test-DockerHealth
    if (-not $health.DockerRunning) {
        throw "Docker is not running. Please ensure Docker Desktop is started and try again."
    }
    
    # 3. Run the original cslaunch.ps1 with all arguments
    $cslaunchPath = Join-Path $PSScriptRoot "..\cslaunch.ps1"
    if (-not (Test-Path $cslaunchPath)) {
        throw "cslaunch.ps1 not found at $cslaunchPath"
    }
    
    Write-Log "Launching CaseStrainer..."
    & $cslaunchPath @args
    
    if ($LASTEXITCODE -ne 0) {
        throw "CaseStrainer exited with error code $LASTEXITCODE"
    }
    
    Write-Log "CaseStrainer has completed successfully" -Level INFO
}
catch {
    Write-Log "Error: $_" -Level ERROR
    exit 1
}
