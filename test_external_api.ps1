# Test the external wolf.law.uw.edu API
$url = "https://wolf.law.uw.edu/casestrainer/api/analyze"

$body = @{
    type = "url"
    url = "https://www.courtlistener.com/opinion/10460933/robert-cassell-v-state-of-alaska-department-of-fish-game-board-of-game/"
} | ConvertTo-Json

Write-Host "Submitting URL to API..." -ForegroundColor Cyan
Write-Host "Endpoint: $url" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri $url -Method POST -Body $body -ContentType "application/json"
    
    $taskId = $response.request_id
    Write-Host "`nJob submitted: $taskId" -ForegroundColor Green
    Write-Host "Status: $($response.message)" -ForegroundColor Yellow
    
    # Poll for completion
    $statusUrl = "https://wolf.law.uw.edu/casestrainer/api/task_status/$taskId"
    $maxAttempts = 20
    $attempt = 0
    
    Write-Host "`nPolling for completion..." -ForegroundColor Cyan
    
    while ($attempt -lt $maxAttempts) {
        Start-Sleep -Seconds 2
        $attempt++
        
        try {
            $status = Invoke-RestMethod -Uri $statusUrl -Method GET
            Write-Host "  Attempt $attempt : $($status.status) - $($status.progress)%" -ForegroundColor Gray
            
            if ($status.status -eq "completed" -or $status.status -eq "finished") {
                Write-Host "`nJob completed!" -ForegroundColor Green
                
                # The status response already contains the full result
                $result = $status
                
                Write-Host "`n=== RESULTS ===" -ForegroundColor Cyan
                Write-Host "Total citations: $($result.citations.Count)" -ForegroundColor Yellow
                Write-Host "Total clusters: $($result.clusters.Count)" -ForegroundColor Yellow
                
                $verified = ($result.citations | Where-Object { $_.verified -eq $true }).Count
                Write-Host "Verified citations: $verified" -ForegroundColor $(if ($verified -gt 0) { "Green" } else { "Red" })
                
                Write-Host "`n=== First 5 Citations ===" -ForegroundColor Cyan
                $result.citations | Select-Object -First 5 | ForEach-Object {
                    $check = if ($_.verified) { "[V]" } else { "[X]" }
                    $color = if ($_.verified) { "Green" } else { "Red" }
                    Write-Host "$check $($_.citation)" -ForegroundColor $color
                    Write-Host "    Canonical: $($_.canonical_name) ($($_.canonical_date))" -ForegroundColor Gray
                    Write-Host "    Source: $($_.verification_source)" -ForegroundColor DarkGray
                }
                
                # Save full result
                $result | ConvertTo-Json -Depth 10 | Out-File "test_api_result.json"
                Write-Host "`nFull result saved to: test_api_result.json" -ForegroundColor Green
                
                break
            }
            
            if ($status.status -eq "failed") {
                Write-Host "`nJob failed!" -ForegroundColor Red
                Write-Host "Error: $($status.error)" -ForegroundColor Red
                break
            }
        }
        catch {
            Write-Host "  Error checking status: $_" -ForegroundColor Red
        }
    }
    
    if ($attempt -eq $maxAttempts) {
        Write-Host "`nTimeout waiting for job completion" -ForegroundColor Red
    }
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
