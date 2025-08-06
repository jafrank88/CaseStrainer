# Docker Health Check Script
# Run this periodically to prevent Docker from becoming unresponsive

param(
            [int]$MaxCPUPercent = 320,  # 80% of 4 cores = 320%
    [int]$MaxMemoryPercent = 85,
    [switch]$AutoRestart
)

Write-Host "=== Docker Health Check ===" -ForegroundColor Cyan

# Check if Docker is responsive
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker CLI not responsive"
    }
    Write-Host "✅ Docker CLI is responsive" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker CLI is unresponsive - attempting restart..." -ForegroundColor Red
    if ($AutoRestart) {
        Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
        Stop-Process -Name "com.docker.backend" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        Write-Host "🔄 Docker Desktop restarted" -ForegroundColor Yellow
    }
    exit 1
}

# Check container resource usage
try {
    $stats = docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Cannot get container stats"
    }
    
    $highUsage = $false
    foreach ($line in $stats) {
        if ($line -match "(\d+\.\d+)%") {
            $cpuPercent = [double]$matches[1]
            if ($cpuPercent -gt $MaxCPUPercent) {
                Write-Host "⚠️  High CPU usage detected: $cpuPercent% (${([math]::Round($cpuPercent/4,1))}% per core)" -ForegroundColor Yellow
                $highUsage = $true
            }
        }
    }
    
    if (-not $highUsage) {
        Write-Host "✅ Resource usage is normal" -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ Cannot check container stats" -ForegroundColor Red
}

# Check for stuck containers
try {
    $containers = docker ps -a --format "table {{.Names}}\t{{.Status}}" 2>&1
    $stuckContainers = $containers | Select-String -Pattern "Up.*\(health: unhealthy\)|Up.*\(health: starting\)" | Select-String -Pattern "Up.*\(health: starting\)"
    
    if ($stuckContainers) {
        Write-Host "⚠️  Found containers stuck in 'starting' state:" -ForegroundColor Yellow
        $stuckContainers | ForEach-Object { Write-Host "   $_" -ForegroundColor Yellow }
    } else {
        Write-Host "✅ All containers are healthy" -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ Cannot check container status" -ForegroundColor Red
}

Write-Host "=== Health Check Complete ===" -ForegroundColor Cyan 