# Archive non-essential files for GitHub cleanup
# Date: 2025-01-20

$archiveDir = "archive_2025_01_20"
$rootDir = "d:\dev\casestrainer"

Write-Host "Starting cleanup archive process..." -ForegroundColor Green

# Function to move files safely
function Move-ToArchive {
    param (
        [string]$source,
        [string]$destSubdir
    )
    
    $dest = Join-Path $archiveDir $destSubdir
    if (-not (Test-Path $dest)) {
        New-Item -ItemType Directory -Path $dest -Force | Out-Null
    }
    
    if (Test-Path $source) {
        try {
            Move-Item -Path $source -Destination $dest -Force -ErrorAction Stop
            Write-Host "  Moved: $source" -ForegroundColor Gray
        } catch {
            Write-Host "  Failed to move: $source - $_" -ForegroundColor Yellow
        }
    }
}

# 1. ARCHIVE BUILD SUMMARIES AND STATUS DOCS
Write-Host "`n=== Archiving Build Summaries ===" -ForegroundColor Cyan
$summaryFiles = @(
    "*_SUMMARY.md", "*_COMPLETE.md", "*_STATUS.md", "*_RESULTS.md",
    "*_GUIDE.md", "*_PLAN.md", "*_ANALYSIS.md", "*_FIX.md",
    "*_PROGRESS.md", "*_REPORT.md", "*_DELIVERABLES.md",
    "SESSION_*.md", "PHASE*.md", "FIX_*.md", "FIXES_*.md"
)

foreach ($pattern in $summaryFiles) {
    Get-ChildItem -Path $rootDir -Filter $pattern -File | ForEach-Object {
        Move-ToArchive $_.FullName "build_summaries"
    }
}

# 2. ARCHIVE DEV NOTES AND TODO
Write-Host "`n=== Archiving Dev Notes ===" -ForegroundColor Cyan
$devNoteFiles = @(
    "TODO*.md", "BLOCKER*.md", "NEXT_STEPS.md", "FORWARD_PLAN.md",
    "TODAYS_ACCOMPLISHMENTS.md", "CLEANUP_PROGRESS.md",
    "DEPRECATION_*.md", "REFACTORING_*.md", "CONSOLIDATION_*.md",
    "REORGANIZATION_*.md", "MIGRATION_*.md"
)

foreach ($pattern in $devNoteFiles) {
    Get-ChildItem -Path $rootDir -Filter $pattern -File | ForEach-Object {
        Move-ToArchive $_.FullName "dev_notes"
    }
}

# 3. ARCHIVE TEST FILES
Write-Host "`n=== Archiving Test Files ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path "$archiveDir\test_files" -Force | Out-Null

# Test PDFs
Get-ChildItem -Path $rootDir -Filter "*.pdf" -File | Where-Object {
    $_.Name -match "test|temp|1029764|1033940|1034300|858581|24-2626|25-2808|Park"
} | ForEach-Object {
    Move-ToArchive $_.FullName "test_files"
}

# Test logs and output
$testPatterns = @("test_*.log", "test_*.txt", "test_*.json", "*_test.txt", "*_test.json")
foreach ($pattern in $testPatterns) {
    Get-ChildItem -Path $rootDir -Filter $pattern -File | ForEach-Object {
        Move-ToArchive $_.FullName "test_files"
    }
}

# 4. ARCHIVE LOG FILES
Write-Host "`n=== Archiving Log Files ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path "$archiveDir\logs" -Force | Out-Null

$logPatterns = @(
    "*.log", "*_logs.txt", "worker*.txt", "backend_*.txt",
    "diagnostic*.txt", "debug*.txt", "*_debug.txt",
    "recent*.txt", "latest*.txt", "final*.txt", "all_*.txt"
)

foreach ($pattern in $logPatterns) {
    Get-ChildItem -Path $rootDir -Filter $pattern -File | ForEach-Object {
        Move-ToArchive $_.FullName "logs"
    }
}

# 5. ARCHIVE COMMIT MESSAGES
Write-Host "`n=== Archiving Commit Messages ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path "$archiveDir\commit_messages" -Force | Out-Null
Get-ChildItem -Path $rootDir -Filter "commit_*.txt" -File | ForEach-Object {
    Move-ToArchive $_.FullName "commit_messages"
}

# 6. ARCHIVE BACKUP DIRECTORIES
Write-Host "`n=== Archiving Backup Directories ===" -ForegroundColor Cyan
$backupDirs = @(
    "backup_*", "archive_*", "archived*", "security_backup",
    "temp-*", "*_backup", "casestrainer-vue-backup",
    "backup_before_update", "deployment_package"
)

foreach ($pattern in $backupDirs) {
    Get-ChildItem -Path $rootDir -Directory | Where-Object { $_.Name -like $pattern -and $_.Name -ne "archive_2025_01_20" } | ForEach-Object {
        Move-ToArchive $_.FullName "backup_dirs"
    }
}

# 7. ARCHIVE DOCKER TEST FILES
Write-Host "`n=== Archiving Docker Files ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path "$archiveDir\docker_files" -Force | Out-Null

$dockerPatterns = @(
    "docker_*.ps1", "docker_*.json", "docker-*.json", "docker_*.log",
    "nginx-*.conf", "*.conf.fromcontainer"
)

foreach ($pattern in $dockerPatterns) {
    Get-ChildItem -Path $rootDir -Filter $pattern -File | ForEach-Object {
        # Keep essential docker files
        if ($_.Name -notin @("docker-compose.yml", "docker-compose.prod.yml", "Dockerfile")) {
            Move-ToArchive $_.FullName "docker_files"
        }
    }
}

# 8. ARCHIVE OLD SCRIPTS
Write-Host "`n=== Archiving Old Scripts ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path "$archiveDir\old_scripts" -Force | Out-Null

$scriptPatterns = @(
    "dplaunch*.ps1", "prodlaunch*.ps1", "launch*.ps1",
    "cleanup.ps1", "organize_*.ps1", "execute_*.ps1",
    "reorganize_*.ps1", "apply_*.ps1", "generate_*.ps1",
    "monitor_*.ps1", "*_monitor*.ps1", "prevent_*.ps1",
    "setup_*.ps1", "smart_*.ps1", "test_*.ps1",
    "check_*.ps1", "find_*.py", "show_*.py", "inspect_*.py"
)

foreach ($pattern in $scriptPatterns) {
    Get-ChildItem -Path $rootDir -Filter $pattern -File | ForEach-Object {
        # Keep cslaunch.ps1 and essential scripts
        if ($_.Name -ne "cslaunch.ps1") {
            Move-ToArchive $_.FullName "old_scripts"
        }
    }
}

# 9. ARCHIVE ANALYSIS AND DEBUG FILES
Write-Host "`n=== Archiving Analysis Files ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path "$archiveDir\analysis" -Force | Out-Null

$analysisPatterns = @(
    "*_analysis.txt", "*_analysis.json", "citation_*.json",
    "*_response.json", "*_results.json", "*_output.txt",
    "api_*.json", "frontend_*.json", "sync_*.json", "async_*.json"
)

foreach ($pattern in $analysisPatterns) {
    Get-ChildItem -Path $rootDir -Filter $pattern -File | ForEach-Object {
        Move-ToArchive $_.FullName "analysis"
    }
}

# 10. ARCHIVE HTML TEST FILES
Write-Host "`n=== Archiving HTML Test Files ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path "$archiveDir\html_tests" -Force | Out-Null

Get-ChildItem -Path $rootDir -Filter "*.html" -File | Where-Object {
    $_.Name -match "test|findlaw|leagle|debug|standalone|browser-extension-page|word-plugin-page"
} | ForEach-Object {
    Move-ToArchive $_.FullName "html_tests"
}

# 11. ARCHIVE PYTHON DEBUG/TEST SCRIPTS
Write-Host "`n=== Archiving Python Test Scripts ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path "$archiveDir\python_tests" -Force | Out-Null

$pyTestPatterns = @(
    "test_*.py", "check_*.py", "debug_*.py", "validate_*.py",
    "verify_*.py", "inspect_*.py", "analyze_*.py", "diagnose_*.py",
    "poll_*.py", "fetch_*.py", "retrieve_*.py", "search_*.py",
    "extract_*.py", "process_*.py", "reprocess_*.py"
)

foreach ($pattern in $pyTestPatterns) {
    Get-ChildItem -Path $rootDir -Filter $pattern -File | ForEach-Object {
        Move-ToArchive $_.FullName "python_tests"
    }
}

# 12. ARCHIVE MISC FILES
Write-Host "`n=== Archiving Misc Files ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path "$archiveDir\misc" -Force | Out-Null

$miscFiles = @(
    "null", "o", "qc", "query", "python", "estrainer-vue-new",
    "VERSION", "*_cache", "*.zip"
)

foreach ($file in $miscFiles) {
    Get-ChildItem -Path $rootDir -Filter $file -File | ForEach-Object {
        Move-ToArchive $_.FullName "misc"
    }
}

# 13. CREATE ARCHIVE SUMMARY
Write-Host "`n=== Creating Archive Summary ===" -ForegroundColor Cyan

$archiveSummary = @"
# Archive Summary - January 20, 2025

## Purpose
This archive contains non-essential files removed from the CaseStrainer repository 
to prepare for GitHub cleanup and organization.

## Archive Structure

- **build_summaries/** - Build summaries, status documents, session notes
- **dev_notes/** - TODO lists, blocker notes, planning documents
- **test_files/** - Test PDFs, test logs, test outputs
- **logs/** - Application logs, debug logs, worker logs
- **commit_messages/** - Historical commit message files
- **backup_dirs/** - Backup directories and archived code
- **docker_files/** - Docker configuration experiments
- **old_scripts/** - Development and testing scripts
- **analysis/** - Analysis results and debug outputs
- **html_tests/** - HTML test files and mock pages
- **python_tests/** - Python test and debug scripts
- **misc/** - Miscellaneous temporary files

## What Was Kept in Main Repository

- **Source code** (src/)
- **Browser extension** (browser-extension/)
- **Word add-in** (word_addin/)
- **Documentation** (docs/)
- **Core scripts** (cslaunch.ps1, scripts/)
- **Configuration** (requirements.txt, docker-compose files, Dockerfile)
- **Essential docs** (README.md, SECURITY.md)
- **Git configuration** (.gitignore, .github/)

## Files Archived
$(Get-ChildItem -Path $archiveDir -Recurse -File | Measure-Object).Count files moved to archive

## Archive Date
January 20, 2025

## Notes
- All archived files were non-essential for the GitHub repository
- Original files remain in this archive for historical reference
- Archive can be safely excluded from Git via .gitignore

"@

Set-Content -Path "$archiveDir\README.md" -Value $archiveSummary

Write-Host "`n=== Archive Complete ===" -ForegroundColor Green
Write-Host "Archived files location: $archiveDir" -ForegroundColor Yellow
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Review the archive directory" -ForegroundColor White
Write-Host "2. Add 'archive_2025_01_20/' to .gitignore" -ForegroundColor White
Write-Host "3. Commit the cleaned repository" -ForegroundColor White
Write-Host "4. Push to GitHub" -ForegroundColor White
