Write-Host "Running PDF test..." -ForegroundColor Green
Write-Host ""

# Try to find Python
try {
    $pythonPath = Get-Command python -ErrorAction Stop
    Write-Host "Found Python: $($pythonPath.Source)" -ForegroundColor Yellow
    & python test_api_simple.py
}
catch {
    Write-Host "Python not found in PATH, trying alternatives..." -ForegroundColor Yellow
    
    # Try virtual environment
    if (Test-Path ".venv\Scripts\python.exe") {
        Write-Host "Found Python in virtual environment" -ForegroundColor Yellow
        & .\.venv\Scripts\python.exe test_api_simple.py
    }
    elseif (Test-Path "D:\Python\python.exe") {
        Write-Host "Found system Python" -ForegroundColor Yellow
        & "D:\Python\python.exe" test_api_simple.py
    }
    else {
        Write-Host "Python not found. Please run manually:" -ForegroundColor Red
        Write-Host "python test_api_simple.py" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 