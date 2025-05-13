# PowerShell script to synchronize changes from OneDrive repository to D:\CaseStrainer
# This script should be run with administrator privileges

# Source and destination directories
$sourceDir = "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"
$destDir = "D:\CaseStrainer"

# Create a timestamp for the backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path -Path $destDir -ChildPath "_backup_$timestamp"

Write-Host "Starting synchronization from $sourceDir to $destDir"

# Create a backup of the D:\CaseStrainer directory
Write-Host "Creating backup of D:\CaseStrainer at $backupDir"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Copy only important files to backup (exclude large data files and temp files)
Write-Host "Backing up important files..."
Get-ChildItem -Path $destDir -File -Recurse -Include "*.py", "*.bat", "*.ps1", "*.md", "*.json", "*.html", "*.css", "*.js" |
    Where-Object { -not $_.FullName.Contains("__pycache__") -and -not $_.FullName.Contains("node_modules") } |
    ForEach-Object {
        $relativePath = $_.FullName.Substring($destDir.Length + 1)
        $targetPath = Join-Path -Path $backupDir -ChildPath $relativePath
        $targetDir = Split-Path -Path $targetPath -Parent
        
        if (-not (Test-Path -Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        
        Copy-Item -Path $_.FullName -Destination $targetPath -Force
    }

# Synchronize files from OneDrive to D:\CaseStrainer
Write-Host "Synchronizing files from OneDrive to D:\CaseStrainer..."

# Copy Python files
Get-ChildItem -Path $sourceDir -File -Include "*.py" |
    ForEach-Object {
        $relativePath = $_.FullName.Substring($sourceDir.Length + 1)
        $targetPath = Join-Path -Path $destDir -ChildPath $relativePath
        
        Write-Host "Copying $relativePath to D:\CaseStrainer"
        Copy-Item -Path $_.FullName -Destination $targetPath -Force
    }

# Copy batch files
Get-ChildItem -Path $sourceDir -File -Include "*.bat" |
    ForEach-Object {
        $relativePath = $_.FullName.Substring($sourceDir.Length + 1)
        $targetPath = Join-Path -Path $destDir -ChildPath $relativePath
        
        Write-Host "Copying $relativePath to D:\CaseStrainer"
        Copy-Item -Path $_.FullName -Destination $targetPath -Force
    }

# Copy PowerShell scripts
Get-ChildItem -Path $sourceDir -File -Include "*.ps1" |
    ForEach-Object {
        $relativePath = $_.FullName.Substring($sourceDir.Length + 1)
        $targetPath = Join-Path -Path $destDir -ChildPath $relativePath
        
        Write-Host "Copying $relativePath to D:\CaseStrainer"
        Copy-Item -Path $_.FullName -Destination $targetPath -Force
    }

# Copy markdown files
Get-ChildItem -Path $sourceDir -File -Include "*.md" |
    ForEach-Object {
        $relativePath = $_.FullName.Substring($sourceDir.Length + 1)
        $targetPath = Join-Path -Path $destDir -ChildPath $relativePath
        
        Write-Host "Copying $relativePath to D:\CaseStrainer"
        Copy-Item -Path $_.FullName -Destination $targetPath -Force
    }

# Copy JSON files (except large data files)
Get-ChildItem -Path $sourceDir -File -Include "*.json" |
    Where-Object { $_.Length -lt 10MB } |
    ForEach-Object {
        $relativePath = $_.FullName.Substring($sourceDir.Length + 1)
        $targetPath = Join-Path -Path $destDir -ChildPath $relativePath
        
        Write-Host "Copying $relativePath to D:\CaseStrainer"
        Copy-Item -Path $_.FullName -Destination $targetPath -Force
    }

# Copy Vue.js frontend files if they exist
$vueSourceDir = Join-Path -Path $sourceDir -ChildPath "static\vue"
$vueDestDir = Join-Path -Path $destDir -ChildPath "static\vue"

if (Test-Path -Path $vueSourceDir) {
    Write-Host "Copying Vue.js frontend files..."
    
    if (-not (Test-Path -Path $vueDestDir)) {
        New-Item -ItemType Directory -Path $vueDestDir -Force | Out-Null
    }
    
    Copy-Item -Path "$vueSourceDir\*" -Destination $vueDestDir -Recurse -Force
}

Write-Host "Synchronization complete!"
Write-Host "Your OneDrive repository is now synchronized with D:\CaseStrainer"
Write-Host "A backup of the previous D:\CaseStrainer state is available at $backupDir"
