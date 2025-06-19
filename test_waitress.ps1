# Quick test script to debug Waitress startup
param(
    [string]$Port = "5000"
)

Write-Host "Testing Waitress startup..." -ForegroundColor Cyan

# Set environment
$env:FLASK_ENV = "production"
$env:FLASK_APP = "src/app_final_vue.py"
$env:PYTHONPATH = $PWD

Write-Host "Current directory: $PWD" -ForegroundColor Gray
Write-Host "PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray

# Test 1: Check if the app can be imported
Write-Host "`nTest 1: Testing Flask app import..." -ForegroundColor Yellow
try {
    $importTest = python -c "from src.app_final_vue import create_app; app = create_app(); print('App created successfully')" 2>&1
    Write-Host $importTest -ForegroundColor Green
} catch {
    Write-Host "Import failed: $importTest" -ForegroundColor Red
    exit 1
}

# Test 2: Try different Waitress command formats
Write-Host "`nTest 2: Testing Waitress command formats..." -ForegroundColor Yellow

$testCommands = @(
    "src.app_final_vue:create_app()",
    "src.app_final_vue:create_app",
    "--call src.app_final_vue:create_app"
)

foreach ($cmd in $testCommands) {
    Write-Host "  Testing: waitress-serve --host=127.0.0.1 --port=$Port $cmd" -ForegroundColor Gray
    
    try {
        # Start the process with a timeout
        $process = Start-Process -FilePath "waitress-serve" -ArgumentList "--host=127.0.0.1", "--port=$Port", $cmd -NoNewWindow -PassThru
        
        # Wait a few seconds to see if it starts successfully
        Start-Sleep -Seconds 3
        
        if (!$process.HasExited) {
            Write-Host "  Command started successfully (PID: $($process.Id))" -ForegroundColor Green
            
            # Test if the server is responding
            try {
                $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -TimeoutSec 5 -UseBasicParsing
                Write-Host "  Server responding with status: $($response.StatusCode)" -ForegroundColor Green
            } catch {
                Write-Host "  Server started but not responding: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
            # Stop the process
            Stop-Process -Id $process.Id -Force
            Write-Host "  Process stopped" -ForegroundColor Green
            break
        } else {
            Write-Host "  Command failed immediately (Exit code: $($process.ExitCode))" -ForegroundColor Red
        }
    } catch {
        Write-Host "  Command failed to start: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nTest completed." -ForegroundColor Cyan