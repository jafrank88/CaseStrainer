# Docker Log Analysis Tool
# Analyzes Docker health, restart, and freeze logs to identify patterns

param(
    [int]$Days = 7,  # Number of days to analyze
    [switch]$ShowFreezes,
    [switch]$ShowRestarts,
    [switch]$ShowSummary = $true
)

$LogDir = "logs"
$HealthLog = Join-Path $LogDir "docker_health_monitor.log"
$RestartLog = Join-Path $LogDir "docker_restart_events.log"
$FreezeLog = Join-Path $LogDir "docker_freeze_detection.log"

function Get-LogEntries {
    param(
        [string]$LogFile,
        [int]$Days
    )
    
    if (!(Test-Path $LogFile)) {
        return @()
    }
    
    $cutoffDate = (Get-Date).AddDays(-$Days)
    $entries = @()
    
    Get-Content $LogFile | ForEach-Object {
        if ($_ -match '^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(\w+)\] (.+)$') {
            $timestamp = [DateTime]::ParseExact($matches[1], "yyyy-MM-dd HH:mm:ss", $null)
            if ($timestamp -gt $cutoffDate) {
                $entries += @{
                    Timestamp = $timestamp
                    Level = $matches[2]
                    Message = $matches[3]
                }
            }
        }
    }
    
    return $entries
}

Write-Host "=== Docker Log Analysis (Last $Days days) ===" -ForegroundColor Cyan
Write-Host ""

# Health Check Analysis
$healthEntries = Get-LogEntries -LogFile $HealthLog -Days $Days
if ($healthEntries.Count -gt 0) {
    $healthChecks = $healthEntries | Where-Object { $_.Message -eq "=== HEALTH CHECK STARTED ===" }
    $passedChecks = $healthEntries | Where-Object { $_.Message -eq "=== HEALTH CHECK PASSED ===" }
    $failedChecks = $healthEntries | Where-Object { $_.Message -eq "=== HEALTH CHECK FAILED ===" }
    
    Write-Host "Health Check Summary:" -ForegroundColor Green
    Write-Host "  Total health checks: $($healthChecks.Count)"
    $passedPercent = if($healthChecks.Count -gt 0){[math]::Round(($passedChecks.Count/$healthChecks.Count)*100,1)}else{0}
    $failedPercent = if($healthChecks.Count -gt 0){[math]::Round(($failedChecks.Count/$healthChecks.Count)*100,1)}else{0}
    Write-Host "  Passed: $($passedChecks.Count) ($passedPercent%)"
    Write-Host "  Failed: $($failedChecks.Count) ($failedPercent%)"
    Write-Host ""
}

# Restart Analysis
$restartEntries = Get-LogEntries -LogFile $RestartLog -Days $Days
if ($restartEntries.Count -gt 0) {
    $restartInitiated = $restartEntries | Where-Object { $_.Message -eq "=== DOCKER RESTART INITIATED ===" }
    $restartSuccessful = $restartEntries | Where-Object { $_.Message -eq "=== DOCKER RESTART SUCCESSFUL ===" }
    $restartFailed = $restartEntries | Where-Object { $_.Message -eq "=== DOCKER RESTART FAILED ===" }
    
    Write-Host "Restart Summary:" -ForegroundColor Yellow
    Write-Host "  Total restarts attempted: $($restartInitiated.Count)"
    Write-Host "  Successful: $($restartSuccessful.Count)"
    Write-Host "  Failed: $($restartFailed.Count)"
    
    if ($ShowRestarts -and $restartInitiated.Count -gt 0) {
        Write-Host ""
        Write-Host "Recent Restart Events:" -ForegroundColor Yellow
        foreach ($restart in $restartInitiated | Sort-Object Timestamp -Descending | Select-Object -First 10) {
            $restartId = ($restartEntries | Where-Object { 
                $_.Timestamp -eq $restart.Timestamp -and $_.Message -match "Restart ID: (.+)" 
            } | Select-Object -First 1)
            
            $reason = ($restartEntries | Where-Object { 
                $_.Timestamp -eq $restart.Timestamp -and $_.Message -match "Reason: (.+)" 
            } | Select-Object -First 1)
            
            Write-Host "  $($restart.Timestamp.ToString("MM/dd HH:mm:ss")): $($reason.Message -replace 'Reason: ','')" -ForegroundColor Gray
        }
    }
    Write-Host ""
}

# Freeze Analysis
$freezeEntries = Get-LogEntries -LogFile $FreezeLog -Days $Days
if ($freezeEntries.Count -gt 0) {
    $freezeDetected = $freezeEntries | Where-Object { $_.Message -eq "=== DOCKER FREEZE DETECTED ===" }
    
    Write-Host "Freeze Detection Summary:" -ForegroundColor Red
    Write-Host "  Total freezes detected: $($freezeDetected.Count)"
    
    if ($ShowFreezes -and $freezeDetected.Count -gt 0) {
        Write-Host ""
        Write-Host "Recent Freeze Events:" -ForegroundColor Red
        foreach ($freeze in $freezeDetected | Sort-Object Timestamp -Descending | Select-Object -First 10) {
            $testName = ($freezeEntries | Where-Object { 
                $_.Timestamp -eq $freeze.Timestamp -and $_.Message -match "Test: (.+)" 
            } | Select-Object -First 1)
            
            Write-Host "  $($freeze.Timestamp.ToString("MM/dd HH:mm:ss")): $($testName.Message -replace 'Test: ','')" -ForegroundColor Gray
        }
    }
    Write-Host ""
}

# Pattern Analysis
if ($ShowSummary) {
    Write-Host "Pattern Analysis:" -ForegroundColor Magenta
    
    # Time-based patterns
    if ($healthEntries.Count -gt 0) {
        $hourlyStats = $healthEntries | Where-Object { $_.Message -eq "=== HEALTH CHECK FAILED ===" } | 
                      Group-Object { $_.Timestamp.Hour } | 
                      Sort-Object Name
        
        if ($hourlyStats.Count -gt 0) {
            Write-Host "  Failure patterns by hour:"
            foreach ($hour in $hourlyStats) {
                Write-Host "    $($hour.Name):00 - $($hour.Count) failures" -ForegroundColor Gray
            }
        }
    }
    
    # Recent trend
    if ($healthChecks.Count -gt 0) {
        $recentChecks = $healthChecks | Sort-Object Timestamp -Descending | Select-Object -First 10
        $recentPassed = $passedChecks | Where-Object { $_.Timestamp -in $recentChecks.Timestamp }
        $recentSuccessRate = if($recentChecks.Count -gt 0){[math]::Round(($recentPassed.Count/$recentChecks.Count)*100,1)}else{0}
        
        Write-Host ""
        Write-Host "  Recent trend (last 10 checks): $recentSuccessRate% success rate"
        if ($recentSuccessRate -lt 90) {
            Write-Host "    WARNING: Recent success rate is below 90%" -ForegroundColor Yellow
        } elseif ($recentSuccessRate -eq 100) {
            Write-Host "    All recent checks passed" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "Log Files:" -ForegroundColor Cyan
Write-Host "  Health monitoring: $HealthLog"
Write-Host "  Restart events: $RestartLog"
Write-Host "  Freeze detection: $FreezeLog"
Write-Host ""
Write-Host "Usage examples:"
Write-Host "  .\analyze_docker_logs.ps1 -ShowRestarts -ShowFreezes"
Write-Host "  .\analyze_docker_logs.ps1 -Days 30"
