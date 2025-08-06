# Log Analysis Script for CaseStrainer

param(
    [string]$LogFile = "logs\casestrainer.log",
    [int]$Lines = 100
)

Write-Host "=== CaseStrainer Log Analysis ===" -ForegroundColor Cyan
Write-Host ""

# Check if log file exists
if (-not (Test-Path $LogFile)) {
    Write-Host "Log file not found: $LogFile" -ForegroundColor Red
    exit 1
}

Write-Host "Analyzing: $LogFile" -ForegroundColor Yellow
Write-Host ""

# Recent activity
Write-Host "Recent Activity (last $Lines lines):" -ForegroundColor Green
Get-Content $LogFile -Tail $Lines | ForEach-Object {
    if ($_ -match "ERROR") {
        Write-Host $_ -ForegroundColor Red
    } elseif ($_ -match "WARNING") {
        Write-Host $_ -ForegroundColor Yellow
    } elseif ($_ -match "memory|Memory") {
        Write-Host $_ -ForegroundColor Cyan
    } else {
        Write-Host $_ -ForegroundColor White
    }
}

Write-Host ""
Write-Host "Error Summary:" -ForegroundColor Green
$errors = Select-String "ERROR" $LogFile | Select-Object -Last 10
if ($errors) {
    $errors | ForEach-Object {
        Write-Host "  ERROR: $($_.Line)" -ForegroundColor Red
    }
} else {
    Write-Host "  No recent errors found" -ForegroundColor Green
}

Write-Host ""
Write-Host "Memory Issues:" -ForegroundColor Green
$memory = Select-String "memory|Memory" $LogFile | Select-Object -Last 5
if ($memory) {
    $memory | ForEach-Object {
        Write-Host "  MEMORY: $($_.Line)" -ForegroundColor Cyan
    }
} else {
    Write-Host "  No memory issues found" -ForegroundColor Green
}

Write-Host ""
Write-Host "Timeout Issues:" -ForegroundColor Green
$timeouts = Select-String "timeout|Timeout" $LogFile | Select-Object -Last 5
if ($timeouts) {
    $timeouts | ForEach-Object {
        Write-Host "  TIMEOUT: $($_.Line)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  No timeout issues found" -ForegroundColor Green
}

Write-Host ""
Write-Host "Connection Issues:" -ForegroundColor Green
$connections = Select-String "connection|Connection|connect|Connect" $LogFile | Select-Object -Last 5
if ($connections) {
    $connections | ForEach-Object {
        Write-Host "  CONNECTION: $($_.Line)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  No connection issues found" -ForegroundColor Green
}

Write-Host ""
Write-Host "Performance Metrics:" -ForegroundColor Green
$performance = Select-String "response|Response|duration|Duration" $LogFile | Select-Object -Last 5
if ($performance) {
    $performance | ForEach-Object {
        Write-Host "  PERFORMANCE: $($_.Line)" -ForegroundColor Magenta
    }
} 