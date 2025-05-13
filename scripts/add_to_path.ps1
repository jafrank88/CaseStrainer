$toolsPath = "$env:USERPROFILE\tools"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if (-not $currentPath.Contains($toolsPath)) {
    $newPath = $currentPath + ";" + $toolsPath
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Added $toolsPath to PATH"
} else {
    Write-Host "$toolsPath is already in PATH"
} 