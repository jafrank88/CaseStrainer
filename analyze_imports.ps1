#Requires -Version 5.1
<#
.SYNOPSIS
    Analyze import dependencies for files to be moved
    
.DESCRIPTION
    Scans the codebase to find all imports of specified files.
    Creates a report showing which files import what, so we can
    update imports BEFORE moving files.
    
.PARAMETER TargetFiles
    Array of files to analyze (e.g., "cache_manager.py")
    
.EXAMPLE
    .\analyze_imports.ps1
    .\analyze_imports.ps1 -TargetFiles @("cache_manager.py", "clear_cache.py")
#>

param(
    [string[]]$TargetFiles = @(
        "cache_manager.py",
        "clear_cache.py",
        "clear_stuck_jobs.py",
        "fixed_file_utils.py",
        "nested_file_utils.py"
    )
)

$ErrorActionPreference = 'Stop'

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Import Dependency Analyzer" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Results storage
$results = @{}
$totalImports = 0

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

Write-Host "Analyzing imports for $($TargetFiles.Count) files...`n" -ForegroundColor Yellow

foreach ($targetFile in $TargetFiles) {
    $moduleName = [System.IO.Path]::GetFileNameWithoutExtension($targetFile)
    
    Write-Host "[$moduleName]" -ForegroundColor Cyan
    
    $importers = @()
    
    # Search for imports
    $patterns = @(
        "import $moduleName",
        "from $moduleName import",
        "from .$moduleName import",
        "import .$moduleName"
    )
    
    foreach ($pattern in $patterns) {
        try {
            $found = Get-ChildItem -Path . -Filter "*.py" -Recurse -ErrorAction SilentlyContinue |
                     Where-Object {
                         $exclude = $false
                         foreach ($dir in $excludeDirs) {
                             if ($_.FullName -like "*\$dir\*") {
                                 $exclude = $true
                                 break
                             }
                         }
                         -not $exclude
                     } |
                     Select-String -Pattern $pattern -SimpleMatch |
                     ForEach-Object {
                         @{
                             File = $_.Path
                             Line = $_.LineNumber
                             Text = $_.Line.Trim()
                         }
                     }
            
            $importers += $found
        } catch {
            # Ignore errors
        }
    }
    
    # Remove duplicates
    $uniqueImporters = $importers | 
                       Group-Object -Property File | 
                       ForEach-Object {
                           $file = $_.Name
                           $lines = ($_.Group | Select-Object -ExpandProperty Line) -join ", "
                           $text = ($_.Group | Select-Object -First 1).Text
                           
                           @{
                               File = $file
                               Lines = $lines
                               Text = $text
                           }
                       }
    
    $results[$targetFile] = $uniqueImporters
    $totalImports += $uniqueImporters.Count
    
    if ($uniqueImporters.Count -eq 0) {
        Write-Host "  No imports found (safe to move!)" -ForegroundColor Green
    } else {
        Write-Host "  Found in $($uniqueImporters.Count) file(s):" -ForegroundColor Yellow
        
        foreach ($imp in $uniqueImporters | Sort-Object File) {
            $relativePath = $imp.File -replace [regex]::Escape((Get-Location).Path), "."
            Write-Host "    $relativePath (line $($imp.Lines))" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Total files analyzed: $($TargetFiles.Count)" -ForegroundColor White
Write-Host "Total import locations found: $totalImports`n" -ForegroundColor White

# Files by import count
Write-Host "Import Count by File:" -ForegroundColor Yellow
foreach ($target in $results.Keys | Sort-Object { $results[$_].Count } -Descending) {
    $count = $results[$target].Count
    $color = if ($count -eq 0) { "Green" } elseif ($count -lt 5) { "Yellow" } else { "Red" }
    Write-Host "  $target : $count imports" -ForegroundColor $color
}

# Save detailed report
$reportFile = "import_analysis_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$report = @()
$report += "=" * 80
$report += "Import Dependency Analysis Report"
$report += "Generated: $(Get-Date)"
$report += "=" * 80
$report += ""

foreach ($target in $results.Keys | Sort-Object) {
    $moduleName = [System.IO.Path]::GetFileNameWithoutExtension($target)
    $report += ""
    $report += "-" * 80
    $report += "FILE: $target"
    $report += "MODULE: $moduleName"
    $report += "IMPORTS FOUND: $($results[$target].Count)"
    $report += "-" * 80
    
    if ($results[$target].Count -eq 0) {
        $report += "  No imports found - SAFE TO MOVE"
    } else {
        $report += ""
        foreach ($imp in $results[$target] | Sort-Object File) {
            $relativePath = $imp.File -replace [regex]::Escape((Get-Location).Path), "."
            $report += "  File: $relativePath"
            $report += "  Lines: $($imp.Lines)"
            $report += "  Import: $($imp.Text)"
            $report += ""
        }
    }
}

$report += ""
$report += "=" * 80
$report += "NEXT STEPS:"
$report += "=" * 80
$report += ""
$report += "1. Review this report to understand import dependencies"
$report += "2. Create import update script to fix all imports"
$report += "3. Test import updates with -DryRun first"
$report += "4. Update imports (verify no errors)"
$report += "5. Test application: ./cslaunch"
$report += "6. ONLY THEN move the files"
$report += "7. Test again: ./cslaunch"
$report += "8. Commit if successful"
$report += ""

$report | Out-File -FilePath $reportFile -Encoding UTF8

Write-Host "`nDetailed report saved to: $reportFile" -ForegroundColor Green

# Recommendations
Write-Host "`nRECOMMENDATIONS:" -ForegroundColor Cyan

$highRiskFiles = $results.Keys | Where-Object { $results[$_].Count -gt 10 }
$mediumRiskFiles = $results.Keys | Where-Object { $results[$_].Count -gt 5 -and $results[$_].Count -le 10 }
$lowRiskFiles = $results.Keys | Where-Object { $results[$_].Count -gt 0 -and $results[$_].Count -le 5 }
$safeFiles = $results.Keys | Where-Object { $results[$_].Count -eq 0 }

if ($safeFiles.Count -gt 0) {
    Write-Host "  Safe to move (no imports): $($safeFiles.Count) files" -ForegroundColor Green
    foreach ($f in $safeFiles) {
        Write-Host "    - $f" -ForegroundColor Green
    }
}

if ($lowRiskFiles.Count -gt 0) {
    Write-Host "`n  Low risk (1-5 imports): $($lowRiskFiles.Count) files" -ForegroundColor Yellow
    Write-Host "    Update imports manually or with script" -ForegroundColor Gray
}

if ($mediumRiskFiles.Count -gt 0) {
    Write-Host "`n  Medium risk (6-10 imports): $($mediumRiskFiles.Count) files" -ForegroundColor DarkYellow
    Write-Host "    Strongly recommend using update script" -ForegroundColor Gray
}

if ($highRiskFiles.Count -gt 0) {
    Write-Host "`n  High risk (10+ imports): $($highRiskFiles.Count) files" -ForegroundColor Red
    Write-Host "    MUST use automated update script" -ForegroundColor Gray
    Write-Host "    Test VERY carefully after updates" -ForegroundColor Gray
}

Write-Host "`nNEXT STEP: Review $reportFile, then run update_imports.ps1`n" -ForegroundColor Cyan
