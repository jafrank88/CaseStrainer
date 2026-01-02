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

# Check if fixes file exists
if (-not (Test-Path $fixesPath)) {
    Write-Host "[ERROR] cslaunch_docker_fixes.ps1 not found at: $fixesPath" -ForegroundColor Red
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

# Load the fixes content
$fixesContent = Get-Content -Path $fixesPath -Raw

# Apply Fix 1: Add helper functions at the beginning
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
'@

# Insert helper functions after the parameter block
$pattern = '(?s)(\}\s+# End of parameter block\s+)(# Setup crash logging)'
if ($content -match $pattern) {
    $content = $content -replace $pattern, "`$1$helperFunctions`n`n`$2"
    Write-Host "[FIXED] Added helper functions" -ForegroundColor Green
} else {
    Write-Host "[WARN] Could not insert helper functions" -ForegroundColor Yellow
}

# Apply Fix 2: Add Docker event monitoring to Start-BackgroundMonitoring function
$eventMonitoringCode = @'
    
    # Start Docker event monitoring
    Write-Host "[INFO] Starting Docker event monitoring..." -ForegroundColor Cyan
    $eventJob = Start-DockerEventMonitoring
'@

# Find where to insert the event monitoring code
$pattern = '(Write-Host "\[INFO\] Starting background Docker daemon monitoring\.\.\." -ForegroundColor Cyan\s+)(\s+# Check if running as administrator)'
if ($content -match $pattern) {
    $content = $content -replace $pattern, "`$1$eventMonitoringCode`n`$2"
    Write-Host "[FIXED] Added Docker event monitoring" -ForegroundColor Green
} else {
    Write-Host "[WARN] Could not find insertion point for event monitoring" -ForegroundColor Yellow
}

# Apply Fix 3: Replace Test-DockerDaemonHealth with detailed version
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

# Apply Fix 4: Add the enhanced functions from fixes file
# Extract and add Start-DockerEventMonitoring function
$eventFunctionPattern = '(?s)function Start-DockerEventMonitoring \{[^}]*return \$eventJob[^}]*\n\}'
if ($fixesContent -match $eventFunctionPattern) {
    # Insert before Start-BackgroundMonitoring function
    $pattern = '(?s)(function Start-BackgroundMonitoring)'
    if ($content -match $pattern) {
        $content = $content -replace $pattern, "$($matches[0])`n`n$($matches[0])" -replace "$($matches[0])$($matches[0])", "$($matches[1])`n`n$($matches[0])"
        $content = $content -replace "function Start-BackgroundMonitoring`n`nfunction Start-BackgroundMonitoring", "$($matches[1])`n`n$($matches[1])"
    }
}

# Apply Fix 5: Update the monitoring loop to use exponential backoff
$backoffPattern = 'Start-Sleep -Seconds \$actualDelay'
$backoffReplacement = @'
# Use exponential backoff instead of fixed delay
$backoffDelay = Get-BackoffDelay -AttemptNumber ([math]::Min($dockerDaemonFailures, 10))
Write-DaemonLog "Using exponential backoff: waiting ${backoffDelay}s (attempt $dockerDaemonFailures)" "INFO"
Start-Sleep -Seconds $backoffDelay
'@

if ($content -match $backoffPattern) {
    $content = $content -replace $backoffPattern, $backoffReplacement
    Write-Host "[FIXED] Added exponential backoff to monitoring loop" -ForegroundColor Green
}

# Write the patched script
Write-Host "[INFO] Writing patched script..." -ForegroundColor Gray
Set-Content -Path $scriptPath -Value $content -Encoding UTF8

# Verify the patch
Write-Host "`n[INFO] Verifying patch..." -ForegroundColor Gray
$patchedContent = Get-Content -Path $scriptPath -Raw

$checks = @(
    @{ Name = "Test-AdminPrivileges function"; Pattern = "function Test-AdminPrivileges" },
    @{ Name = "Test-DockerFrozen function"; Pattern = "function Test-DockerFrozen" },
    @{ Name = "Get-BackoffDelay function"; Pattern = "function Get-BackoffDelay" },
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

if ($Backup) {
    Write-Host "`n[INFO] Original script backed up to: $backupPath" -ForegroundColor Gray
}

Write-Host "`n[DONE] Patch operation completed." -ForegroundColor Cyan
