# Integrate the monitoring fixes into cslaunch.ps1

Write-Host "=== Integrating Monitoring Fixes ===" -ForegroundColor Cyan

# Read the current script
$scriptPath = ".\cslaunch.ps1"
$content = Get-Content $scriptPath -Raw

# Define the improved Start-DockerEventMonitoring function
$improvedEventMonitoring = @'
function Start-DockerEventMonitoring {
    $eventLogPath = Join-Path $PSScriptRoot "logs\docker_events.log"
    
    $eventScriptBlock = {
        param($LogPath)
        
        function Write-DockerEventLogInternal {
            param([string]$Message)
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logEntry = "[$timestamp] $Message"
            Add-Content -Path $LogPath -Value $logEntry
        }
        
        try {
            Write-DockerEventLogInternal "=== DOCKER EVENT MONITORING STARTED ==="
            # Use simple format to avoid parsing errors
            docker events 2>&1 | ForEach-Object {
                if ($_ -and $_.ToString() -and $_.ToString().Trim()) {
                    Write-DockerEventLogInternal $_.ToString()
                }
            }
        } catch {
            Write-DockerEventLogInternal "ERROR: Docker event monitoring failed: $($_.Exception.Message)"
        }
    }
    
    $eventJob = Start-Job -Name "Docker-Event-Monitor" -ScriptBlock $eventScriptBlock -ArgumentList $eventLogPath
    
    Write-Host "[EVENTS] Docker event monitoring started (job ID: $($eventJob.Id))" -ForegroundColor Cyan
    Write-Host "  - Event log: $eventLogPath" -ForegroundColor Gray
    
    return $eventJob
}
'@

# Replace the existing Start-DockerEventMonitoring function
$pattern = 'function Start-DockerEventMonitoring \{[^}]*\}'
if ($content -match $pattern) {
    $content = $content -replace $pattern, $improvedEventMonitoring.Trim()
    Write-Host "[OK] Updated Start-DockerEventMonitoring function" -ForegroundColor Green
}

# Fix the monitoring script block to use simpler, more reliable approach
$improvedMonitorScript = @'
    # Create a simple, reliable monitoring script
    $monitorScriptBlock = {
        param(
            $ScriptRoot,
            $MonitorInterval,
            $DockerDaemonTimeout,
            $MaxDockerRestartsPerHour,
            $ExtendedDowntimeMinutes
        )

        $ErrorActionPreference = "Continue"
        $dockerDaemonLogPath = Join-Path $ScriptRoot "logs\docker_daemon_monitor.log"
        
        function Write-DaemonLog {
            param(
                [string]$Message,
                [string]$Level = "INFO"
            )
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logEntry = "[$timestamp] [$Level] $Message"
            Add-Content -Path $dockerDaemonLogPath -Value $logEntry
            
            switch ($Level) {
                "ERROR" { Write-Host $Message -ForegroundColor Red }
                "WARN"  { Write-Host $Message -ForegroundColor Yellow }
                "SUCCESS" { Write-Host $Message -ForegroundColor Green }
                default { Write-Host $Message }
            }
        }

        # Initialize monitoring variables
        $dockerDaemonFailures = 0
        $lastRestartTime = $null
        $restartCount = 0
        $extendedDowntimeStart = $null
        $isAdmin = Test-AdminPrivileges
        $dockerRestartHistory = [System.Collections.Generic.List[DateTime]]::new()

        Write-DaemonLog "=== ENHANCED DOCKER MONITOR STARTED ===" "SUCCESS"
        Write-DaemonLog "Monitor interval: ${MonitorInterval}s" "INFO"
        Write-DaemonLog "Docker timeout: ${DockerDaemonTimeout}s" "INFO"
        Write-DaemonLog "Max restarts/hour: $MaxDockerRestartsPerHour" "INFO"
        Write-DaemonLog "Extended downtime: ${ExtendedDowntimeMinutes}min" "INFO"
        Write-DaemonLog "Running as admin: $isAdmin" "INFO"

        # Main monitoring loop
        while ($true) {
            $dockerHealthy = $false
            
            # Check Docker daemon health
            try {
                # Use simple docker info check
                $null = docker info 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $dockerHealthy = $true
                    $dockerDaemonFailures = 0
                    Write-DaemonLog "Docker daemon is healthy" "SUCCESS"
                } else {
                    throw "Docker info command failed"
                }
            } catch {
                $dockerDaemonFailures++
                Write-DaemonLog "Docker daemon health check FAILED (attempt $dockerDaemonFailures)" "ERROR"
                Write-DaemonLog "  Error: $($_.Exception.Message)" "ERROR"
                
                # Attempt restart if needed
                if ($dockerDaemonFailures -ge 3 -and $isAdmin) {
                    Write-DaemonLog "Attempting to restart Docker..." "WARN"
                    # Simple restart attempt
                    try {
                        & "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe" -shutdown
                        Start-Sleep -Seconds 5
                        Start-Process -FilePath "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
                        Write-DaemonLog "Docker restart initiated" "INFO"
                        Start-Sleep -Seconds 30  # Wait for Docker to stabilize
                    } catch {
                        Write-DaemonLog "Docker restart failed: $($_.Exception.Message)" "ERROR"
                    }
                }
            }

            # Wait before next check
            $actualDelay = $MonitorInterval
            if ($dockerDaemonFailures -gt 0) {
                # Use exponential backoff
                $backoffDelay = [math]::Min(30 * [math]::Pow(2, [math]::Min($dockerDaemonFailures, 10)), 300)
                $actualDelay = $backoffDelay
                Write-DaemonLog "Using exponential backoff: waiting ${actualDelay}s (attempt $dockerDaemonFailures)" "INFO"
            }
            
            Start-Sleep -Seconds $actualDelay
        }
    }
'@

# Replace the monitor script block
$pattern = '\$monitorScriptBlock = \{[^}]*\}'
if ($content -match $pattern) {
    # This is a complex replacement, so we'll find the start and end positions
    $startPos = $content.IndexOf('$monitorScriptBlock = {')
    if ($startPos -gt 0) {
        $braceCount = 0
        $pos = $startPos
        $endPos = $startPos
        
        # Find the matching closing brace
        while ($pos -lt $content.Length) {
            if ($content[$pos] -eq '{') { $braceCount++ }
            elseif ($content[$pos] -eq '}') { 
                $braceCount--
                if ($braceCount -eq 0) {
                    $endPos = $pos + 1
                    break
                }
            }
            $pos++
        }
        
        if ($endPos -gt $startPos) {
            $content = $content.Substring(0, $startPos) + $improvedMonitorScript.Trim() + $content.Substring($endPos)
            Write-Host "[OK] Updated monitor script block" -ForegroundColor Green
        }
    }
}

# Write the updated script
Set-Content -Path $scriptPath -Value $content -Encoding UTF8

Write-Host "`n[SUCCESS] Monitoring fixes integrated!" -ForegroundColor Green
Write-Host "The improved monitoring will now run automatically when you run .\cslaunch" -ForegroundColor Gray
Write-Host "`nChanges:" -ForegroundColor Cyan
Write-Host "  - Fixed Docker event monitoring (simpler format)" -ForegroundColor Gray
Write-Host "  - Improved daemon health checks" -ForegroundColor Gray
Write-Host "  - Added exponential backoff" -ForegroundColor Gray
Write-Host "  - More reliable restart logic" -ForegroundColor Gray
