# analyze-crash-logs.ps1
# Analyzes crash_log.txt to provide insights about container failures

param(
    [switch]$Summary,        # Show summary statistics
    [switch]$Recent,         # Show only recent crashes (last 24 hours)
    [switch]$ByContainer,    # Group by container
    [switch]$ByError,        # Group by error type
    [int]$LastN = 0          # Show last N crashes
)

$logPath = Join-Path $PSScriptRoot "..\logs\crash_log.txt"

if (-not (Test-Path $logPath)) {
    Write-Host "[ERROR] Crash log not found at: $logPath" -ForegroundColor Red
    Write-Host "[INFO] Start monitoring mode first: .\cslaunch.ps1 -Monitor" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CaseStrainer Crash Log Analysis" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Read the log file
$logContent = Get-Content $logPath

if ($logContent.Count -eq 0) {
    Write-Host "[INFO] No crashes recorded yet. System is healthy!" -ForegroundColor Green
    exit 0
}

# Parse crash reports
$crashReports = @()
$currentReport = $null

foreach ($line in $logContent) {
    if ($line -match "^=+ CRASH REPORT: (.+) =+$") {
        if ($currentReport) {
            $crashReports += $currentReport
        }
        $currentReport = @{
            Container = $matches[1]
            Time = $null
            Status = $null
            ExitCode = $null
            RestartCount = $null
            Health = $null
            Errors = @()
            LogLines = @()
        }
    }
    elseif ($currentReport) {
        if ($line -match "^Time: (.+)$") {
            $currentReport.Time = [DateTime]::Parse($matches[1])
        }
        elseif ($line -match "^Status: (.+)$") {
            $currentReport.Status = $matches[1]
        }
        elseif ($line -match "^Exit Code: (.+)$") {
            $currentReport.ExitCode = $matches[1]
        }
        elseif ($line -match "^Restart Count: (.+)$") {
            $currentReport.RestartCount = $matches[1]
        }
        elseif ($line -match "^Health: (.+)$") {
            $currentReport.Health = $matches[1]
        }
        elseif ($line -match "^\[.+\] \[ERROR\]\s+FOUND: (.+)$") {
            $currentReport.Errors += $matches[1]
        }
        elseif ($line -match "--- Last 50 Log Lines ---") {
            # Start collecting log lines
            $collectingLogs = $true
        }
        elseif ($collectingLogs -and $line -match "^=+$") {
            # End of crash report
            $collectingLogs = $false
        }
        elseif ($collectingLogs) {
            $currentReport.LogLines += $line
        }
    }
}

# Add the last report
if ($currentReport) {
    $crashReports += $currentReport
}

Write-Host "Total Crashes: $($crashReports.Count)" -ForegroundColor Yellow
Write-Host ""

# Filter by time if requested
if ($Recent) {
    $cutoff = (Get-Date).AddHours(-24)
    $crashReports = $crashReports | Where-Object { $_.Time -and $_.Time -gt $cutoff }
    Write-Host "Showing crashes from last 24 hours: $($crashReports.Count)" -ForegroundColor Cyan
    Write-Host ""
}

# Show last N crashes if requested
if ($LastN -gt 0) {
    $crashReports = $crashReports | Select-Object -Last $LastN
    Write-Host "Showing last $LastN crashes" -ForegroundColor Cyan
    Write-Host ""
}

# Summary statistics
if ($Summary -or (-not $ByContainer -and -not $ByError -and $LastN -eq 0)) {
    Write-Host "=== SUMMARY ===" -ForegroundColor Green
    Write-Host ""
    
    # Crashes by container
    Write-Host "Crashes by Container:" -ForegroundColor Yellow
    $crashReports | Group-Object Container | Sort-Object Count -Descending | ForEach-Object {
        $percentage = [math]::Round(($_.Count / $crashReports.Count) * 100, 1)
        Write-Host "  $($_.Name): " -NoNewline -ForegroundColor White
        Write-Host "$($_.Count) crashes ($percentage%)" -ForegroundColor Cyan
    }
    Write-Host ""
    
    # Most common exit codes
    Write-Host "Most Common Exit Codes:" -ForegroundColor Yellow
    $exitCodes = $crashReports | Where-Object { $_.ExitCode } | Group-Object ExitCode | Sort-Object Count -Descending
    foreach ($code in $exitCodes | Select-Object -First 5) {
        $meaning = switch ($code.Name) {
            "0" { "(Normal exit)" }
            "1" { "(General error)" }
            "137" { "(SIGKILL - OOM)" }
            "139" { "(Segmentation fault)" }
            "143" { "(SIGTERM)" }
            default { "" }
        }
        $percentage = [math]::Round(($code.Count / $crashReports.Count) * 100, 1)
        Write-Host "  Exit Code $($code.Name) $meaning " -NoNewline -ForegroundColor White
        Write-Host "$($code.Count) times ($percentage%)" -ForegroundColor Cyan
    }
    Write-Host ""
    
    # Most common errors
    Write-Host "Most Common Error Patterns:" -ForegroundColor Yellow
    $allErrors = $crashReports | ForEach-Object { $_.Errors } | Group-Object | Sort-Object Count -Descending
    foreach ($errorItem in $allErrors | Select-Object -First 5) {
        $percentage = [math]::Round(($errorItem.Count / $crashReports.Count) * 100, 1)
        Write-Host "  $($errorItem.Name): " -NoNewline -ForegroundColor White
        Write-Host "$($errorItem.Count) times ($percentage%)" -ForegroundColor Red
    }
    Write-Host ""
    
    # Timeline
    if ($crashReports.Count -gt 1) {
        $firstCrash = ($crashReports | Where-Object { $_.Time } | Sort-Object Time | Select-Object -First 1).Time
        $lastCrash = ($crashReports | Where-Object { $_.Time } | Sort-Object Time | Select-Object -Last 1).Time
        
        if ($firstCrash -and $lastCrash) {
            Write-Host "Timeline:" -ForegroundColor Yellow
            Write-Host "  First Crash: $($firstCrash.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
            Write-Host "  Last Crash: $($lastCrash.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
            
            $duration = $lastCrash - $firstCrash
            if ($duration.TotalDays -gt 1) {
                Write-Host "  Duration: $([math]::Round($duration.TotalDays, 1)) days" -ForegroundColor White
            }
            elseif ($duration.TotalHours -gt 1) {
                Write-Host "  Duration: $([math]::Round($duration.TotalHours, 1)) hours" -ForegroundColor White
            }
            else {
                Write-Host "  Duration: $([math]::Round($duration.TotalMinutes, 1)) minutes" -ForegroundColor White
            }
            
            # Crash frequency
            if ($duration.TotalHours -gt 0) {
                $crashesPerHour = $crashReports.Count / $duration.TotalHours
                Write-Host "  Average Frequency: $([math]::Round($crashesPerHour, 2)) crashes/hour" -ForegroundColor White
            }
            Write-Host ""
        }
    }
}

# Group by container
if ($ByContainer) {
    Write-Host "=== CRASHES BY CONTAINER ===" -ForegroundColor Green
    Write-Host ""
    
    $crashReports | Group-Object Container | Sort-Object Count -Descending | ForEach-Object {
        Write-Host "$($_.Name):" -ForegroundColor Yellow
        Write-Host "  Total Crashes: $($_.Count)" -ForegroundColor Cyan
        
        # Recent crashes
        $recentCrashes = $_.Group | Where-Object { $_.Time } | Sort-Object Time -Descending | Select-Object -First 3
        if ($recentCrashes) {
            Write-Host "  Recent Crashes:" -ForegroundColor White
            foreach ($crash in $recentCrashes) {
                Write-Host "    $($crash.Time.ToString('yyyy-MM-dd HH:mm:ss')) - Exit Code: $($crash.ExitCode)" -ForegroundColor Gray
                if ($crash.Errors) {
                    foreach ($error in $crash.Errors) {
                        Write-Host "      [!] $error" -ForegroundColor Red
                    }
                }
            }
        }
        Write-Host ""
    }
}

# Group by error type
if ($ByError) {
    Write-Host "=== CRASHES BY ERROR TYPE ===" -ForegroundColor Green
    Write-Host ""
    
    $allErrors = $crashReports | ForEach-Object { 
        $containerName = $_.Container
        $errorTime = $_.Time
        $_.Errors | ForEach-Object { 
            [PSCustomObject]@{
                ErrorType = $_
                Container = $containerName
                Time = $errorTime
            }
        }
    } | Group-Object ErrorType | Sort-Object Count -Descending
    
    foreach ($errorGroup in $allErrors) {
        Write-Host "$($errorGroup.Name):" -ForegroundColor Red
        Write-Host "  Occurrences: $($errorGroup.Count)" -ForegroundColor Cyan
        Write-Host "  Affected Containers:" -ForegroundColor White
        
        $containers = $errorGroup.Group | Group-Object Container | Sort-Object Count -Descending
        foreach ($containerItem in $containers) {
            Write-Host "    $($containerItem.Name): $($containerItem.Count) times" -ForegroundColor Gray
        }
        Write-Host ""
    }
}

# Recommendations
Write-Host "=== RECOMMENDATIONS ===" -ForegroundColor Green
Write-Host ""

# Check for OOM issues
$oomCrashes = $crashReports | Where-Object { $_.ExitCode -eq "137" -or $_.Errors -contains "Process killed (likely OOM)" -or $_.Errors -contains "Memory limit exceeded" }
if ($oomCrashes.Count -gt 0) {
    Write-Host "[!] MEMORY ISSUES DETECTED ($($oomCrashes.Count) OOM crashes)" -ForegroundColor Red
    Write-Host "    Action: Increase memory limits in docker-compose.prod.yml" -ForegroundColor Yellow
    Write-Host "    Current limits: backend=4g, workers=2g" -ForegroundColor White
    Write-Host "    Suggested: backend=6g, workers=3g" -ForegroundColor Green
    Write-Host ""
}

# Check for connection issues
$connCrashes = $crashReports | Where-Object { $_.Errors -contains "Service connection failed" -or $_.Errors -contains "Redis connection issue" }
if ($connCrashes.Count -gt 0) {
    Write-Host "[!] CONNECTION ISSUES DETECTED ($($connCrashes.Count) crashes)" -ForegroundColor Red
    Write-Host "    Action: Check Redis and database connectivity" -ForegroundColor Yellow
    Write-Host "    Commands:" -ForegroundColor White
    Write-Host "      docker exec casestrainer-redis-prod redis-cli ping" -ForegroundColor Green
    Write-Host "      docker logs casestrainer-redis-prod" -ForegroundColor Green
    Write-Host ""
}

# Check for dependency issues
$depCrashes = $crashReports | Where-Object { $_.Errors -contains "Missing Python dependency" }
if ($depCrashes.Count -gt 0) {
    Write-Host "[!] DEPENDENCY ISSUES DETECTED ($($depCrashes.Count) crashes)" -ForegroundColor Red
    Write-Host "    Action: Rebuild containers with --no-cache" -ForegroundColor Yellow
    Write-Host "    Command: .\cslaunch.ps1 -Build -NoCache" -ForegroundColor Green
    Write-Host ""
}

# Check for frequent crashes
if ($crashReports.Count -gt 10) {
    $recentHour = $crashReports | Where-Object { $_.Time -and $_.Time -gt (Get-Date).AddHours(-1) }
    if ($recentHour.Count -gt 5) {
        Write-Host "[!] HIGH CRASH FREQUENCY DETECTED" -ForegroundColor Red
        Write-Host "    $($recentHour.Count) crashes in the last hour" -ForegroundColor Yellow
        Write-Host "    This may indicate a systemic issue requiring immediate attention" -ForegroundColor White
        Write-Host ""
    }
}

Write-Host "For more details, check: $logPath" -ForegroundColor Gray
Write-Host ""
