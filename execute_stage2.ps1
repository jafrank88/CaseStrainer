#Requires -Version 5.1
<#
.SYNOPSIS
    Execute Stage 2: Move Entry Points and Scripts
    
.DESCRIPTION
    Moves entry point scripts and analysis tools to appropriate directories.
    
.PARAMETER DryRun
    Show what would be moved without actually moving
    
.EXAMPLE
    .\execute_stage2.ps1 -DryRun
    .\execute_stage2.ps1
#>

param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Stage 2: Move Scripts & Entry Points" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Create backup
if (-not $DryRun) {
    $backupDir = "backup_stage2_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "[BACKUP] Creating safety backup..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Get-ChildItem -Path . -Filter "*.py" -File | Copy-Item -Destination $backupDir -Force
    Write-Host "  Backup created: $backupDir`n" -ForegroundColor Green
}

# Ensure directories exist
$directories = @("scripts", "scripts/analysis")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir) -and -not $DryRun) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Green
    }
}

# Define moves
$moves = @{
    "Entry Points" = @{
        'destination' = 'scripts'
        'files' = @(
            "launch_app.py",
            "run.py",
            "run_app.py",
            "run_test_with_output.py",
            "start_app.py",
            "start_backend.py",
            "start_flask.py",
            "start_server.py",
            "start_worker.py",
            "build_and_run.py",
            "do_cleanup.py"
        )
    }
    
    "Analysis Tools" = @{
        'destination' = 'scripts/analysis'
        'files' = @(
            "complex_citation_analyzer.py",
            "pdf_structure_analysis.py",
            "review_codebase_comprehensive.py",
            "simple_reporter_analysis.py"
        )
    }
}

# Files to delete (one-off analysis)
$deleteFiles = @(
    "evaluate_extraction_with_toa.py",
    "evaluate_production_results.py",
    "examine_toa_context.py",
    "analyze_remaining_files.py",
    "critical_fixes_summary.py",
    "diagnosis_report.py"
)

$totalMoved = 0
$totalDeleted = 0

# Move files
foreach ($category in $moves.Keys) {
    $categoryInfo = $moves[$category]
    $destination = $categoryInfo['destination']
    $files = $categoryInfo['files']
    
    Write-Host "`n[$category -> $destination/]" -ForegroundColor Cyan
    Write-Host "  Files: $($files.Count)`n" -ForegroundColor Gray
    
    foreach ($file in $files) {
        if (Test-Path $file) {
            $targetPath = Join-Path $destination $file
            
            if ($DryRun) {
                Write-Host "  [DRY RUN] Would move: $file -> $targetPath" -ForegroundColor Yellow
            } else {
                try {
                    Move-Item $file $targetPath -Force
                    Write-Host "  Moved: $file" -ForegroundColor Green
                    $totalMoved++
                } catch {
                    Write-Host "  Error moving $file : $_" -ForegroundColor Red
                }
            }
        } else {
            Write-Host "  Not found: $file" -ForegroundColor DarkGray
        }
    }
}

# Delete files
Write-Host "`n[Delete One-Off Analysis Files]" -ForegroundColor Cyan
Write-Host "  Files: $($deleteFiles.Count)`n" -ForegroundColor Gray

foreach ($file in $deleteFiles) {
    if (Test-Path $file) {
        if ($DryRun) {
            Write-Host "  [DRY RUN] Would delete: $file" -ForegroundColor Yellow
        } else {
            try {
                Remove-Item $file -Force
                Write-Host "  Deleted: $file" -ForegroundColor Green
                $totalDeleted++
            } catch {
                Write-Host "  Error deleting $file : $_" -ForegroundColor Red
            }
        }
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "[DRY RUN] No files were actually moved or deleted" -ForegroundColor Yellow
} else {
    Write-Host "Stage 2 Complete!" -ForegroundColor Green
    Write-Host "  Files moved: $totalMoved" -ForegroundColor Gray
    Write-Host "  Files deleted: $totalDeleted" -ForegroundColor Gray
    Write-Host "  Backup: $backupDir`n" -ForegroundColor Gray
    
    Write-Host "NEXT STEPS:" -ForegroundColor Cyan
    Write-Host "  1. TEST APPLICATION: ./cslaunch" -ForegroundColor Yellow
    Write-Host "  2. If successful, commit: git add . && git commit -m 'Stage 2: Move scripts and entry points'" -ForegroundColor Gray
    Write-Host "  3. Continue to Stage 3: .\execute_stage3.ps1`n" -ForegroundColor Gray
}

Write-Host ""
