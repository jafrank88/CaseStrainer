# enhanced_docker_restart.ps1 - Advanced Docker restart procedures for recurring crashes
# Addresses specific issues causing Docker Desktop to freeze every 24-48 hours

param(
    [switch]$Force,                    # Force restart even if Docker appears healthy
    [switch]$DeepClean,                # Perform deep cleanup of Docker state
    [switch]$MemoryOptimize,           # Optimize memory settings before restart
    [int]$MaxWaitTime = 300,           # Maximum wait time for Docker to become ready (5 minutes)
    [string]$LogPath = "logs\enhanced_restart.log"
)

# Setup logging
$ErrorActionPreference = "Stop"
$script:LogPath = Join-Path $PSScriptRoot $LogPath
$script:StartTime = Get-Date

# Ensure logs directory exists
$logDir = Split-Path $script:LogPath -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-RestartLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $elapsed = "{0:mm\:ss}" - (Get-Date - $script:StartTime)
    $logEntry = "[$timestamp] [Elapsed: $elapsed] [$Level] $Message"
    
    Add-Content -Path $script:LogPath -Value $logEntry
    
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARN"  { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        "CRITICAL" { Write-Host $logEntry -ForegroundColor Magenta }
        default { Write-Host $logEntry }
    }
}

function Get-DockerProcessTree {
    <#
    .SYNOPSIS
    Get complete Docker process tree for proper cleanup
    #>
    
    $processes = @()
    
    try {
        # Get all Docker-related processes
        $dockerProcesses = Get-Process | Where-Object { 
            $_.ProcessName -match "docker|com\.docker" -or 
            ($_.CommandLine -and $_.CommandLine -match "docker")
        }
        
        foreach ($process in $dockerProcesses) {
            $processInfo = @{
                Id = $process.Id
                Name = $process.ProcessName
                StartTime = $process.StartTime
                WorkingSet = $process.WorkingSet64
                CommandLine = if ($process.CommandLine) { $process.CommandLine } else { "N/A" }
                ParentId = $null
                Children = @()
            }
            
            # Get parent process
            try {
                $parent = Get-CimInstance -ClassName Win32_Process -Filter "ProcessId = $($process.Id)" | Select-Object ParentProcessId
                if ($parent.ParentProcessId) {
                    $processInfo.ParentId = $parent.ParentProcessId
                }
            } catch {
                # Ignore errors getting parent process
            }
            
            $processes += $processInfo
        }
        
        # Build process tree
        foreach ($process in $processes) {
            $process.Children = $processes | Where-Object { $_.ParentId -eq $process.Id }
        }
        
        Write-RestartLog "Found $($processes.Count) Docker-related processes" "INFO"
        
    } catch {
        Write-RestartLog "Failed to get Docker process tree: $($_.Exception.Message)" "ERROR"
    }
    
    return $processes
}

function Stop-DockerProcesses {
    <#
    .SYNOPSIS
    Gracefully stop all Docker processes with proper cleanup
    #>
    
    Write-RestartLog "=== STOPPING DOCKER PROCESSES ===" "WARN"
    
    $processes = Get-DockerProcessTree
    
    if ($processes.Count -eq 0) {
        Write-RestartLog "No Docker processes found" "INFO"
        return $true
    }
    
    try {
        # Phase 1: Graceful shutdown (30 seconds)
        Write-RestartLog "Phase 1: Graceful shutdown..." "INFO"
        
        # Stop Docker Desktop first (main process)
        $dockerDesktop = $processes | Where-Object { $_.Name -eq "Docker Desktop" }
        foreach ($process in $dockerDesktop) {
            try {
                Write-RestartLog "Stopping Docker Desktop (PID: $($process.Id))" "INFO"
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            } catch {
                Write-RestartLog "Failed to stop Docker Desktop: $($_.Exception.Message)" "WARN"
            }
        }
        
        # Wait for graceful shutdown
        Start-Sleep -Seconds 15
        
        # Phase 2: Force remaining processes
        Write-RestartLog "Phase 2: Force shutdown of remaining processes..." "INFO"
        
        $remainingProcesses = Get-DockerProcessTree
        foreach ($process in $remainingProcesses) {
            try {
                Write-RestartLog "Force stopping $($process.Name) (PID: $($process.Id))" "INFO"
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            } catch {
                Write-RestartLog "Failed to stop $($process.Name): $($_.Exception.Message)" "WARN"
            }
        }
        
        # Phase 3: Verify cleanup
        Start-Sleep -Seconds 5
        $finalCheck = Get-DockerProcessTree
        
        if ($finalCheck.Count -eq 0) {
            Write-RestartLog "All Docker processes stopped successfully" "SUCCESS"
            return $true
        } else {
            Write-RestartLog "$($finalCheck.Count) processes still running after cleanup" "WARN"
            foreach ($process in $finalCheck) {
                Write-RestartLog "  Remaining: $($process.Name) (PID: $($process.Id))" "WARN"
            }
            return $false
        }
        
    } catch {
        Write-RestartLog "Error stopping Docker processes: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Clear-DockerState {
    <#
    .SYNOPSIS
    Clear Docker state files and caches to prevent corruption issues
    #>
    
    Write-RestartLog "=== CLEARING DOCKER STATE ===" "WARN"
    
    if (-not $DeepClean) {
        Write-RestartLog "Deep clean not specified - skipping state cleanup" "INFO"
        return $true
    }
    
    try {
        # Stop Docker service if running
        Write-RestartLog "Stopping Docker service..." "INFO"
        Stop-Service -Name "com.docker.service" -Force -ErrorAction SilentlyContinue
        
        # Clear common Docker state locations
        $dockerPaths = @(
            "$env:LOCALAPPDATA\Docker",
            "$env:APPDATA\Docker",
            "$env:USERPROFILE\.docker"
        )
        
        foreach ($path in $dockerPaths) {
            if (Test-Path $path) {
                Write-RestartLog "Clearing Docker state at $path" "INFO"
                
                # Remove specific subdirectories that commonly cause issues
                $cleanupDirs = @(
                    "buildx",
                    "contexts", 
                    "plugins",
                    "vms",
                    "desktop",
                    "cli-plugins"
                )
                
                foreach ($dir in $cleanupDirs) {
                    $fullPath = Join-Path $path $dir
                    if (Test-Path $fullPath) {
                        try {
                            Write-RestartLog "Removing $fullPath" "INFO"
                            Remove-Item -Path $fullPath -Recurse -Force -ErrorAction SilentlyContinue
                        } catch {
                            Write-RestartLog "Failed to remove $fullPath : $($_.Exception.Message)" "WARN"
                        }
                    }
                }
            }
        }
        
        # Clear WSL Docker data (if using WSL2 backend)
        try {
            Write-RestartLog "Clearing WSL Docker data..." "INFO"
            $wslOutput = wsl --list --verbose 2>$null
            if ($wslOutput -match "docker-desktop") {
                Write-RestartLog "Shutting down WSL Docker instances..." "INFO"
                wsl --shutdown docker-desktop 2>$null
                wsl --shutdown docker-desktop-data 2>$null
            }
        } catch {
            Write-RestartLog "WSL cleanup failed: $($_.Exception.Message)" "WARN"
        }
        
        Write-RestartLog "Docker state cleanup completed" "SUCCESS"
        return $true
        
    } catch {
        Write-RestartLog "Docker state cleanup failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Optimize-DockerMemory {
    <#
    .SYNOPSIS
    Optimize system memory before starting Docker
    #>
    
    Write-RestartLog "=== OPTIMIZING SYSTEM MEMORY ===" "INFO"
    
    if (-not $MemoryOptimize) {
        Write-RestartLog "Memory optimization not specified - skipping" "INFO"
        return $true
    }
    
    try {
        # Get current memory usage
        $os = Get-CimInstance -ClassName Win32_OperatingSystem
        $totalMemory = $os.TotalVisibleMemorySize / 1MB
        $freeMemory = $os.FreePhysicalMemory / 1MB
        $usedMemory = $totalMemory - $freeMemory
        $memoryPercent = ($usedMemory / $totalMemory) * 100
        
        Write-RestartLog "Memory usage: $([math]::Round($usedMemory, 1))MB / $([math]::Round($totalMemory, 1))MB ($([math]::Round($memoryPercent, 1))%)" "INFO"
        
        # If memory usage is high, try to free some
        if ($memoryPercent -gt 80) {
            Write-RestartLog "High memory usage detected - attempting cleanup..." "WARN"
            
            # Clear system caches
            Write-RestartLog "Clearing system caches..." "INFO"
            [System.GC]::Collect()
            [System.GC]::WaitForPendingFinalizers()
            [System.GC]::Collect()
            
            # Suggest memory-intensive applications to close (optional)
            $memoryHogs = Get-Process | Where-Object { $_.WorkingSet64 -gt 500MB } | Sort-Object -Property WorkingSet64 -Descending | Select-Object -First 5
            
            if ($memoryHogs.Count -gt 0) {
                Write-RestartLog "Top memory-consuming processes:" "INFO"
                foreach ($process in $memoryHogs) {
                    $memoryMB = [math]::Round($process.WorkingSet64 / 1MB, 1)
                    Write-RestartLog "  $($process.ProcessName): ${memoryMB}MB (PID: $($process.Id))" "INFO"
                }
            }
            
            # Wait a moment for memory to stabilize
            Start-Sleep -Seconds 10
            
            # Check memory after cleanup
            $osAfter = Get-CimInstance -ClassName Win32_OperatingSystem
            $freeMemoryAfter = $osAfter.FreePhysicalMemory / 1MB
            $memoryPercentAfter = (($totalMemory - $freeMemoryAfter) / $totalMemory) * 100
            
            Write-RestartLog "Memory after cleanup: $([math]::Round($freeMemoryAfter, 1))MB free ($([math]::Round($memoryPercentAfter, 1))% used)" "INFO"
            
            if ($memoryPercentAfter -lt $memoryPercent) {
                Write-RestartLog "Memory optimization freed $([math]::Round($freeMemoryAfter - $freeMemory, 1))MB" "SUCCESS"
            }
        } else {
            Write-RestartLog "Memory usage is acceptable - no optimization needed" "INFO"
        }
        
        return $true
        
    } catch {
        Write-RestartLog "Memory optimization failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Start-DockerEnhanced {
    <#
    .SYNOPSIS
    Start Docker with enhanced monitoring and verification
    #>
    
    Write-RestartLog "=== STARTING DOCKER ===" "WARN"
    
    try {
        # Find Docker Desktop executable
        $dockerDesktop = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
        if (-not (Test-Path $dockerDesktop)) {
            $dockerDesktop = "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
        }
        
        if (-not (Test-Path $dockerDesktop)) {
            Write-RestartLog "Docker Desktop executable not found" "CRITICAL"
            return $false
        }
        
        Write-RestartLog "Starting Docker Desktop from: $dockerDesktop" "INFO"
        
        # Start Docker Desktop minimized
        Start-Process -FilePath $dockerDesktop -WindowStyle Minimized
        
        Write-RestartLog "Docker Desktop started, waiting for readiness..." "INFO"
        
        # Enhanced readiness check with multiple methods
        $ready = $false
        $attempts = 0
        $maxAttempts = [math]::Floor($MaxWaitTime / 10)
        
        while (-not $ready -and $attempts -lt $maxAttempts) {
            $attempts++
            $elapsed = $attempts * 10
            
            try {
                # Method 1: Docker info command
                $infoJob = Start-Job -ScriptBlock { docker info 2>&1 }
                if (Wait-Job $infoJob -Timeout 15) {
                    $infoOutput = Receive-Job $infoJob
                    Remove-Job $infoJob -Force
                    if ($LASTEXITCODE -eq 0) {
                        $ready = $true
                        Write-RestartLog "Docker info command successful" "SUCCESS"
                    }
                } else {
                    Stop-Job $infoJob -ErrorAction SilentlyContinue
                    Remove-Job $infoJob -Force -ErrorAction SilentlyContinue
                }
                
                # Method 2: Check if Docker processes are running
                if (-not $ready) {
                    $dockerProcesses = Get-Process "*Docker*" -ErrorAction SilentlyContinue
                    if ($dockerProcesses.Count -gt 0) {
                        Write-RestartLog "Docker processes running ($($dockerProcesses.Count) processes)" "INFO"
                    }
                }
                
                # Method 3: Check container accessibility
                if ($ready) {
                    try {
                        $containers = docker ps --format "{{.Names}}" 2>$null
                        if ($LASTEXITCODE -eq 0) {
                            $containerCount = ($containers -split "`n" | Where-Object { $_.Trim() }).Count
                            Write-RestartLog "Docker fully ready - $containerCount containers accessible" "SUCCESS"
                        }
                    } catch {
                        Write-RestartLog "Docker ready but containers not yet accessible" "WARN"
                    }
                }
                
            } catch {
                Write-RestartLog "Readiness check attempt $attempts failed: $($_.Exception.Message)" "WARN"
            }
            
            if (-not $ready -and $attempts -lt $maxAttempts) {
                Write-RestartLog "Still waiting... (${elapsed}s elapsed, attempt $attempts of $maxAttempts)" "INFO"
                Start-Sleep -Seconds 10
            }
        }
        
        if ($ready) {
            $totalTime = $attempts * 10
            Write-RestartLog "=== DOCKER STARTUP SUCCESSFUL ===" "SUCCESS"
            Write-RestartLog "Docker ready after ${totalTime} seconds" "SUCCESS"
            
            # Final verification
            try {
                $version = docker --version 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-RestartLog "Docker version: $version" "INFO"
                }
                
                $info = docker info --format "{{.ServerVersion}}" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-RestartLog "Docker engine version: $info" "INFO"
                }
            } catch {
                Write-RestartLog "Final verification failed: $($_.Exception.Message)" "WARN"
            }
            
            return $true
        } else {
            Write-RestartLog "=== DOCKER STARTUP FAILED ===" "CRITICAL"
            Write-RestartLog "Docker did not become ready within $MaxWaitTime seconds" "CRITICAL"
            Write-RestartLog "Attempts made: $attempts" "ERROR"
            return $false
        }
        
    } catch {
        Write-RestartLog "Docker startup failed: $($_.Exception.Message)" "CRITICAL"
        return $false
    }
}

function Invoke-EnhancedDockerRestart {
    <#
    .SYNOPSIS
    Main enhanced Docker restart procedure
    #>
    
    Write-RestartLog "=== ENHANCED DOCKER RESTART PROCEDURE STARTED ===" "CRITICAL"
    Write-RestartLog "Parameters: Force=$Force, DeepClean=$DeepClean, MemoryOptimize=$MemoryOptimize" "INFO"
    Write-RestartLog "Max wait time: ${MaxWaitTime}s" "INFO"
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $success = $false
    
    try {
        # Step 1: Health check (unless forced)
        if (-not $Force) {
            Write-RestartLog "Checking current Docker health..." "INFO"
            try {
                $healthCheck = Start-Job -ScriptBlock { docker info 2>&1 }
                if (Wait-Job $healthCheck -Timeout 10) {
                    $output = Receive-Job $healthCheck
                    Remove-Job $healthCheck -Force
                    if ($LASTEXITCODE -eq 0) {
                        Write-RestartLog "Docker appears to be healthy - use -Force to restart anyway" "WARN"
                        return $true
                    }
                } else {
                    Stop-Job $healthCheck -ErrorAction SilentlyContinue
                    Remove-Job $healthCheck -Force -ErrorAction SilentlyContinue
                }
            } catch {
                Write-RestartLog "Health check failed - proceeding with restart" "WARN"
            }
        }
        
        # Step 2: Memory optimization
        if (-not (Optimize-DockerMemory)) {
            Write-RestartLog "Memory optimization failed - continuing anyway" "WARN"
        }
        
        # Step 3: Stop Docker processes
        if (-not (Stop-DockerProcesses)) {
            Write-RestartLog "Failed to stop all Docker processes - attempting restart anyway" "WARN"
        }
        
        # Step 4: Clear Docker state (if requested)
        if (-not (Clear-DockerState)) {
            Write-RestartLog "Docker state cleanup failed - continuing anyway" "WARN"
        }
        
        # Step 5: Start Docker
        $success = Start-DockerEnhanced
        
        if ($success) {
            # Wait for full stabilization
            Write-RestartLog "Waiting for Docker to fully stabilize..." "INFO"
            Start-Sleep -Seconds 30
            
            # Final health verification
            try {
                $finalCheck = docker ps --format "table {{.Names}}\t{{.Status}}" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $containers = $finalCheck -split "`n" | Where-Object { $_.Trim() } | Select-Object -Skip 1
                    Write-RestartLog "Final verification: $($containers.Count) containers running" "SUCCESS"
                }
            } catch {
                Write-RestartLog "Final verification failed: $($_.Exception.Message)" "WARN"
            }
        }
        
    } catch {
        Write-RestartLog "Enhanced restart procedure failed: $($_.Exception.Message)" "CRITICAL"
        $success = $false
    }
    
    $stopwatch.Stop()
    $totalTime = $stopwatch.Elapsed.TotalSeconds
    
    if ($success) {
        Write-RestartLog "=== ENHANCED DOCKER RESTART SUCCESSFUL ===" "SUCCESS"
        Write-RestartLog "Total time: $([math]::Round($totalTime, 1)) seconds" "SUCCESS"
    } else {
        Write-RestartLog "=== ENHANCED DOCKER RESTART FAILED ===" "CRITICAL"
        Write-RestartLog "Total time: $([math]::Round($totalTime, 1)) seconds" "ERROR"
        Write-RestartLog "Manual intervention may be required" "CRITICAL"
    }
    
    return $success
}

# Main execution
Write-RestartLog "Enhanced Docker Restart Tool v1.0 starting..." "INFO"

$result = Invoke-EnhancedDockerRestart

if ($result) {
    Write-RestartLog "Enhanced restart completed successfully" "SUCCESS"
    exit 0
} else {
    Write-RestartLog "Enhanced restart failed" "ERROR"
    exit 1
}
