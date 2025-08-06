# Docker Recovery Script for CaseStrainer
# Handles various Docker unresponsiveness scenarios

param(
    [switch]$Quick,
    [switch]$Full,
    [switch]$Emergency,
    [switch]$CheckOnly,
    [string]$ContainerName = ""
)

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-DockerResponsiveness {
    Write-ColorOutput "Testing Docker responsiveness..." "Cyan"
    
    $startTime = Get-Date
    try {
        $result = docker info 2>&1
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ Docker responds in $([math]::Round($duration, 2))s" "Green"
            return $true
        } else {
            Write-ColorOutput "✗ Docker is unresponsive" "Red"
            return $false
        }
    } catch {
        Write-ColorOutput "✗ Docker is not accessible" "Red"
        return $false
    }
}

function Get-ContainerHealth {
    param([string]$ContainerName)
    
    Write-ColorOutput "Checking container: $ContainerName" "Yellow"
    
    # Check if container exists
    $exists = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $ContainerName }
    if (-not $exists) {
        Write-ColorOutput "✗ Container $ContainerName not found" "Red"
        return $false
    }
    
    # Check container status
    $status = docker inspect --format "{{.State.Status}}" $ContainerName 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "✗ Cannot inspect container $ContainerName" "Red"
        return $false
    }
    
    Write-ColorOutput "Container status: $status" "Yellow"
    
    # Test container responsiveness
    $startTime = Get-Date
    $result = docker exec $ContainerName echo "test" 2>&1
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✓ Container responds in $([math]::Round($duration, 2))s" "Green"
        return $true
    } else {
        Write-ColorOutput "✗ Container is unresponsive" "Red"
        return $false
    }
}

function Invoke-QuickRecovery {
    Write-ColorOutput "=== Quick Recovery ===" "Cyan"
    
    # 1. Restart unresponsive containers
    Write-ColorOutput "1. Restarting containers..." "Yellow"
    $containers = docker ps --format "{{.Names}}" | Where-Object { $_ -like "*casestrainer*" }
    
    foreach ($container in $containers) {
        $healthy = Get-ContainerHealth $container
        if (-not $healthy) {
            Write-ColorOutput "Restarting $container..." "Yellow"
            docker restart $container 2>$null
            Start-Sleep -Seconds 5
        }
    }
    
    # 2. Clean up Docker system
    Write-ColorOutput "2. Cleaning up Docker system..." "Yellow"
    docker system prune -f 2>$null
    
    # 3. Restart application stack
    Write-ColorOutput "3. Restarting application stack..." "Yellow"
    docker-compose -f docker-compose.prod.yml restart 2>$null
    
    Write-ColorOutput "✓ Quick recovery completed" "Green"
}

function Invoke-FullRecovery {
    Write-ColorOutput "=== Full Recovery ===" "Cyan"
    
    # 1. Stop all containers
    Write-ColorOutput "1. Stopping all containers..." "Yellow"
    docker stop $(docker ps -q) 2>$null
    
    # 2. Clean up everything
    Write-ColorOutput "2. Cleaning up Docker resources..." "Yellow"
    docker container prune -f 2>$null
    docker image prune -f 2>$null
    docker volume prune -f 2>$null
    docker network prune -f 2>$null
    docker system prune -f 2>$null
    
    # 3. Restart Docker Desktop
    Write-ColorOutput "3. Restarting Docker Desktop..." "Yellow"
    Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 10
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    # 4. Wait for Docker to be ready
    Write-ColorOutput "4. Waiting for Docker to start..." "Yellow"
    $timeout = 120
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        try {
            docker info >$null 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✓ Docker is ready" "Green"
                break
            }
        } catch {
            # Continue waiting
        }
        Start-Sleep -Seconds 5
        $elapsed += 5
        Write-ColorOutput "Waiting... ($elapsed/$timeout seconds)" "Yellow"
    }
    
    if ($elapsed -ge $timeout) {
        Write-ColorOutput "✗ Docker failed to start within timeout" "Red"
        return $false
    }
    
    # 5. Rebuild and restart application
    Write-ColorOutput "5. Rebuilding and starting application..." "Yellow"
    docker-compose -f docker-compose.prod.yml up -d --build
    
    Write-ColorOutput "✓ Full recovery completed" "Green"
    return $true
}

function Invoke-EmergencyRecovery {
    Write-ColorOutput "=== Emergency Recovery ===" "Cyan"
    Write-ColorOutput "This will completely reset Docker and restart the system" "Red"
    
    $confirmation = Read-Host "Are you sure you want to proceed? (y/N)"
    if ($confirmation -ne "y" -and $confirmation -ne "Y") {
        Write-ColorOutput "Emergency recovery cancelled" "Yellow"
        return
    }
    
    # 1. Stop all Docker processes
    Write-ColorOutput "1. Stopping all Docker processes..." "Yellow"
    Get-Process | Where-Object { 
        $_.ProcessName -like "*docker*" -or 
        $_.ProcessName -like "*com.docker*" -or
        $_.ProcessName -like "*Docker Desktop*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # 2. Clean up Docker data (optional)
    Write-ColorOutput "2. Cleaning Docker data..." "Yellow"
    $dockerDataPath = "$env:USERPROFILE\AppData\Local\Docker"
    if (Test-Path $dockerDataPath) {
        Write-ColorOutput "Docker data found at: $dockerDataPath" "Yellow"
        $cleanData = Read-Host "Do you want to clean Docker data? This will reset all containers and images (y/N)"
        if ($cleanData -eq "y" -or $cleanData -eq "Y") {
            Remove-Item -Path "$dockerDataPath\wsl" -Recurse -Force -ErrorAction SilentlyContinue
            Write-ColorOutput "Docker data cleaned" "Green"
        }
    }
    
    # 3. Restart Docker Desktop
    Write-ColorOutput "3. Starting Docker Desktop..." "Yellow"
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    # 4. Wait for Docker to be ready
    Write-ColorOutput "4. Waiting for Docker to initialize..." "Yellow"
    $timeout = 180
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        try {
            docker info >$null 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✓ Docker is ready" "Green"
                break
            }
        } catch {
            # Continue waiting
        }
        Start-Sleep -Seconds 10
        $elapsed += 10
        Write-ColorOutput "Waiting... ($elapsed/$timeout seconds)" "Yellow"
    }
    
    if ($elapsed -ge $timeout) {
        Write-ColorOutput "✗ Docker failed to start within timeout" "Red"
        Write-ColorOutput "You may need to restart your computer" "Red"
        return $false
    }
    
    # 5. Rebuild everything from scratch
    Write-ColorOutput "5. Rebuilding application from scratch..." "Yellow"
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml up -d --build --force-recreate
    
    Write-ColorOutput "✓ Emergency recovery completed" "Green"
    return $true
}

function Get-SystemDiagnostics {
    Write-ColorOutput "=== System Diagnostics ===" "Cyan"
    
    # Docker responsiveness
    $dockerHealthy = Test-DockerResponsiveness
    
    # System resources
    $cpu = Get-Counter "\Processor(_Total)\% Processor Time" | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue
    $memory = Get-Counter "\Memory\Available MBytes" | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue
    $totalMemory = (Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1MB
    $memoryPercent = (($totalMemory - $memory) / $totalMemory) * 100
    
    Write-ColorOutput "System Resources:" "Yellow"
    Write-ColorOutput "  CPU Usage: $([math]::Round($cpu, 2))%" $(if ($cpu -gt 80) { "Red" } elseif ($cpu -gt 60) { "Yellow" } else { "Green" })
    Write-ColorOutput "  Memory Usage: $([math]::Round($memoryPercent, 2))%" $(if ($memoryPercent -gt 85) { "Red" } elseif ($memoryPercent -gt 70) { "Yellow" } else { "Green" })
    Write-ColorOutput "  Docker Status: $(if ($dockerHealthy) { "Healthy" } else { "Unresponsive" })" $(if ($dockerHealthy) { "Green" } else { "Red" })
    
    # Container health
    if ($dockerHealthy) {
        Write-ColorOutput "`nContainer Health:" "Yellow"
        $containers = docker ps --format "{{.Names}}" | Where-Object { $_ -like "*casestrainer*" }
        foreach ($container in $containers) {
            $healthy = Get-ContainerHealth $container
            Write-ColorOutput "  $container : $(if ($healthy) { "Healthy" } else { "Unhealthy" })" $(if ($healthy) { "Green" } else { "Red" })
        }
    }
}

# Main execution
if ($CheckOnly) {
    Get-SystemDiagnostics
}
elseif ($Quick) {
    if (Test-DockerResponsiveness) {
        Invoke-QuickRecovery
    } else {
        Write-ColorOutput "Docker is unresponsive, trying full recovery..." "Yellow"
        Invoke-FullRecovery
    }
}
elseif ($Full) {
    Invoke-FullRecovery
}
elseif ($Emergency) {
    Invoke-EmergencyRecovery
}
elseif ($ContainerName) {
    Get-ContainerHealth $ContainerName
}
else {
    Write-ColorOutput "Docker Recovery Script for CaseStrainer" "Cyan"
    Write-ColorOutput "Usage:" "White"
    Write-ColorOutput "  .\docker_recovery.ps1 -CheckOnly           # Run diagnostics only" "White"
    Write-ColorOutput "  .\docker_recovery.ps1 -Quick              # Quick recovery (restart containers)" "White"
    Write-ColorOutput "  .\docker_recovery.ps1 -Full               # Full recovery (restart Docker)" "White"
    Write-ColorOutput "  .\docker_recovery.ps1 -Emergency          # Emergency recovery (reset everything)" "White"
    Write-ColorOutput "  .\docker_recovery.ps1 -ContainerName 'name' # Check specific container" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Recommended approach:" "Yellow"
    Write-ColorOutput "1. Start with -CheckOnly to diagnose the issue" "White"
    Write-ColorOutput "2. Try -Quick for minor issues" "White"
    Write-ColorOutput "3. Use -Full for persistent problems" "White"
    Write-ColorOutput "4. Use -Emergency as a last resort" "White"
} 