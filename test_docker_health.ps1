# Test Docker Health Check Functions
# This script tests the Docker health check functions independently

Write-Host "=== Testing Docker Health Check Functions ===" -ForegroundColor Cyan

# Test Docker Health Check Function
function Test-DockerHealth {
    [CmdletBinding()]
    [OutputType([hashtable])]
    param(
        [int]$MaxCPUPercent = 320,  # 80% of 4 cores = 320%
        [int]$MaxMemoryPercent = 85,
        [switch]$AutoRestart
    )
    
    $results = @{
        DockerCLI = $false
        ResourceUsage = $false
        ContainersHealthy = $false
        HighCPU = $false
        HighMemory = $false
        StuckContainers = @()
        Details = @()
    }
    
    # Check if Docker CLI is responsive
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $results.DockerCLI = $true
            $results.Details += "✅ Docker CLI is responsive"
        } else {
            throw "Docker CLI not responsive"
        }
    } catch {
        $results.Details += "❌ Docker CLI is unresponsive"
        if ($AutoRestart) {
            $results.Details += "🔄 Attempting Docker restart..."
            Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
            Stop-Process -Name "com.docker.backend" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 5
            Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
            $results.Details += "🔄 Docker Desktop restarted"
        }
        return $results
    }
    
    # Check container resource usage
    try {
        $stats = docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $results.ResourceUsage = $true
            $highUsage = $false
            
            foreach ($line in $stats) {
                if ($line -match "(\d+\.\d+)%") {
                    $cpuPercent = [double]$matches[1]
                    if ($cpuPercent -gt $MaxCPUPercent) {
                        $results.HighCPU = $true
                        $results.Details += "⚠️  High CPU usage detected: $cpuPercent% (${([math]::Round($cpuPercent/4,1))}% per core)"
                        $highUsage = $true
                    }
                }
            }
            
            if (-not $highUsage) {
                $results.Details += "✅ Resource usage is normal"
            }
        } else {
            $results.Details += "❌ Cannot check container stats"
        }
    } catch {
        $results.Details += "❌ Cannot check container stats: $_"
    }
    
    # Check for stuck containers
    try {
        $containers = docker ps -a --format "table {{.Names}}\t{{.Status}}" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $stuckContainers = $containers | Select-String -Pattern "Up.*\(health: starting\)" | ForEach-Object { $_.ToString().Trim() }
            
            if ($stuckContainers) {
                $results.StuckContainers = $stuckContainers
                $results.Details += "⚠️  Found containers stuck in 'starting' state:"
                foreach ($container in $stuckContainers) {
                    $results.Details += "   $container"
                }
            } else {
                $results.ContainersHealthy = $true
                $results.Details += "✅ All containers are healthy"
            }
        } else {
            $results.Details += "❌ Cannot check container status"
        }
    } catch {
        $results.Details += "❌ Cannot check container status: $_"
    }
    
    return $results
}

# Test the function
Write-Host "Running Docker health check..." -ForegroundColor Yellow
try {
    $healthResults = Test-DockerHealth
    Write-Host "`n=== Docker Health Check Results ===" -ForegroundColor Cyan
    foreach ($detail in $healthResults.Details) {
        Write-Host $detail
    }
    
    if ($healthResults.DockerCLI -and $healthResults.ResourceUsage -and $healthResults.ContainersHealthy) {
        Write-Host "`n✅ Docker is healthy!" -ForegroundColor Green
    } else {
        Write-Host "`n⚠️  Docker health issues detected" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error running Docker health check: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan 