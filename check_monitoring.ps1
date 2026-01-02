# Check Docker and monitoring status

Write-Host "=== Docker and Monitoring Status Check ===" -ForegroundColor Cyan

# Check Docker containers
Write-Host "`n1. Docker Containers:" -ForegroundColor Yellow
$containers = docker ps --filter name=casestrainer --format "{{.Names}}:{{.Status}}"
$healthyCount = 0
$totalCount = 0

foreach ($container in $containers) {
    $totalCount++
    if ($container -match "healthy") {
        $healthyCount++
        Write-Host "  ✓ $container" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $container" -ForegroundColor Red
    }
}

Write-Host "`n  Summary: $healthyCount/$totalCount containers healthy" -ForegroundColor $(if($healthyCount -eq $totalCount) {"Green"} else {"Yellow"})

# Check monitoring task
Write-Host "`n2. Persistent Monitoring Task:" -ForegroundColor Yellow
$task = Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -ErrorAction SilentlyContinue
if ($task) {
    Write-Host "  Status: $($task.State)" -ForegroundColor $(if($task.State -eq "Running") {"Green"} else {"Red"})
    Write-Host "  Last Run: $($task.LastRunTime)" -ForegroundColor Gray
    Write-Host "  Next Run: $($task.NextRunTime)" -ForegroundColor Gray
} else {
    Write-Host "  ✗ Monitoring task not found!" -ForegroundColor Red
}

# Check recent logs
Write-Host "`n3. Recent Monitoring Activity:" -ForegroundColor Yellow
if (Test-Path "logs\docker_daemon_monitor.log") {
    $logs = Get-Content "logs\docker_daemon_monitor.log" -Tail 20
    $recentLogs = $logs | Where-Object { $_ -match "ERROR|WARN|SUCCESS|healthy|failed" } | Select-Object -Last 5
    
    if ($recentLogs) {
        foreach ($log in $recentLogs) {
            if ($log -match "ERROR") {
                Write-Host "  $log" -ForegroundColor Red
            } elseif ($log -match "WARN") {
                Write-Host "  $log" -ForegroundColor Yellow
            } elseif ($log -match "SUCCESS") {
                Write-Host "  $log" -ForegroundColor Green
            } else {
                Write-Host "  $log" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  No recent activity found" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✗ Log file not found!" -ForegroundColor Red
}

# Check event monitoring
Write-Host "`n4. Docker Event Monitoring:" -ForegroundColor Yellow
if (Test-Path "logs\docker_events.log") {
    $eventLogs = Get-Content "logs\docker_events.log" -Tail 5
    if ($eventLogs -and $eventLogs.Count -gt 0) {
        Write-Host "  Event monitoring active" -ForegroundColor Green
        Write-Host "  Latest events:" -ForegroundColor Gray
        $eventLogs | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    } else {
        Write-Host "  Event log is empty" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ Event log not found!" -ForegroundColor Red
}

# Test Docker restart capability
Write-Host "`n5. Auto-Restore Capability Test:" -ForegroundColor Yellow
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    Write-Host "  ✓ Running as Administrator - can restart Docker" -ForegroundColor Green
    Write-Host "  Monitoring will attempt to restart Docker if it fails" -ForegroundColor Gray
} else {
    Write-Host "  ⚠ Not running as Administrator - limited restart capability" -ForegroundColor Yellow
    Write-Host "  Monitoring will detect failures but cannot restart Docker service" -ForegroundColor Gray
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
if ($healthyCount -eq $totalCount -and $task -and $task.State -eq "Running") {
    Write-Host "✓ All systems operational!" -ForegroundColor Green
    Write-Host "  Docker is healthy and monitoring is active" -ForegroundColor Gray
    Write-Host "  Auto-restart is configured and ready" -ForegroundColor Gray
} else {
    Write-Host "⚠ Some issues detected" -ForegroundColor Yellow
    if ($healthyCount -lt $totalCount) {
        Write-Host "  - Some containers are not healthy" -ForegroundColor Yellow
    }
    if (-not $task -or $task.State -ne "Running") {
        Write-Host "  - Monitoring is not running" -ForegroundColor Yellow
        Write-Host "  - Run: .\install_persistent_monitoring.ps1" -ForegroundColor Gray
    }
}
