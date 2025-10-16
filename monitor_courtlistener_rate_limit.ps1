# Monitor CourtListener API Rate Limit
# Tests every 10 minutes and displays results

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "COURTLISTENER API RATE LIMIT MONITOR" -ForegroundColor Cyan
Write-Host "Testing every 10 minutes..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$testCount = 0

while ($true) {
    $testCount++
    
    Write-Host ""
    Write-Host "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))] Test #$testCount" -ForegroundColor Yellow
    Write-Host "----------------------------------------------------------------------------" -ForegroundColor Gray
    
    # Run the Python test
    $output = & python test_courtlistener_rate_limit.py 2>&1 | Out-String
    
    # Check if rate limited or successful
    if ($output -match "RATE LIMITED") {
        Write-Host "Status: STILL RATE LIMITED ❌" -ForegroundColor Red
        
        # Try to extract wait time from output
        if ($output -match '"wait_until":"([^"]+)"') {
            $waitUntil = $matches[1]
            Write-Host "Wait until: $waitUntil" -ForegroundColor Yellow
        }
    }
    elseif ($output -match "SUCCESS - API is working") {
        Write-Host "Status: API ACCESSIBLE! ✓" -ForegroundColor Green
        Write-Host ""
        Write-Host "============================================================================" -ForegroundColor Green
        Write-Host "RATE LIMIT HAS RESET - API IS NOW AVAILABLE!" -ForegroundColor Green
        Write-Host "============================================================================" -ForegroundColor Green
        
        # Play a beep to alert user
        [console]::beep(800, 500)
        
        break
    }
    else {
        Write-Host "Status: Unknown (check output above)" -ForegroundColor Yellow
    }
    
    # Wait 10 minutes before next test
    Write-Host ""
    Write-Host "Waiting 10 minutes until next test..." -ForegroundColor Gray
    Write-Host "Next test at: $((Get-Date).AddMinutes(10).ToString('HH:mm:ss'))" -ForegroundColor Gray
    
    Start-Sleep -Seconds 600  # 10 minutes
}

Write-Host ""
Write-Host "Monitoring stopped." -ForegroundColor Cyan
