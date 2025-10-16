#Requires -Version 5.1
<#
.SYNOPSIS
    Phase 2: Reorganize remaining Python files in root directory
    
.DESCRIPTION
    Moves diagnose_*, cleanup_*, comprehensive_* and other files to appropriate locations.
    
.PARAMETER DryRun
    Show what would be moved without actually moving files
    
.EXAMPLE
    .\reorganize_phase2.ps1 -DryRun
#>

param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Phase 2: Codebase Reorganization" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Create backup
if (-not $DryRun) {
    $backupDir = "backup_phase2_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "[BACKUP] Creating backup in $backupDir..." -ForegroundColor Yellow
    
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Get-ChildItem -Path . -Filter "*.py" -File | ForEach-Object {
        Copy-Item $_.FullName -Destination $backupDir -Force
    }
    
    $count = (Get-ChildItem $backupDir | Measure-Object).Count
    Write-Host "  Backed up $count files" -ForegroundColor Green
}

# Create additional directories
$additionalDirs = @(
    "tests/integration",
    "scripts/maintenance",
    "scripts/analysis"
)

if (-not $DryRun) {
    Write-Host "`n[SETUP] Creating additional directories..." -ForegroundColor Yellow
    foreach ($dir in $additionalDirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "  Created $dir" -ForegroundColor Green
        }
    }
}

# Define file mappings
$fileMappings = @{
    "diagnose_*.py" = "tests/debug"
    "cleanup_*.py" = "scripts/maintenance"
    "comprehensive_*.py" = "tests/integration"
    "compare_*.py" = "tests/analysis"
    "count_*.py" = "scripts/analysis"
    "copy_*.py" = "scripts/misc"
}

# Files to keep in root (configuration/entry points)
$keepInRoot = @(
    "config.py",
    "setup.py",
    "__init__.py"
)

# Potentially deletable files (need review)
$reviewForDeletion = @(
    "temp_*.py",
    "old_*.py",
    "*_backup.py",
    "*_old.py"
)

$totalMoved = 0
$filesByType = @{}

Write-Host "`n[SCAN] Processing files by pattern..." -ForegroundColor Yellow

foreach ($pattern in $fileMappings.Keys) {
    $destination = $fileMappings[$pattern]
    $files = Get-ChildItem -Path . -Filter $pattern -File | Where-Object {
        $keepInRoot -notcontains $_.Name
    }
    
    if ($files) {
        Write-Host "`n  Pattern: $pattern" -ForegroundColor Cyan
        Write-Host "  Destination: $destination" -ForegroundColor Gray
        Write-Host "  Files found: $($files.Count)" -ForegroundColor Gray
        
        foreach ($file in $files) {
            $targetPath = Join-Path $destination $file.Name
            
            if ($DryRun) {
                Write-Host "    [DRY RUN] Would move: $($file.Name) -> $targetPath" -ForegroundColor Yellow
            } else {
                try {
                    # Create destination directory if needed
                    $destDir = Split-Path $targetPath -Parent
                    if (-not (Test-Path $destDir)) {
                        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                    }
                    
                    Move-Item -Path $file.FullName -Destination $targetPath -Force
                    Write-Host "    Moved: $($file.Name)" -ForegroundColor Green
                    $totalMoved++
                } catch {
                    Write-Host "    Error moving $($file.Name): $_" -ForegroundColor Red
                }
            }
        }
    }
}

# Scan for files that might be deletable
Write-Host "`n[REVIEW] Files that might be temporary/deletable:" -ForegroundColor Yellow
$possiblyDeletable = @()

foreach ($pattern in $reviewForDeletion) {
    $files = Get-ChildItem -Path . -Filter $pattern -File
    if ($files) {
        foreach ($file in $files) {
            $possiblyDeletable += $file
            Write-Host "  ? $($file.Name)" -ForegroundColor DarkYellow
        }
    }
}

# Identify remaining files in root
Write-Host "`n[ANALYSIS] Remaining Python files in root..." -ForegroundColor Yellow
$remaining = Get-ChildItem -Path . -Filter "*.py" -File | Where-Object {
    $keepInRoot -notcontains $_.Name
}

if ($remaining) {
    Write-Host "  Found $($remaining.Count) files still in root" -ForegroundColor Gray
    
    # Categorize remaining files
    $categories = @{
        "Production" = @()
        "Scripts" = @()
        "Unknown" = @()
    }
    
    foreach ($file in $remaining) {
        $content = Get-Content $file.FullName -First 20 -ErrorAction SilentlyContinue
        
        # Simple heuristic to categorize
        if ($content -match "class.*:|def.*:") {
            $categories["Production"] += $file.Name
        } elseif ($content -match "if __name__.*==.*__main__") {
            $categories["Scripts"] += $file.Name
        } else {
            $categories["Unknown"] += $file.Name
        }
    }
    
    Write-Host "`n  Categorization:" -ForegroundColor Cyan
    foreach ($category in $categories.Keys) {
        if ($categories[$category].Count -gt 0) {
            Write-Host "    $category ($($categories[$category].Count) files)" -ForegroundColor Gray
            $categories[$category] | Select-Object -First 5 | ForEach-Object {
                Write-Host "      - $_" -ForegroundColor DarkGray
            }
            if ($categories[$category].Count -gt 5) {
                Write-Host "      ... and $($categories[$category].Count - 5) more" -ForegroundColor DarkGray
            }
        }
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Phase 2 Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "`n[DRY RUN] No files were actually moved" -ForegroundColor Yellow
    Write-Host "Run without -DryRun to perform Phase 2" -ForegroundColor Yellow
} else {
    Write-Host "`nPhase 2 complete!" -ForegroundColor Green
    Write-Host "  Files moved: $totalMoved" -ForegroundColor Gray
    Write-Host "  Backup: $backupDir" -ForegroundColor Gray
}

Write-Host "`nStatistics:" -ForegroundColor Cyan
Write-Host "  Possibly deletable: $($possiblyDeletable.Count)" -ForegroundColor Gray
Write-Host "  Remaining in root: $($remaining.Count)" -ForegroundColor Gray

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "  1. Review remaining files" -ForegroundColor Gray
Write-Host "  2. Move production code to /src if needed" -ForegroundColor Gray
Write-Host "  3. Delete temporary files" -ForegroundColor Gray
Write-Host "  4. Test application: ./cslaunch" -ForegroundColor Gray
Write-Host "  5. Commit changes" -ForegroundColor Gray

Write-Host "`n"
