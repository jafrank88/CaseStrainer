# Docker Diagnostic and Recovery Script
# This script helps diagnose and recover from Docker unresponsiveness issues

param(
    [switch]$Diagnose,
    [switch]$Recover,
    [switch]$Monitor,
    [int]$MonitorInterval = 30
)

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Get-DockerHealth {
    Write-ColorOutput "=== Docker Health Check ===" "Cyan"
    
    # Check if Docker is running
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ Docker is running" "Green"
        } else {
            Write-ColorOutput "✗ Docker is not responding" "Red"
            return $false
        }
    } catch {
        Write-ColorOutput "✗ Docker is not accessible" "Red"
        return $false
    }
    
    # Check container status
    Write-ColorOutput "`n=== Container Status ===" "Cyan"
    $containers = docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-ColorOutput $containers "Yellow"
    
    # Check resource usage
    Write-ColorOutput "`n=== Resource Usage ===" "Cyan"
    $stats = docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
    Write-ColorOutput $stats "Yellow"
    
    return $true
}

function Get-SystemResources {
    Write-ColorOutput "`n=== System Resources ===" "Cyan"
    
    # CPU Usage
    $cpu = Get-Counter "\Processor(_Total)\% Processor Time" | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue
    Write-ColorOutput "CPU Usage: $([math]::Round($cpu, 2))%" $(if ($cpu -gt 80) { "Red" } elseif ($cpu -gt 60) { "Yellow" } else { "Green" })
    
    # Memory Usage
    $memory = Get-Counter "\Memory\Available MBytes" | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue
    $totalMemory = (Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1MB
    $memoryPercent = (($totalMemory - $memory) / $totalMemory) * 100
    $memoryText = "Memory Usage: $([math]::Round($memoryPercent, 2))% ($([math]::Round($memory, 0)) MB available)"
    $memoryColor = if ($memoryPercent -gt 85) { "Red" } elseif ($memoryPercent -gt 70) { "Yellow" } else { "Green" }
    Write-ColorOutput $memoryText $memoryColor
    
    # Disk Usage
    $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'" | Select-Object Size, FreeSpace
    $diskPercent = (($disk.Size - $disk.FreeSpace) / $disk.Size) * 100
    $diskText = "Disk Usage: $([math]::Round($diskPercent, 2))%"
    $diskColor = if ($diskPercent -gt 90) { "Red" } elseif ($diskPercent -gt 80) { "Yellow" } else { "Green" }
    Write-ColorOutput $diskText $diskColor
}

function Get-DockerProcesses {
    Write-ColorOutput "`n=== Docker Processes ===" "Cyan"
    $dockerProcesses = Get-Process | Where-Object { 
        $_.ProcessName -like "*docker*" -or 
        $_.ProcessName -like "*com.docker*" -or
        $_.ProcessName -like "*Docker Desktop*"
    } | Select-Object ProcessName, Id, CPU, WorkingSet, VirtualMemorySize
    
    $dockerProcesses | Format-Table -AutoSize
}

function Test-ContainerResponsiveness {
    Write-ColorOutput "`n=== Container Responsiveness Test ===" "Cyan"
    
    $containers = docker ps --format "{{.Names}}" | Where-Object { $_ -like "*casestrainer*" }
    
    foreach ($container in $containers) {
        Write-ColorOutput "Testing $container..." "Yellow"
        
        # Test if container responds to basic commands
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
}

function Invoke-DockerRecovery {
    Write-ColorOutput "`n=== Docker Recovery Actions ===" "Cyan"
    
    Write-ColorOutput "1. Stopping all containers..." "Yellow"
    docker stop $(docker ps -q) 2>$null
    
    Write-ColorOutput "2. Removing stopped containers..." "Yellow"
    docker container prune -f 2>$null
    
    Write-ColorOutput "3. Cleaning up unused images..." "Yellow"
    docker image prune -f 2>$null
    
    Write-ColorOutput "4. Cleaning up unused volumes..." "Yellow"
    docker volume prune -f 2>$null
    
    Write-ColorOutput "5. Cleaning up unused networks..." "Yellow"
    docker network prune -f 2>$null
    
    Write-ColorOutput "6. Restarting Docker Desktop..." "Yellow"
    Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 5
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    Write-ColorOutput "7. Waiting for Docker to start..." "Yellow"
    $timeout = 60
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
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-ColorOutput "Waiting... ($elapsed/$timeout seconds)" "Yellow"
    }
    
    if ($elapsed -ge $timeout) {
        Write-ColorOutput "✗ Docker failed to start within timeout" "Red"
        return $false
    }
    
    Write-ColorOutput "8. Restarting application containers..." "Yellow"
    docker-compose -f docker-compose.prod.yml up -d
    
    return $true
}

function Start-Monitoring {
    Write-ColorOutput "Starting continuous monitoring..." "Cyan"
    Write-ColorOutput "Press Ctrl+C to stop monitoring" "Yellow"
    
    while ($true) {
        Clear-Host
        Write-ColorOutput "=== Docker Monitor - $(Get-Date) ===" "Magenta"
        
        Get-DockerHealth
        Get-SystemResources
        Get-DockerProcesses
        Test-ContainerResponsiveness
        
        Write-ColorOutput "`nMonitoring will refresh in $MonitorInterval seconds..." "Gray"
        Start-Sleep -Seconds $MonitorInterval
    }
}

# Main execution
if ($Diagnose) {
    Write-ColorOutput "Running Docker Diagnostics..." "Cyan"
    Get-DockerHealth
    Get-SystemResources
    Get-DockerProcesses
    Test-ContainerResponsiveness
}
elseif ($Recover) {
    Write-ColorOutput "Running Docker Recovery..." "Cyan"
    $success = Invoke-DockerRecovery
    if ($success) {
        Write-ColorOutput "✓ Recovery completed successfully" "Green"
    } else {
        Write-ColorOutput "✗ Recovery failed" "Red"
    }
}
elseif ($Monitor) {
    Start-Monitoring
}
else {
    Write-ColorOutput "Docker Diagnostic and Recovery Script" "Cyan"
    Write-ColorOutput "Usage:" "White"
    Write-ColorOutput "  .\docker_diagnostic.ps1 -Diagnose    # Run diagnostics" "White"
    Write-ColorOutput "  .\docker_diagnostic.ps1 -Recover     # Attempt recovery" "White"
    Write-ColorOutput "  .\docker_diagnostic.ps1 -Monitor     # Start monitoring" "White"
    Write-ColorOutput "  .\docker_diagnostic.ps1 -Monitor -MonitorInterval 60  # Monitor with custom interval" "White"
} 