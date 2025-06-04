<#
.SYNOPSIS
    Deploys the CaseStrainer Vue.js frontend to the production server.
.DESCRIPTION
    This script builds the Vue.js application and deploys it to the specified directory.
    It handles the build process and ensures proper file permissions.
.PARAMETER TargetDir
    The target directory where the built files should be copied.
    Default is '..\..\static\vue' (relative to the script location).
.EXAMPLE
    .\deploy.ps1 -TargetDir "C:\path\to\deployment\directory"
.NOTES
    Requires Node.js and npm to be installed.
    Must be run with administrative privileges if deploying to protected directories.
#>

param (
    [string]$TargetDir = (Join-Path (Split-Path -Parent $PSScriptRoot) 'static\vue')
)

# Stop on first error
$ErrorActionPreference = 'Stop'

# Function to log messages with timestamps
function Write-Log {
    param([string]$Message)
    Write-Output "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

try {
    Write-Log "Starting deployment of CaseStrainer Vue.js frontend..."
    
    # Verify Node.js and npm are installed
    $nodeVersion = node --version
    $npmVersion = npm --version
    
    Write-Log "Using Node.js $nodeVersion and npm $npmVersion"
    
    # Install dependencies if needed
    if (-not (Test-Path 'node_modules')) {
        Write-Log 'Installing dependencies...'
        npm install
        if ($LASTEXITCODE -ne 0) {
            throw 'Failed to install dependencies.'
        }
    }
    
    # Build the application
    Write-Log 'Building the application...'
    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw 'Build failed.'
    }
    
    # Create target directory if it doesn't exist
    if (-not (Test-Path $TargetDir)) {
        Write-Log "Creating target directory: $TargetDir"
        New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    }
    
    # Copy files to target directory
    Write-Log "Copying files to $TargetDir..."
    $sourceDir = Join-Path $PSScriptRoot 'dist\*'
    
    # Remove existing files in the target directory
    if (Test-Path $TargetDir) {
        Remove-Item -Path (Join-Path $TargetDir '*') -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    # Copy new files
    Copy-Item -Path $sourceDir -Destination $TargetDir -Recurse -Force
    
    Write-Log "Deployment completed successfully to $TargetDir"
    Write-Log "The application should now be accessible at the configured URL."
    
} catch {
    Write-Error "Deployment failed: $_"
    exit 1
}
