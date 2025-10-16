#Requires -Version 5.1
<#
.SYNOPSIS
    Update imports for files being moved to new locations
    
.DESCRIPTION
    Updates all import statements for files moving to new locations.
    CRITICAL: Run this BEFORE moving files!
    
.PARAMETER DryRun
    Show what would be changed without actually changing files
    
.PARAMETER Category
    Which category to update: utilities, models, integration, processors, or all
    
.EXAMPLE
    .\update_imports.ps1 -DryRun
    .\update_imports.ps1 -Category utilities
    .\update_imports.ps1 -Category all
#>

param(
    [switch]$DryRun,
    [ValidateSet('utilities', 'models', 'integration', 'processors', 'all')]
    [string]$Category = 'utilities'
)

$ErrorActionPreference = 'Stop'

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Import Statement Updater" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "[DRY RUN MODE - No changes will be made]" -ForegroundColor Yellow
}
Write-Host "========================================`n" -ForegroundColor Cyan

# Create backup
if (-not $DryRun) {
    $backupDir = "backup_imports_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "[BACKUP] Creating safety backup..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Get-ChildItem -Path . -Filter "*.py" -File | Copy-Item -Destination $backupDir -Force
    Write-Host "  Backup created: $backupDir`n" -ForegroundColor Green
}

# Define mappings for each category
$mappings = @{
    'utilities' = @{
        'cache_manager' = 'src.utils.cache_manager'
        'clear_cache' = 'src.utils.clear_cache'
        'clear_stuck_jobs' = 'src.utils.clear_stuck_jobs'
        'fixed_file_utils' = 'src.utils.fixed_file_utils'
        'nested_file_utils' = 'src.utils.nested_file_utils'
    }
    
    'models' = @{
        'database_manager' = 'src.models.database_manager'
        'init_database' = 'src.models.init_database'
        'migrate_citation_databases' = 'src.models.migrate_citation_databases'
    }
    
    'integration' = @{
        'api_integration' = 'src.integration.api_integration'
        'citation_integration' = 'src.integration.citation_integration'
        'enhanced_api_integration' = 'src.integration.enhanced_api_integration'
        'final_citation_integration' = 'src.integration.final_citation_integration'
        'final_integration' = 'src.integration.final_integration'
    }
    
    'processors' = @{
        'a_plus_citation_processor' = 'src.processors.a_plus_citation_processor'
        'document_based_hybrid_processor' = 'src.processors.document_based_hybrid_processor'
        'enhanced_case_extractor' = 'src.processors.enhanced_case_extractor'
        'enhanced_citation_extractor' = 'src.processors.enhanced_citation_extractor'
        'enhanced_citation_processor' = 'src.processors.enhanced_citation_processor'
        'enhanced_pdf_citation_extractor' = 'src.processors.enhanced_pdf_citation_extractor'
        'enhanced_unified_citation_processor_standalone' = 'src.processors.enhanced_unified_citation_processor_standalone'
        'final_citation_extractor' = 'src.processors.final_citation_extractor'
        'hybrid_citation_processor' = 'src.processors.hybrid_citation_processor'
        'modify_processor' = 'src.processors.modify_processor'
        'pdf_citation_extractor' = 'src.processors.pdf_citation_extractor'
        'pdf_processor' = 'src.processors.pdf_processor'
        'wl_extractor' = 'src.processors.wl_extractor'
    }
}

# Select which mappings to use
$selectedMappings = @{}
if ($Category -eq 'all') {
    foreach ($cat in $mappings.Keys) {
        foreach ($key in $mappings[$cat].Keys) {
            $selectedMappings[$key] = $mappings[$cat][$key]
        }
    }
} else {
    $selectedMappings = $mappings[$Category]
}

Write-Host "Updating imports for category: $Category" -ForegroundColor Yellow
Write-Host "Modules to update: $($selectedMappings.Keys.Count)`n" -ForegroundColor Gray

# Exclude directories
$excludeDirs = @(
    ".venv",
    "venv",
    "node_modules",
    ".git",
    "__pycache__",
    "backup_*",
    "archive*",
    "casestrainer-vue*"
)

# Get all Python files
$pyFiles = Get-ChildItem -Path . -Filter "*.py" -Recurse -ErrorAction SilentlyContinue |
            Where-Object {
                $exclude = $false
                foreach ($dir in $excludeDirs) {
                    if ($_.FullName -like "*\$dir\*") {
                        $exclude = $true
                        break
                    }
                }
                -not $exclude
            }

Write-Host "Scanning $($pyFiles.Count) Python files...`n" -ForegroundColor Gray

$filesChanged = 0
$totalReplacements = 0

foreach ($file in $pyFiles) {
    $relativePath = $file.FullName -replace [regex]::Escape((Get-Location).Path), "."
    $content = Get-Content $file.FullName -Raw
    $originalContent = $content
    $fileChanges = 0
    
    foreach ($oldModule in $selectedMappings.Keys) {
        $newModule = $selectedMappings[$oldModule]
        
        # Pattern 1: import module
        $pattern1 = "import $oldModule"
        $replacement1 = "from $newModule import *"
        if ($content -match [regex]::Escape($pattern1)) {
            $content = $content -replace [regex]::Escape($pattern1), $replacement1
            $fileChanges++
        }
        
        # Pattern 2: from module import ...
        $pattern2 = "from $oldModule import"
        $replacement2 = "from $newModule import"
        if ($content -match [regex]::Escape($pattern2)) {
            $content = $content -replace [regex]::Escape($pattern2), $replacement2
            $fileChanges++
        }
        
        # Pattern 3: from .module import ...
        $pattern3 = "from \.$oldModule import"
        $replacement3 = "from $newModule import"
        if ($content -match [regex]::Escape($pattern3)) {
            $content = $content -replace [regex]::Escape($pattern3), $replacement3
            $fileChanges++
        }
        
        # Pattern 4: import .module
        $pattern4 = "import \.$oldModule"
        $replacement4 = "from $newModule import *"
        if ($content -match [regex]::Escape($pattern4)) {
            $content = $content -replace [regex]::Escape($pattern4), $replacement4
            $fileChanges++
        }
    }
    
    if ($content -ne $originalContent) {
        $filesChanged++
        $totalReplacements += $fileChanges
        
        if ($DryRun) {
            Write-Host "[DRY RUN] Would update: $relativePath ($fileChanges changes)" -ForegroundColor Yellow
        } else {
            Set-Content -Path $file.FullName -Value $content -NoNewline
            Write-Host "Updated: $relativePath ($fileChanges changes)" -ForegroundColor Green
        }
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "[DRY RUN] No files were actually modified" -ForegroundColor Yellow
    Write-Host "  Files that would be changed: $filesChanged" -ForegroundColor White
    Write-Host "  Total replacements: $totalReplacements`n" -ForegroundColor White
    
    Write-Host "NEXT STEPS:" -ForegroundColor Cyan
    Write-Host "  1. Review the changes above" -ForegroundColor Gray
    Write-Host "  2. Run without -DryRun to apply changes" -ForegroundColor Gray
    Write-Host "  3. Test: ./cslaunch" -ForegroundColor Yellow
    Write-Host "  4. If successful, move the files" -ForegroundColor Gray
    Write-Host "  5. Test again: ./cslaunch" -ForegroundColor Yellow
} else {
    Write-Host "Import updates complete!" -ForegroundColor Green
    Write-Host "  Files modified: $filesChanged" -ForegroundColor White
    Write-Host "  Total replacements: $totalReplacements" -ForegroundColor White
    Write-Host "  Backup: $backupDir`n" -ForegroundColor Gray
    
    Write-Host "CRITICAL NEXT STEPS:" -ForegroundColor Red
    Write-Host "  1. TEST IMMEDIATELY: ./cslaunch" -ForegroundColor Yellow
    Write-Host "  2. Check for import errors in logs" -ForegroundColor Yellow
    Write-Host "  3. If successful, NOW move the files" -ForegroundColor Green
    Write-Host "  4. Test again after moving: ./cslaunch" -ForegroundColor Yellow
    Write-Host "  5. Commit if all tests pass`n" -ForegroundColor Green
}

Write-Host ""
