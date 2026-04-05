# docker-crash-diagnostic.ps1
# Comprehensive diagnostic tool for Docker crashes
# Run immediately after Docker crash to capture root cause analysis

param(
    [Parameter()]
    [switch]$FullAnalysis,

    [Parameter()]
    [switch]$ExportReport,

    [Parameter()]
    [string]$ReportPath = "logs\docker-crash-report-$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
)

function Write-Diagnostic {
    param([string]$Message, [string]$Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARN"  { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        "CRITICAL" { Write-Host $logEntry -ForegroundColor Magenta }
        default  { Write-Host $logEntry -ForegroundColor Cyan }
    }
    
    if ($ExportReport) {
        Add-Content -Path $ReportPath -Value $logEntry -ErrorAction SilentlyContinue
    }
}

function Get-CrashTimeline {
    Write-Diagnostic "=== CRASH TIMELINE ANALYSIS ===" "INFO"
    
    # Check recent Docker events
    try {
        Write-Diagnostic "Recent Docker events (last 30 minutes):" "INFO"
        $events = docker events --since 30m --format "{{.Time}} {{.Type}} {{.Action}} {{.Actor.Attributes.name}}" 2>&1
        if ($LASTEXITCODE -eq 0 -and $events) {
            $events | ForEach-Object { Write-Diagnostic "  $_" "INFO" }
        } else {
            Write-Diagnostic "  No recent Docker events or unable to retrieve" "WARN"
        }
    } catch {
        Write-Diagnostic "Failed to get Docker events: $($_.Exception.Message)" "ERROR"
    }
    
    # Check Windows Event Log for Docker-related errors
    try {
        Write-Diagnostic "Windows Application Log (Docker-related, last 1 hour):" "INFO"
        $dockerEvents = Get-WinEvent -LogName Application -ProviderName "*Docker*" -MaxEvents 10 -ErrorAction SilentlyContinue | 
            Where-Object { $_.TimeCreated -gt (Get-Date).AddHours(-1) }
        
        if ($dockerEvents) {
            foreach ($event in $dockerEvents) {
                $level = switch ($event.LevelDisplayName) {
                    "Error" { "ERROR" }
                    "Warning" { "WARN" }
                    "Critical" { "CRITICAL" }
                    default { "INFO" }
                }
                Write-Diagnostic "  [$($event.TimeCreated)] $($event.LevelDisplayName): $($event.Message)" $level
            }
        } else {
            Write-Diagnostic "  No recent Docker-related Windows events" "INFO"
        }
    } catch {
        Write-Diagnostic "Failed to read Windows Event Log: $($_.Exception.Message)" "ERROR"
    }
    
    # Check System Event Log
    try {
        Write-Diagnostic "Windows System Log (service-related, last 1 hour):" "INFO"
        $systemEvents = Get-WinEvent -LogName System -MaxEvents 10 -ErrorAction SilentlyContinue | 
            Where-Object { $_.TimeCreated -gt (Get-Date).AddHours(-1) -and ($_.Message -match "Docker|service") }
        
        if ($systemEvents) {
            foreach ($event in $systemEvents) {
                $level = switch ($event.LevelDisplayName) {
                    "Error" { "ERROR" }
                    "Warning" { "WARN" }
                    "Critical" { "CRITICAL" }
                    default { "INFO" }
                }
                Write-Diagnostic "  [$($event.TimeCreated)] $($event.LevelDisplayName): $($event.Message)" $level
            }
        } else {
            Write-Diagnostic "  No recent service-related system events" "INFO"
        }
    } catch {
        Write-Diagnostic "Failed to read System Event Log: $($_.Exception.Message)" "ERROR"
    }
}

function Get-SystemSnapshot {
    Write-Diagnostic "=== SYSTEM SNAPSHOT AT CRASH TIME ===" "INFO"
    
    # Memory usage
    try {
        $memInfo = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
        if ($memInfo) {
            $totalGB = [math]::Round($memInfo.TotalVisibleMemorySize / 1MB, 2)
            $freeGB = [math]::Round($memInfo.FreePhysicalMemory / 1MB, 2)
            $usedPercent = [math]::Round((($totalGB - $freeGB) / $totalGB) * 100, 1)
            
            Write-Diagnostic "Memory: $freeGB GB free of $totalGB GB ($usedPercent% used)" "INFO"
            
            if ($freeGB -lt 2) {
                Write-Diagnostic "⚠️ CRITICAL: Low memory condition detected" "CRITICAL"
            } elseif ($freeGB -lt 4) {
                Write-Diagnostic "⚠️ WARNING: Low memory warning" "WARN"
            }
        }
    } catch {
        Write-Diagnostic "Failed to get memory info: $($_.Exception.Message)" "ERROR"
    }
    
    # Disk space
    try {
        $drives = Get-CimInstance Win32_LogicalDisk -ErrorAction SilentlyContinue
        foreach ($drive in $drives) {
            if ($drive.DriveType -eq 3) { # Fixed disk
                $freeGB = [math]::Round($drive.FreeSpace / 1GB, 2)
                $totalGB = [math]::Round($drive.Size / 1GB, 2)
                $usedPercent = [math]::Round((($totalGB - $freeGB) / $totalGB) * 100, 1)
                
                Write-Diagnostic "Disk $($drive.DeviceID): $freeGB GB free of $totalGB GB ($usedPercent% used)" "INFO"
                
                if ($freeGB -lt 5) {
                    Write-Diagnostic "⚠️ CRITICAL: Low disk space on $($drive.DeviceID)" "CRITICAL"
                } elseif ($freeGB -lt 10) {
                    Write-Diagnostic "⚠️ WARNING: Low disk space on $($drive.DeviceID)" "WARN"
                }
            }
        }
    } catch {
        Write-Diagnostic "Failed to get disk info: $($_.Exception.Message)" "ERROR"
    }
    
    # CPU usage
    try {
        $cpu = Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue
        if ($cpu) {
            $cpuPercent = $cpu.LoadPercentage
            Write-Diagnostic "CPU: $cpuPercent% utilization" "INFO"
            
            if ($cpuPercent -gt 90) {
                Write-Diagnostic "⚠️ WARNING: High CPU utilization" "WARN"
            }
        }
    } catch {
        Write-Diagnostic "Failed to get CPU info: $($_.Exception.Message)" "ERROR"
    }
    
    # Process snapshot
    try {
        Write-Diagnostic "Top processes by memory usage:" "INFO"
        $processes = Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10
        foreach ($proc in $processes) {
            $memoryMB = [math]::Round($proc.WorkingSet64 / 1MB, 2)
            Write-Diagnostic "  $($proc.ProcessName): $memoryMB MB" "INFO"
        }
    } catch {
        Write-Diagnostic "Failed to get process info: $($_.Exception.Message)" "ERROR"
    }
}

function Get-DockerStateAnalysis {
    Write-Diagnostic "=== DOCKER STATE ANALYSIS ===" "INFO"
    
    # Docker Desktop processes
    try {
        $dockerProcs = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        if ($dockerProcs) {
            Write-Diagnostic "Docker Desktop processes found:" "INFO"
            foreach ($proc in $dockerProcs) {
                $memoryMB = [math]::Round($proc.WorkingSet64 / 1MB, 2)
                $cpuTime = [math]::Round($proc.CPU, 2)
                Write-Diagnostic "  PID $($proc.Id): $memoryMB MB, CPU: $cpuTime sec, Started: $($proc.StartTime)" "INFO"
            }
        } else {
            Write-Diagnostic "❌ Docker Desktop processes not found" "ERROR"
        }
    } catch {
        Write-Diagnostic "Failed to check Docker Desktop processes: $($_.Exception.Message)" "ERROR"
    }
    
    # Docker service
    try {
        $svc = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($svc) {
            Write-Diagnostic "Docker service: $($svc.Status) (StartType: $($svc.StartType))" "INFO"
            
            if ($svc.Status -ne "Running") {
                Write-Diagnostic "❌ Docker service is not running" "ERROR"
                
                # Try to get service exit code if available
                try {
                    $serviceDetails = Get-CimInstance Win32_Service -Filter "Name='com.docker.service'" -ErrorAction SilentlyContinue
                    if ($serviceDetails) {
                        Write-Diagnostic "  Service details: ExitCode=$($serviceDetails.ExitCode), State=$($serviceDetails.State)" "INFO"
                    }
                } catch {
                    Write-Diagnostic "  Could not get detailed service information" "WARN"
                }
            }
        } else {
            Write-Diagnostic "❌ Docker service not found" "ERROR"
        }
    } catch {
        Write-Diagnostic "Failed to check Docker service: $($_.Exception.Message)" "ERROR"
    }
    
    # Docker daemon connectivity
    try {
        Write-Diagnostic "Testing Docker daemon connectivity..." "INFO"
        $testResult = docker version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Diagnostic "✅ Docker daemon responding" "SUCCESS"
        } else {
            Write-Diagnostic "❌ Docker daemon not responding (exit code: $LASTEXITCODE)" "ERROR"
            Write-Diagnostic "Error output: $($testResult -join ' ')" "ERROR"
        }
    } catch {
        Write-Diagnostic "❌ Exception testing Docker daemon: $($_.Exception.Message)" "ERROR"
    }
    
    # WSL state
    try {
        Write-Diagnostic "Checking WSL state..." "INFO"
        $wslList = wsl --list --verbose 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Diagnostic "WSL distributions:" "INFO"
            $wslList | ForEach-Object { Write-Diagnostic "  $_" "INFO" }
        } else {
            Write-Diagnostic "Failed to get WSL list: $($wslList -join ' ')" "WARN"
        }
    } catch {
        Write-Diagnostic "Failed to check WSL state: $($_.Exception.Message)" "WARN"
    }
}

function Get-RootCauseAnalysis {
    Write-Diagnostic "=== ROOT CAUSE ANALYSIS ===" "INFO"
    
    $potentialCauses = @()
    
    # Check for common crash patterns
    try {
        # Memory pressure
        $memInfo = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
        if ($memInfo) {
            $freeGB = [math]::Round($memInfo.FreePhysicalMemory / 1MB, 2)
            if ($freeGB -lt 2) {
                $potentialCauses += "MEMORY_PRESSURE: System low on memory ($freeGB GB free)"
            }
        }
        
        # Disk space
        $systemDrive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'" -ErrorAction SilentlyContinue
        if ($systemDrive) {
            $freeGB = [math]::Round($systemDrive.FreeSpace / 1GB, 2)
            if ($freeGB -lt 5) {
                $potentialCauses += "DISK_SPACE: Low disk space on system drive ($freeGB GB free)"
            }
        }
        
        # Service issues
        $svc = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if (-not $svc -or $svc.Status -ne "Running") {
            $potentialCauses += "SERVICE_FAILURE: Docker Desktop service not running"
        }
        
        # Process issues
        $dockerProcs = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        if (-not $dockerProcs) {
            $potentialCauses += "PROCESS_FAILURE: Docker Desktop processes not found"
        }
        
        # Recent Windows updates
        try {
            $updates = Get-HotFix | Where-Object { $_.InstalledOn -gt (Get-Date).AddDays(-1) } -ErrorAction SilentlyContinue
            if ($updates) {
                $potentialCauses += "WINDOWS_UPDATE: Recent Windows updates may have affected Docker"
            }
        } catch {
            # Ignore if can't check updates
        }
        
    } catch {
        Write-Diagnostic "Error during root cause analysis: $($_.Exception.Message)" "ERROR"
    }
    
    # Report findings
    if ($potentialCauses.Count -gt 0) {
        Write-Diagnostic "🔍 POTENTIAL ROOT CAUSES IDENTIFIED:" "WARN"
        foreach ($cause in $potentialCauses) {
            Write-Diagnostic "  ❌ $cause" "WARN"
        }
    } else {
        Write-Diagnostic "✅ No obvious root causes detected - may be random crash" "SUCCESS"
    }
}

function Get-RecoveryRecommendations {
    Write-Diagnostic "=== RECOVERY RECOMMENDATIONS ===" "INFO"
    
    Write-Diagnostic "IMMEDIATE RECOVERY STEPS:" "INFO"
    Write-Diagnostic "1. Run PowerShell as Administrator" "INFO"
    Write-Diagnostic "2. Execute: Start-Service com.docker.service" "INFO"
    Write-Diagnostic "3. Start Docker Desktop from Start Menu" "INFO"
    Write-Diagnostic "4. Wait 2-3 minutes for full initialization" "INFO"
    Write-Diagnostic "5. Test with: docker version" "INFO"
    
    Write-Diagnostic "" "INFO"
    Write-Diagnostic "ENHANCED RECOVERY (if immediate fails):" "INFO"
    Write-Diagnostic "1. Stop all Docker processes: Get-Process 'Docker Desktop' | Stop-Process -Force" "INFO"
    Write-Diagnostic "2. Reset WSL: wsl --shutdown" "INFO"
    Write-Diagnostic "3. Clear Docker data: docker system prune -a -f" "INFO"
    Write-Diagnostic "4. Restart Docker Desktop" "INFO"
    
    Write-Diagnostic "" "INFO"
    Write-Diagnostic "PREVENTION MEASURES:" "INFO"
    Write-Diagnostic "• Use enhanced launcher: .\cslauncher_enhanced.ps1" "INFO"
    Write-Diagnostic "• Run health monitor: .\docker-health-monitor.ps1 -AutoRecover" "INFO"
    Write-Diagnostic "• Ensure adequate system resources (4GB+ RAM, 10GB+ disk)" "INFO"
    Write-Diagnostic "• Avoid system updates during critical operations" "INFO"
    Write-Diagnostic "• Consider Docker auto-restart service installation" "INFO"
}

# Main diagnostic execution
Write-Diagnostic "=== DOCKER CRASH DIAGNOSTIC STARTED ===" "CRITICAL"
Write-Diagnostic "Timestamp: $(Get-Date)" "INFO"
Write-Diagnostic "Analysis level: $(if ($FullAnalysis) { 'Full' } else { 'Standard' })" "INFO"

if ($ExportReport) {
    $reportDir = Split-Path $ReportPath -Parent
    if (-not (Test-Path $reportDir)) {
        New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
    }
    Write-Diagnostic "Report will be saved to: $ReportPath" "INFO"
}

Get-CrashTimeline
Get-SystemSnapshot
Get-DockerStateAnalysis
Get-RootCauseAnalysis
Get-RecoveryRecommendations

Write-Diagnostic "=== DIAGNOSTIC COMPLETE ===" "SUCCESS"

if ($ExportReport) {
    Write-Diagnostic "Full report saved to: $ReportPath" "SUCCESS"
}

Write-Diagnostic "" "INFO"
Write-Diagnostic "Next steps:" "INFO"
Write-Diagnostic "1. Review the potential root causes above" "INFO"
Write-Diagnostic "2. Follow the immediate recovery steps" "INFO"
Write-Diagnostic "3. Consider using enhanced launcher for future launches" "INFO"
Write-Diagnostic "4. Set up health monitoring to prevent future crashes" "INFO"
