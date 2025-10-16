#Requires -Version 5.1
<#
.SYNOPSIS
    Phase 3: Move production code to /src with safety checks
    
.DESCRIPTION
    Carefully moves production Python files to appropriate locations in /src.
    This phase is HIGHER RISK - test thoroughly after each category.
    
.PARAMETER DryRun
    Show what would be moved without actually moving files
    
.PARAMETER Category
    Move only a specific category: processors, utilities, models, services, api, or all
    
.EXAMPLE
    .\reorganize_phase3.ps1 -DryRun
    .\reorganize_phase3.ps1 -Category processors
#>

param(
    [switch]$DryRun,
    [ValidateSet('processors', 'utilities', 'models', 'services', 'api', 'entry_points', 'all')]
    [string]$Category = 'all'
)

$ErrorActionPreference = 'Stop'

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Phase 3: Production Code Refactoring" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
Write-Host "WARNING: This phase modifies production code" -ForegroundColor Yellow
Write-Host "         Test thoroughly after each step!`n" -ForegroundColor Yellow

# Create backup
if (-not $DryRun) {
    $backupDir = "backup_phase3_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "[BACKUP] Creating backup in $backupDir..." -ForegroundColor Yellow
    
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Get-ChildItem -Path . -Filter "*.py" -File | ForEach-Object {
        Copy-Item $_.FullName -Destination $backupDir -Force
    }
    
    $count = (Get-ChildItem $backupDir | Measure-Object).Count
    Write-Host "  Backed up $count files`n" -ForegroundColor Green
}

# Define categories with specific file patterns
$categories = @{
    'processors' = @{
        'patterns' = @('*_processor*.py', '*_extractor*.py', '*_verifier*.py', '*_clusterer*.py')
        'destination' = 'src/processors'
        'description' = 'Citation processors, extractors, verifiers'
    }
    'utilities' = @{
        'patterns' = @('*_utils*.py', '*_helper*.py', 'cache_*.py', 'clear_*.py')
        'destination' = 'src/utils'
        'description' = 'Utility functions and helpers'
    }
    'models' = @{
        'patterns' = @('*_model*.py', 'database_*.py', 'citation_integration.py')
        'destination' = 'src/models'
        'description' = 'Data models and database'
    }
    'services' = @{
        'patterns' = @('*_service*.py', '*_manager*.py', 'api_integration.py')
        'destination' = 'src/services'
        'description' = 'Business logic services'
    }
    'api' = @{
        'patterns' = @('*_api*.py', '*_endpoint*.py')
        'destination' = 'src/api'
        'description' = 'API endpoints and handlers'
    }
    'entry_points' = @{
        'patterns' = @('run*.py', 'start_*.py', 'launch_*.py', 'build_*.py')
        'destination' = 'scripts'
        'description' = 'Application entry points'
    }
}

# Files to NEVER move (critical)
$neverMove = @(
    'config.py',
    'setup.py',
    '__init__.py',
    'app.py',
    'app_final.py',
    'app_final_vue.py',
    'wsgi.py'
)

# Create directories
if (-not $DryRun) {
    Write-Host "[SETUP] Creating src directories..." -ForegroundColor Yellow
    foreach ($cat in $categories.Keys) {
        $dest = $categories[$cat]['destination']
        if (-not (Test-Path $dest)) {
            New-Item -ItemType Directory -Path $dest -Force | Out-Null
            Write-Host "  Created $dest" -ForegroundColor Green
        }
    }
    Write-Host ""
}

function Move-FilesToCategory {
    param(
        [string]$CategoryName,
        [hashtable]$CategoryInfo
    )
    
    Write-Host "`n[CATEGORY: $CategoryName]" -ForegroundColor Cyan
    Write-Host "  Description: $($CategoryInfo['description'])" -ForegroundColor Gray
    Write-Host "  Destination: $($CategoryInfo['destination'])`n" -ForegroundColor Gray
    
    $movedCount = 0
    $patterns = $CategoryInfo['patterns']
    $destination = $CategoryInfo['destination']
    
    foreach ($pattern in $patterns) {
        $files = Get-ChildItem -Path . -Filter $pattern -File | Where-Object {
            $neverMove -notcontains $_.Name -and
            $_.Name -notlike "test_*" -and
            $_.Name -notlike "validate_*" -and
            $_.Name -notlike "analyze_*"
        }
        
        if ($files) {
            Write-Host "  Pattern: $pattern ($($files.Count) files)" -ForegroundColor DarkCyan
            
            foreach ($file in $files) {
                $targetPath = Join-Path $destination $file.Name
                
                if ($DryRun) {
                    Write-Host "    [DRY RUN] $($file.Name) -> $targetPath" -ForegroundColor Yellow
                } else {
                    try {
                        Move-Item -Path $file.FullName -Destination $targetPath -Force
                        Write-Host "    Moved: $($file.Name)" -ForegroundColor Green
                        $movedCount++
                    } catch {
                        Write-Host "    ERROR: $($file.Name) - $_" -ForegroundColor Red
                    }
                }
            }
        }
    }
    
    return $movedCount
}

# Process categories
$totalMoved = 0

if ($Category -eq 'all') {
    foreach ($catName in $categories.Keys) {
        $moved = Move-FilesToCategory -CategoryName $catName -CategoryInfo $categories[$catName]
        $totalMoved += $moved
        
        if (-not $DryRun -and $moved -gt 0) {
            Write-Host "`n  PAUSE: $moved files moved in category '$catName'" -ForegroundColor Yellow
            Write-Host "         Test the application before continuing!" -ForegroundColor Yellow
            $response = Read-Host "         Continue to next category? (y/n)"
            
            if ($response -ne 'y' -and $response -ne 'Y') {
                Write-Host "`n[STOPPED] User requested stop. You can resume with -Category parameter." -ForegroundColor Yellow
                break
            }
        }
    }
} else {
    if ($categories.ContainsKey($Category)) {
        $moved = Move-FilesToCategory -CategoryName $Category -CategoryInfo $categories[$Category]
        $totalMoved += $moved
    } else {
        Write-Host "[ERROR] Unknown category: $Category" -ForegroundColor Red
        exit 1
    }
}

# Analyze remaining files
Write-Host "`n[ANALYSIS] Remaining files in root..." -ForegroundColor Yellow
$remaining = Get-ChildItem -Path . -Filter "*.py" -File | Where-Object {
    $neverMove -notcontains $_.Name
}

if ($remaining) {
    Write-Host "  Remaining: $($remaining.Count) files`n" -ForegroundColor Gray
    
    # Show first 10
    $remaining | Select-Object -First 10 | ForEach-Object {
        Write-Host "    - $($_.Name)" -ForegroundColor DarkGray
    }
    
    if ($remaining.Count -gt 10) {
        Write-Host "    ... and $($remaining.Count - 10) more" -ForegroundColor DarkGray
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Phase 3 Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "[DRY RUN] No files were actually moved" -ForegroundColor Yellow
    Write-Host "Run without -DryRun to perform Phase 3`n" -ForegroundColor Yellow
} else {
    Write-Host "Phase 3 progress:" -ForegroundColor Green
    Write-Host "  Files moved: $totalMoved" -ForegroundColor Gray
    if ($totalMoved -gt 0) {
        Write-Host "  Backup: $backupDir`n" -ForegroundColor Gray
    }
}

Write-Host "CRITICAL: Test the application NOW!" -ForegroundColor Red
Write-Host "  Run: ./cslaunch`n" -ForegroundColor Yellow

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. TEST APPLICATION (./cslaunch)" -ForegroundColor Gray
Write-Host "  2. Check for import errors" -ForegroundColor Gray
Write-Host "  3. If broken, restore from backup" -ForegroundColor Gray
Write-Host "  4. Update imports if needed" -ForegroundColor Gray
Write-Host "  5. Move to next category if successful`n" -ForegroundColor Gray

if (-not $DryRun) {
    Write-Host "To restore if something breaks:" -ForegroundColor Yellow
    Write-Host ("  Copy-Item -Path " + $backupDir + "\* -Destination . -Force`n") -ForegroundColor Gray
}

Write-Host ""
