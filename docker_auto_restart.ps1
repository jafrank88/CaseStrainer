# Docker Desktop Auto-Restart Script
# Run this in background to keep Docker Desktop running

while ($true) {
    $dockerProcesses = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if ($dockerProcesses.Count -eq 0) {
        Write-Host "Docker Desktop crashed, restarting..." -ForegroundColor Yellow
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Minimized
        Start-Sleep -Seconds 30
    }
    Start-Sleep -Seconds 10
}
