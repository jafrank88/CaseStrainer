# CaseStrainer 500 Error Diagnostic Script
Write-Host "=== CaseStrainer 500 Error Diagnostic ===" -ForegroundColor Cyan
Write-Host "This script will help identify the cause of the 500 error" -ForegroundColor Yellow
Write-Host ""

$config = @{
    BackendPort = 5000
    FrontendPort = 443
}

# Function to test a URL and show detailed response
function Test-URLDetailed {
    param(
        [string]$Url,
        [string]$Description
    )
    
    Write-Host "Testing $Description..." -ForegroundColor Cyan
    Write-Host "  URL: $Url" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        Write-Host "  Status: $($response.StatusCode) $($response.StatusDescription)" -ForegroundColor Green
        
        if ($response.Content.Length -lt 500) {
            Write-Host "  Content: $($response.Content)" -ForegroundColor Gray
        } else {
            Write-Host "  Content Length: $($response.Content.Length) bytes" -ForegroundColor Gray
        }
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode) {
            Write-Host "  Status: $statusCode" -ForegroundColor Red
            
            # Try to get error details
            try {
                $errorResponse = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($errorResponse)
                $errorContent = $reader.ReadToEnd()
                Write-Host "  Error Content: $errorContent" -ForegroundColor Red
            } catch {
                Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "  Connection Failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    Write-Host ""
}

# Step 1: Check if processes are running
Write-Host "=== Step 1: Process Check ===" -ForegroundColor Yellow
Write-Host ""

$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
$nginxProcesses = Get-Process nginx -ErrorAction SilentlyContinue

Write-Host "Python processes:" -ForegroundColor Cyan
if ($pythonProcesses) {
    $pythonProcesses | ForEach-Object {
        Write-Host "  PID $($_.Id): $($_.ProcessName)" -ForegroundColor Green
    }
} else {
    Write-Host "  No Python processes running" -ForegroundColor Red
}

Write-Host ""
Write-Host "Nginx processes:" -ForegroundColor Cyan
if ($nginxProcesses) {
    $nginxProcesses | ForEach-Object {
        Write-Host "  PID $($_.Id): $($_.ProcessName)" -ForegroundColor Green
    }
} else {
    Write-Host "  No Nginx processes running" -ForegroundColor Red
}

Write-Host ""

# Step 2: Check ports
Write-Host "=== Step 2: Port Check ===" -ForegroundColor Yellow
Write-Host ""

$portTests = @(
    @{ Port = $config.BackendPort; Service = "Backend Flask/Waitress" },
    @{ Port = $config.FrontendPort; Service = "Frontend Nginx" }
)

foreach ($test in $portTests) {
    Write-Host "Checking port $($test.Port) ($($test.Service))..." -ForegroundColor Cyan
    
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $test.Port -InformationLevel Quiet
        if ($connection) {
            Write-Host "  Port $($test.Port): OPEN" -ForegroundColor Green
        } else {
            Write-Host "  Port $($test.Port): CLOSED" -ForegroundColor Red
        }
    } catch {
        Write-Host "  Port $($test.Port): ERROR - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Step 3: Test Backend URLs
Write-Host "=== Step 3: Backend URL Tests ===" -ForegroundColor Yellow
Write-Host ""

$backendTests = @(
    @{ Url = "http://127.0.0.1:$($config.BackendPort)/"; Description = "Backend Root" },
    @{ Url = "http://127.0.0.1:$($config.BackendPort)/casestrainer/"; Description = "Backend CaseStrainer Root" },
    @{ Url = "http://127.0.0.1:$($config.BackendPort)/casestrainer/api/"; Description = "Backend API Root" },
    @{ Url = "http://127.0.0.1:$($config.BackendPort)/casestrainer/api/health"; Description = "Backend Health Check" }
)

foreach ($test in $backendTests) {
    Test-URLDetailed -Url $test.Url -Description $test.Description
}

# Step 4: Test Frontend URLs (through Nginx)
Write-Host "=== Step 4: Frontend URL Tests (through Nginx) ===" -ForegroundColor Yellow
Write-Host ""

$frontendTests = @(
    @{ Url = "https://localhost:$($config.FrontendPort)/"; Description = "Nginx Root" },
    @{ Url = "https://localhost:$($config.FrontendPort)/casestrainer/"; Description = "Frontend App" },
    @{ Url = "https://localhost:$($config.FrontendPort)/casestrainer/api/health"; Description = "API through Nginx" }
)

foreach ($test in $frontendTests) {
    Test-URLDetailed -Url $test.Url -Description $test.Description
}

# Step 5: Check log files
Write-Host "=== Step 5: Log File Check ===" -ForegroundColor Yellow
Write-Host ""

$logFiles = @(
    "logs/backend.log",
    "logs/backend_error.log",
    "logs/access.log",
    "logs/error.log"
)

foreach ($logFile in $logFiles) {
    Write-Host "Checking $logFile..." -ForegroundColor Cyan
    if (Test-Path $logFile) {
        $content = Get-Content $logFile -Tail 5 -ErrorAction SilentlyContinue
        if ($content) {
            Write-Host "  Last 5 lines:" -ForegroundColor Green
            $content | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        } else {
            Write-Host "  File exists but is empty" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  File not found" -ForegroundColor Red
    }
    Write-Host ""
}

# Step 6: Test Flask app import
Write-Host "=== Step 6: Flask App Import Test ===" -ForegroundColor Yellow
Write-Host ""

Write-Host "Testing Flask app import..." -ForegroundColor Cyan
try {
    $testResult = python -c "from src.app_final_vue import create_app; app = create_app(); print('SUCCESS: Flask app imported and created')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Flask Import: SUCCESS" -ForegroundColor Green
        Write-Host "  Output: $testResult" -ForegroundColor Gray
    } else {
        Write-Host "  Flask Import: FAILED" -ForegroundColor Red
        Write-Host "  Error: $testResult" -ForegroundColor Red
    }
} catch {
    Write-Host "  Flask Import: ERROR - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Step 7: Manual Waitress test
Write-Host "=== Step 7: Manual Waitress Test ===" -ForegroundColor Yellow
Write-Host ""

Write-Host "Testing Waitress command..." -ForegroundColor Cyan
Write-Host "Command: waitress-serve --host=127.0.0.1 --port=5001 --call src.app_final_vue:create_app" -ForegroundColor Gray
Write-Host ""

# Set environment variables
$env:FLASK_ENV = "production"
$env:FLASK_APP = "src/app_final_vue.py"
$env:PYTHONPATH = $PWD

try {
    Write-Host "Starting test Waitress server on port 5001..." -ForegroundColor Cyan
    $testProcess = Start-Process -FilePath "waitress-serve" -ArgumentList "--host=127.0.0.1", "--port=5001", "--call", "src.app_final_vue:create_app" -NoNewWindow -PassThru
    
    Write-Host "  Process started (PID: $($testProcess.Id))" -ForegroundColor Green
    Write-Host "  Waiting 5 seconds for startup..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    if ($testProcess.HasExited) {
        Write-Host "  Process exited immediately (Exit Code: $($testProcess.ExitCode))" -ForegroundColor Red
    } else {
        Write-Host "  Process is running" -ForegroundColor Green
        
        # Test the temporary server
        Test-URLDetailed -Url "http://127.0.0.1:5001/casestrainer/api/health" -Description "Test Waitress Server"
        
        # Stop the test process
        Write-Host "Stopping test server..." -ForegroundColor Yellow
        Stop-Process -Id $testProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  Test server stopped" -ForegroundColor Green
    }
} catch {
    Write-Host "  Failed to start test server: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Step 8: Recommendations
Write-Host "=== Step 8: Diagnostic Summary & Recommendations ===" -ForegroundColor Yellow
Write-Host ""

Write-Host "Based on the tests above, here are the most likely causes of the 500 error:" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Backend Issues:" -ForegroundColor White
Write-Host "   - Flask app import failure (check Step 6)" -ForegroundColor Gray
Write-Host "   - Waitress configuration problem (check Step 7)" -ForegroundColor Gray
Write-Host "   - Python dependencies missing" -ForegroundColor Gray
Write-Host "   - Database connection issues" -ForegroundColor Gray
Write-Host ""

Write-Host "2. Nginx Configuration Issues:" -ForegroundColor White
Write-Host "   - Incorrect proxy_pass configuration" -ForegroundColor Gray
Write-Host "   - SSL certificate problems" -ForegroundColor Gray
Write-Host "   - Static file path issues" -ForegroundColor Gray
Write-Host ""

Write-Host "3. Port Conflicts:" -ForegroundColor White
Write-Host "   - Another service using port 5000 or 443" -ForegroundColor Gray
Write-Host "   - Windows firewall blocking connections" -ForegroundColor Gray
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Green
Write-Host "1. Check the log files shown above for specific error messages" -ForegroundColor White
Write-Host "2. If Flask import failed (Step 6), fix Python/Flask issues first" -ForegroundColor White
Write-Host "3. If Waitress test failed (Step 7), there's a backend configuration issue" -ForegroundColor White
Write-Host "4. If backend works but frontend gives 500, it's an Nginx configuration issue" -ForegroundColor White
Write-Host ""

Write-Host "=== Diagnostic Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..." -NoNewline
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')