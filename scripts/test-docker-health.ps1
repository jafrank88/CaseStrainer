# Test Docker health check functionality
$ErrorActionPreference = "Stop"

# Import the Docker module
$dockerModulePath = Join-Path $PSScriptRoot "modules\Docker.psm1"
if (-not (Test-Path $dockerModulePath)) {
    Write-Error "Docker module not found at $dockerModulePath"
    exit 1
}

# Import the module
Import-Module $dockerModulePath -Force -ErrorAction Stop

# Run basic tests
Write-Host "=== Testing Docker Module ===" -ForegroundColor Cyan

# 1. Test basic Docker availability
Write-Host "`n[TEST] Basic Docker availability..." -ForegroundColor Yellow
$dockerAvailable = Test-DockerAvailability
Write-Host "Docker available: $dockerAvailable" -ForegroundColor $(if ($dockerAvailable) { "Green" } else { "Red" })

# 2. Test Docker processes
Write-Host "`n[TEST] Docker processes..." -ForegroundColor Yellow
$processes = Test-DockerProcesses
Write-Host "Docker processes running: $processes" -ForegroundColor $(if ($processes) { "Green" } else { "Red" })

# 3. Test Docker CLI
Write-Host "`n[TEST] Docker CLI..." -ForegroundColor Yellow
$cli = Test-DockerCLI
Write-Host "Docker CLI available: $cli" -ForegroundColor $(if ($cli) { "Green" } else { "Red" })

# 4. Test Docker daemon
Write-Host "`n[TEST] Docker daemon..." -ForegroundColor Yellow
$daemon = Test-DockerDaemon
Write-Host "Docker daemon available: $daemon" -ForegroundColor $(if ($daemon) { "Green" } else { "Red" })

# 5. Test Docker resources
Write-Host "`n[TEST] Docker resources..." -ForegroundColor Yellow
$resources = Test-DockerResources
Write-Host "Docker resources check passed: $resources" -ForegroundColor $(if ($resources) { "Green" } else { "Red" })

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
