# Check if fallback verification is being called

Write-Host "Searching worker logs for fallback verification..." -ForegroundColor Cyan

$logs1 = docker logs casestrainer-rqworker1-prod --tail 1000 --since 30m 2>&1 | Out-String
$logs2 = docker logs casestrainer-rqworker2-prod --tail 1000 --since 30m 2>&1 | Out-String
$logs3 = docker logs casestrainer-rqworker3-prod --tail 1000 --since 30m 2>&1 | Out-String

$allLogs = $logs1 + $logs2 + $logs3

Write-Host "`nSearching for fallback patterns..."

$started = ([regex]::Matches($allLogs, "FALLBACK_VERIFY: Starting")).Count
$success = ([regex]::Matches($allLogs, "FALLBACK SUCCESS")).Count
$failed = ([regex]::Matches($allLogs, "FALLBACK FAILED")).Count
$error = ([regex]::Matches($allLogs, "FALLBACK ERROR")).Count

Write-Host "`nRESULTS:" -ForegroundColor Yellow
Write-Host "Fallback Started: $started"
Write-Host "Fallback Success: $success"  
Write-Host "Fallback Failed: $failed"
Write-Host "Fallback Error: $error"

if ($started -eq 0) {
    Write-Host "`nPROBLEM: Fallback is NOT being called at all!" -ForegroundColor Red
} elseif ($success -eq 0) {
    Write-Host "`nPROBLEM: Fallback is called but ALL attempts fail!" -ForegroundColor Red
} else {
    Write-Host "`nSUCCESS: Fallback verification is working!" -ForegroundColor Green
}
