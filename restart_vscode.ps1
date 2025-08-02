#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Restart VS Code and verify Pylance configuration for CaseStrainer project.

.DESCRIPTION
    This script helps restart VS Code to pick up the new Pylance configuration
    that excludes archived and deprecated files to reduce the 10K+ error count.

.NOTES
    Run this script after updating pyrightconfig.json and .vscode/settings.json
#>

Write-Host "Restarting VS Code for Pylance Configuration Update..." -ForegroundColor Yellow

# Check if VS Code is running
$vscodeProcesses = Get-Process -Name "Code" -ErrorAction SilentlyContinue

if ($vscodeProcesses) {
    Write-Host "Found running VS Code processes:" -ForegroundColor Cyan
    $vscodeProcesses | ForEach-Object { Write-Host "  - PID: $($_.Id), Started: $($_.StartTime)" }
    
    Write-Host "`nStopping VS Code processes..." -ForegroundColor Yellow
    $vscodeProcesses | Stop-Process -Force
    Start-Sleep -Seconds 2
}

# Verify configuration files exist
Write-Host "`nChecking configuration files..." -ForegroundColor Green
$configFiles = @(
    "pyrightconfig.json",
    ".vscode/settings.json"
)

foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file missing!" -ForegroundColor Red
    }
}

# Show current exclusions
Write-Host "`nCurrent Pylance exclusions:" -ForegroundColor Cyan
$pyrightConfig = Get-Content "pyrightconfig.json" | ConvertFrom-Json
Write-Host "  Include: $($pyrightConfig.include -join ', ')" -ForegroundColor White
Write-Host "  Exclude count: $($pyrightConfig.exclude.Count)" -ForegroundColor White

# Start VS Code
Write-Host "`nStarting VS Code..." -ForegroundColor Green
Start-Process "code" -ArgumentList "."

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Wait for VS Code to fully load" -ForegroundColor White
Write-Host "2. Check the Problems panel - should show ~335 errors instead of 10K+" -ForegroundColor White
Write-Host "3. If still showing 10K+ errors:" -ForegroundColor White
Write-Host "   - Press Ctrl+Shift+P" -ForegroundColor White
Write-Host "   - Type: Python: Restart Language Server" -ForegroundColor White
Write-Host "   - Press Enter" -ForegroundColor White
Write-Host "4. Verify archived files are excluded:" -ForegroundColor White
Write-Host "   - Open src/archived_case_name_extraction.py" -ForegroundColor White
Write-Host "   - Should show no Pylance errors" -ForegroundColor White

Write-Host "`nVS Code restart complete!" -ForegroundColor Green