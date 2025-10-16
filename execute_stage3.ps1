#Requires -Version 5.1
<#
.SYNOPSIS
    Execute Stage 3: Move Production Code to src/
    
.DESCRIPTION
    Carefully moves production code to proper locations in src/.
    Tests after EACH category to ensure nothing breaks.
    
.PARAMETER DryRun
    Show what would be moved
    
.PARAMETER Category
    Move only specific category: utilities, models, integration, processors, or all
    
.EXAMPLE
    .\execute_stage3.ps1 -DryRun
    .\execute_stage3.ps1 -Category utilities
    .\execute_stage3.ps1
#>

param(
    [switch]$DryRun,
    [ValidateSet('utilities', 'models', 'integration', 'processors', 'all')]
    [string]$Category = 'all'
)

$ErrorActionPreference = 'Stop'

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Stage 3: Move Production Code" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
Write-Host "WARNING: This moves production code" -ForegroundColor Yellow
Write-Host "         Test AFTER EACH CATEGORY!`n" -ForegroundColor Yellow

# Create backup
if (-not $DryRun) {
    $backupDir = "backup_stage3_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "[BACKUP] Creating safety backup..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Get-ChildItem -Path . -Filter "*.py" -File | Copy-Item -Destination $backupDir -Force
    Write-Host "  Backup created: $backupDir`n" -ForegroundColor Green
}

# Define categories
$categories = @{
    'utilities' = @{
        'destination' = 'src/utils'
        'files' = @(
            "cache_manager.py",
            "clear_cache.py",
            "clear_stuck_jobs.py",
            "fixed_file_utils.py",
            "nested_file_utils.py"
        )
        'description' = 'Utility functions (LOWEST RISK)'
    }
    
    'models' = @{
        'destination' = 'src/models'
        'files' = @(
            "database_manager.py",
            "init_database.py",
            "migrate_citation_databases.py"
        )
        'description' = 'Data models and database'
    }
    
    'integration' = @{
        'destination' = 'src/integration'
        'files' = @(
            "api_integration.py",
            "citation_integration.py",
            "enhanced_api_integration.py",
            "final_citation_integration.py",
            "final_integration.py"
        )
        'description' = 'Integration code'
    }
    
    'processors' = @{
        'destination' = 'src/processors'
        'files' = @(
            "a_plus_citation_processor.py",
            "document_based_hybrid_processor.py",
            "enhanced_case_extractor.py",
            "enhanced_citation_extractor.py",
            "enhanced_citation_processor.py",
            "enhanced_pdf_citation_extractor.py",
            "enhanced_unified_citation_processor_standalone.py",
            "final_citation_extractor.py",
            "hybrid_citation_processor.py",
            "modify_processor.py",
            "pdf_citation_extractor.py",
            "pdf_processor.py",
            "wl_extractor.py"
        )
        'description' = 'Citation processors (HIGHEST RISK - Test carefully!)'
    }
}

function Move-Category {
    param(
        [string]$CategoryName,
        [hashtable]$CategoryInfo
    )
    
    Write-Host "`n[CATEGORY: $CategoryName]" -ForegroundColor Cyan
    Write-Host "  $($CategoryInfo['description'])" -ForegroundColor Gray
    Write-Host "  Destination: $($CategoryInfo['destination'])" -ForegroundColor Gray
    Write-Host "  Files: $($CategoryInfo['files'].Count)`n" -ForegroundColor Gray
    
    # Create destination
    if (-not (Test-Path $CategoryInfo['destination']) -and -not $DryRun) {
        New-Item -ItemType Directory -Path $CategoryInfo['destination'] -Force | Out-Null
        Write-Host "  Created: $($CategoryInfo['destination'])" -ForegroundColor Green
    }
    
    $moved = 0
    foreach ($file in $CategoryInfo['files']) {
        if (Test-Path $file) {
            $targetPath = Join-Path $CategoryInfo['destination'] $file
            
            if ($DryRun) {
                Write-Host "  [DRY RUN] Would move: $file" -ForegroundColor Yellow
            } else {
                try {
                    Move-Item $file $targetPath -Force
                    Write-Host "  Moved: $file" -ForegroundColor Green
                    $moved++
                } catch {
                    Write-Host "  Error: $file - $_" -ForegroundColor Red
                }
            }
        } else {
            Write-Host "  Not found: $file" -ForegroundColor DarkGray
        }
    }
    
    if ($moved -gt 0 -and -not $DryRun) {
        Write-Host "`n  CRITICAL: TEST NOW!" -ForegroundColor Red
        Write-Host "  Run: ./cslaunch" -ForegroundColor Yellow
        $response = Read-Host "  Did test pass? (y/n/q=quit)"
        
        if ($response -eq 'q' -or $response -eq 'n') {
            Write-Host "`n  STOPPED: Test failed or user quit" -ForegroundColor Red
            Write-Host "  To restore: Copy-Item -Path $backupDir\* -Destination . -Force" -ForegroundColor Yellow
            exit 1
        }
        
        Write-Host "  Great! Continuing...`n" -ForegroundColor Green
    }
    
    return $moved
}

$totalMoved = 0

if ($Category -eq 'all') {
    # Move in order of risk (lowest to highest)
    $order = @('utilities', 'models', 'integration', 'processors')
    
    foreach ($cat in $order) {
        $moved = Move-Category -CategoryName $cat -CategoryInfo $categories[$cat]
        $totalMoved += $moved
    }
} else {
    if ($categories.ContainsKey($Category)) {
        $moved = Move-Category -CategoryName $Category -CategoryInfo $categories[$Category]
        $totalMoved += $moved
    } else {
        Write-Host "Unknown category: $Category" -ForegroundColor Red
        exit 1
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "[DRY RUN] No files were moved" -ForegroundColor Yellow
} else {
    Write-Host "Stage 3 Complete!" -ForegroundColor Green
    Write-Host "  Files moved: $totalMoved" -ForegroundColor Gray
    Write-Host "  Backup: $backupDir`n" -ForegroundColor Gray
    
    Write-Host "NEXT STEPS:" -ForegroundColor Cyan
    Write-Host "  1. FINAL TEST: ./cslaunch AND process a document" -ForegroundColor Yellow
    Write-Host "  2. If successful, commit: git add . && git commit -m 'Stage 3: Move production code to src/'" -ForegroundColor Gray
    Write-Host "  3. Continue to Stage 4: Manual review of remaining files`n" -ForegroundColor Gray
}

Write-Host ""
