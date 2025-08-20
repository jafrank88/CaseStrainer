# CaseStrainer Service Startup Script
# This script starts CaseStrainer as a background service

param(
    [switch]$Stop,
    [switch]$Status,
    [switch]$Restart
)

$ServiceName = "CaseStrainer"
$LogFile = "logs\casestrainer_service.log"
$PidFile = "logs\casestrainer.pid"

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    Write-Host "[$timestamp] $Message"
}

function Start-CaseStrainerService {
    Write-Log "Starting CaseStrainer service..."
    
    # Check if already running
    if (Test-Path $PidFile) {
        $processId = Get-Content $PidFile -ErrorAction SilentlyContinue
        if (Get-Process -Id $processId -ErrorAction SilentlyContinue) {
            Write-Log "CaseStrainer is already running with PID: $processId"
            return
        }
    }
    
    # Start CaseStrainer in background
    $process = Start-Process -FilePath "python" -ArgumentList "src\app_final_vue.py" -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru
    
    # Save PID
    $process.Id | Out-File -FilePath $PidFile -Encoding UTF8
    
    # Wait a moment for startup
    Start-Sleep -Seconds 5
    
    # Test if it's responding
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Log "✅ CaseStrainer started successfully with PID: $($process.Id)"
            Write-Log "🌐 Access URL: http://localhost:5000/casestrainer/"
            Write-Log "🔧 API Health: http://localhost:5000/casestrainer/api/health"
        } else {
            Write-Log "⚠️ CaseStrainer started but health check failed: $($response.StatusCode)"
        }
    } catch {
        Write-Log "❌ Failed to start CaseStrainer: $($_.Exception.Message)"
    }
}

function Stop-CaseStrainerService {
    Write-Log "Stopping CaseStrainer service..."
    
    if (Test-Path $PidFile) {
        $processId = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($processId) {
            try {
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                Write-Log "✅ CaseStrainer stopped (PID: $processId)"
            } catch {
                Write-Log "⚠️ Could not stop process $processId: $($_.Exception.Message)"
            }
        }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    } else {
        Write-Log "No PID file found"
    }
    
    # Also stop any Python processes running app_final_vue.py
    Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
        $_.ProcessName -eq "python" 
    } | ForEach-Object {
        try {
            Stop-Process -Id $_.Id -Force
            Write-Log "Stopped Python process: $($_.Id)"
        } catch {
            Write-Log "Could not stop Python process $($_.Id)"
        }
    }
}

function Get-CaseStrainerStatus {
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($pid -and (Get-Process -Id $pid -ErrorAction SilentlyContinue)) {
            Write-Log "✅ CaseStrainer is running (PID: $pid)"
            
            # Test health endpoint
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -UseBasicParsing -TimeoutSec 5
                Write-Log "🌐 Health check: OK (Status: $($response.StatusCode))"
                Write-Log "🔗 Access URL: http://localhost:5000/casestrainer/"
            } catch {
                Write-Log "❌ Health check failed: $($_.Exception.Message)"
            }
        } else {
            Write-Log "❌ CaseStrainer is not running (stale PID file)"
        }
    } else {
        Write-Log "❌ CaseStrainer is not running (no PID file)"
    }
}

# Main execution
if ($Stop) {
    Stop-CaseStrainerService
} elseif ($Status) {
    Get-CaseStrainerStatus
} elseif ($Restart) {
    Stop-CaseStrainerService
    Start-Sleep -Seconds 2
    Start-CaseStrainerService
} else {
    Start-CaseStrainerService
}
