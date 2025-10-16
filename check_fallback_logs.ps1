# Check if fallback verification is actually being called

Write-Host "`nSearching worker logs for fallback verification attempts..." -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

# Get logs from all workers
$workers = @("casestrainer-rqworker1-prod", "casestrainer-rqworker2-prod", "casestrainer-rqworker3-prod")

$fallbackStarted = 0
$fallbackSuccess = 0
$fallbackFailed = 0

foreach ($worker in $workers) {
    Write-Host "`nChecking $worker..." -ForegroundColor Yellow
    
    $logs = docker logs $worker --tail 1000 --since 30m 2>&1 | Out-String
    
    # Search for fallback messages
    $startMatches = [regex]::Matches($logs, "FALLBACK_VERIFY: Starting enhanced fallback")
    $successMatches = [regex]::Matches($logs, "FALLBACK SUCCESS")
    $failedMatches = [regex]::Matches($logs, "FALLBACK FAILED")
    $errorMatches = [regex]::Matches($logs, "FALLBACK ERROR")
    
    $fallbackStarted += $startMatches.Count
    $fallbackSuccess += $successMatches.Count
    $fallbackFailed += $failedMatches.Count + $errorMatches.Count
    
    if ($startMatches.Count -gt 0) {
        Write-Host "  ✓ Fallback started: $($startMatches.Count) times" -ForegroundColor Green
    }
    if ($successMatches.Count -gt 0) {
        Write-Host "  ✅ Fallback succeeded: $($successMatches.Count) times" -ForegroundColor Green
    }
    if ($failedMatches.Count -gt 0 -or $errorMatches.Count -gt 0) {
        Write-Host "  ❌ Fallback failed: $($failedMatches.Count + $errorMatches.Count) times" -ForegroundColor Red
    }
}

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "FALLBACK VERIFICATION SUMMARY" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""
Write-Host "Fallback Started:  $fallbackStarted" -ForegroundColor $(if ($fallbackStarted -gt 0) { 'Green' } else { 'Red' })
Write-Host "Fallback Success:  $fallbackSuccess" -ForegroundColor $(if ($fallbackSuccess -gt 0) { 'Green' } else { 'Red' })
Write-Host "Fallback Failed:   $fallbackFailed" -ForegroundColor Yellow
Write-Host ""

if ($fallbackStarted -eq 0) {
    Write-Host "Problem: Fallback verification is NOT being called!" -ForegroundColor Red
    Write-Host "   The code flow is not reaching the fallback verification method." -ForegroundColor Yellow
} elseif ($fallbackSuccess -eq 0) {
    Write-Host "Problem: Fallback is being called but ALL attempts are failing!" -ForegroundColor Yellow
    Write-Host "   Need to investigate why alternative sources are not working." -ForegroundColor Yellow
} else {
    Write-Host "Success: Fallback verification is working!" -ForegroundColor Green
}
