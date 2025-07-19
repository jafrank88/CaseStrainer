#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Restart Cursor and verify Pylance configuration for CaseStrainer project.

.DESCRIPTION
    This script helps restart Cursor to pick up the new Pylance configuration
    that excludes .md files and other non-Python file types to reduce Pylance noise.

.NOTES
    Run this script after updating pyrightconfig.json and .cursor/settings.json
#>

Write-Host "Restarting Cursor for Pylance Configuration Update..." -ForegroundColor Yellow

# Check if Cursor is running
$cursorProcesses = Get-Process -Name "Cursor" -ErrorAction SilentlyContinue

if ($cursorProcesses) {
    Write-Host "Found running Cursor processes:" -ForegroundColor Cyan
    $cursorProcesses | ForEach-Object { Write-Host "  - PID: $($_.Id), Started: $($_.StartTime)" }
    
    Write-Host "Stopping Cursor processes..." -ForegroundColor Yellow
    $cursorProcesses | Stop-Process -Force
    Start-Sleep -Seconds 3
} else {
    Write-Host "No running Cursor processes found" -ForegroundColor Cyan
}

# Verify configuration files exist
Write-Host "Checking configuration files..." -ForegroundColor Green
$configFiles = @(
    "pyrightconfig.json",
    ".cursor/settings.json"
)

foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "  $file exists" -ForegroundColor Green
    } else {
        Write-Host "  $file missing!" -ForegroundColor Red
    }
}

# Show current exclusions
Write-Host "Current Pylance exclusions:" -ForegroundColor Cyan
$pyrightConfig = Get-Content "pyrightconfig.json" | ConvertFrom-Json
Write-Host "  Include: $($pyrightConfig.include -join ', ')" -ForegroundColor White
Write-Host "  Exclude count: $($pyrightConfig.exclude.Count)" -ForegroundColor White

# Check if .md files are excluded
if ($pyrightConfig.exclude -contains "**/*.md") {
    Write-Host "  .md files are excluded" -ForegroundColor Green
} else {
    Write-Host "  .md files are NOT excluded" -ForegroundColor Red
}

# Check if other common file types are excluded
$commonExclusions = @("**/*.js", "**/*.ts", "**/*.json", "**/*.html", "**/*.css")
foreach ($exclusion in $commonExclusions) {
    if ($pyrightConfig.exclude -contains $exclusion) {
        Write-Host "  $exclusion is excluded" -ForegroundColor Green
    } else {
        Write-Host "  $exclusion is NOT excluded" -ForegroundColor Red
    }
}

# Start Cursor
Write-Host "Starting Cursor..." -ForegroundColor Green
try {
    Start-Process "Cursor" -ArgumentList "."
    Write-Host "  Cursor started successfully" -ForegroundColor Green
} catch {
    Write-Host "  Failed to start Cursor: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Wait for Cursor to fully load" -ForegroundColor White
Write-Host "2. Check the Problems panel - should show significantly fewer errors" -ForegroundColor White
Write-Host "3. If still showing many errors:" -ForegroundColor White
Write-Host "   - Press Ctrl+Shift+P" -ForegroundColor White
Write-Host "   - Type: Python: Restart Language Server" -ForegroundColor White
Write-Host "   - Press Enter" -ForegroundColor White
Write-Host "4. Verify .md files are excluded:" -ForegroundColor White
Write-Host "   - Open any .md file in the project" -ForegroundColor White
Write-Host "   - Should show no Pylance errors" -ForegroundColor White

Write-Host "Cursor restart complete!" -ForegroundColor Green
Write-Host "Expected Results:" -ForegroundColor Cyan
Write-Host "- .md files: No Pylance errors" -ForegroundColor White
Write-Host "- .js/.ts files: No Pylance errors" -ForegroundColor White
Write-Host "- .json files: No Pylance errors" -ForegroundColor White
Write-Host "- Core Python files: Only relevant errors" -ForegroundColor White 