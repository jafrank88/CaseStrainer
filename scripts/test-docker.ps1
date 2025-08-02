# Test Docker module functionality
$ErrorActionPreference = "Stop"

# Import the Docker module
$modulePath = Join-Path $PSScriptRoot "modules\Docker.psm1"
if (-not (Test-Path $modulePath)) {
    Write-Error "Docker module not found at $modulePath"
    exit 1
}

# Import the module
Write-Host "Importing Docker module from $modulePath..." -ForegroundColor Cyan
Import-Module $modulePath -Force -ErrorAction Stop

# Test basic Docker availability
Write-Host "`n=== Testing Docker Availability ===" -ForegroundColor Cyan
$dockerAvailable = Test-DockerAvailability
Write-Host "Docker available: $dockerAvailable" -ForegroundColor $(if ($dockerAvailable) { "Green" } else { "Red" })

# Run health check
Write-Host "`n=== Running Docker Health Check ===" -ForegroundColor Cyan
$health = Invoke-DockerHealthCheck -Detailed

# Display results
Write-Host "`n=== Health Check Results ===" -ForegroundColor Cyan
$health.Results | Format-Table @{
    Name = "Test"
    Expression = { $_.Key }
}, @{
    Name = "Status"
    Expression = { if ($_.Value) { "[OK]" } else { "[FAIL]" } }
    FormatString = "{0,-10}"
} -AutoSize

Write-Host "`nOverall Status: $(if ($health.Overall) { 'HEALTHY' } else { 'UNHEALTHY' })" -ForegroundColor $(if ($health.Overall) { 'Green' } else { 'Red' })

# Check resource usage
Write-Host "`n=== Docker Resource Usage ===" -ForegroundColor Cyan
$usage = Get-DockerResourceUsage
$usage | Format-List

Write-Host "`nTest complete!" -ForegroundColor Green
