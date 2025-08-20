# Simple CaseStrainer Startup Script
Write-Host "Starting CaseStrainer..." -ForegroundColor Green

# Stop any existing Python processes
$existingProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
    $_.ProcessName -eq "python" 
}

if ($existingProcess) {
    Write-Host "Stopping existing Python processes..." -ForegroundColor Yellow
    $existingProcess | ForEach-Object { 
        try { 
            Stop-Process -Id $_.Id -Force 
            Write-Host "Stopped Python process: $($_.Id)" -ForegroundColor Green
        } catch {
            Write-Host "Could not stop Python process $($_.Id)" -ForegroundColor Red
        }
    }
    Start-Sleep -Seconds 2
}

# Start CaseStrainer
Write-Host "Starting CaseStrainer Flask app..." -ForegroundColor Cyan
$process = Start-Process -FilePath "python" -ArgumentList "src\app_final_vue.py" -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru

# Wait for startup
Write-Host "Waiting for CaseStrainer to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test if it's responding
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ CaseStrainer started successfully with PID: $($process.Id)" -ForegroundColor Green
        Write-Host "🌐 Access URL: http://localhost:5000/casestrainer/" -ForegroundColor Cyan
        Write-Host "🔧 API Health: http://localhost:5000/casestrainer/api/health" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "To make it accessible at https://wolf.law.uw.edu/casestrainer/:" -ForegroundColor Yellow
        Write-Host "1. Configure your web server to proxy /casestrainer/ to localhost:5000" -ForegroundColor White
        Write-Host "2. Set up SSL certificates for HTTPS" -ForegroundColor White
        Write-Host "3. Configure firewall rules to allow external access" -ForegroundColor White
    } else {
        Write-Host "⚠️ CaseStrainer started but health check failed: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Failed to start CaseStrainer: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check the logs for more details" -ForegroundColor Yellow
}