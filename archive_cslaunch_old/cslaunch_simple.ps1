param(
    [switch]$Help,
    [switch]$Windows,
    [switch]$Direct
)

function Start-DirectMode {
    Write-Host "Starting CaseStrainer directly on Windows..." -ForegroundColor Green
    
    if (-not (Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    }
    
    # Stop any existing components
    Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
        $_.ProcessName -eq "python" 
    } | ForEach-Object {
        try { 
            Stop-Process -Id $_.Id -Force 
            Write-Host "Stopped Python process: $($_.Id)" -ForegroundColor Green
        } catch {
            Write-Host "Could not stop Python process $($_.Id)" -ForegroundColor Red
        }
    }
    Start-Sleep -Seconds 2
    
    # Start CaseStrainer
    Write-Host "Starting CaseStrainer Flask app..." -ForegroundColor Cyan
    try {
        $process = Start-Process -FilePath "python" -ArgumentList "src\app_final_vue.py" -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru
        $process.Id | Out-File -FilePath "logs\casestrainer.pid" -Encoding UTF8
        Write-Host "CaseStrainer started with PID: $($process.Id)" -ForegroundColor Green
    } catch {
        Write-Host "Failed to start CaseStrainer: $($_.Exception.Message)" -ForegroundColor Red
        return
    }
    
    Write-Host "Waiting for CaseStrainer to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "CaseStrainer started successfully!" -ForegroundColor Green
            Write-Host "Access URL: http://localhost:5000/casestrainer/" -ForegroundColor Cyan
        } else {
            Write-Host "CaseStrainer started but health check failed: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "CaseStrainer may still be starting up..." -ForegroundColor Yellow
    }
}

# Main script logic
if ($Help) { 
    Write-Host "CaseStrainer Simple Launcher" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "  .\cslaunch_simple.ps1        # Start CaseStrainer directly on Windows" -ForegroundColor Green
    Write-Host "  .\cslaunch_simple.ps1 -Help  # Show this help" -ForegroundColor Green
    Write-Host "  .\cslaunch_simple.ps1 -Windows # Start CaseStrainer directly on Windows" -ForegroundColor Green
    Write-Host "  .\cslaunch_simple.ps1 -Direct # Start CaseStrainer directly on Windows" -ForegroundColor Green
    Write-Host ""
    Write-Host "Note: This script runs CaseStrainer directly on Windows without Docker." -ForegroundColor Yellow
    Write-Host "Use this when Docker is not working or you prefer direct Windows mode." -ForegroundColor Yellow
}
elseif ($Windows -or $Direct) {
    Start-DirectMode
}
else {
    # Default behavior - start directly on Windows
    Start-DirectMode
} 