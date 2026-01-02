# Clean up stale CaseStrainer containers
# Usage: .\cleanup_containers.ps1

Write-Host "=== CaseStrainer Container Cleanup ===" -ForegroundColor Cyan

# Get all containers
$containers = docker ps -a --filter name=casestrainer --format "table {{.Names}}\t{{.Status}}\t{{.CreatedAt}}" 2>$null

if (-not $containers) {
    Write-Host "No CaseStrainer containers found." -ForegroundColor Green
    exit 0
}

Write-Host "`nAll CaseStrainer containers:"
Write-Host $containers

# Find and remove stale containers
$stale = docker ps -a --filter name=casestrainer --filter status=created --format "{{.ID}}" 2>$null
$exited = docker ps -a --filter name=casestrainer --filter status=exited --format "{{.ID}}" 2>$null
$dead = docker ps -a --filter name=casestrainer --filter status=dead --format "{{.ID}}" 2>$null

$toRemove = @($stale, $exited, $dead) | Where-Object { $_ }

if ($toRemove.Count -eq 0) {
    Write-Host "`n✓ No stale containers to clean up." -ForegroundColor Green
    exit 0
}

Write-Host "`nFound $($toRemove.Count) stale containers to remove:" -ForegroundColor Yellow
foreach ($id in $toRemove) {
    $name = docker inspect $id --format "{{.Name}}" 2>$null
    Write-Host "  - $name ($id)" -ForegroundColor Gray
}

# Remove them
Write-Host "`nRemoving..." -ForegroundColor Yellow
foreach ($id in $toRemove) {
    try {
        docker rm $id | Out-Null
        Write-Host "  ✓ Removed $id" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to remove $id" -ForegroundColor Red
    }
}

Write-Host "`n=== Cleanup Complete ===" -ForegroundColor Cyan

# Show remaining containers
Write-Host "`nActive containers:"
docker ps --filter name=casestrainer --format "table {{.Names}}\t{{.Status}}"
