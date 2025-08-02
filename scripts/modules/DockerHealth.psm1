# Docker Health Tests - Clean and Robust Version

function Test-DockerProcesses {
    <#
    .SYNOPSIS
    Tests if Docker Desktop processes are running
    #>
    try {
        $dockerProcesses = Get-Process -Name "*docker*" -ErrorAction SilentlyContinue
        
        if ($dockerProcesses.Count -eq 0) {
            Write-Host "[ERROR] No Docker processes found" -ForegroundColor Red
            return $false
        }
        
        Write-Host "[OK] Docker processes running: $($dockerProcesses.Count)" -ForegroundColor Green
        foreach ($proc in $dockerProcesses) {
            Write-Host "  - $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Gray
        }
        
        return $true
    } catch {
        Write-Host "[ERROR] Error checking Docker processes: $_" -ForegroundColor Red
        return $false
    }
}

function Test-DockerCLI {
    <#
    .SYNOPSIS
    Tests if Docker CLI is available and responsive
    #>
    try {
        $version = docker --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Docker CLI not found or not responding" -ForegroundColor Red
            return $false
        }
        
        Write-Host "✅ Docker CLI: $version" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Docker CLI error: $_" -ForegroundColor Red
        return $false
    }
}

function Test-DockerDaemon {
    <#
    .SYNOPSIS
    Tests if Docker daemon is accessible and healthy
    #>
    try {
        # Test daemon connectivity
        $info = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Docker daemon not accessible" -ForegroundColor Red
            Write-Host "Error: $info" -ForegroundColor Red
            return $false
        }
        
        # Parse key daemon info with error handling
        $infoLines = $info -split "`n"
        
        try {
            $containerLine = $infoLines | Where-Object { $_ -match "Containers:" } | Select-Object -First 1
            $containers = if ($containerLine) { $containerLine.Split(":")[1].Trim() } else { "Unknown" }
            
            $imageLine = $infoLines | Where-Object { $_ -match "Images:" } | Select-Object -First 1
            $images = if ($imageLine) { $imageLine.Split(":")[1].Trim() } else { "Unknown" }
            
            $versionLine = $infoLines | Where-Object { $_ -match "Server Version:" } | Select-Object -First 1
            $serverVersion = if ($versionLine) { $versionLine.Split(":")[1].Trim() } else { "Unknown" }
        } catch {
            Write-Host "⚠️  Could not parse daemon info details" -ForegroundColor Yellow
            $containers = "Unknown"
            $images = "Unknown" 
            $serverVersion = "Unknown"
        }
        
        Write-Host "✅ Docker daemon healthy" -ForegroundColor Green
        Write-Host "  - Server Version: $serverVersion" -ForegroundColor Gray
        Write-Host "  - Containers: $containers" -ForegroundColor Gray
        Write-Host "  - Images: $images" -ForegroundColor Gray
        
        return $true
    } catch {
        Write-Host "❌ Docker daemon error: $_" -ForegroundColor Red
        return $false
    }
}

function Test-DockerContainerRun {
    <#
    .SYNOPSIS
    Tests if Docker can actually run containers (ultimate health test)
    #>
    try {
        Write-Host "⏳ Testing container execution..." -ForegroundColor Yellow
        
        # Run a simple test container
        $result = docker run --rm hello-world 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Container execution failed" -ForegroundColor Red
            Write-Host "Error: $result" -ForegroundColor Red
            return $false
        }
        
        if ($result -like "*Hello from Docker*") {
            Write-Host "✅ Container execution successful" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Container ran but with unexpected output" -ForegroundColor Red
            return $false
        }
        
    } catch {
        Write-Host "❌ Container test error: $_" -ForegroundColor Red
        return $false
    }
}

function Test-DockerCompose {
    <#
    .SYNOPSIS
    Tests if Docker Compose is available and working
    #>
    try {
        $version = docker-compose --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Docker Compose not available" -ForegroundColor Red
            return $false
        }
        
        Write-Host "✅ Docker Compose: $version" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Docker Compose error: $_" -ForegroundColor Red
        return $false
    }
}

function Test-DockerResources {
    <#
    .SYNOPSIS
    Tests Docker resource allocation and disk space
    #>
    try {
        # Check Docker disk usage
        $diskUsage = docker system df 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️  Could not check Docker disk usage" -ForegroundColor Yellow
        } else {
            Write-Host "✅ Docker disk usage:" -ForegroundColor Green
            $diskUsage | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        }
        
        # Check available disk space on Docker root
        $dockerInfo = docker info --format "{{.DockerRootDir}}" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $rootDir = $dockerInfo.Trim()
            $drive = (Split-Path $rootDir -Qualifier).Replace(":", "")
            $freeSpace = Get-WmiObject -Class Win32_LogicalDisk | Where-Object { $_.DeviceID -eq "$drive" + ":" }
            
            if ($freeSpace) {
                $freeGB = [math]::Round($freeSpace.FreeSpace / 1GB, 2)
                if ($freeGB -lt 5) {
                    Write-Host "⚠️  Low disk space: ${freeGB}GB free" -ForegroundColor Yellow
                } else {
                    Write-Host "✅ Disk space: ${freeGB}GB free" -ForegroundColor Green
                }
            }
        }
        
        return $true
    } catch {
        Write-Host "⚠️  Resource check error: $_" -ForegroundColor Yellow
        return $true # Don't fail entire health check for this
    }
}

function Test-DockerNetwork {
    <#
    .SYNOPSIS
    Tests Docker networking functionality
    #>
    try {
        # List networks
        $networks = docker network ls 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Docker networking not working" -ForegroundColor Red
            return $false
        }
        
        # Check for default networks
        $networkList = $networks -split "`n" | Select-Object -Skip 1
        $bridgeNetwork = $networkList | Where-Object { $_ -match "bridge" }
        $hostNetwork = $networkList | Where-Object { $_ -match "host" }
        
        if ($bridgeNetwork -and $hostNetwork) {
            Write-Host "✅ Docker networks healthy" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠️  Some default networks missing" -ForegroundColor Yellow
            return $true # Don't fail for this
        }
        
    } catch {
        Write-Host "❌ Network test error: $_" -ForegroundColor Red
        return $false
    }
}

function Invoke-DockerHealthCheck {
    <#
    .SYNOPSIS
    Runs comprehensive Docker health checks
    .PARAMETER IncludeContainerTest
    Whether to run the container execution test (slower but thorough)
    #>
    param(
        [switch]$IncludeContainerTest,
        [switch]$Detailed
    )
    
    Write-Host "`n[INFO] Docker Health Check Starting..." -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan
    
    $results = @{}
    $overallHealthy = $true
    
    # Run all tests
    $tests = @(
        @{ Name = "Processes"; Function = "Test-DockerProcesses" },
        @{ Name = "CLI"; Function = "Test-DockerCLI" },
        @{ Name = "Daemon"; Function = "Test-DockerDaemon" },
        @{ Name = "Compose"; Function = "Test-DockerCompose" },
        @{ Name = "Network"; Function = "Test-DockerNetwork" },
        @{ Name = "Resources"; Function = "Test-DockerResources" }
    )
    
    if ($IncludeContainerTest) {
        $tests += @{ Name = "Container"; Function = "Test-DockerContainerRun" }
    }
    
    foreach ($test in $tests) {
        Write-Host "`n--- $($test.Name) Test ---" -ForegroundColor Cyan
        $result = & $test.Function
        $results[$test.Name] = $result
        
        if (-not $result) {
            $overallHealthy = $false
        }
    }
    
    # Summary
    Write-Host "`n" + ("=" * 50) -ForegroundColor Cyan
    Write-Host "🏥 Health Check Summary:" -ForegroundColor Cyan
    
    foreach ($result in $results.GetEnumerator()) {
        $status = if ($result.Value) { "✅ PASS" } else { "❌ FAIL" }
        $color = if ($result.Value) { "Green" } else { "Red" }
        Write-Host "  $($result.Key): $status" -ForegroundColor $color
    }
    
    if ($overallHealthy) {
        Write-Host "`n🎉 Docker is healthy and ready!" -ForegroundColor Green
    } else {
        Write-Host "`n⚠️  Docker has issues that need attention" -ForegroundColor Yellow
    }
    
    return @{
        Overall = $overallHealthy
        Results = $results
    }
}

# Quick health check function
function Test-DockerHealth {
    <#
    .SYNOPSIS
    Quick Docker health check (essential tests only)
    #>
    $cliOk = Test-DockerCLI
    $daemonOk = Test-DockerDaemon
    
    return ($cliOk -and $daemonOk)
}

# Export functions
Export-ModuleMember -Function Test-DockerProcesses, Test-DockerCLI, Test-DockerDaemon, Test-DockerContainerRun, Test-DockerCompose, Test-DockerResources, Test-DockerNetwork, Invoke-DockerHealthCheck, Test-DockerHealth
