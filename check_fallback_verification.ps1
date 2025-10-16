# Check the most recent completed job for fallback verification
$taskId = "cda7e81a-f9b7-4b42-ac7f-4f9705975084"  # Your earlier completed job
$url = "https://wolf.law.uw.edu/casestrainer/api/task_status/$taskId"

Write-Host "`nChecking Fallback Verification Results" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Task ID: $taskId`n" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri $url -Method Get
    
    $citations = $response.citations
    $verified = 0
    $courtlistener = 0
    $fallback = 0
    $not_verified = 0
    
    Write-Host "Total Citations: $($citations.Count)" -ForegroundColor White
    Write-Host ""
    
    # Analyze verification sources
    foreach ($cit in $citations) {
        if ($cit.verified) {
            $verified++
            $source = $cit.verification_source
            
            if ($source -like "*courtlistener*" -or $source -like "*CourtListener*") {
                $courtlistener++
            } else {
                $fallback++
                Write-Host "✅ FALLBACK VERIFIED: $($cit.citation)" -ForegroundColor Green
                Write-Host "   Source: $source" -ForegroundColor Yellow
                Write-Host "   Name: $($cit.canonical_name)" -ForegroundColor Gray
                Write-Host ""
            }
        } else {
            $not_verified++
        }
    }
    
    Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
    Write-Host "VERIFICATION SUMMARY" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Total Citations:        $($citations.Count)" -ForegroundColor White
    Write-Host "Verified:               $verified" -ForegroundColor $(if ($verified -gt 0) { 'Green' } else { 'Red' })
    Write-Host "  - CourtListener:      $courtlistener" -ForegroundColor Yellow
    Write-Host "  - Fallback Sources:   $fallback" -ForegroundColor $(if ($fallback -gt 0) { 'Green' } else { 'Yellow' })
    Write-Host "Not Verified:           $not_verified" -ForegroundColor Red
    Write-Host ""
    
    if ($fallback -eq 0) {
        Write-Host "❌ NO FALLBACK VERIFICATION OCCURRED" -ForegroundColor Red
        Write-Host "   This means fallback sources (Justia, Leagle, etc.) are not being used." -ForegroundColor Yellow
    } else {
        Write-Host "✅ FALLBACK VERIFICATION IS WORKING!" -ForegroundColor Green
        Write-Host "   $fallback citations verified via alternative sources" -ForegroundColor Green
    }
    
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
