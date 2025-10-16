#Requires -Version 5.1
<#
.SYNOPSIS
    Execute Stage 1: Quick Wins - Delete obvious test and old files
    
.DESCRIPTION
    Safely deletes deprecated files and obvious test files with confirmation.
    Creates backup before any deletions.
    
.PARAMETER DryRun
    Show what would be deleted without actually deleting
    
.PARAMETER Auto
    Auto-confirm deletions (use with caution!)
    
.EXAMPLE
    .\execute_stage1.ps1 -DryRun
    .\execute_stage1.ps1
#>

param(
    [switch]$DryRun,
    [switch]$Auto
)

$ErrorActionPreference = 'Stop'

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Stage 1: Quick Wins - Delete Old Files" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Create backup
if (-not $DryRun) {
    $backupDir = "backup_stage1_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "[BACKUP] Creating safety backup..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Get-ChildItem -Path . -Filter "*.py" -File | Copy-Item -Destination $backupDir -Force
    Write-Host "  Backup created: $backupDir`n" -ForegroundColor Green
}

# Define files to delete by category
$categories = @{
    "Deprecated" = @(
        "verify_no_deprecated_calls.py"
    )
    
    "Simple Tests" = @(
        "simple_endpoint_test.py",
        "simple_name_test.py",
        "simple_pdf_routing_test.py",
        "simple_pdf_test.py",
        "simple_pdf_wl_test.py",
        "simple_test.py",
        "simple_url_test.py",
        "simple_wl_test.py",
        "simple_extract.py",
        "simple_upload.py",
        "simple_url_check.py",
        "simple_cl_verify.py",
        "simple_clustering_debug.py",
        "simple_context_check.py",
        "simple_server.py"
    )
    
    "Quick Tests" = @(
        "quick_pdf_test.py",
        "quick_test.py",
        "quick_test_24-2626.py",
        "quick_test_direct.py",
        "quick_url_test.py",
        "quick_wl_test.py"
    )
    
    "Direct Tests" = @(
        "direct_extraction_test.py",
        "direct_extraction_test_fixed.py",
        "direct_test.py"
    )
    
    "Final/Focused Tests" = @(
        "final_clustering_fix.py",
        "final_contamination_test.py",
        "final_test_summary.py",
        "final_verification_test.py",
        "get_unverified_citations_final.py",
        "focused_url_test.py",
        "focused_wl_test.py",
        "minimal_wl_test.py"
    )
    
    "Old Analysis" = @(
        "crosscontamination_analysis.py",
        "date_overwrite_analysis.py",
        "document_vs_network_analysis.py",
        "critical_issues_analysis.py",
        "deprecation_analysis.py",
        "review_mismatches_report.py"
    )
}

$totalDeleted = 0

foreach ($category in $categories.Keys) {
    $files = $categories[$category]
    
    Write-Host "`n[CATEGORY: $category]" -ForegroundColor Cyan
    Write-Host "  Files to delete: $($files.Count)`n" -ForegroundColor Gray
    
    foreach ($file in $files) {
        if (Test-Path $file) {
            if ($DryRun) {
                Write-Host "  [DRY RUN] Would delete: $file" -ForegroundColor Yellow
            } else {
                if (-not $Auto) {
                    $response = Read-Host "  Delete $file ? (y/n/a=yes to all/q=quit)"
                    if ($response -eq 'q') {
                        Write-Host "`nStopped by user" -ForegroundColor Yellow
                        exit 0
                    }
                    if ($response -eq 'a') {
                        $Auto = $true
                    }
                    if ($response -ne 'y' -and $response -ne 'a') {
                        Write-Host "  Skipped: $file" -ForegroundColor Gray
                        continue
                    }
                }
                
                try {
                    Remove-Item $file -Force
                    Write-Host "  Deleted: $file" -ForegroundColor Green
                    $totalDeleted++
                } catch {
                    Write-Host "  Error deleting $file : $_" -ForegroundColor Red
                }
            }
        } else {
            Write-Host "  Not found: $file" -ForegroundColor DarkGray
        }
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "[DRY RUN] No files were actually deleted" -ForegroundColor Yellow
    Write-Host "Run without -DryRun to execute deletions`n" -ForegroundColor Yellow
} else {
    Write-Host "Stage 1 Complete!" -ForegroundColor Green
    Write-Host "  Files deleted: $totalDeleted" -ForegroundColor Gray
    if ($totalDeleted -gt 0) {
        Write-Host "  Backup: $backupDir`n" -ForegroundColor Gray
    }
    
    Write-Host "NEXT STEPS:" -ForegroundColor Cyan
    Write-Host "  1. TEST APPLICATION: ./cslaunch" -ForegroundColor Yellow
    Write-Host "  2. If successful, commit: git add . && git commit -m 'Stage 1: Delete old test files'" -ForegroundColor Gray
    Write-Host "  3. Continue to Stage 2: .\execute_stage2.ps1`n" -ForegroundColor Gray
}

Write-Host ""
