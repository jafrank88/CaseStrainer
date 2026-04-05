# cslauncher_enhanced.ps1
# Enhanced version with additional robustness checks and pre-emptive monitoring
# Usage: .\cslauncher_enhanced.ps1 [same parameters as cslauncher.ps1]

[CmdletBinding()]
param(
    [Parameter()]
    [switch]$Build = $true,

    [Parameter()]
    [switch]$CleanDocker,

    [Parameter()]
    [int]$MemoryThresholdGB = 3,

    [Parameter()]
    [int]$DiskThresholdGB = 25,

    [Parameter()]
    [switch]$SkipHealthCheck,

    [Parameter()]
    [switch]$LogErrors,

    [Parameter()]
    [switch]$ServicesOff,

    [Parameter()]
    [switch]$UpdateDocker,

    [Parameter()]
    [switch]$InstallService,

    [Parameter()]
    [switch]$RunFullDocumentTest,

    [Parameter()]
    [switch]$WaitForServices,

    [Parameter()]
    [switch]$CleanupStuckJobs,

    # NEW: Enhanced robustness parameters
    [Parameter()]
    [switch]$PreFlightCheck,

    [Parameter()]
    [switch]$ForceAdminRecovery,

    [Parameter()]
    [int]$MaxRecoveryAttempts = 3
)

# Import all functions from original cslauncher
$originalLauncher = Join-Path $PSScriptRoot "cslauncher.ps1"

# Enhanced pre-flight checks
function Test-SystemHealth {
    Write-Host "=== SYSTEM PRE-FLIGHT CHECKS ===" -ForegroundColor Cyan
    
    $issues = @()
    
    # Check available memory
    $memInfo = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
    if ($memInfo) {
        $availableGB = [math]::Round($memInfo.FreePhysicalMemory / 1MB, 2)
        $totalGB = [math]::Round($memInfo.TotalVisibleMemorySize / 1MB, 2)
        $usedPercent = [math]::Round((($totalGB - $availableGB) / $totalGB) * 100, 1)
        
        Write-Host "   Memory: $availableGB GB available ($usedPercent% used)" -ForegroundColor $(if ($availableGB -lt 4) { 'Yellow' } else { 'Green' })
        
        if ($availableGB -lt 2) {
            $issues += "CRITICAL: Low memory ($availableGB GB available)"
        }
    }
    
    # Check disk space
    $systemDrive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'" -ErrorAction SilentlyContinue
    if ($systemDrive) {
        $freeGB = [math]::Round($systemDrive.FreeSpace / 1GB, 2)
        $totalGB = [math]::Round($systemDrive.Size / 1GB, 2)
        $usedPercent = [math]::Round((($totalGB - $freeGB) / $totalGB) * 100, 1)
        
        Write-Host "   Disk C: $freeGB GB free ($usedPercent% used)" -ForegroundColor $(if ($freeGB -lt 10) { 'Yellow' } else { 'Green' })
        
        if ($freeGB -lt 5) {
            $issues += "WARNING: Low disk space ($freeGB GB free)"
        }
    }
    
    # Check Docker Desktop process health
    $dockerProcs = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if ($dockerProcs) {
        $totalMemory = ($dockerProcs | Measure-Object WorkingSet64 -Sum).Sum / 1MB
        Write-Host "   Docker Desktop: Running ($([math]::Round($totalMemory, 2)) MB memory)" -ForegroundColor Green
    } else {
        $issues += "WARNING: Docker Desktop not running"
    }
    
    # Check Docker service status
    $svc = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
    if ($svc) {
        Write-Host "   Docker Service: $($svc.Status)" -ForegroundColor $(if ($svc.Status -eq 'Running') { 'Green' } else { 'Red' })
        if ($svc.Status -ne 'Running') {
            $issues += "ERROR: Docker service is $($svc.Status)"
        }
    } else {
        $issues += "WARNING: Docker service not found"
    }
    
    # Report issues
    if ($issues.Count -gt 0) {
        Write-Host ""
        Write-Host "   ISSUES DETECTED:" -ForegroundColor Red
        foreach ($issue in $issues) {
            Write-Host "     - $issue" -ForegroundColor Red
        }
        return $false
    } else {
        Write-Host "   ✅ System health looks good" -ForegroundColor Green
        return $true
    }
}

# Enhanced Docker service recovery with multiple attempts
function Invoke-EnhancedDockerRecovery {
    param([int]$MaxAttempts = 3)
    
    Write-Host "=== ENHANCED DOCKER RECOVERY ===" -ForegroundColor Cyan
    
    $attempt = 0
    while ($attempt -lt $MaxAttempts) {
        $attempt++
        Write-Host "   Recovery attempt $attempt/$MaxAttempts..." -ForegroundColor Yellow
        
        # Force kill all Docker processes
        try {
            Write-Host "   Stopping Docker Desktop processes..." -ForegroundColor Gray
            Get-Process -Name "Docker Desktop","com.docker.backend","com.docker.service" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 3
        } catch {
            Write-Host "   Process stop failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
        # Reset WSL
        try {
            Write-Host "   Resetting WSL..." -ForegroundColor Gray
            wsl --shutdown 2>$null
            Start-Sleep -Seconds 2
        } catch {
            Write-Host "   WSL reset failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
        # Start Docker Desktop with admin privileges if needed
        $isAdmin = Test-AdminPrivileges
        $dockerExe = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
        
        if (Test-Path $dockerExe) {
            if ($isAdmin -or $ForceAdminRecovery) {
                Write-Host "   Starting Docker Desktop with elevated privileges..." -ForegroundColor Gray
                Start-Process -FilePath $dockerExe -Verb RunAs -ErrorAction SilentlyContinue
            } else {
                Write-Host "   Starting Docker Desktop..." -ForegroundColor Gray
                Start-Process -FilePath $dockerExe -ErrorAction SilentlyContinue
            }
        }
        
        # Wait for Docker to become healthy
        $maxWait = 90
        $waited = 0
        $healthy = $false
        
        while ($waited -lt $maxWait -and -not $healthy) {
            Start-Sleep -Seconds 5
            $waited += 5
            
            try {
                $testInfo = docker info 2>&1
                if ($LASTEXITCODE -eq 0 -and $testInfo -notmatch "500 Internal Server Error|Cannot connect|error|ERROR") {
                    $healthy = $true
                    Write-Host "   Docker is healthy after $waited seconds" -ForegroundColor Green
                    break
                }
            } catch {
                # Still waiting
            }
            
            if ($waited % 15 -eq 0) {
                Write-Host "   Still waiting... ($waited/$maxWait sec)" -ForegroundColor Gray
            }
        }
        
        if ($healthy) {
            Write-Host "   ✅ Recovery successful on attempt $attempt" -ForegroundColor Green
            return $true
        } else {
            Write-Host "   ❌ Recovery attempt $attempt failed" -ForegroundColor Red
            if ($attempt -lt $MaxAttempts) {
                Write-Host "   Waiting 10 seconds before next attempt..." -ForegroundColor Gray
                Start-Sleep -Seconds 10
            }
        }
    }
    
    Write-Host "   ❌ All recovery attempts failed" -ForegroundColor Red
    return $false
}

# Enhanced health check with pre-emptive monitoring
function Test-EnhancedDockerHealth {
    # Check basic Docker connectivity
    try {
        $info = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   ❌ Docker daemon not responding" -ForegroundColor Red
            return $false
        }
        
        if ($info -match "error|ERROR|Cannot connect|500 Internal Server Error") {
            Write-Host "   ❌ Docker daemon reporting errors" -ForegroundColor Red
            return $false
        }
        
        # Check container health
        $containers = docker ps --format "{{.Names}}|{{.Status}}" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $runningCount = ($containers | Where-Object { $_ -match "Up" }).Count
            Write-Host "   ✅ Docker daemon healthy ($runningCount containers running)" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️ Docker daemon healthy but container query failed" -ForegroundColor Yellow
        }
        
        return $true
    } catch {
        Write-Host "   ❌ Exception checking Docker health: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Main execution with enhanced checks
Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  CaseStrainer Enhanced Development Launcher" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

# Pre-flight system health check
if ($PreFlightCheck) {
    $systemHealthy = Test-SystemHealth
    if (-not $systemHealthy) {
        Write-Host ""
        Write-Host "⚠️ System health issues detected. Continue anyway? (Y/N)" -ForegroundColor Yellow
        $response = Read-Host
        if ($response -ne 'Y' -and $response -ne 'y') {
            Write-Host "   Exiting due to system health issues" -ForegroundColor Red
            exit 1
        }
    }
    Write-Host ""
}

# Enhanced Docker health check
Write-Host "=== ENHANCED DOCKER HEALTH CHECK ===" -ForegroundColor Cyan
if (-not (Test-EnhancedDockerHealth)) {
    Write-Host "   Docker not healthy, attempting enhanced recovery..." -ForegroundColor Yellow
    
    if (Invoke-EnhancedDockerRecovery -MaxAttempts $MaxRecoveryAttempts) {
        Write-Host "   ✅ Docker recovery successful" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Docker recovery failed" -ForegroundColor Red
        Write-Host ""
        Write-Host "Manual recovery steps:" -ForegroundColor Yellow
        Write-Host "1. Run PowerShell as Administrator" -ForegroundColor Gray
        Write-Host "2. Execute: Start-Service com.docker.service" -ForegroundColor Gray
        Write-Host "3. Start Docker Desktop from Start Menu" -ForegroundColor Gray
        Write-Host "4. Wait 2-3 minutes for full initialization" -ForegroundColor Gray
        exit 1
    }
}

# If we reach here, Docker is healthy - delegate to original launcher
Write-Host "   Delegating to original cslauncher.ps1..." -ForegroundColor Cyan
Write-Host ""

# Build parameter list to pass through to original launcher
$launcherArgs = @()
if ($Build) { $launcherArgs += "-Build" }
if ($CleanDocker) { $launcherArgs += "-CleanDocker" }
if ($SkipHealthCheck) { $launcherArgs += "-SkipHealthCheck" }
if ($LogErrors) { $launcherArgs += "-LogErrors" }
if ($ServicesOff) { $launcherArgs += "-ServicesOff" }
if ($UpdateDocker) { $launcherArgs += "-UpdateDocker" }
if ($InstallService) { $launcherArgs += "-InstallService" }
if ($RunFullDocumentTest) { $launcherArgs += "-RunFullDocumentTest" }
if ($WaitForServices) { $launcherArgs += "-WaitForServices" }
if ($CleanupStuckJobs) { $launcherArgs += "-CleanupStuckJobs" }

# Add numeric parameters
$launcherArgs += "-MemoryThresholdGB", $MemoryThresholdGB
$launcherArgs += "-DiskThresholdGB", $DiskThresholdGB

try {
    & $originalLauncher @launcherArgs
} catch {
    Write-Host "   ❌ Original launcher failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Check logs at: logs\reload.log" -ForegroundColor Yellow
    exit 1
}
