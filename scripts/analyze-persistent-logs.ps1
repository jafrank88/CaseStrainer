#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Analyze persistent logs to diagnose crashes and restarts

.DESCRIPTION
    This script analyzes the persistent logs from CaseStrainer to help diagnose
    why the system stopped. It shows startup/shutdown events, crashes, and patterns.

.PARAMETER LogDir
    Directory containing the persistent logs (default: d:\dev\casestrainer\logs)

.PARAMETER LastSessions
    Number of recent sessions to show (default: 5)

.PARAMETER ShowCrashes
    Show all crash reports

.PARAMETER ShowEvents
    Show all startup/shutdown events

.PARAMETER Before
    Show logs before a specific timestamp (format: "2025-12-09 16:00:00")

.EXAMPLE
    .\analyze-persistent-logs.ps1
    Shows overview of recent activity

.EXAMPLE
    .\analyze-persistent-logs.ps1 -ShowCrashes
    Shows all crashes

.EXAMPLE
    .\analyze-persistent-logs.ps1 -Before "2025-12-09 16:00:00"
    Shows what happened before 4pm on Dec 9
#>

param(
    [string]$LogDir = "d:\dev\casestrainer\logs",
    [int]$LastSessions = 5,
    [switch]$ShowCrashes,
    [switch]$ShowEvents,
    [string]$Before
)

$ErrorActionPreference = "Stop"

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "CaseStrainer Persistent Log Analyzer" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check if log directory exists
if (-not (Test-Path $LogDir)) {
    Write-Host "❌ Log directory not found: $LogDir" -ForegroundColor Red
    exit 1
}

# Find all log files
$eventLog = Join-Path $LogDir "casestrainer-backend_events.log"
$crashLog = Join-Path $LogDir "casestrainer-backend_crashes.log"
$sessionFiles = Get-ChildItem -Path $LogDir -Filter "session_*.json" -ErrorAction SilentlyContinue

Write-Host "📁 Log Directory: $LogDir" -ForegroundColor Yellow
Write-Host "📄 Event Log: $(if (Test-Path $eventLog) { '✓ Found' } else { '✗ Not found' })" -ForegroundColor Yellow
Write-Host "📄 Crash Log: $(if (Test-Path $crashLog) { '✓ Found' } else { '✗ Not found' })" -ForegroundColor Yellow
Write-Host "📄 Session Files: $($sessionFiles.Count) found" -ForegroundColor Yellow
Write-Host ""

# Function to parse timestamp
function Parse-LogTimestamp {
    param([string]$Line)
    
    if ($Line -match '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}') {
        try {
            return [datetime]::ParseExact($Matches[0], "yyyy-MM-dd HH:mm:ss", $null)
        } catch {
            return $null
        }
    }
    return $null
}

# Show recent sessions
if ($sessionFiles.Count -gt 0) {
    Write-Host "=" * 80 -ForegroundColor Green
    Write-Host "RECENT SESSIONS (Last $LastSessions)" -ForegroundColor Green
    Write-Host "=" * 80 -ForegroundColor Green
    Write-Host ""
    
    $sessions = $sessionFiles | Sort-Object LastWriteTime -Descending | Select-Object -First $LastSessions
    
    foreach ($sessionFile in $sessions) {
        try {
            $session = Get-Content $sessionFile.FullName | ConvertFrom-Json
            
            Write-Host "📋 Session: $($session.session_id)" -ForegroundColor Cyan
            Write-Host "   Started:  $($session.timestamp)" -ForegroundColor White
            
            if ($session.shutdown_time) {
                Write-Host "   Stopped:  $($session.shutdown_time)" -ForegroundColor White
                Write-Host "   Type:     $($session.shutdown_type)" -ForegroundColor $(if ($session.shutdown_type -eq 'normal') { 'Green' } else { 'Yellow' })
                if ($session.uptime_seconds) {
                    $uptime = [timespan]::FromSeconds($session.uptime_seconds)
                    Write-Host "   Uptime:   $($uptime.ToString())" -ForegroundColor White
                }
            } elseif ($session.crash_time) {
                Write-Host "   Crashed:  $($session.crash_time)" -ForegroundColor Red
                Write-Host "   Type:     💥 $($session.crash_type)" -ForegroundColor Red
                Write-Host "   Error:    $($session.exception_type): $($session.exception_message)" -ForegroundColor Red
            } else {
                Write-Host "   Status:   ⚠️  No clean shutdown recorded (possible kill/OOM)" -ForegroundColor Yellow
            }
            
            if ($session.memory) {
                Write-Host "   Memory:   $($session.memory.available_gb)GB available / $($session.memory.total_gb)GB total ($($session.memory.percent_used)% used)" -ForegroundColor White
            }
            
            Write-Host "   PID:      $($session.pid)" -ForegroundColor Gray
            Write-Host "   Env:      $($session.env.FLASK_ENV)" -ForegroundColor Gray
            Write-Host ""
        } catch {
            Write-Host "   ⚠️  Error reading session file: $_" -ForegroundColor Yellow
        }
    }
}

# Show crashes
if ($ShowCrashes -and (Test-Path $crashLog)) {
    Write-Host "=" * 80 -ForegroundColor Red
    Write-Host "CRASH REPORTS" -ForegroundColor Red
    Write-Host "=" * 80 -ForegroundColor Red
    Write-Host ""
    
    $crashes = Get-Content $crashLog | Select-String -Pattern "UNCAUGHT EXCEPTION" -Context 0,20
    
    if ($crashes.Count -eq 0) {
        Write-Host "✅ No crashes recorded!" -ForegroundColor Green
    } else {
        Write-Host "Found $($crashes.Count) crash(es):" -ForegroundColor Yellow
        Write-Host ""
        
        foreach ($crash in $crashes) {
            Write-Host $crash.Line -ForegroundColor Red
            foreach ($contextLine in $crash.Context.PostContext) {
                if ($contextLine -match "Exception Type:|Exception Value:|Session:") {
                    Write-Host $contextLine -ForegroundColor Yellow
                }
            }
            Write-Host ""
        }
    }
}

# Show events
if ($ShowEvents -and (Test-Path $eventLog)) {
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "STARTUP/SHUTDOWN EVENTS" -ForegroundColor Cyan
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host ""
    
    $beforeDate = $null
    if ($Before) {
        try {
            $beforeDate = [datetime]::Parse($Before)
            Write-Host "📅 Showing events before: $($beforeDate.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Yellow
            Write-Host ""
        } catch {
            Write-Host "⚠️  Invalid date format for -Before parameter" -ForegroundColor Yellow
        }
    }
    
    $events = Get-Content $eventLog | Where-Object { 
        $_ -match "STARTUP|SHUTDOWN|SIGNAL|CRASH"
    }
    
    if ($beforeDate) {
        $events = $events | ForEach-Object {
            $ts = Parse-LogTimestamp $_
            if ($ts -and $ts -lt $beforeDate) {
                $_
            }
        }
    }
    
    foreach ($event in $events | Select-Object -Last 50) {
        if ($event -match "STARTUP") {
            Write-Host $event -ForegroundColor Green
        } elseif ($event -match "SHUTDOWN") {
            Write-Host $event -ForegroundColor Yellow
        } elseif ($event -match "SIGNAL") {
            Write-Host $event -ForegroundColor Magenta
        } elseif ($event -match "CRASH") {
            Write-Host $event -ForegroundColor Red
        } else {
            Write-Host $event
        }
    }
}

# Summary analysis
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "SUMMARY ANALYSIS" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

if (Test-Path $eventLog) {
    $allEvents = Get-Content $eventLog
    $startups = $allEvents | Select-String -Pattern "APPLICATION STARTUP"
    $normalShutdowns = $allEvents | Select-String -Pattern "NORMAL SHUTDOWN"
    $signalShutdowns = $allEvents | Select-String -Pattern "SIGNAL RECEIVED"
    $crashes = if (Test-Path $crashLog) { Get-Content $crashLog | Select-String -Pattern "UNCAUGHT EXCEPTION" } else { @() }
    
    Write-Host "Total Startups:        $($startups.Count)" -ForegroundColor White
    Write-Host "Normal Shutdowns:      $($normalShutdowns.Count)" -ForegroundColor Green
    Write-Host "Signal Shutdowns:      $($signalShutdowns.Count)" -ForegroundColor Yellow
    Write-Host "Crashes:               $($crashes.Count)" -ForegroundColor $(if ($crashes.Count -gt 0) { 'Red' } else { 'Green' })
    
    $unexplainedStops = $startups.Count - ($normalShutdowns.Count + $signalShutdowns.Count + $crashes.Count)
    if ($unexplainedStops -gt 0) {
        Write-Host "Unexplained Stops:     $unexplainedStops (possibly OOM kills or forcekilled)" -ForegroundColor Red
        Write-Host ""
        Write-Host "⚠️  WARNING: $unexplainedStops unexplained stops detected!" -ForegroundColor Red
        Write-Host "   These are likely OOM (Out of Memory) kills or force kills" -ForegroundColor Yellow
        Write-Host "   Check Docker stats and consider increasing memory limits" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "USAGE TIPS" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "• To see all crashes:            .\analyze-persistent-logs.ps1 -ShowCrashes" -ForegroundColor White
Write-Host "• To see all events:             .\analyze-persistent-logs.ps1 -ShowEvents" -ForegroundColor White
Write-Host "• To see what happened before:   .\analyze-persistent-logs.ps1 -Before '2025-12-09 16:00:00'" -ForegroundColor White
Write-Host "• To see more sessions:          .\analyze-persistent-logs.ps1 -LastSessions 10" -ForegroundColor White
Write-Host ""
Write-Host "✅ Analysis complete!" -ForegroundColor Green
