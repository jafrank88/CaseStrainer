param([switch]$Help)

function Show-Help {
    Write-Host "Test Launcher" -ForegroundColor Cyan
}

if ($Help) {
    Show-Help
} else {
    Write-Host "Test successful" -ForegroundColor Green
} 