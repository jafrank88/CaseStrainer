# Force restart Docker Desktop
Write-Host "Force restarting Docker Desktop..." -ForegroundColor Yellow

# Kill all Docker processes
try {
    Stop-Process -Name "Docker Desktop" -Force -ErrorAction Stop
    Stop-Process -Name "Docker for Windows" -Force -ErrorAction SilentlyContinue
    Stop-Process -Name "Docker" -Force -ErrorAction SilentlyContinue
    
    # Kill any remaining Docker processes
    Get-Process | Where-Object { $_.ProcessName -like "*docker*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Wait a moment
    Start-Sleep -Seconds 5
    
    # Start Docker Desktop
    Write-Host "Starting Docker Desktop..." -ForegroundColor Green
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    # Wait for Docker to start
    $maxWait = 120  # seconds
    $startTime = Get-Date
    $dockerReady = $false
    
    Write-Host "Waiting for Docker to start..." -ForegroundColor Cyan
    
    while (((Get-Date) - $startTime).TotalSeconds -lt $maxWait) {
        try {
            $dockerInfo = docker info 2>&1
            if ($LASTEXITCODE -eq 0) {
                $dockerReady = $true
                break
            }
        } catch {}
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }
    
    if ($dockerReady) {
        Write-Host "`nDocker Desktop restarted successfully!" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "`nFailed to restart Docker Desktop. Please try manually." -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
