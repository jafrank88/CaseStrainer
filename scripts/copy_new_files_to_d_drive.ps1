# PowerShell script to copy new files from OneDrive to D:\CaseStrainer
# This script should be run with administrator privileges

# Source and destination directories
$sourceDir = "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"
$destDir = "D:\CaseStrainer"

# Files to copy (the ones we created recently)
$filesToCopy = @(
    "download_wa_briefs_to_c_drive.py",
    "process_c_drive_wa_briefs.py",
    "download_and_process_wa_briefs_c_drive.bat",
    "update_d_drive_git.ps1"
)

# Copy each file
foreach ($file in $filesToCopy) {
    $sourcePath = Join-Path -Path $sourceDir -ChildPath $file
    $destPath = Join-Path -Path $destDir -ChildPath $file
    
    if (Test-Path -Path $sourcePath) {
        Write-Host "Copying $file to D:\CaseStrainer..."
        Copy-Item -Path $sourcePath -Destination $destPath -Force
        Write-Host "Copied $file successfully."
    } else {
        Write-Host "Warning: $file not found in source directory."
    }
}

Write-Host "File copying complete. You can now run the Git update script to commit these changes."
