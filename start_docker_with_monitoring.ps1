# Docker startup with monitoring
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"D:\dev\casestrainer\persistent_monitor.ps1`"" -WindowStyle Hidden

# Start Docker Desktop
& "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Wait for Docker to start
Write-Host "Waiting for Docker to start..." -ForegroundColor Yellow
$timeout = 300  # 5 minutes
$elapsed = 0

while ($elapsed -lt $timeout) {
    $null = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker is ready!" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 5
    $elapsed += 5
    Write-Host "." -NoNewline
}

if ($elapsed -ge $timeout) {
    Write-Host "`nDocker failed to start within 5 minutes" -ForegroundColor Red
} else {
    # Start CaseStrainer containers
    Write-Host "Starting CaseStrainer containers..." -ForegroundColor Yellow
    & "D:\dev\casestrainer\cslaunch.bat"
}
