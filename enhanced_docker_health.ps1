# Enhanced Docker Health Check Script
# Provides detailed diagnostics for Docker issues

function Write-Header($message) {
    Write-Host "`n=== $message ===" -ForegroundColor Cyan
}

function Write-Success($message) {
    Write-Host "✅ $message" -ForegroundColor Green
}

function Write-Warning($message) {
    Write-Host "⚠️  $message" -ForegroundColor Yellow
}

function Write-Error($message) {
    Write-Host "❌ $message" -ForegroundColor Red
}

function Test-DockerInstallation {
    Write-Header "1. Docker Installation Check"
    
    $dockerPath = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerPath) {
        Write-Error "Docker CLI not found in PATH"
        return $false
    }
    
    Write-Success "Docker CLI found at $($dockerPath.Source)"
    return $true
}

function Test-DockerService {
    Write-Header "2. Docker Service Status"
    
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction Stop
        if ($service.Status -ne 'Running') {
            Write-Error "Docker service is not running (Status: $($service.Status))"
            return $false
        }
        Write-Success "Docker service is running"
        return $true
    } catch {
        Write-Error "Failed to check Docker service: $_"
        return $false
    }
}

function Test-DockerDaemon {
    Write-Header "3. Docker Daemon Communication"
    
    try {
        $dockerVersion = docker version --format '{{.Server.Version}}' 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw $dockerVersion
        }
        Write-Success "Docker daemon is responsive (Version: $dockerVersion)"
        return $true
    } catch {
        Write-Error "Failed to communicate with Docker daemon: $_"
        return $false
    }
}

function Test-ContainerStatus {
    Write-Header "4. Container Status"
    
    try {
        $containers = docker ps -a --format '{{.Names}}|{{.Status}}|{{.State}}|{{.Health}}' 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw $containers
        }
        
        if (-not $containers) {
            Write-Warning "No containers found"
            return $true
        }
        
        $allHealthy = $true
        foreach ($container in $containers) {
            $fields = $container -split '\|'
            $name = $fields[0]
            $status = $fields[1]
            $state = $fields[2]
            $health = $fields[3]
            
            if ($state -eq 'running' -and $health -match 'unhealthy') {
                Write-Error "Container '$name' is running but unhealthy (Status: $status)"
                $allHealthy = $false
            } elseif ($state -ne 'running') {
                Write-Warning "Container '$name' is not running (State: $state)"
                $allHealthy = $false
            } else {
                Write-Success "Container '$name' is healthy (Status: $status)"
            }
        }
        
        return $allHealthy
    } catch {
        Write-Error "Failed to check container status: $_"
        return $false
    }
}

function Test-ResourceUsage {
    Write-Header "5. Resource Usage"
    
    try {
        $stats = docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}' 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw $stats
        }
        
        if (-not $stats) {
            Write-Warning "No resource usage data available"
            return $true
        }
        
        Write-Host "Container Resource Usage:"
        Write-Host "----------------------"
        $stats | Select-Object -Skip 1 | ForEach-Object {
            $fields = $_ -split '\s+'
            $name = $fields[0]
            $cpu = $fields[1]
            $mem = $fields[2]
            $memPerc = $fields[3]
            $netIO = $fields[4]
            $blockIO = $fields[5]
            
            Write-Host "$name - CPU: $cpu, Memory: $mem ($memPerc), Network: $netIO, Disk: $blockIO"
        }
        
        return $true
    } catch {
        Write-Error "Failed to check resource usage: $_"
        return $false
    }
}

function Test-PortConflicts {
    Write-Header "6. Port Conflict Check"
    
    $ports = @(80, 443, 5000, 8000, 8080, 3306, 5432, 6379, 9000)
    $conflicts = @()
    
    foreach ($port in $ports) {
        $listener = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($listener) {
            $process = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
            $processName = if ($process) { $process.ProcessName } else { "Unknown" }
            $conflicts += "Port $port is in use by $processName (PID: $($listener.OwningProcess))"
        }
    }
    
    if ($conflicts.Count -gt 0) {
        Write-Warning "Potential port conflicts detected:"
        $conflicts | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
        return $false
    } else {
        Write-Success "No port conflicts detected on common Docker ports"
        return $true
    }
}

function Test-DockerNetworking {
    Write-Header "7. Docker Networking"
    
    try {
        $networks = docker network ls --format '{{.Name}}' 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw $networks
        }
        
        Write-Success "Available Docker networks: $($networks -join ', ')"
        
        # Test DNS resolution
        $dnsTest = docker run --rm busybox nslookup google.com 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker DNS resolution is working"
        } else {
            Write-Warning "Docker DNS resolution test failed"
            Write-Host "DNS Test Output: $dnsTest" -ForegroundColor Yellow
        }
        
        return $true
    } catch {
        Write-Error "Failed to check Docker networking: $_"
        return $false
    }
}

# Main execution
Write-Host "`n=== Enhanced Docker Health Check ===`n" -ForegroundColor Cyan

$results = @{
    DockerInstalled = Test-DockerInstallation
    DockerService = $false
    DockerDaemon = $false
    ContainersHealthy = $false
    ResourcesAvailable = $false
    NoPortConflicts = $false
    NetworkingWorking = $false
}

if ($results.DockerInstalled) {
    $results.DockerService = Test-DockerService
    
    if ($results.DockerService) {
        $results.DockerDaemon = Test-DockerDaemon
        
        if ($results.DockerDaemon) {
            $results.ContainersHealthy = Test-ContainerStatus
            $results.ResourcesAvailable = Test-ResourceUsage
            $results.NetworkingWorking = Test-DockerNetworking
        }
    }
}

$results.NoPortConflicts = Test-PortConflicts

# Summary
Write-Header "Health Check Summary"
$results.GetEnumerator() | Sort-Object Key | ForEach-Object {
    $status = if ($_.Value) { "✅" } else { "❌" }
    $name = $_.Key -replace '([a-z])([A-Z])', '$1 $2'  # Add space before capital letters
    Write-Host "$status $($name): $($_.Value)"
}

# Final recommendation
if ($results.Values -contains $false) {
    Write-Host "`nRecommendation: There are issues with your Docker setup that need to be addressed." -ForegroundColor Red
} else {
    Write-Host "`n✅ Your Docker environment appears to be healthy!" -ForegroundColor Green
}

Write-Host "`n=== End of Docker Health Check ===`n" -ForegroundColor Cyan
