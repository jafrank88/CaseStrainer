# Simple SSL Test for CaseStrainer
Write-Host "=== Simple SSL Test ===" -ForegroundColor Cyan
Write-Host ""

# Check certificate files
Write-Host "Certificate Files:" -ForegroundColor Yellow
$certFile = "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\ssl\WolfCertBundle.crt"
$keyFile = "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\ssl\wolf.law.uw.edu.key"

Write-Host "  Certificate: $(if (Test-Path $certFile) { 'EXISTS' } else { 'MISSING' })" -ForegroundColor $(if (Test-Path $certFile) { 'Green' } else { 'Red' })
Write-Host "  Key: $(if (Test-Path $keyFile) { 'EXISTS' } else { 'MISSING' })" -ForegroundColor $(if (Test-Path $keyFile) { 'Green' } else { 'Red' })

# Check processes
Write-Host ""
Write-Host "Process Status:" -ForegroundColor Yellow
$nginxCount = (Get-Process nginx -ErrorAction SilentlyContinue).Count
$pythonCount = (Get-Process python -ErrorAction SilentlyContinue).Count

Write-Host "  Nginx processes: $nginxCount" -ForegroundColor $(if ($nginxCount -gt 0) { 'Green' } else { 'Red' })
Write-Host "  Python processes: $pythonCount" -ForegroundColor $(if ($pythonCount -gt 0) { 'Green' } else { 'Red' })

# Test port
Write-Host ""
Write-Host "Port Test:" -ForegroundColor Yellow
try {
    $portOpen = Test-NetConnection -ComputerName localhost -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
    Write-Host "  Port 443: $(if ($portOpen) { 'OPEN' } else { 'CLOSED' })" -ForegroundColor $(if ($portOpen) { 'Green' } else { 'Red' })
} catch {
    Write-Host "  Port 443: ERROR" -ForegroundColor Red
}

# Test backend directly
Write-Host ""
Write-Host "Backend Test:" -ForegroundColor Yellow
try {
    $backend = Invoke-RestMethod -Uri "http://127.0.0.1:5000/casestrainer/api/health" -TimeoutSec 5
    Write-Host "  Backend API: SUCCESS ($($backend.status))" -ForegroundColor Green
} catch {
    Write-Host "  Backend API: FAILED" -ForegroundColor Red
}

# Quick nginx log check
Write-Host ""
Write-Host "Nginx Logs:" -ForegroundColor Yellow
$logFile = "nginx/logs/error.log"
if (Test-Path $logFile) {
    $errors = Get-Content $logFile -Tail 3 -ErrorAction SilentlyContinue
    if ($errors) {
        Write-Host "  Recent errors found - check manually" -ForegroundColor Yellow
    } else {
        Write-Host "  No recent errors" -ForegroundColor Green
    }
} else {
    Write-Host "  Error log not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Browser Test Required ===" -ForegroundColor Cyan
Write-Host "PowerShell SSL tests are unreliable." -ForegroundColor Yellow
Write-Host "Please test in your browser:" -ForegroundColor White
Write-Host ""
Write-Host "1. https://wolf.law.uw.edu/casestrainer/" -ForegroundColor Green
Write-Host "2. https://localhost:443/casestrainer/" -ForegroundColor Green
Write-Host ""
Write-Host "Expected results:" -ForegroundColor White
Write-Host "- No SSL warnings (you have real certificates)" -ForegroundColor Gray
Write-Host "- Vue.js application loads" -ForegroundColor Gray
Write-Host "- API calls work" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to exit"