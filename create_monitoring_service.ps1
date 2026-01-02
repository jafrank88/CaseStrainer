# Create a Windows Service for CaseStrainer Monitoring

Write-Host "=== Creating CaseStrainer Monitoring Service ===" -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] This script must be run as Administrator to create a Windows service" -ForegroundColor Red
    Write-Host "Right-click PowerShell -> 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Install NSSM (Non-Sucking Service Manager) if not present
$nssmPath = "C:\tools\nssm\nssm.exe"
if (-not (Test-Path $nssmPath)) {
    Write-Host "`n[INFO] NSSM not found. Installing NSSM..." -ForegroundColor Yellow
    
    # Create tools directory
    New-Item -Path "C:\tools\nssm" -ItemType Directory -Force | Out-Null
    
    # Download NSSM
    Write-Host "Downloading NSSM..." -ForegroundColor Gray
    $nssmZip = "C:\tools\nssm.zip"
    Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile $nssmZip
    
    # Extract
    Write-Host "Extracting NSSM..." -ForegroundColor Gray
    Expand-Archive -Path $nssmZip -DestinationPath "C:\tools\nssm" -Force
    
    # Move to correct location
    Move-Item "C:\tools\nssm\nssm-2.24\win64\nssm.exe" "C:\tools\nssm\" -Force
    
    # Cleanup
    Remove-Item $nssmZip -Force
    Remove-Item "C:\tools\nssm\nssm-2.24" -Recurse -Force
    
    Write-Host "[OK] NSSM installed to C:\tools\nssm\" -ForegroundColor Green
}

# Create the monitoring service script
$serviceScript = @'
# CaseStrainer Monitoring Service Script
$daemonLog = "D:\dev\casestrainer\logs\docker_daemon_monitor.log"
$eventLog = "D:\dev\casestrainer\logs\docker_events.log"

# Ensure log directory exists
New-Item -Path (Split-Path $daemonLog) -ItemType Directory -Force | Out-Null
New-Item -Path (Split-Path $eventLog) -ItemType Directory -Force | Out-Null

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] [SERVICE] $Message"
    Add-Content -Path $daemonLog -Value $logEntry
}

function Write-EventLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    Add-Content -Path $eventLog -Value $logEntry
}

# Main service loop
Write-Log "=== CASESTRAINER MONITORING SERVICE STARTED ===" "SUCCESS"

# Start event monitoring in background
$eventScript = {
    $eventLog = "D:\dev\casestrainer\logs\docker_events.log"
    function Write-EventLog {
        param([string]$Message)
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "[$timestamp] $Message"
        Add-Content -Path $eventLog -Value $logEntry
    }
    try {
        Write-EventLog "=== DOCKER EVENT MONITORING STARTED (SERVICE) ==="
        docker events 2>&1 | ForEach-Object {
            if ($_ -and $_.ToString() -and $_.ToString().Trim()) {
                Write-EventLog $_.ToString()
            }
        }
    } catch {
        Write-EventLog "ERROR: $($_.Exception.Message)"
    }
}

Start-Job -Name "Docker-Events-Service" -ScriptBlock $eventScript | Out-Null

# Main monitoring loop
while ($true) {
    try {
        # Check Docker daemon
        $null = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Docker daemon is healthy" "SUCCESS"
        } else {
            Write-Log "Docker daemon health check FAILED" "ERROR"
            
            # Attempt restart if needed
            try {
                Write-Log "Attempting Docker restart..." "WARN"
                & "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe" -shutdown
                Start-Sleep -Seconds 10
                Start-Process -FilePath "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
                Write-Log "Docker restart initiated" "INFO"
                Start-Sleep -Seconds 30
            } catch {
                Write-Log "Docker restart failed: $($_.Exception.Message)" "ERROR"
            }
        }
        
        # Check CaseStrainer containers
        $containers = docker ps --filter name=casestrainer --format "{{.Names}}" 2>$null
        if ($containers) {
            $containerCount = ($containers | Measure-Object).Count
            Write-Log "Found $containerCount CaseStrainer containers running" "INFO"
        } else {
            Write-Log "No CaseStrainer containers found" "WARN"
        }
        
    } catch {
        Write-Log "Error in monitoring loop: $($_.Exception.Message)" "ERROR"
    }
    
    # Wait before next check (5 minutes)
    Start-Sleep -Seconds 300
}
'@

# Save the service script
$serviceScriptPath = "D:\dev\casestrainer\service_monitor.ps1"
$serviceScript | Out-File -FilePath $serviceScriptPath -Encoding UTF8 -Force
Write-Host "[OK] Created service script: $serviceScriptPath" -ForegroundColor Green

# Create the Windows service using NSSM
Write-Host "`n[INFO] Creating Windows service..." -ForegroundColor Yellow
& $nssmPath install CaseStrainerMonitor powershell.exe
& $nssmPath set CaseStrainerMonitor Arguments "-NoProfile -ExecutionPolicy Bypass -File `"$serviceScriptPath`""
& $nssmPath set CaseStrainerMonitor DisplayName "CaseStrainer Monitoring Service"
& $nssmPath set CaseStrainerMonitor Description "Monitors Docker daemon and CaseStrainer containers"
& $nssmPath set CaseStrainerMonitor Start SERVICE_AUTO_START
& $nssmPath set CaseStrainerMonitor AppStdout "D:\dev\casestrainer\logs\service_stdout.log"
& $nssmPath set CaseStrainerMonitor AppStderr "D:\dev\casestrainer\logs\service_stderr.log"

Write-Host "`n[SUCCESS] Windows service created!" -ForegroundColor Green
Write-Host "Service name: CaseStrainerMonitor" -ForegroundColor Gray
Write-Host "Display name: CaseStrainer Monitoring Service" -ForegroundColor Gray
Write-Host "Startup type: Automatic" -ForegroundColor Gray

# Start the service
Write-Host "`n[INFO] Starting the service..." -ForegroundColor Yellow
Start-Service CaseStrainerMonitor -ErrorAction SilentlyContinue

# Check service status
$service = Get-Service CaseStrainerMonitor -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "`n[OK] Service status: $($service.Status)" -ForegroundColor Cyan
    if ($service.Status -eq "Running") {
        Write-Host "[SUCCESS] CaseStrainer monitoring is now running as a Windows service!" -ForegroundColor Green
    }
} else {
    Write-Host "`n[ERROR] Failed to create service" -ForegroundColor Red
}

Write-Host "`n=== Service Management Commands ===" -ForegroundColor Cyan
Write-Host "Check status: Get-Service CaseStrainerMonitor" -ForegroundColor Gray
Write-Host "Start service: Start-Service CaseStrainerMonitor" -ForegroundColor Gray
Write-Host "Stop service: Stop-Service CaseStrainerMonitor" -ForegroundColor Gray
Write-Host "Remove service: nssm remove CaseStrainerMonitor" -ForegroundColor Gray
Write-Host "View logs: Get-Content logs\docker_daemon_monitor.log -Tail 50 -Wait" -ForegroundColor Gray
