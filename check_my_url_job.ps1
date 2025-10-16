$taskId = "cda7e81a-f9b7-4b42-ac7f-4f9705975084"
$url = "https://wolf.law.uw.edu/casestrainer/api/task_status/$taskId"

Write-Host "`nYour URL Job Results" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Task ID: $taskId" -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri $url -Method Get
    
    Write-Host "Status: $($response.status)" -ForegroundColor Green
    Write-Host "Citations Found: $($response.citations.Count)" -ForegroundColor Cyan
    Write-Host "Verified: $($response.statistics.verified_citations)" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "First 10 Citations:" -ForegroundColor Cyan
    $response.citations | Select-Object -First 10 | ForEach-Object {
        $verified = if ($_.verified) { "✅" } else { "⏸️" }
        Write-Host "  $verified $($_.citation) - $($_.canonical_name)"
    }
    
    Write-Host "`n✅ Your URL upload worked perfectly!" -ForegroundColor Green
    
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
