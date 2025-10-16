# Wait a moment then check job status
Start-Sleep -Seconds 8

$taskId = "client-1760575745397-i2wi7x3i5"
$url = "https://wolf.law.uw.edu/casestrainer/api/task_status/$taskId"

Write-Host "`nChecking job: $taskId" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri $url -Method Get
    
    Write-Host "`nStatus: $($response.status)" -ForegroundColor $(if ($response.status -eq 'completed') { 'Green' } elseif ($response.status -eq 'processing') { 'Yellow' } else { 'Red' })
    Write-Host "Success: $($response.success)"
    
    if ($response.citations) {
        Write-Host "Citations Found: $($response.citations.Count)" -ForegroundColor Green
    }
    
    if ($response.progress_data) {
        $prog = $response.progress_data
        Write-Host "`nProgress: $($prog.overall_progress)%" -ForegroundColor Cyan
        Write-Host "Step: $($prog.current_step)/$($prog.total_steps)"
        Write-Host "Message: $($prog.current_message)"
        
        if ($prog.elapsed_time) {
            $elapsed = [math]::Round($prog.elapsed_time, 1)
            Write-Host "Elapsed: ${elapsed}s"
        }
        
        Write-Host "`nSteps:" -ForegroundColor Cyan
        foreach ($step in $prog.steps) {
            $icon = switch ($step.status) {
                'completed' { '✅' }
                'in_progress' { '⏳' }
                'pending' { '⏸️' }
                default { '❓' }
            }
            Write-Host "  $icon $($step.name): $($step.progress)% - $($step.status)"
        }
    }
    
    if ($response.error) {
        Write-Host "`nError: $($response.error)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "Error checking status: $_" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Yellow
}
