$taskId = "cfd88650-6d95-4c25-9370-6fc788ee385f"
$url = "https://wolf.law.uw.edu/casestrainer/api/task_status/$taskId"

try {
    $response = Invoke-RestMethod -Uri $url -Method Get
    
    Write-Host "`nTask Status for: $taskId" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Status: $($response.status)" -ForegroundColor Yellow
    Write-Host "Success: $($response.success)" -ForegroundColor Yellow
    
    if ($response.citations) {
        Write-Host "Citations: $($response.citations.Count)" -ForegroundColor Green
    }
    
    if ($response.error) {
        Write-Host "Error: $($response.error)" -ForegroundColor Red
    }
    
    if ($response.progress_data) {
        Write-Host ""
        Write-Host "Progress:" -ForegroundColor Cyan
        Write-Host "  Overall: $($response.progress_data.overall_progress)%" -ForegroundColor White
        Write-Host "  Current Step: $($response.progress_data.current_step)/$($response.progress_data.total_steps)" -ForegroundColor White
        Write-Host "  Message: $($response.progress_data.current_message)" -ForegroundColor White
        
        if ($response.progress_data.elapsed_time) {
            $elapsed = [math]::Round($response.progress_data.elapsed_time, 1)
            Write-Host "  Elapsed: ${elapsed}s" -ForegroundColor White
        }
    }
    
    Write-Host ""
    Write-Host "Full Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 5
    
} catch {
    Write-Host "Error checking task: $_" -ForegroundColor Red
}
