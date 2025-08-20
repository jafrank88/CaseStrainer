# Complete CaseStrainer Startup Script for Windows
# This script starts all required components for CaseStrainer to work properly

param(
    [switch]$Stop,
    [switch]$Status,
    [switch]$Help
)

if ($Help) {
    Write-Host "CaseStrainer Complete Startup Script" -ForegroundColor Cyan
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  .\start_casestrainer_complete.ps1        # Start all components" -ForegroundColor Green
    Write-Host "  .\start_casestrainer_complete.ps1 -Stop  # Stop all components" -ForegroundColor Red
    Write-Host "  .\start_casestrainer_complete.ps1 -Status # Show status" -ForegroundColor Yellow
    Write-Host "  .\start_casestrainer_complete.ps1 -Help  # Show this help" -ForegroundColor Blue
    exit
}

# Configuration
$LogFile = "logs\casestrainer_complete.log"
$PidFile = "logs\casestrainer.pid"
$RedisPidFile = "logs\redis.pid"
$WorkerPidFile = "logs\rq_worker.pid"

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

function Stop-AllComponents {
    Write-Log "Stopping all CaseStrainer components..."
    
    # Stop Flask app
    if (Test-Path $PidFile) {
        $processId = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($processId) {
            try {
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                Write-Log "✅ Stopped Flask app (PID: $processId)"
            } catch {
                Write-Log "⚠️ Could not stop Flask process $processId"
            }
        }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    }
    
    # Stop RQ worker
    if (Test-Path $WorkerPidFile) {
        $workerId = Get-Content $WorkerPidFile -ErrorAction SilentlyContinue
        if ($workerId) {
            try {
                Stop-Process -Id $workerId -Force -ErrorAction SilentlyContinue
                Write-Log "✅ Stopped RQ worker (PID: $workerId)"
            } catch {
                Write-Log "⚠️ Could not stop RQ worker $workerId"
            }
        }
        Remove-Item $WorkerPidFile -Force -ErrorAction SilentlyContinue
    }
    
    # Stop Redis (if running as Windows service)
    try {
        $redisService = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
        if ($redisService -and $redisService.Status -eq "Running") {
            Stop-Service -Name "Redis" -Force
            Write-Log "✅ Stopped Redis service"
        }
    } catch {
        Write-Log "Redis service not found or already stopped"
    }
    
    # Stop any remaining Python processes
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
    
    Write-Log "All components stopped"
}

function Get-ComponentStatus {
    Write-Log "Checking component status..."
    
    $status = @{
        Flask = $false
        Redis = $false
        RQWorker = $false
        Nginx = $false
    }
    
    # Check Flask
    if (Test-Path $PidFile) {
        $processId = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($processId -and (Get-Process -Id $processId -ErrorAction SilentlyContinue)) {
            $status.Flask = $true
            Write-Log "✅ Flask app is running (PID: $processId)"
        }
    }
    
    # Check Redis
    try {
        $redisService = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
        if ($redisService -and $redisService.Status -eq "Running") {
            $status.Redis = $true
            Write-Log "✅ Redis service is running"
        } else {
            Write-Log "❌ Redis service is not running"
        }
    } catch {
        Write-Log "❌ Redis service not found"
    }
    
    # Check RQ worker
    if (Test-Path $WorkerPidFile) {
        $workerId = Get-Content $WorkerPidFile -ErrorAction SilentlyContinue
        if ($workerId -and (Get-Process -Id $workerId -ErrorAction SilentlyContinue)) {
            $status.RQWorker = $true
            Write-Log "✅ RQ worker is running (PID: $workerId)"
        }
    }
    
    # Check Nginx
    try {
        $nginxProcess = Get-Process nginx -ErrorAction SilentlyContinue
        if ($nginxProcess) {
            $status.Nginx = $true
            Write-Log "✅ Nginx is running"
        } else {
            Write-Log "❌ Nginx is not running"
        }
    } catch {
        Write-Log "❌ Nginx not found"
    }
    
    # Test Flask health endpoint
    if ($status.Flask) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -UseBasicParsing -TimeoutSec 5
            Write-Log "🌐 Flask health check: OK (Status: $($response.StatusCode))"
        } catch {
            Write-Log "❌ Flask health check failed: $($_.Exception.Message)"
            $status.Flask = $false
        }
    }
    
    return $status
}

function Start-AllComponents {
    Write-Log "Starting CaseStrainer components..."
    
    # 1. Start Redis (if not already running)
    Write-Log "Starting Redis..."
    try {
        $redisService = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
        if ($redisService) {
            if ($redisService.Status -ne "Running") {
                Start-Service -Name "Redis"
                Write-Log "✅ Redis service started"
            } else {
                Write-Log "✅ Redis service already running"
            }
        } else {
            Write-Log "⚠️ Redis service not found. You may need to install Redis for Windows."
            Write-Log "   Download from: https://github.com/microsoftarchive/redis/releases"
            Write-Log "   Or use: winget install Redis.Redis"
        }
    } catch {
        Write-Log "❌ Failed to start Redis: $($_.Exception.Message)"
    }
    
    # Wait for Redis to be ready
    Start-Sleep -Seconds 3
    
    # 2. Start RQ worker
    Write-Log "Starting RQ worker..."
    try {
        $workerProcess = Start-Process -FilePath "python" -ArgumentList "-m", "rq", "worker", "casestrainer" -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru
        $workerProcess.Id | Out-File -FilePath $WorkerPidFile -Encoding UTF8
        Write-Log "✅ RQ worker started (PID: $($workerProcess.Id))"
    } catch {
        Write-Log "❌ Failed to start RQ worker: $($_.Exception.Message)"
    }
    
    # Wait for worker to start
    Start-Sleep -Seconds 5
    
    # 3. Start Flask app
    Write-Log "Starting Flask app..."
    try {
        $flaskProcess = Start-Process -FilePath "python" -ArgumentList "src\app_final_vue.py" -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru
        $flaskProcess.Id | Out-File -FilePath $PidFile -Encoding UTF8
        Write-Log "✅ Flask app started (PID: $($flaskProcess.Id))"
    } catch {
        Write-Log "❌ Failed to start Flask app: $($_.Exception.Message)"
    }
    
    # Wait for Flask to start
    Write-Log "Waiting for Flask app to start..."
    Start-Sleep -Seconds 15
    
    # 4. Test all components
    Write-Log "Testing all components..."
    $status = Get-ComponentStatus
    
    if ($status.Flask -and $status.Redis) {
        Write-Log "✅ CaseStrainer is running successfully!"
        Write-Host ""
        Write-Host "🌐 Access URLs:" -ForegroundColor Green
        Write-Host "   Local: http://localhost:5000/casestrainer/" -ForegroundColor Cyan
        Write-Host "   Health: http://localhost:5000/casestrainer/api/health" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "📋 Next steps to make it accessible at https://wolf.law.uw.edu/casestrainer/:" -ForegroundColor Yellow
        Write-Host "   1. Install and configure Nginx to proxy /casestrainer/ to localhost:5000" -ForegroundColor White
        Write-Host "   2. Set up SSL certificates for HTTPS" -ForegroundColor White
        Write-Host "   3. Configure firewall rules to allow external access" -ForegroundColor White
        Write-Host ""
        Write-Host "🔧 Management commands:" -ForegroundColor Blue
        Write-Host "   Status: .\start_casestrainer_complete.ps1 -Status" -ForegroundColor White
        Write-Host "   Stop:   .\start_casestrainer_complete.ps1 -Stop" -ForegroundColor White
    } else {
        Write-Log "❌ Some components failed to start. Check the logs above."
    }
}

# Main execution
if ($Stop) {
    Stop-AllComponents
} elseif ($Status) {
    Get-ComponentStatus
} else {
    Start-AllComponents
}
