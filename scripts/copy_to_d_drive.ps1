# PowerShell script to copy CaseStrainer files to D:\CaseStrainer
$sourceDir = "c:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer"
$destDir = "D:\CaseStrainer"

# Create destination directory if it doesn't exist
if (-not (Test-Path -Path $destDir)) {
    New-Item -ItemType Directory -Path $destDir -Force
    Write-Host "Created directory: $destDir"
}

# Copy all files and folders
try {
    Copy-Item -Path "$sourceDir\*" -Destination $destDir -Recurse -Force
    Write-Host "Successfully copied all files to $destDir"
} catch {
    Write-Host "Error copying files: $_"
}
