# Deprecate Redundant Tests Script
# This script moves redundant test files to a deprecated_tests directory
# and leaves a deprecation notice in their place

$ErrorActionPreference = "Stop"

# Define paths
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$deprecatedDir = Join-Path $rootDir "deprecated_tests"
$logFile = Join-Path $rootDir "deprecation_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# List of test files to deprecate
$testFilesToDeprecate = @(
    "test_simple.bat",
    "test_nginx.bat",
    "test_nginx_fix.bat",
    "test_path.bat",
    "test_paths.bat",
    "test_file.bat"
)

# Create deprecated directory if it doesn't exist
if (-not (Test-Path $deprecatedDir)) {
    New-Item -ItemType Directory -Path $deprecatedDir | Out-Null
    "Created directory: $deprecatedDir" | Out-File -FilePath $logFile -Append
}

# Create README in deprecated directory
$readmePath = Join-Path $deprecatedDir "README.md"
if (-not (Test-Path $readmePath)) {
    @"
# Deprecated Tests

This directory contains test files that have been deprecated in favor of the integrated testing functionality in `start_casestrainer.bat`.

## Why were these tests deprecated?

- The functionality of these tests has been integrated into the main `start_casestrainer.bat` script
- The new implementation provides better error handling and logging
- Centralized testing makes it easier to maintain and update tests

## How to run tests now

Simply run `start_casestrainer.bat` and the integrated tests will run automatically after the services start.

## File Information

| Original Path | Deprecation Date | Replaced By |
|--------------|------------------|-------------|
"@ | Out-File -FilePath $readmePath -Encoding utf8
}

# Process each test file
foreach ($testFile in $testFilesToDeprecate) {
    $sourcePath = Join-Path $rootDir $testFile
    $destPath = Join-Path $deprecatedDir $testFile
    
    if (Test-Path $sourcePath) {
        try {
            # Move the file to deprecated directory
            Move-Item -Path $sourcePath -Destination $destPath -Force
            
            # Create deprecation notice
            $deprecationNotice = "@echo off
:: ===================================================================
::  DEPRECATED: This test file has been deprecated
:: ===================================================================
::
:: This test file has been moved to the 'deprecated_tests' directory.
:: The functionality has been integrated into 'start_casestrainer.bat'.
::
:: To run tests, simply run 'start_casestrainer.bat' and the integrated
:: tests will run automatically after the services start.
::
:: Original file: deprecated_tests\$testFile
:: Deprecated on: $(Get-Date -Format 'yyyy-MM-dd')
:: ===================================================================

echo This test file has been deprecated. Please use 'start_casestrainer.bat' instead.
pause"
            
            $deprecationNotice | Out-File -FilePath $sourcePath -Encoding ascii
            
            # Log the action
            "Deprecated: $testFile -> $destPath" | Out-File -FilePath $logFile -Append
            Write-Host "Deprecated: $testFile" -ForegroundColor Yellow
        }
        catch {
            "ERROR processing $testFile : $_" | Out-File -FilePath $logFile -Append
            Write-Host "ERROR processing $testFile : $_" -ForegroundColor Red
        }
    }
    else {
        "Not found: $testFile" | Out-File -FilePath $logFile -Append
        Write-Host "Not found: $testFile" -ForegroundColor Gray
    }
}

# Show completion message
$completionMsg = @"

Deprecation complete!

Summary of actions:
- Moved redundant test files to 'deprecated_tests' directory
- Left deprecation notices in place of original files
- Created/updated README.md in deprecated_tests directory

A log of all actions has been saved to:
$logFile

You can now use 'start_casestrainer.bat' to run all tests automatically.
"@

Write-Host $completionMsg -ForegroundColor Green
