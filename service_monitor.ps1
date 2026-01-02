# CaseStrainer Monitoring Service Script
$daemonLog = "D:\dev\casestrainer\logs\docker_daemon_monitor.log"
$eventLog = "D:\dev\casestrainer\logs\docker_events.log"

# Ensure log directory exists
New-Item -Path (Split-Path $daemonLog) -ItemType Directory -Force | Out-Null
New-Item -Path (Split-Path $eventLog) -ItemType Directory -Force | Out-Null

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] [SERVICE] $Message"
    Add-Content -Path $daemonLog -Value $logEntry
}

function Write-EventLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    Add-Content -Path $eventLog -Value $logEntry
}

# Main service loop
Write-Log "=== CASESTRAINER MONITORING SERVICE STARTED ===" "SUCCESS"

# Start event monitoring in background
$eventScript = {
    $eventLog = "D:\dev\casestrainer\logs\docker_events.log"
    function Write-EventLog {
        param([string]$Message)
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "[$timestamp] $Message"
        Add-Content -Path $eventLog -Value $logEntry
    }
    try {
        Write-EventLog "=== DOCKER EVENT MONITORING STARTED (SERVICE) ==="
        docker events 2>&1 | ForEach-Object {
            if ($_ -and $_.ToString() -and $_.ToString().Trim()) {
                Write-EventLog $_.ToString()
            }
        }
    } catch {
        Write-EventLog "ERROR: $($_.Exception.Message)"
    }
}

Start-Job -Name "Docker-Events-Service" -ScriptBlock $eventScript | Out-Null

# Main monitoring loop
while ($true) {
    try {
        # Check Docker daemon
        $null = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Docker daemon is healthy" "SUCCESS"
        } else {
            Write-Log "Docker daemon health check FAILED" "ERROR"
            
            # Attempt restart if needed
            try {
                Write-Log "Attempting Docker restart..." "WARN"
                & "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe" -shutdown
                Start-Sleep -Seconds 10
                Start-Process -FilePath "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
                Write-Log "Docker restart initiated" "INFO"
                Start-Sleep -Seconds 30
            } catch {
                Write-Log "Docker restart failed: $($_.Exception.Message)" "ERROR"
            }
        }
        
        # Check CaseStrainer containers
        $containers = docker ps --filter name=casestrainer --format "{{.Names}}" 2>$null
        if ($containers) {
            $containerCount = ($containers | Measure-Object).Count
            Write-Log "Found $containerCount CaseStrainer containers running" "INFO"
        } else {
            Write-Log "No CaseStrainer containers found" "WARN"
        }
        
    } catch {
        Write-Log "Error in monitoring loop: $($_.Exception.Message)" "ERROR"
    }
    
    # Wait before next check (5 minutes)
    Start-Sleep -Seconds 300
}
