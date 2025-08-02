# Quick Docker Diagnostics
# Gathers essential Docker diagnostic information

$ErrorActionPreference = "Stop"
$diagnostics = @{}

# 1. Basic System Info
$os = Get-CimInstance Win32_OperatingSystem
$diagnostics.System = @{
    OS = "$($os.Caption) (Build $($os.BuildNumber))"
    Uptime = (Get-Date) - $os.LastBootUpTime
    MemoryGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
}

# 2. Docker Status
$dockerVersion = docker --version 2>&1
$diagnostics.Docker = @{
    Installed = $LASTEXITCODE -eq 0
    Version = if ($LASTEXITCODE -eq 0) { $dockerVersion } else { $null }
}

# 3. Docker Daemon Status
try {
    $info = docker info --format '{{json .}}' 2>&1
    if ($LASTEXITCODE -eq 0) {
        $diagnostics.Docker.Daemon = $info | ConvertFrom-Json
    } else {
        $diagnostics.Docker.Error = $info
    }
} catch {
    $diagnostics.Docker.Error = $_.Exception.Message
}

# 4. Docker Processes
$processes = Get-Process -Name "*docker*" -ErrorAction SilentlyContinue
$diagnostics.Processes = if ($processes) {
    $processes | Select-Object Id, ProcessName, CPU, WorkingSet, StartTime
} else { @() }

# 5. Docker Logs (last 5 minutes)
$logs = Get-EventLog -LogName Application -Source Docker -After (Get-Date).AddMinutes(-5) -ErrorAction SilentlyContinue
$diagnostics.Logs = if ($logs) { $logs | Select-Object -First 10 } else { @() }

# 6. Docker Disk Usage
try {
    $diskUsage = docker system df 2>&1
    $diagnostics.DiskUsage = if ($LASTEXITCODE -eq 0) { $diskUsage } else { $diskUsage -join "`n" }
} catch {
    $diagnostics.DiskUsage = $_.Exception.Message
}

# 7. Docker Containers
try {
    $containers = docker ps -a 2>&1
    $diagnostics.Containers = if ($LASTEXITCODE -eq 0) { $containers } else { $containers -join "`n" }
} catch {
    $diagnostics.Containers = $_.Exception.Message
}

# 8. Docker Images
try {
    $images = docker images 2>&1
    $diagnostics.Images = if ($LASTEXITCODE -eq 0) { $images } else { $images -join "`n" }
} catch {
    $diagnostics.Images = $_.Exception.Message
}

# 9. Docker Network
try {
    $network = docker network ls 2>&1
    $diagnostics.Network = if ($LASTEXITCODE -eq 0) { $network } else { $network -join "`n" }
} catch {
    $diagnostics.Network = $_.Exception.Message
}

# 10. Docker Desktop Logs
$desktopLog = "$env:USERPROFILE\AppData\Local\Docker\log\docker-desktop.log"
if (Test-Path $desktopLog) {
    $diagnostics.DesktopLog = Get-Content $desktopLog -Tail 20 -ErrorAction SilentlyContinue
}

# Display results
Write-Host "`n=== Docker Diagnostics ===`n" -ForegroundColor Cyan

# System Info
Write-Host "SYSTEM:" -ForegroundColor Green
Write-Host "  OS: $($diagnostics.System.OS)"
Write-Host "  Uptime: $($diagnostics.System.Uptime.Days)d $($diagnostics.System.Uptime.Hours)h $($diagnostics.System.Uptime.Minutes)m"
Write-Host "  Memory: $($diagnostics.System.MemoryGB) GB"

# Docker Status
Write-Host "`nDOCKER:" -ForegroundColor Green
if ($diagnostics.Docker.Installed) {
    Write-Host "  $($diagnostics.Docker.Version)"
    
    if ($diagnostics.Docker.Daemon) {
        $d = $diagnostics.Docker.Daemon
        Write-Host "  Status: Running (Server: $($d.ServerVersion))"
        Write-Host "  Containers: $($d.Containers) (Running: $($d.ContainersRunning), Paused: $($d.ContainersPaused), Stopped: $($d.ContainersStopped))"
        Write-Host "  Images: $($d.Images)"
    } elseif ($diagnostics.Docker.Error) {
        Write-Host "  Status: ERROR" -ForegroundColor Red
        Write-Host "  Error: $($diagnostics.Docker.Error)" -ForegroundColor Red
    }
} else {
    Write-Host "  Docker is not installed or not in PATH" -ForegroundColor Red
}

# Processes
if ($diagnostics.Processes.Count -gt 0) {
    Write-Host "`nDOCKER PROCESSES:" -ForegroundColor Green
    $diagnostics.Processes | Format-Table -AutoSize | Out-String -Stream | ForEach-Object { "  $_" }
}

# Disk Usage
if ($diagnostics.DiskUsage) {
    Write-Host "`nDISK USAGE:" -ForegroundColor Green
    $diagnostics.DiskUsage | ForEach-Object { "  $_" }
}

# Containers
if ($diagnostics.Containers) {
    Write-Host "`nCONTAINERS:" -ForegroundColor Green
    $diagnostics.Containers | ForEach-Object { "  $_" }
}

# Logs
if ($diagnostics.Logs.Count -gt 0) {
    Write-Host "`nRECENT LOGS:" -ForegroundColor Green
    $diagnostics.Logs | ForEach-Object { 
        $color = if ($_.EntryType -eq 'Error') { 'Red' } else { 'Gray' }
        Write-Host "  $($_.TimeGenerated) [$($_.EntryType)] $($_.Message -replace '\s+', ' ')" -ForegroundColor $color
    }
}

# Save full diagnostics to file
$outputFile = "docker-diagnostics-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
$diagnostics | ConvertTo-Json -Depth 5 | Out-File $outputFile -Force
Write-Host "`nFull diagnostics saved to: $outputFile" -ForegroundColor Cyan
