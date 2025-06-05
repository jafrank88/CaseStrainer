# Setup environment files for Vue.js project

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges to set up environment files." -ForegroundColor Yellow
    Write-Host "Please run this script in an elevated PowerShell window." -ForegroundColor Yellow
    exit 1
}

# Define file paths
$envFiles = @{
    ".env" = "_env"
    ".env.development" = "_env.development"
    ".env.production" = "_env.production"
    ".env.example" = "_env.example"
}

# Copy files and remove originals
foreach ($file in $envFiles.GetEnumerator()) {
    $src = $file.Value
    $dest = $file.Key
    
    if (Test-Path $src) {
        if (Test-Path $dest) {
            $backup = "${dest}.bak"
            Write-Host "Backing up existing $dest to $backup" -ForegroundColor Yellow
            Move-Item -Path $dest -Destination $backup -Force
        }
        
        Write-Host "Creating $dest" -ForegroundColor Green
        Copy-Item -Path $src -Destination $dest
        Remove-Item -Path $src
    }
}

Write-Host "`nEnvironment setup complete!" -ForegroundColor Green
Write-Host "Please restart your development server for changes to take effect." -ForegroundColor Green
