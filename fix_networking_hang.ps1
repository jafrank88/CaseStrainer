# Fix for container networking test hang
# Adds timeout protection and better error handling

function Test-ContainerNetworkingWithTimeout {
    param(
        [int]$TimeoutSeconds = 30
    )
    
    Write-Host "Testing container networking with timeout protection..." -ForegroundColor Cyan
    
    try {
        # First, check if Docker daemon is responsive
        $dockerCheck = Start-Job -ScriptBlock { docker info } 
        $dockerResult = Wait-Job -Job $dockerCheck -Timeout $TimeoutSeconds
        
        if (!$dockerResult) {
            Stop-Job -Job $dockerCheck -Force
            Write-Host "Docker daemon is not responding within timeout" -ForegroundColor Red
            return $false
        }
        
        $dockerInfo = Receive-Job -Job $dockerCheck
        if (!$dockerInfo) {
            Write-Host "Docker daemon is not accessible" -ForegroundColor Red
            return $false
        }
        
        # Get running containers
        $containers = docker ps --format "{{.Names}}" 2>$null
        if (!$containers) {
            Write-Host "No running containers found" -ForegroundColor Yellow
            return $true
        }
        
        Write-Host "Found containers: $($containers -join ', ')" -ForegroundColor Green
        
        # Test each container with timeout
        $allHealthy = $true
        foreach ($container in $containers) {
            Write-Host "Testing container: $container" -ForegroundColor Gray
            
            $healthJob = Start-Job -ScriptBlock { 
                param($c)
                docker inspect --format='{{.State.Health.Status}}' $c 2>$null
            } -ArgumentList $container
            
            $healthResult = Wait-Job -Job $healthJob -Timeout 10
            
            if ($healthResult) {
                $health = Receive-Job -Job $healthJob
                if ($health -eq "unhealthy") {
                    Write-Host "  Container $container is unhealthy" -ForegroundColor Red
                    $allHealthy = $false
                } else {
                    Write-Host "  Container $container is healthy" -ForegroundColor Green
                }
            } else {
                Stop-Job -Job $healthJob -Force
                Write-Host "  Container $container health check timed out" -ForegroundColor Yellow
                $allHealthy = $false
            }
            
            Remove-Job -Job $healthJob -Force
        }
        
        return $allHealthy
        
    } catch {
        Write-Host "Error testing container networking: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Run the fixed networking test
$result = Test-ContainerNetworkingWithTimeout -TimeoutSeconds 30
Write-Host "Network test completed: $result" -ForegroundColor $(if ($result) { "Green" } else { "Red" })
