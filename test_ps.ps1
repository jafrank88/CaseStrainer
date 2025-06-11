# Get current directory
$currentDir = Get-Location
Write-Host "Current directory: $currentDir"

# Check file existence using relative path
$relativePath = Join-Path -Path $currentDir -ChildPath "src\app_final_vue.py"
Write-Host "Checking: $relativePath"
if (Test-Path $relativePath) {
    Write-Host "[SUCCESS] File found at: $relativePath"
} else {
    Write-Host "[ERROR] File not found at: $relativePath"
}

# List contents of src directory
$srcDir = Join-Path -Path $currentDir -ChildPath "src"
Write-Host "`nContents of src directory:"
Get-ChildItem -Path $srcDir -Filter "app_final*" | Select-Object Name, FullName

# List all Python files in src
Write-Host "`nPython files in src directory:"
Get-ChildItem -Path $srcDir -Filter "*.py" | Select-Object -First 10 Name

Write-Host "`nPress any key to continue..."
[Console]::ReadKey($true) | Out-Null
