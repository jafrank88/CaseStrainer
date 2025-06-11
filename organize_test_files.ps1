# PowerShell script to organize test files
# Moves test files to the tests directory

# Define the root directory and target directory
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$testDir = Join-Path $rootDir "tests"

# Ensure the tests directory exists
if (-not (Test-Path $testDir)) {
    New-Item -ItemType Directory -Path $testDir | Out-Null
    Write-Host "Created directory: $testDir"
}

# List of test files to keep in the root directory
$keepFiles = @(
    "run_tests.bat"
)

# Find all test files in the root directory
Get-ChildItem -Path $rootDir -Filter "test_*.py" | ForEach-Object {
    $file = $_.Name
    $sourcePath = $_.FullName
    $destination = Join-Path $testDir $file
    
    # Skip files in the keep list
    if ($keepFiles -contains $file) {
        Write-Host "Skipping (keep file): $file"
        return
    }
    
    # Handle naming conflicts
    $count = 1
    while (Test-Path $destination) {
        $nameWithoutExt = [System.IO.Path]::GetFileNameWithoutExtension($file)
        $ext = [System.IO.Path]::GetExtension($file)
        $newName = "${nameWithoutExt}_${count}${ext}"
        $destination = Join-Path $testDir $newName
        $count++
    }
    
    # Move the file
    Move-Item -Path $sourcePath -Destination $destination -Force
    Write-Host "Moved: $file -> tests\$(Split-Path $destination -Leaf)"
}

Write-Host "Test file organization complete!"
Write-Host "Kept files: $($keepFiles -join ', ')"
Write-Host "Other test files have been moved to the 'tests' folder."
