# Simple backend test to isolate the issue
Write-Host "Testing backend startup in isolation..." -ForegroundColor Cyan

# Set environment variables
$env:FLASK_ENV = "production"
$env:FLASK_APP = "src/app_final_vue.py"
$env:CORS_ORIGINS = "https://wolf.law.uw.edu"
$env:DATABASE_PATH = "data/citations.db"
$env:LOG_LEVEL = "INFO"
$env:PYTHONPATH = $PWD

Write-Host "Environment variables set:" -ForegroundColor Gray
Write-Host "  FLASK_ENV: $env:FLASK_ENV" -ForegroundColor Gray
Write-Host "  FLASK_APP: $env:FLASK_APP" -ForegroundColor Gray
Write-Host "  PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray

# Create data directory
$dataDir = "data"
if (!(Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force
    Write-Host "Created data directory: $dataDir" -ForegroundColor Green
}

# Test 1: Direct Python execution
Write-Host "`nTest 1: Testing direct Python execution..." -ForegroundColor Yellow
try {
    $result = python -c "from src.app_final_vue import create_app; app = create_app(); print('Flask app created successfully')" 2>&1
    Write-Host "Result: $result" -ForegroundColor Green
} catch {
    Write-Host "Error: $result" -ForegroundColor Red
    exit 1
}

# Test 2: Waitress command
Write-Host "`nTest 2: Testing Waitress startup..." -ForegroundColor Yellow
$waitressArgs = @(
    "--host=127.0.0.1"
    "--port=5000"
    "--threads=4"
    "--call"
    "src.app_final_vue:create_app"
)

Write-Host "Command: waitress-serve $($waitressArgs -join ' ')" -ForegroundColor Gray

try {
    # Create log directory
    if (!(Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs" -Force
    }
    
    # Start waitress and capture output
    $process = Start-Process -FilePath "waitress-serve" -ArgumentList $waitressArgs -NoNewWindow -PassThru -RedirectStandardOutput "logs/test_backend.log" -RedirectStandardError "logs/test_backend_error.log"
    
    Write-Host "Process started with PID: $($process.Id)" -ForegroundColor Green
    
    # Wait and check if it's still running
    Start-Sleep -Seconds 5
    
    if ($process.HasExited) {
        $exitCode = $process.ExitCode
        Write-Host "Process exited with code: $exitCode" -ForegroundColor Red
        Write-Host "Error log contents:" -ForegroundColor Red
        Get-Content "logs/test_backend_error.log" -ErrorAction SilentlyContinue
        Write-Host "Output log contents:" -ForegroundColor Yellow
        Get-Content "logs/test_backend.log" -ErrorAction SilentlyContinue
    } else {
        Write-Host "Process is still running!" -ForegroundColor Green
        
        # Test if server responds
        Start-Sleep -Seconds 2
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -TimeoutSec 5 -UseBasicParsing
            Write-Host "Server responds with status: $($response.StatusCode)" -ForegroundColor Green
        } catch {
            Write-Host "Server not responding: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "Error log contents:" -ForegroundColor Red
            Get-Content "logs/test_backend_error.log" -ErrorAction SilentlyContinue
        }
        
        # Stop the process
        Write-Host "Stopping test process..." -ForegroundColor Yellow
        Stop-Process -Id $process.Id -Force
    }
} catch {
    Write-Host "Failed to start process: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nTest completed." -ForegroundColor Cyan