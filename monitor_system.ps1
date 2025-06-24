# CaseStrainer System Monitor
# This script monitors the system to identify why health checks are failing

param(
    [int]$Interval = 10  # Check every 10 seconds
)

Write-Host "=== CaseStrainer System Monitor ===" -ForegroundColor Cyan
Write-Host "Monitoring every $Interval seconds..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Gray
Write-Host ""

$startTime = Get-Date
$checkCount = 0

while ($true) {
    $checkCount++
    $currentTime = Get-Date
    $elapsed = $currentTime - $startTime
    
    Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Check #$checkCount (Elapsed: $($elapsed.ToString('mm\:ss')))" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Gray
    
    # Check Docker containers
    Write-Host "Docker Containers:" -ForegroundColor Yellow
    try {
        $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host $containers -ForegroundColor White
        } else {
            Write-Host "Docker not accessible" -ForegroundColor Red
        }
    } catch {
        Write-Host "Docker error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Check ports
    Write-Host "`nPort Status:" -ForegroundColor Yellow
    $ports = @(443, 5000, 6379)
    foreach ($port in $ports) {
        $listening = netstat -an | findstr ":$port " | findstr "LISTENING"
        if ($listening) {
            Write-Host "Port $port`: LISTENING" -ForegroundColor Green
        } else {
            Write-Host "Port $port`: NOT LISTENING" -ForegroundColor Red
        }
    }
    
    # Check processes
    Write-Host "`nKey Processes:" -ForegroundColor Yellow
    $processes = @("nginx", "python", "waitress-serve")
    foreach ($proc in $processes) {
        $count = (Get-Process -Name $proc -ErrorAction SilentlyContinue).Count
        if ($count -gt 0) {
            Write-Host "$proc`: $count running" -ForegroundColor Green
        } else {
            Write-Host "$proc`: NOT RUNNING" -ForegroundColor Red
        }
    }
    
    # Test health endpoints
    Write-Host "`nHealth Checks:" -ForegroundColor Yellow
    
    # Test backend directly
    try {
        $backendResponse = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "Backend (5000): $($backendResponse.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "Backend (5000): FAILED - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test Nginx proxy
    try {
        # Use a PowerShell version-compatible approach for SSL certificate handling
        $nginxResponse = Invoke-WebRequest -Uri "https://localhost:443/casestrainer/api/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "Nginx (443): $($nginxResponse.StatusCode)" -ForegroundColor Green
    } catch {
        # If the above fails, try with a different approach
        try {
            $nginxResponse = Invoke-WebRequest -Uri "https://localhost:443/casestrainer/api/health" -TimeoutSec 3 -ErrorAction Stop -UseBasicParsing
            Write-Host "Nginx (443): $($nginxResponse.StatusCode)" -ForegroundColor Green
        } catch {
            Write-Host "Nginx (443): FAILED - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Test Redis
    try {
        $redisTest = python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping(); print('OK')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Redis (6379): OK" -ForegroundColor Green
        } else {
            Write-Host "Redis (6379): FAILED" -ForegroundColor Red
        }
    } catch {
        Write-Host "Redis (6379): ERROR - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Check recent log entries
    Write-Host "`nRecent Log Activity:" -ForegroundColor Yellow
    $recentLogs = Get-ChildItem logs -Name "crash_log_*" | Sort-Object -Descending | Select-Object -First 1
    if ($recentLogs) {
        $lastLog = Get-Content "logs/$recentLogs" -Tail 3
        foreach ($line in $lastLog) {
            if ($line -match "WARN|ERROR") {
                Write-Host $line -ForegroundColor Red
            } elseif ($line -match "INFO") {
                Write-Host $line -ForegroundColor Blue
            } else {
                Write-Host $line -ForegroundColor Gray
            }
        }
    }
    
    Write-Host "`n" + ("=" * 60) -ForegroundColor Gray
    Start-Sleep -Seconds $Interval
} 