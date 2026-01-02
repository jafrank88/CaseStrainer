# Cleanup stale CaseStrainer containers
# This script removes containers that are in "Created" state but not running

Write-Host "=== CaseStrainer Container Cleanup ===" -ForegroundColor Cyan

# Get all CaseStrainer containers
$containers = docker ps -a --filter name=casestrainer --format "{{.ID}}\t{{.Names}}\t{{.Status}}"

if (-not $containers) {
    Write-Host "No CaseStrainer containers found." -ForegroundColor Green
    exit 0
}

Write-Host "`nFound CaseStrainer containers:" -ForegroundColor Yellow
Write-Host $containers

# Find stale containers (Created but not running)
$staleContainers = @()
foreach ($line in $containers) {
    $parts = $line -split "`t"
    if ($parts.Count -ge 3) {
        $id = $parts[0].Trim()
        $name = $parts[1].Trim()
        $status = $parts[2].Trim()
        
        if ($status -eq "Created" -or $status -like "Exited*" -or $status -like "Dead*") {
            $staleContainers += @{
                ID = $id
                Name = $name
                Status = $status
            }
        }
    }
}

if ($staleContainers.Count -eq 0) {
    Write-Host "`n✓ No stale containers found." -ForegroundColor Green
    exit 0
}

Write-Host "`nFound $($staleContainers.Count) stale containers:" -ForegroundColor Red
foreach ($container in $staleContainers) {
    Write-Host "  - $($container.ID) ($($container.Name)) - $($container.Status)" -ForegroundColor Gray
}

# Ask for confirmation
$response = Read-Host "`nRemove these stale containers? (y/N)"
if ($response -ne 'y' -and $response -ne 'Y') {
    Write-Host "Cleanup cancelled." -ForegroundColor Yellow
    exit 0
}

# Remove stale containers
Write-Host "`nRemoving stale containers..." -ForegroundColor Yellow
$removed = 0

foreach ($container in $staleContainers) {
    try {
        Write-Host "  Removing $($container.Name)..." -ForegroundColor Gray
        docker rm $container.ID | Out-Null
        $removed++
        Write-Host "  ✓ Removed" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to remove: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== Cleanup Complete ===" -ForegroundColor Cyan
Write-Host "Removed $removed stale containers." -ForegroundColor Green

# Show remaining containers
$remaining = docker ps -a --filter name=casestrainer --format "{{.Names}}\t{{.Status}}"
if ($remaining) {
    Write-Host "`nRemaining containers:" -ForegroundColor Gray
    Write-Host $remaining
}
