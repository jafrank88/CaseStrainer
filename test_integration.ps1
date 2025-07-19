Write-Host "Activating virtual environment..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"

Write-Host "Running integration test..." -ForegroundColor Green
Set-Location src
python integration_test_streamlined.py quick

Write-Host "Test complete!" -ForegroundColor Green
Read-Host "Press Enter to continue" 