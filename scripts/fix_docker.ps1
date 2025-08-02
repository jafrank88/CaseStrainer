# fix_docker.ps1 - Script to diagnose and fix Docker service issues

# Import the Docker diagnostics module
$modulePath = Join-Path $PSScriptRoot "modules\DockerDiagnostics.ps1"
if (-not (Test-Path $modulePath)) {
    Write-Host "Error: DockerDiagnostics module not found at $modulePath" -ForegroundColor Red
    exit 1
}

Import-Module $modulePath -Force -ErrorAction Stop

Write-Host "`n=== Docker Service Status ===`n" -ForegroundColor Cyan

# Check current status
$status = Get-DockerStatus -Detailed

if (-not $status.DockerInstalled) {
    Write-Host "Docker is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Docker Version: $($status.DockerVersion)" -ForegroundColor Green

if (-not $status.DockerRunning) {
    Write-Host "Docker Desktop is not running" -ForegroundColor Yellow
    try {
        Start-Process -FilePath "C:\Program Files\Docker\Docker\Docker Desktop.exe" -PassThru | Out-Null
        Write-Host "Started Docker Desktop. Please wait for it to fully initialize..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        $status = Get-DockerStatus -Detailed
    } catch {
        Write-Host "Failed to start Docker Desktop: $_" -ForegroundColor Red
        exit 1
    }
}

# Check service status
if ($status.DockerServiceStatus.Status -ne 'Running') {
    Write-Host "`nDocker service is not running. Attempting to start..." -ForegroundColor Yellow
    try {
        Start-Service -Name "com.docker.service" -ErrorAction Stop
        Write-Host "Docker service started successfully" -ForegroundColor Green
        Start-Sleep -Seconds 5
        $status = Get-DockerStatus -Detailed
    } catch {
        Write-Host "Failed to start Docker service: $_" -ForegroundColor Red
        
        # Try resetting Docker Desktop
        Write-Host "`nAttempting to reset Docker Desktop..." -ForegroundColor Yellow
        try {
            Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            & "C:\Program Files\Docker\Docker\Docker Desktop.exe" --uninstall-service
            Start-Sleep -Seconds 2
            & "C:\Program Files\Docker\Docker\Docker Desktop.exe" --install-service
            Start-Sleep -Seconds 5
            
            # Start Docker Desktop
            Start-Process -FilePath "C:\Program Files\Docker\Docker\Docker Desktop.exe"
            Write-Host "Docker Desktop has been reset. Please wait for it to start..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10
            
            $status = Get-DockerStatus -Detailed
        } catch {
            Write-Host "Failed to reset Docker Desktop: $_" -ForegroundColor Red
            exit 1
        }
    }
}

# Final status check
if (-not $status.DockerDaemonAccessible) {
    Write-Host "`nDocker daemon is still not accessible. Please try the following:" -ForegroundColor Red
    Write-Host "1. Open Docker Desktop and check for any error messages"
    Write-Host "2. Restart your computer"
    Write-Host "3. If the issue persists, try reinstalling Docker Desktop"
    exit 1
}

# Verify Docker is working
Write-Host "`n=== Docker Status ===" -ForegroundColor Green
Write-Host "Docker Version: $($status.DockerVersion)"
Write-Host "Docker Service: $($status.DockerServiceStatus.Status)"
Write-Host "Docker Daemon Accessible: $($status.DockerDaemonAccessible)"

# Run a test container
try {
    Write-Host "`nRunning test container..." -ForegroundColor Cyan
    $testOutput = docker run --rm hello-world 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nDocker is working correctly!" -ForegroundColor Green
        $testOutput | Select-Object -First 10 | ForEach-Object { Write-Host $_ }
        if ($testOutput.Count -gt 10) { Write-Host "... (output truncated)" }
    } else {
        Write-Host "`nDocker test failed:" -ForegroundColor Red
        $testOutput | ForEach-Object { Write-Host $_ }
    }
} catch {
    Write-Host "Error running test container: $_" -ForegroundColor Red
}

Write-Host "`nDocker troubleshooting complete!" -ForegroundColor Cyan
