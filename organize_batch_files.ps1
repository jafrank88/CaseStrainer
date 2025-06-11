# PowerShell script to organize batch files
# Moves deprecated batch files to the deprecated_scripts folder

# Define the root directory and target directory
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$deprecatedDir = Join-Path $rootDir "deprecated_scripts"

# Ensure the deprecated_scripts directory exists
if (-not (Test-Path $deprecatedDir)) {
    New-Item -ItemType Directory -Path $deprecatedDir | Out-Null
    Write-Host "Created directory: $deprecatedDir"
}

# List of batch files to keep (do not move these)
$keepFiles = @(
    "start_casestrainer.bat",
    "stop_casestrainer.bat",
    "organize_batch_files.ps1"
)

# List of batch files that are duplicates or deprecated
$deprecatedPatterns = @(
    "^start_.*\.bat$",
    "^run_.*\.bat$",
    "^launch_.*\.bat$",
    "^stop_.*\.bat$",
    "^restart_.*\.bat$",
    "^update_.*\.bat$",
    "^build_.*\.bat$"
)

# Function to check if a file should be moved to deprecated
function Should-MoveToDeprecated {
    param (
        [string]$fileName
    )
    
    # Always keep files in the keep list
    if ($keepFiles -contains $fileName) {
        return $false
    }
    
    # Check if file matches any deprecated pattern
    foreach ($pattern in $deprecatedPatterns) {
        if ($fileName -match $pattern) {
            # But exclude the main start/stop scripts we want to keep
            if (-not ($fileName -eq "start_casestrainer.bat" -or $fileName -eq "stop_casestrainer.bat")) {
                return $true
            }
        }
    }
    
    return $false
}

# Process all batch files in the root directory
Get-ChildItem -Path $rootDir -Filter "*.bat" | ForEach-Object {
    $file = $_.Name
    $fullPath = $_.FullName
    
    if (Should-MoveToDeprecated -fileName $file) {
        $destination = Join-Path $deprecatedDir $file
        
        # Handle naming conflicts
        $count = 1
        while (Test-Path $destination) {
            $nameWithoutExt = [System.IO.Path]::GetFileNameWithoutExtension($file)
            $ext = [System.IO.Path]::GetExtension($file)
            $newName = "${nameWithoutExt}_${count}${ext}"
            $destination = Join-Path $deprecatedDir $newName
            $count++
        }
        
        # Move the file
        Move-Item -Path $fullPath -Destination $destination -Force
        Write-Host "Moved: $file -> deprecated_scripts\$(Split-Path $destination -Leaf)"
    }
}

Write-Host "Batch file organization complete!"
Write-Host "Kept files: $($keepFiles -join ', ')"
Write-Host "Other batch files have been moved to the 'deprecated_scripts' folder."
