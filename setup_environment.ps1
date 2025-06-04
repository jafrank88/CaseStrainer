# Setup Environment Script for CaseStrainer
# Run this script as Administrator to configure the production environment

# Stop script on first error
$ErrorActionPreference = "Stop"

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "This script requires Administrator privileges. Please run as Administrator." -ForegroundColor Red
    exit 1
}

# Function to generate a secure random string
function Generate-SecureString {
    param (
        [int]$length = 50
    )
    $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+{}|:<>?[]\;\',./`~' -split '' | Where-Object { $_ }
    $rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
    $bytes = New-Object byte[]($length)
    $rng.GetBytes($bytes)
    $result = ""
    foreach ($b in $bytes) {
        $result += $chars[$b % $chars.Length]
    }
    return $result
}

# Check if .env.production exists
$envFile = ".env.production"
$templateFile = ".env.production.template"

# Create template if it doesn't exist
if (-not (Test-Path $templateFile)) {
    @"
# Production Environment Variables
FLASK_ENV=production
FLASK_APP=src/app_final_vue.py
SECRET_KEY=your-secure-secret-key-here
COURTLISTENER_API_KEY=your-courtlistener-api-key
DATABASE_URL=sqlite:///citations.db
UPLOAD_FOLDER=./uploads
ALLOWED_EXTENSIONS={"pdf","docx","doc","txt"}
SESSION_TYPE=filesystem
SESSION_FILE_DIR=./sessions
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
LOG_LEVEL=INFO
LOG_FILE=./logs/casestrainer.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
RATELIMIT_DEFAULT=200 per day
RATELIMIT_STRATEGY=fixed-window
RATELIMIT_STORAGE_URL=memory://
CORS_ORIGINS=https://wolf.law.uw.edu
CORS_SUPPORTS_CREDENTIALS=True
CACHE_TYPE=SimpleCache
CACHE_DEFAULT_TIMEOUT=300
MAIL_SERVER=smtp.your-email-provider.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=your-email@example.com
ADMINS=admin@example.com
"@ | Out-File -FilePath $templateFile -Encoding utf8
}

# Create .env.production if it doesn't exist
if (-not (Test-Path $envFile)) {
    Write-Host "Creating $envFile from template..." -ForegroundColor Yellow
    Copy-Item -Path $templateFile -Destination $envFile
    
    # Generate a secure secret key
    $secretKey = Generate-SecureString -length 50
    (Get-Content $envFile) -replace 'SECRET_KEY=.*', "SECRET_KEY=$secretKey" | Set-Content $envFile
    
    Write-Host "Please edit $envFile and update the configuration values." -ForegroundColor Yellow
    notepad.exe $envFile
} else {
    Write-Host "$envFile already exists. Opening for review..." -ForegroundColor Yellow
    notepad.exe $envFile
}

# Create necessary directories
$directories = @("logs", "uploads", "sessions", "static")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Green
    }
}

# Set proper permissions (if needed)
# This might require additional configuration based on your setup

Write-Host "`nEnvironment setup complete!`n" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review and update the .env.production file with your actual settings"
Write-Host "2. Make sure all required Python packages are installed (run 'pip install -r requirements.txt')"
Write-Host "3. Run 'start_casestrainer.bat' to start the application`n"

# Check Python virtual environment
$venvPath = "C:\Users\jafrank\venv_casestrainer"
if (-not (Test-Path $venvPath)) {
    Write-Host "Python virtual environment not found at $venvPath" -ForegroundColor Yellow
    $createVenv = Read-Host "Would you like to create a new virtual environment? (y/n)"
    if ($createVenv -eq 'y') {
        python -m venv $venvPath
        Write-Host "Virtual environment created at $venvPath" -ForegroundColor Green
        Write-Host "Activate it using: .\$venvPath\Scripts\Activate.ps1" -ForegroundColor Cyan
    }
}

# Check if requirements are installed
$requirementsFile = "requirements.txt"
if (Test-Path $requirementsFile) {
    Write-Host "Checking Python requirements..." -ForegroundColor Cyan
    $missing = python -c "import pkg_resources; [print(pkg) for pkg in [line.strip() for line in open('requirements.txt') if not line.startswith('#') and line.strip()] if not pkg_resources.working_set.by_key.get(pkg.split('==')[0].lower().replace('-', '_'), None)]" 2>$null
    
    if ($missing) {
        Write-Host "The following packages are missing:" -ForegroundColor Yellow
        $missing | ForEach-Object { Write-Host "- $_" }
        $install = Read-Host "Would you like to install them now? (y/n)"
        if ($install -eq 'y') {
            & "$venvPath\Scripts\pip" install -r $requirementsFile
        }
    } else {
        Write-Host "All Python requirements are satisfied." -ForegroundColor Green
    }
}

Write-Host "`nSetup complete! You can now run 'start_casestrainer.bat' to start the application." -ForegroundColor Green
