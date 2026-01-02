# Patch script to fix Docker event logging and restart issues in cslaunch.ps1
# Run this script to apply the fixes

param(
    [switch]$Backup,
    [switch]$Force = $false
)

# Paths
$scriptPath = Join-Path $PSScriptRoot "cslaunch.ps1"
$backupPath = Join-Path $PSScriptRoot "cslaunch.ps1.backup"
$fixesPath = Join-Path $PSScriptRoot "cslaunch_docker_fixes.ps1"

Write-Host "=== CSLAUNCH.PS1 DOCKER FIXES PATCH ===" -ForegroundColor Cyan

# Check if script exists
if (-not (Test-Path $scriptPath)) {
    Write-Host "[ERROR] cslaunch.ps1 not found at: $scriptPath" -ForegroundColor Red
    exit 1
}

# Create backup if requested
if ($Backup) {
    if (Test-Path $backupPath) {
        Write-Host "[WARN] Backup already exists at: $backupPath" -ForegroundColor Yellow
        if (-not $Force) {
            $response = Read-Host "Overwrite backup? (y/N)"
            if ($response -ne 'y' -and $response -ne 'Y') {
                Write-Host "Patch cancelled." -ForegroundColor Yellow
                exit 0
            }
        }
    }
    
    Write-Host "[INFO] Creating backup: $backupPath" -ForegroundColor Gray
    Copy-Item -Path $scriptPath -Destination $backupPath -Force
} else {
    Write-Host "[INFO] Skipping backup (use -Backup to create one)" -ForegroundColor Gray
}

# Read the original script
$content = Get-Content -Path $scriptPath -Raw

# Fix 1: Add Docker event monitoring to Start-BackgroundMonitoring function
$eventMonitoringCode = @'
    
    # Start Docker event monitoring
    Write-Host "[INFO] Starting Docker event monitoring..." -ForegroundColor Cyan
    $eventJob = Start-DockerEventMonitoring
'@

# Find where to insert the event monitoring code (after starting background monitoring)
$pattern = '(Write-Host "\[INFO\] Starting background Docker daemon monitoring\.\.\." -ForegroundColor Cyan\s+)(\s+# Check if running as administrator)'
if ($content -match $pattern) {
    $content = $content -replace $pattern, "`$1$eventMonitoringCode`n`$2"
    Write-Host "[FIXED] Added Docker event monitoring" -ForegroundColor Green
} else {
    Write-Host "[WARN] Could not find insertion point for event monitoring" -ForegroundColor Yellow
}

# Fix 2: Replace Test-DockerDaemonHealth with detailed version
$detailedHealthFunction = @'
function Test-DockerDaemonHealth {
    param([int]$TimeoutSeconds = 15)
    
    # Use the detailed health check with diagnostics
    $health = Test-DockerDaemonHealthDetailed -TimeoutSeconds $TimeoutSeconds
    
    # Return compatible format for existing code
    return @{
        DockerInfo = $health.DockerInfo
        DockerVersion = $health.DockerVersion
        DockerPs = $health.DockerPs
        DockerService = $health.DockerService
        Diagnostics = $health.Diagnostics
    }
}
'@

# Replace the existing Test-DockerDaemonHealth function
$pattern = '(?s)function Test-DockerDaemonHealth \{[^}]*\n\}'
if ($content -match $pattern) {
    $content = $content -replace $pattern, $detailedHealthFunction
    Write-Host "[FIXED] Enhanced Docker health check with diagnostics" -ForegroundColor Green
} else {
    Write-Host "[WARN] Could not replace Test-DockerDaemonHealth function" -ForegroundColor Yellow
}

# Fix 3: Replace Restart-DockerEnhanced with fixed version
# First, find and remove the duplicate Restart-DockerEnhanced function
$pattern = '(?s)function Restart-DockerEnhanced \{[^}]*param\(\[string\]\$Reason = "Manual enhanced restart"\)[^}]*\n\}'
$content = $content -replace $pattern, ''

# Now replace the main Restart-DockerEnhanced function
$restartFunctionPattern = '(?s)function Restart-DockerEnhanced \{[^}]*\n\}'
if ($content -match $restartFunctionPattern) {
    # Load the fixed function from the fixes file
    $fixesContent = Get-Content -Path $fixesPath -Raw
    $fixedRestartPattern = '(?s)function Restart-DockerEnhancedFixed \{[^}]*return \$true[^}]*\n\}'
    if ($fixesContent -match $fixedRestartPattern) {
        $fixedFunction = $matches[0] -replace 'Restart-DockerEnhancedFixed', 'Restart-DockerEnhanced'
        $content = $content -replace $restartFunctionPattern, $fixedFunction
        Write-Host "[FIXED] Enhanced Docker restart with diagnostics and better error handling" -ForegroundColor Green
    }
}

# Fix 4: Add missing helper functions at the beginning of the script
$helperFunctions = @'

# Helper function to test admin privileges
function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Helper function to check if Docker is frozen (not just slow)
function Test-DockerFrozen {
    param([int]$TimeoutSeconds = 15)
    
    $frozen = $false
    $diagnostics = ""
    
    # Test 1: Check if docker info responds within timeout
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $job = Start-Job -ScriptBlock { docker info 2>&1 }
        
        if (Wait-Job $job -Timeout $TimeoutSeconds) {
            $output = Receive-Job $job
            $stopwatch.Stop()
            
            if ($LASTEXITCODE -ne 0) {
                $frozen = $true
                $diagnostics = "Docker info returned error: $($output -join '`n')"
            } elseif ($stopwatch.Elapsed.TotalSeconds -gt ($TimeoutSeconds * 0.8)) {
                $diagnostics = "Docker responding very slowly ($([math]::Round($stopwatch.Elapsed.TotalSeconds, 1))s)"
            }
        } else {
            $frozen = $true
            $diagnostics = "Docker info timed out after ${TimeoutSeconds}s"
            Stop-Job $job -ErrorAction SilentlyContinue
            Remove-Job $job -Force -ErrorAction SilentlyContinue
        }
    } catch {
        $frozen = $true
        $diagnostics = "Exception testing Docker: $($_.Exception.Message)"
    }
    
    return @{
        Frozen = $frozen
        Diagnostics = $diagnostics
    }
}

# Function to implement exponential backoff for restart attempts
function Get-BackoffDelay {
    param(
        [int]$AttemptNumber,
        [int]$BaseDelay = 30,
        [int]$MaxDelay = 300
    )
    
    $delay = [math]::Min($BaseDelay * [math]::Pow(2, $AttemptNumber - 1), $MaxDelay)
    return $delay
}

# Enhanced function to capture Docker events
function Start-DockerEventMonitoring {
    <#
    .SYNOPSIS
        Starts capturing Docker events in the background and logs them.
    #>
    
    $eventLogPath = Join-Path $PSScriptRoot "logs\docker_events.log"
    
    # Create event monitoring script block
    $eventScriptBlock = {
        param($LogPath, $ScriptRoot)
        
        # Import logging function
        function Write-EventLog {
            param([string]$Message)
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logEntry = "[$timestamp] $Message"
            Add-Content -Path $LogPath -Value $logEntry
        }
        
        try {
            Write-EventLog "=== DOCKER EVENT MONITORING STARTED ==="
            
            # Stream Docker events continuously
            docker events --format 'Type={{.Type}} Action={{.Action}} Object={{.Object}} Time={{.Time}} Status={{.Status}}' 2>&1 | ForEach-Object {
                if ($_ -and $_.Trim()) {
                    Write-EventLog $_
                }
            }
        } catch {
            Write-EventLog "ERROR: Docker event monitoring failed: $($_.Exception.Message)"
        }
    }
    
    # Start event monitoring in background job
    $eventJob = Start-Job -Name "Docker-Event-Monitor" -ScriptBlock $eventScriptBlock -ArgumentList $eventLogPath, $PSScriptRoot
    
    Write-Host "[EVENTS] Docker event monitoring started (job ID: $($eventJob.Id))" -ForegroundColor Cyan
    Write-Host "  - Event log: $eventLogPath" -ForegroundColor Gray
    Write-Host "  - Stop with: Stop-Job -Name Docker-Event-Monitor; Remove-Job -Name Docker-Event-Monitor" -ForegroundColor Gray
    
    return $eventJob
}

# Enhanced Docker health test with better diagnostics
function Test-DockerDaemonHealthDetailed {
    param([int]$TimeoutSeconds = 15)
    
    $healthChecks = @{
        DockerInfo = $false
        DockerVersion = $false
        DockerPs = $false
        DockerService = $false
        Diagnostics = ""
    }
    
    # Check 1: Docker info with detailed error capture
    try {
        $job = Start-Job -ScriptBlock { 
            $result = docker info 2>&1 
            if ($LASTEXITCODE -eq 0) { 
                return @{ success = $true; output = $result }
            } else { 
                return @{ success = $false; output = $result; error = $Error[0].Exception.Message }
            }
        }
        
        if (Wait-Job $job -Timeout $TimeoutSeconds) {
            $result = Receive-Job $job
            Remove-Job $job -Force
            
            if ($result.success) {
                $healthChecks.DockerInfo = $true
            } else {
                $healthChecks.Diagnostics += "Docker info failed: $($result.error)`n"
            }
        } else {
            Stop-Job $job -ErrorAction SilentlyContinue
            Remove-Job $job -Force -ErrorAction SilentlyContinue
            $healthChecks.Diagnostics += "Docker info check timed out after ${TimeoutSeconds}s`n"
        }
    } catch {
        $healthChecks.Diagnostics += "Docker info exception: $($_.Exception.Message)`n"
    }
    
    # Check 2: Docker service status
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($service) {
            $healthChecks.DockerService = ($service.Status -eq "Running")
            if (-not $healthChecks.DockerService) {
                $healthChecks.Diagnostics += "Docker service status: $($service.Status)`n"
            }
        } else {
            $healthChecks.Diagnostics += "Docker service not found`n"
        }
    } catch {
        $healthChecks.Diagnostics += "Failed to check Docker service: $($_.Exception.Message)`n"
    }
    
    # Check 3: Docker Desktop process
    try {
        $dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        if (-not $dockerProcess) {
            $healthChecks.Diagnostics += "Docker Desktop process not running`n"
        }
    } catch {
        $healthChecks.Diagnostics += "Failed to check Docker Desktop process: $($_.Exception.Message)`n"
    }
    
    # Check 4: Quick docker ps test
    if ($healthChecks.DockerInfo) {
        try {
            $job = Start-Job -ScriptBlock { docker ps 2>&1 }
            if (Wait-Job $job -Timeout 5) {
                $output = Receive-Job $job
                Remove-Job $job -Force
                if ($LASTEXITCODE -eq 0) {
                    $healthChecks.DockerPs = $true
                } else {
                    $healthChecks.Diagnostics += "Docker ps failed: $($output -join "`n")`n"
                }
            } else {
                Stop-Job $job -ErrorAction SilentlyContinue
                Remove-Job $job -Force -ErrorAction SilentlyContinue
                $healthChecks.Diagnostics += "Docker ps check timed out`n"
            }
        } catch {
            $healthChecks.Diagnostics += "Docker ps exception: $($_.Exception.Message)`n"
        }
    }
    
    return $healthChecks
}
'@

# Insert helper functions after the parameter block
$pattern = '(?s)(\}\s+# End of parameter block\s+)(# Setup crash logging)'
if ($content -match $pattern) {
    $content = $content -replace $pattern, "`$1$helperFunctions`n`n`$2"
    Write-Host "[FIXED] Added helper functions" -ForegroundColor Green
} else {
    Write-Host "[WARN] Could not insert helper functions" -ForegroundColor Yellow
}

# Fix 5: Update the monitoring loop to use exponential backoff
$backoffPattern = 'Start-Sleep -Seconds \$actualDelay'
$backoffReplacement = @'
# Use exponential backoff instead of fixed delay
$backoffDelay = Get-BackoffDelay -AttemptNumber ([math]::Min($dockerDaemonFailures, 10))
Write-DaemonLog "Using exponential backoff: waiting ${backoffDelay}s (attempt $dockerDaemonFailures)" "INFO"
Start-Sleep -Seconds $backoffDelay
'@

$content = $content -replace $backoffPattern, $backoffReplacement

# Fix 6: Add Docker event monitoring cleanup to the monitoring watchdog
$eventCleanupCode = @'
    
    # Also check and restart Docker event monitoring if needed
    $eventJob = Get-Job -Name "Docker-Event-Monitor" -ErrorAction SilentlyContinue
    if (-not $eventJob -or $eventJob.State -eq 'Failed' -or $eventJob.State -eq 'Stopped') {
        Write-WatchdogLog "Docker event monitoring job not running - restarting..." "WARN"
        if ($eventJob) {
            Remove-Job -Job $eventJob -Force -ErrorAction SilentlyContinue
        }
        # Restart event monitoring
        try {
            . (Join-Path $ScriptRoot "cslaunch.ps1" -ErrorAction Stop)
            Start-DockerEventMonitoring | Out-Null
            Write-WatchdogLog "Docker event monitoring restarted" "INFO"
        } catch {
            Write-WatchdogLog "Failed to restart Docker event monitoring: $($_.Exception.Message)" "ERROR"
        }
    }
'@

# Insert event monitoring cleanup after monitoring job check
$pattern = '(?s)(Write-WatchdogLog "Monitoring job recreation initiated via cslaunch\.ps1" "INFO"\s+} catch \{\s+Write-WatchdogLog "Failed to recreate monitoring job: \$\(\_\.\Exception\.Message\)" "ERROR"\s+\}\s+)(} elseif \(\$monitorJob\.State)'
if ($content -match $pattern) {
    $content = $content -replace $pattern, "`$1$eventCleanupCode`n`$2"
    Write-Host "[FIXED] Added Docker event monitoring to watchdog" -ForegroundColor Green
}

# Write the patched script
Write-Host "[INFO] Writing patched script..." -ForegroundColor Gray
Set-Content -Path $scriptPath -Value $content -Encoding UTF8

# Verify the patch
Write-Host "`n[INFO] Verifying patch..." -ForegroundColor Gray
$patchedContent = Get-Content -Path $scriptPath -Raw

$checks = @(
    @{ Name = "Docker event monitoring function"; Pattern = "function Start-DockerEventMonitoring" },
    @{ Name = "Detailed health check function"; Pattern = "function Test-DockerDaemonHealthDetailed" },
    @{ Name = "Frozen detection function"; Pattern = "function Test-DockerFrozen" },
    @{ Name = "Backoff delay function"; Pattern = "function Get-BackoffDelay" },
    @{ Name = "Event monitoring start"; Pattern = "Start-DockerEventMonitoring" },
    @{ Name = "Exponential backoff"; Pattern = "Using exponential backoff" }
)

$allPassed = $true
foreach ($check in $checks) {
    if ($patchedContent -match $check.Pattern) {
        Write-Host "  ✓ $($check.Name)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $($check.Name)" -ForegroundColor Red
        $allPassed = $false
    }
}

if ($allPassed) {
    Write-Host "`n[SUCCESS] All patches applied successfully!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "1. Review the changes in cslaunch.ps1" -ForegroundColor Gray
    Write-Host "2. Test the enhanced monitoring: .\cslaunch.ps1 -Monitor" -ForegroundColor Gray
    Write-Host "3. Check Docker events log: logs\docker_events.log" -ForegroundColor Gray
    Write-Host "4. Monitor improved restart logs: logs\docker_daemon_monitor.log" -ForegroundColor Gray
} else {
    Write-Host "`n[WARNING] Some patches may not have been applied correctly" -ForegroundColor Yellow
    Write-Host "Please review the script manually." -ForegroundColor Yellow
}

Write-Host "`n[INFO] Original script backed up to: $backupPath" -ForegroundColor Gray
