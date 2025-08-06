Write-Host "=== Testing Recovery Script ===" -ForegroundColor Cyan

# Test Docker responsiveness
Write-Host "Testing Docker responsiveness..." -ForegroundColor Yellow
$startTime = Get-Date
docker info >$null 2>&1
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker is responsive (response time: $([math]::Round($duration, 2))s)" -ForegroundColor Green
} else {
    Write-Host "✗ Docker is unresponsive" -ForegroundColor Red
}

# Test container status
Write-Host "`nContainer Status:" -ForegroundColor Yellow
docker ps -a

Write-Host "`n✓ Recovery script test completed" -ForegroundColor Green 