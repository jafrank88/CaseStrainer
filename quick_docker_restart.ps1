# Quick Docker Restart Script
# Use this when Docker becomes unresponsive

Write-Host "=== Emergency Docker Restart ===" -ForegroundColor Red

Write-Host "Stopping Docker processes..." -ForegroundColor Yellow
Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "com.docker.backend" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "com.docker.build" -Force -ErrorAction SilentlyContinue

Write-Host "Waiting for processes to stop..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "Starting Docker Desktop..." -ForegroundColor Green
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

Write-Host "Waiting for Docker to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "Testing Docker responsiveness..." -ForegroundColor Cyan
try {
    $version = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker is responsive!" -ForegroundColor Green
        Write-Host "Docker version: $version" -ForegroundColor Green
    } else {
        throw "Docker still not responsive"
    }
} catch {
    Write-Host "❌ Docker is still not responsive. Try restarting your computer." -ForegroundColor Red
    exit 1
}

Write-Host "=== Restart Complete ===" -ForegroundColor Green 