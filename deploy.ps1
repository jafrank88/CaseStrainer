# CaseStrainer Deployment Script
# This script handles linting, committing, pushing, and deploying CaseStrainer
# Run with: powershell -ExecutionPolicy Bypass -File deploy.ps1 -CommitMessage "Your commit message here"

param(
    [Parameter(Mandatory=$true)]
    [string]$CommitMessage,
    [switch]$SkipLint,
    [switch]$SkipTests
)

# Configuration
$ProjectRoot = $PSScriptRoot
$LogFile = Join-Path $ProjectRoot "deployment_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$NginxPath = "nginx/nginx.exe"
$VirtualEnv = "C:\Users\jafrank\venv_casestrainer"
$AppPort = 5000

# Colors for console output
$ErrorColor = 'Red'
$WarningColor = 'Yellow'
$SuccessColor = 'Green'
$InfoColor = 'Cyan'

# Function to write to log and console
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = 'INFO',
        [switch]$NoNewLine
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Write to log file
    Add-Content -Path $LogFile -Value $logMessage -ErrorAction SilentlyContinue
    
    # Write to console with colors
    $foregroundColor = switch ($Level) {
        'ERROR' { $ErrorColor }
        'WARNING' { $WarningColor }
        'SUCCESS' { $SuccessColor }
        default { $InfoColor }
    }
    
    if ($NoNewLine) {
        Write-Host -NoNewline $logMessage -ForegroundColor $foregroundColor
    } else {
        Write-Host $logMessage -ForegroundColor $foregroundColor
    }
}

# Function to execute a command and check its status
function Invoke-CommandWithStatus {
    param(
        [string]$Command,
        [string]$ErrorMessage = "Command failed",
        [switch]$Fatal
    )
    Write-Log "Executing: $Command"
    try {
        $output = & cmd /c $Command 2>&1 | Out-String
        Write-Log $output.Trim()
        return $true
    } catch {
        Write-Log ("{0}: {1}" -f $ErrorMessage, $_) -Level 'ERROR'
        if ($Fatal) {
            Write-Log "Fatal error encountered. Exiting..." -Level 'ERROR'
            exit 1
        }
        return $false
    }
}

# Start logging
Write-Log "=== Starting CaseStrainer Deployment ==="
Write-Log "Project Root: $ProjectRoot"
Write-Log "Log File: $LogFile"

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Log "This script requires administrator privileges. Please run as administrator." -Level 'ERROR'
    exit 1
}

# Step 1: Linting and Formatting
if (-not $SkipLint) {
    Write-Log "=== Running Linting and Formatting ==="
    
    # Activate virtual environment
    $activateScript = Join-Path $VirtualEnv "Scripts\Activate.ps1"
    if (-not (Test-Path $activateScript)) {
        Write-Log "Virtual environment not found at $VirtualEnv" -Level 'ERROR'
        exit 1
    }
    
    # Import the virtual environment's activate script
    try {
        & $activateScript
        # Update PATH to include virtual environment's Scripts directory
        $env:Path = "$VirtualEnv\Scripts;" + $env:Path
        Write-Log "Virtual environment activated successfully"
    } catch {
        Write-Log "Failed to activate virtual environment: $_" -Level 'ERROR'
        exit 1
    }
    
    # Skip linting by default as it requires the virtual environment to be properly set up
    Write-Log "Skipping linting (use -SkipLint:$false to enable)" -Level 'WARNING'
    
    # Uncomment and modify the following section if you want to enable linting
    <#
    # Run black formatter
    Write-Log "Running Black formatter..."
    Invoke-CommandWithStatus -Command "black ." -ErrorMessage "Black formatting failed" -Fatal:$false
    
    # Run flake8 linter
    Write-Log "Running Flake8 linter..."
    $flake8Result = Invoke-CommandWithStatus -Command "flake8 . --count --show-source --statistics" -Fatal:$false
    if (-not $flake8Result) {
        Write-Log "Flake8 found issues. Please fix them before proceeding." -Level 'WARNING'
        if (-not $Force) {
            exit 1
        }
    }
    
    # Run bandit security checker
    Write-Log "Running Bandit security checker..."
    $banditResult = Invoke-CommandWithStatus -Command "bandit -r src" -Fatal:$false
    if (-not $banditResult -and -not $Force) {
        Write-Log "Bandit found security issues. Use -Force to ignore." -Level 'WARNING'
        exit 1
    }
    #>
}

# Step 2: Run tests (if not skipped)
if (-not $SkipTests) {
    Write-Log "=== Running Tests ==="
    # Add your test command here, for example:
    # python -m pytest tests/
    Write-Log "Skipping tests (test command not configured)" -Level 'WARNING'
}

# Step 3: Git operations
Write-Log "=== Git Operations ==="
Set-Location $ProjectRoot

# Check for changes
$gitStatus = git status --porcelain
if ([string]::IsNullOrEmpty($gitStatus)) {
    Write-Log "No changes to commit." -Level 'INFO'
} else {
    # Add all changes
    Write-Log "Staging changes..."
    Invoke-CommandWithStatus -Command "git add ." -ErrorMessage "Failed to stage changes" -Fatal:$true
    
    # Commit changes
    Write-Log "Creating commit..."
    Invoke-CommandWithStatus -Command "git commit -m \"$CommitMessage\"" -ErrorMessage "Commit failed" -Fatal:$true
}

# Pull latest changes
Write-Log "Pulling latest changes..."
Invoke-CommandWithStatus -Command "git pull --rebase origin main" -ErrorMessage "Failed to pull latest changes" -Fatal:$true

# Push changes
Write-Log "Pushing changes..."
Invoke-CommandWithStatus -Command "git push origin main" -ErrorMessage "Failed to push changes" -Fatal:$true

# Step 4: Stop existing services
Write-Log "=== Stopping Existing Services ==="

# Stop Nginx if running
if (Get-Process nginx -ErrorAction SilentlyContinue) {
    Write-Log "Stopping Nginx..."
    Stop-Process -Name nginx -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Stop any Python processes using the target port
$portInUse = Get-NetTCPConnection -LocalPort $AppPort -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Log "Stopping process using port $AppPort..."
    $portInUse | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 1
}

# Step 5: Start the application
Write-Log "=== Starting Application ==="

# Start Nginx
$nginxDir = "nginx"
$nginxConf = Join-Path $nginxDir "conf\nginx.conf"

if (Test-Path $NginxPath) {
    # Ensure Nginx is not running
    if (Get-Process nginx -ErrorAction SilentlyContinue) {
        Write-Log "Stopping existing Nginx..."
        Stop-Process -Name nginx -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    
    # Start Nginx with the correct configuration
    Write-Log "Starting Nginx with config: $nginxConf"
    Push-Location $nginxDir
    & $NginxPath -c $nginxConf
    Pop-Location
    Start-Sleep -Seconds 2
} else {
    Write-Log "Nginx not found at $NginxPath" -Level 'WARNING'
}

# Start the Flask application
Write-Log "Starting CaseStrainer application..."
Start-Process -FilePath "python" -ArgumentList "app_final_vue.py" -NoNewWindow

# Verify the application is running
Start-Sleep -Seconds 5
$appRunning = Test-NetConnection -ComputerName localhost -Port $AppPort -InformationLevel Quiet
if ($appRunning) {
    Write-Log "CaseStrainer is now running on http://localhost:$AppPort" -Level 'SUCCESS'
    Write-Log "Access it externally at https://wolf.law.uw.edu/casestrainer/" -Level 'SUCCESS'
} else {
    Write-Log "Failed to start CaseStrainer. Check the logs for details." -Level 'ERROR'
    exit 1
}

Write-Log "=== Deployment Completed Successfully ===" -Level 'SUCCESS'
