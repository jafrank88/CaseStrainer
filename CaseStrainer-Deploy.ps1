# CaseStrainer Deployment Script for Windows
# Save as CaseStrainer-Deploy.ps1

# Requires running as Administrator
#Requires -RunAsAdministrator

# Logging setup
$logDir = "C:\Logs\CaseStrainer"
$logFile = "$logDir\deploy_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Ensure log directory exists
if (-not (Test-Path -Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Start logging
Start-Transcript -Path $logFile -Append

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARNING", "ERROR", "SUCCESS")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "INFO" { Write-Host $logMessage -ForegroundColor Cyan }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
    }
    
    Add-Content -Path $logFile -Value $logMessage
}

function Find-CaseStrainerDir {
    Write-Log "Searching for CaseStrainer installation..."
    
    $possibleDirs = @(
        "C:\CaseStrainer",
        "C:\inetpub\wwwroot\casestrainer",
        "D:\CaseStrainer",
        "E:\CaseStrainer",
        "C:\Users\Public\CaseStrainer",
        "C:\Users\$env:USERNAME\CaseStrainer"
    )
    
    foreach ($dir in $possibleDirs) {
        if (Test-Path -Path "$dir\app_final.py") {
            Write-Log "Found CaseStrainer at: $dir" -Level SUCCESS
            return $dir
        }
    }
    
    # If not found in common locations, search the system
    Write-Log "Could not find in common locations. Searching system..." -Level WARNING
    $foundDir = Get-ChildItem -Path "C:\" -Recurse -Filter "app_final.py" -ErrorAction SilentlyContinue | 
                Select-Object -First 1 -ExpandProperty DirectoryName
    
    if ($foundDir) {
        Write-Log "Found CaseStrainer at: $foundDir" -Level SUCCESS
        return $foundDir
    }
    
    Write-Log "Could not find CaseStrainer installation." -Level ERROR
    return $null
}

function Get-ServiceStatus {
    $service = Get-Service -Name "CaseStrainer" -ErrorAction SilentlyContinue
    
    if ($service) {
        $status = $service.Status
        Write-Log "Windows Service Status: $status"
        return $status
    }
    else {
        Write-Log "No Windows Service found for CaseStrainer" -Level WARNING
    }
    
    # Check for running Python process
    $process = Get-Process -Name "python*" -ErrorAction SilentlyContinue | 
               Where-Object { $_.CommandLine -like "*app_final.py*" }
    
    if ($process) {
        Write-Log "Found running Python process (PID: $($process.Id))" -Level WARNING
        return "Running (Manual)"
    }
    
    Write-Log "CaseStrainer is not running" -Level WARNING
    return "Stopped"
}

function Update-Application {
    param(
        [string]$AppDir
    )
    
    if (-not $AppDir -or -not (Test-Path $AppDir)) {
        Write-Log "Invalid application directory" -Level ERROR
        return $false
    }
    
    try {
        Set-Location -Path $AppDir
        
        # Backup current state
        Write-Log "Backing up current state..."
        if (Get-Command git -ErrorAction SilentlyContinue) {
            git stash push -m "Backup before deployment $(Get-Date -Format 'yyyyMMdd_HHmmss')"
        }
        
        # Pull updates
        Write-Log "Pulling latest changes..."
        git pull origin main
        
        # Install dependencies
        Write-Log "Installing dependencies..."
        pip install -r requirements.txt
        
        return $true
    }
    catch {
        Write-Log "Error during update: $_" -Level ERROR
        return $false
    }
}

function Restart-Service {
    param(
        [string]$AppDir
    )
    
    # Stop existing processes
    $processes = Get-Process -Name "python*" -ErrorAction SilentlyContinue | 
                 Where-Object { $_.CommandLine -like "*app_final.py*" }
    
    if ($processes) {
        Write-Log "Stopping existing processes..."
        $processes | Stop-Process -Force
        Start-Sleep -Seconds 2
    }
    
    # Start new instance
    try {
        $pythonPath = (Get-Command python).Source
        $appPath = Join-Path -Path $AppDir -ChildPath "app_final.py"
        
        $processStartInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processStartInfo.FileName = $pythonPath
        $processStartInfo.Arguments = "`"$appPath`" --host 0.0.0.0 --port 5000"
        $processStartInfo.WorkingDirectory = $AppDir
        $processStartInfo.UseShellExecute = $false
        $processStartInfo.RedirectStandardOutput = $true
        $processStartInfo.RedirectStandardError = $true
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $processStartInfo
        $process.Start() | Out-Null
        
        Write-Log "Started CaseStrainer (PID: $($process.Id))" -Level SUCCESS
        return $true
    }
    catch {
        Write-Log "Failed to start application: $_" -Level ERROR
        return $false
    }
}

function Show-Menu {
    param(
        [string]$AppDir,
        [string]$Status
    )
    
    Clear-Host
    Write-Host "=== CaseStrainer Deployment Tool ===" -ForegroundColor Cyan
    Write-Host "Application Directory: " -NoNewline
    if ($AppDir) {
        Write-Host $AppDir -ForegroundColor Green
    } else {
        Write-Host "Not found" -ForegroundColor Red
    }
    
    Write-Host "Status: " -NoNewline
    if ($Status -eq "Stopped") {
        Write-Host $Status -ForegroundColor Red
    } else {
        Write-Host $Status -ForegroundColor Green
    }
    
    Write-Host "`n1. Find Application"
    Write-Host "2. Check Status"
    Write-Host "3. Deploy Updates"
    Write-Host "4. Restart Service"
    Write-Host "5. View Logs"
    Write-Host "6. Exit"
    Write-Host "`nSelect an option (1-6): " -NoNewline
}

# Main execution
$appDir = $null
$status = "Unknown"

while ($true) {
    Show-Menu -AppDir $appDir -Status $status
    $choice = Read-Host
    
    switch ($choice) {
        "1" { 
            $appDir = Find-CaseStrainerDir 
            if ($appDir) {
                $status = Get-ServiceStatus
            }
        }
        "2" { $status = Get-ServiceStatus }
        "3" { 
            if ($appDir) {
                if (Update-Application -AppDir $appDir) {
                    $status = Get-ServiceStatus
                }
            } else {
                Write-Log "Please find the application directory first" -Level WARNING
            }
        }
        "4" { 
            if ($appDir) {
                if (Restart-Service -AppDir $appDir) {
                    $status = Get-ServiceStatus
                }
            } else {
                Write-Log "Please find the application directory first" -Level WARNING
            }
        }
        "5" { 
            if (Test-Path $logFile) {
                notepad $logFile
            } else {
                Write-Log "No log file found" -Level WARNING
            }
        }
        "6" { 
            Write-Log "Exiting..."
            Stop-Transcript | Out-Null
            exit 0 
        }
        default { Write-Log "Invalid option" -Level WARNING }
    }
    
    if ($choice -ne "6") {
        Write-Host "`nPress Enter to continue..."
        $null = Read-Host
    }
}