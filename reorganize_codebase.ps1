#Requires -Version 5.1
<#
.SYNOPSIS
    Reorganize CaseStrainer codebase - Move test and analysis files to proper directories
    
.DESCRIPTION
    This script organizes the codebase by moving test/analysis files from root to appropriate directories.
    Creates backups before moving anything.
    
.PARAMETER DryRun
    Show what would be moved without actually moving files
    
.PARAMETER SkipBackup
    Skip creating backup (not recommended)
    
.EXAMPLE
    .\reorganize_codebase.ps1 -DryRun
    
.EXAMPLE
    .\reorganize_codebase.ps1
#>

param(
    [switch]$DryRun,
    [switch]$SkipBackup
)

$ErrorActionPreference = 'Stop'

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CaseStrainer Codebase Reorganization" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "src") -or -not (Test-Path "cslaunch.ps1")) {
    Write-Host "[ERROR] Not in CaseStrainer root directory" -ForegroundColor Red
    Write-Host "  Please run this from d:\dev\casestrainer\" -ForegroundColor Yellow
    exit 1
}

# Create backup if not skipped
if (-not $SkipBackup -and -not $DryRun) {
    $backupDir = "backup_reorganization_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "[BACKUP] Creating backup in $backupDir..." -ForegroundColor Yellow
    
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    
    # Copy all Python files to backup
    Get-ChildItem -Path . -Filter "*.py" -File | ForEach-Object {
        Copy-Item $_.FullName -Destination $backupDir -Force
    }
    
    Write-Host "  ✅ Backed up $(Get-ChildItem $backupDir | Measure-Object | Select-Object -ExpandProperty Count) files" -ForegroundColor Green
}

# Define target directories
$dirs = @{
    "tests" = @{
        "unit" = @()
        "integration" = @()
        "validation" = @()
        "analysis" = @()
        "debug" = @()
    }
}

# Create directory structure
if (-not $DryRun) {
    Write-Host "`n[SETUP] Creating directory structure..." -ForegroundColor Yellow
    
    foreach ($testType in $dirs["tests"].Keys) {
        $path = Join-Path "tests" $testType
        if (-not (Test-Path $path)) {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
            Write-Host "  ✅ Created $path" -ForegroundColor Green
        }
    }
}

# Define file patterns and their destinations
$fileMapping = @{
    "test_*.py" = "tests/unit"
    "validate_*.py" = "tests/validation"
    "analyze_*.py" = "tests/analysis"
    "check_*.py" = "tests/debug"
    "debug_*.py" = "tests/debug"
}

# Special cases - files to keep in root
$keepInRoot = @(
    "setup.py"
    "test.py"  # If it's a main test runner
)

Write-Host "`n[SCAN] Scanning for files to move..." -ForegroundColor Yellow

$totalMoved = 0
$filesByType = @{}

foreach ($pattern in $fileMapping.Keys) {
    $destination = $fileMapping[$pattern]
    $files = Get-ChildItem -Path . -Filter $pattern -File | Where-Object {
        $keepInRoot -notcontains $_.Name
    }
    
    if ($files) {
        $filesByType[$pattern] = @{
            "files" = $files
            "destination" = $destination
        }
        
        Write-Host "`n  Pattern: $pattern" -ForegroundColor Cyan
        Write-Host "  Destination: $destination" -ForegroundColor Gray
        Write-Host "  Files found: $($files.Count)" -ForegroundColor Gray
        
        foreach ($file in $files) {
            $targetPath = Join-Path $destination $file.Name
            
            if ($DryRun) {
                Write-Host "    [DRY RUN] Would move: $($file.Name) -> $targetPath" -ForegroundColor Yellow
            } else {
                try {
                    Move-Item -Path $file.FullName -Destination $targetPath -Force
                    Write-Host "    ✅ Moved: $($file.Name)" -ForegroundColor Green
                    $totalMoved++
                } catch {
                    Write-Host "    ❌ Error moving $($file.Name): $_" -ForegroundColor Red
                }
            }
        }
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "`n[DRY RUN] No files were actually moved" -ForegroundColor Yellow
    Write-Host "Run without -DryRun to perform the reorganization" -ForegroundColor Yellow
} else {
    Write-Host "`n✅ Reorganization complete!" -ForegroundColor Green
    Write-Host "  Files moved: $totalMoved" -ForegroundColor Gray
    
    if (-not $SkipBackup) {
        Write-Host "  Backup created: $backupDir" -ForegroundColor Gray
    }
}

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "  1. Test the application: ./cslaunch" -ForegroundColor Gray
Write-Host "  2. Update imports if needed" -ForegroundColor Gray
Write-Host "  3. Run tests to verify everything works" -ForegroundColor Gray
Write-Host "  4. Commit changes to git" -ForegroundColor Gray

if (-not $DryRun -and -not $SkipBackup) {
    Write-Host "`nIf something breaks:" -ForegroundColor Yellow
    Write-Host ("  Restore from: " + $backupDir) -ForegroundColor Gray
}

Write-Host "`n"
