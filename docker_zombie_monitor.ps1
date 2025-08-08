# Docker Zombie Process Monitor for CaseStrainer
# Automatically detects and kills zombie Docker processes

param(
    [int]$CheckInterval = 60,  # Check every 60 seconds
    [int]$MaxProcesses = 10,   # Maximum allowed Docker processes
    [switch]$Verbose,
    [switch]$DryRun
)

# Configuration
$LogFile = "logs/docker_zombie_monitor.log"
$StateFile = "logs/docker_zombie_state.json"

# Ensure logs directory exists
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

function Write-Log {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logMessage -Force
    
    if ($Verbose) {
        $color = switch($Level) { 
            "ERROR" { "Red" } 
            "WARN" { "Yellow" } 
            "INFO" { "Green" } 
            "KILL" { "Magenta" } 
            default { "White" } 
        }
        Write-Host $logMessage -ForegroundColor $color
    }
}

function Get-DockerProcessCount {
    $dockerProcesses = Get-Process *docker* -ErrorAction SilentlyContinue
    return $dockerProcesses.Count
}

function Get-DockerProcessDetails {
    return Get-Process *docker* -ErrorAction SilentlyContinue | 
           Select-Object ProcessName, Id, CPU, WorkingSet, StartTime
}

function Kill-ZombieDockerProcesses {
    param($Threshold = 10)
    
    Write-Log "Checking for zombie Docker processes..."
    
    $dockerProcesses = Get-DockerProcessDetails
    $processCount = $dockerProcesses.Count
    
    Write-Log "Found $processCount Docker processes"
    
    if ($processCount -gt $Threshold) {
        Write-Log "Zombie process detected: $processCount > $Threshold processes" -Level "WARN"
        
        # Sort by CPU usage (zombies usually have low CPU)
        $zombieCandidates = $dockerProcesses | 
                          Where-Object { $_.CPU -lt 1.0 } |
                          Sort-Object CPU
        
        $killCount = 0
        foreach ($process in $zombieCandidates) {
            if ($process.ProcessName -notmatch "com\.docker\.service|Docker Desktop") {
                Write-Log "Killing zombie process: $($process.ProcessName) (PID: $($process.Id))" -Level "KILL"
                
                if (!$DryRun) {
                    try {
                        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                        $killCount++
                    }
                    catch {
                        Write-Log "Failed to kill process $($process.Id): $($_.Exception.Message)" -Level "ERROR"
                    }
                }
            }
        }
        
        Write-Log "Killed $killCount zombie Docker processes"
        return $killCount
    }
    
    return 0
}

function Test-DockerHealth {
    try {
        $dockerInfo = docker info 2>$null
        return $null -ne $dockerInfo
    }
    catch {
        return $false
    }
}

function Restart-DockerIfNeeded {
    if (!(Test-DockerHealth)) {
        Write-Log "Docker daemon appears unresponsive, attempting restart..." -Level "WARN"
        
        # Kill all Docker processes
        $processes = Get-Process *docker* -ErrorAction SilentlyContinue
        foreach ($proc in $processes) {
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
            catch {
                Write-Log "Could not stop process $($proc.Id): $($_.Exception.Message)" -Level "ERROR"
            }
        }
        
        # Restart Docker service
        try {
            Restart-Service com.docker.service -Force
            Write-Log "Docker service restarted successfully"
            return $true
        }
        catch {
            Write-Log "Failed to restart Docker service: $($_.Exception.Message)" -Level "ERROR"
            return $false
        }
    }
    return $false
}

function Start-ContinuousMonitoring {
    Write-Log "Starting Docker zombie process monitoring (interval: ${CheckInterval}s)"
    
    while ($true) {
        try {
            $killed = Kill-ZombieDockerProcesses -Threshold $MaxProcesses
            $restarted = Restart-DockerIfNeeded
            
            if ($killed -gt 0 -or $restarted) {
                Write-Log "Maintenance performed: Killed=$killed, Restarted=$restarted"
            }
            
            Start-Sleep -Seconds $CheckInterval
        }
        catch {
            Write-Log "Error in monitoring loop: $($_.Exception.Message)" -Level "ERROR"
            Start-Sleep -Seconds $CheckInterval
        }
    }
}

# Main execution
Write-Log "Docker Zombie Process Monitor started"

if ($DryRun) {
    Write-Log "DRY RUN MODE - No processes will be killed"
    $processes = Get-DockerProcessDetails
    Write-Log "Current Docker processes: $($processes.Count)"
    $processes | ForEach-Object { Write-Log "$($_.ProcessName) (PID: $($_.Id)) CPU: $($_.CPU) RAM: $($_.WorkingSet)" }
    exit
}

# Start monitoring
Start-ContinuousMonitoring
