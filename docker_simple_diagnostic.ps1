# Simple Docker Diagnostic Script for CaseStrainer

param(
    [switch]$Diagnose,
    [switch]$Recover,
    [switch]$Monitor
)

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-DockerHealth {
    Write-ColorOutput "=== Docker Health Check ===" "Cyan"
    
    try {
        $startTime = Get-Date
        $result = docker info 2>&1
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ Docker is running (response time: $([math]::Round($duration, 2))s)" "Green"
            return $true
        } else {
            Write-ColorOutput "✗ Docker is not responding" "Red"
            return $false
        }
    } catch {
        Write-ColorOutput "✗ Docker is not accessible" "Red"
        return $false
    }
}

function Get-ContainerStatus {
    Write-ColorOutput "`n=== Container Status ===" "Cyan"
    
    try {
        $containers = docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        Write-ColorOutput $containers "Yellow"
    } catch {
        Write-ColorOutput "✗ Cannot get container status" "Red"
    }
}

function Get-ResourceUsage {
    Write-ColorOutput "`n=== Resource Usage ===" "Cyan"
    
    try {
        $stats = docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
        Write-ColorOutput $stats "Yellow"
    } catch {
        Write-ColorOutput "✗ Cannot get resource usage" "Red"
    }
}

function Get-SystemResources {
    Write-ColorOutput "`n=== System Resources ===" "Cyan"
    
    try {
        # CPU Usage
        $cpu = Get-Counter "\Processor(_Total)\% Processor Time" | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue
        Write-ColorOutput "CPU Usage: $([math]::Round($cpu, 2))%" $(if ($cpu -gt 80) { "Red" } elseif ($cpu -gt 60) { "Yellow" } else { "Green" })
        
        # Memory Usage
        $memory = Get-Counter "\Memory\Available MBytes" | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue
        $totalMemory = (Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1MB
        $memoryPercent = (($totalMemory - $memory) / $totalMemory) * 100
        Write-ColorOutput "Memory Usage: $([math]::Round($memoryPercent, 2))%" $(if ($memoryPercent -gt 85) { "Red" } elseif ($memoryPercent -gt 70) { "Yellow" } else { "Green" })
        
        # Disk Usage
        $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'" | Select-Object Size, FreeSpace
        $diskPercent = (($disk.Size - $disk.FreeSpace) / $disk.Size) * 100
        Write-ColorOutput "Disk Usage: $([math]::Round($diskPercent, 2))%" $(if ($diskPercent -gt 90) { "Red" } elseif ($diskPercent -gt 80) { "Yellow" } else { "Green" })
    } catch {
        Write-ColorOutput "✗ Cannot get system resources" "Red"
    }
}

function Test-ContainerResponsiveness {
    Write-ColorOutput "`n=== Container Responsiveness Test ===" "Cyan"
    
    try {
        $containers = docker ps --format "{{.Names}}" | Where-Object { $_ -like "*casestrainer*" }
        
        foreach ($container in $containers) {
            Write-ColorOutput "Testing $container..." "Yellow"
            
            $startTime = Get-Date
            $result = docker exec $container echo "test" 2>&1
            $endTime = Get-Date
            $duration = ($endTime - $startTime).TotalSeconds
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✓ $container responds in $([math]::Round($duration, 2))s" "Green"
            } else {
                Write-ColorOutput "✗ $container is unresponsive" "Red"
            }
        }
    } catch {
        Write-ColorOutput "✗ Cannot test container responsiveness" "Red"
    }
}

function Invoke-QuickRecovery {
    Write-ColorOutput "`n=== Quick Recovery ===" "Cyan"
    
    Write-ColorOutput "1. Restarting containers..." "Yellow"
    try {
        docker-compose -f docker-compose.prod.yml restart
        Write-ColorOutput "✓ Containers restarted" "Green"
    } catch {
        Write-ColorOutput "✗ Failed to restart containers" "Red"
    }
    
    Write-ColorOutput "2. Cleaning up Docker system..." "Yellow"
    try {
        docker system prune -f
        Write-ColorOutput "✓ Docker system cleaned" "Green"
    } catch {
        Write-ColorOutput "✗ Failed to clean Docker system" "Red"
    }
}

function Invoke-FullRecovery {
    Write-ColorOutput "`n=== Full Recovery ===" "Cyan"
    
    Write-ColorOutput "1. Stopping all containers..." "Yellow"
    try {
        docker stop $(docker ps -q)
        Write-ColorOutput "✓ All containers stopped" "Green"
    } catch {
        Write-ColorOutput "✗ Failed to stop containers" "Red"
    }
    
    Write-ColorOutput "2. Cleaning up Docker resources..." "Yellow"
    try {
        docker container prune -f
        docker image prune -f
        docker volume prune -f
        docker network prune -f
        Write-ColorOutput "✓ Docker resources cleaned" "Green"
    } catch {
        Write-ColorOutput "✗ Failed to clean Docker resources" "Red"
    }
    
    Write-ColorOutput "3. Restarting Docker Desktop..." "Yellow"
    try {
        Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 10
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        Write-ColorOutput "✓ Docker Desktop restarted" "Green"
    } catch {
        Write-ColorOutput "✗ Failed to restart Docker Desktop" "Red"
    }
    
    Write-ColorOutput "4. Waiting for Docker to be ready..." "Yellow"
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
    
    Write-ColorOutput "5. Rebuilding and starting application..." "Yellow"
    try {
        docker-compose -f docker-compose.prod.yml up -d --build
        Write-ColorOutput "✓ Application rebuilt and started" "Green"
    } catch {
        Write-ColorOutput "✗ Failed to rebuild application" "Red"
    }
    
    return $true
}

# Main execution
if ($Diagnose) {
    Write-ColorOutput "Running Docker Diagnostics..." "Cyan"
    Test-DockerHealth
    Get-ContainerStatus
    Get-ResourceUsage
    Get-SystemResources
    Test-ContainerResponsiveness
}
elseif ($Recover) {
    Write-ColorOutput "Running Docker Recovery..." "Cyan"
    if (Test-DockerHealth) {
        Invoke-QuickRecovery
    } else {
        Write-ColorOutput "Docker is unresponsive, trying full recovery..." "Yellow"
        Invoke-FullRecovery
    }
}
elseif ($Monitor) {
    Write-ColorOutput "Starting continuous monitoring..." "Cyan"
    Write-ColorOutput "Press Ctrl+C to stop monitoring" "Yellow"
    
    while ($true) {
        Clear-Host
        Write-ColorOutput "=== Docker Monitor - $(Get-Date) ===" "Magenta"
        
        Test-DockerHealth
        Get-ContainerStatus
        Get-ResourceUsage
        Get-SystemResources
        Test-ContainerResponsiveness
        
        Write-ColorOutput "`nMonitoring will refresh in 30 seconds..." "Gray"
        Start-Sleep -Seconds 30
    }
}
else {
    Write-ColorOutput "Simple Docker Diagnostic Script for CaseStrainer" "Cyan"
    Write-ColorOutput "Usage:" "White"
    Write-ColorOutput "  .\docker_simple_diagnostic.ps1 -Diagnose    # Run diagnostics" "White"
    Write-ColorOutput "  .\docker_simple_diagnostic.ps1 -Recover     # Attempt recovery" "White"
    Write-ColorOutput "  .\docker_simple_diagnostic.ps1 -Monitor     # Start monitoring" "White"
} 