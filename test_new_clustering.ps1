# Test clustering fix with a new request
$testText = "A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"

$payload = @{
    type = "text"
    text = $testText
} | ConvertTo-Json

$headers = @{
    "Content-Type" = "application/json"
}

Write-Host "Testing clustering fix with new request..." -ForegroundColor Green

try {
    # Submit new request
    $response = Invoke-WebRequest -Uri "http://localhost:5001/casestrainer/api/analyze" -Method POST -Body $payload -Headers $headers
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "Response Status: $($data.status)" -ForegroundColor Yellow
    
    if ($data.status -eq "processing" -and $data.task_id) {
        $taskId = $data.task_id
        Write-Host "Async task submitted: $taskId" -ForegroundColor Green
        
        # Poll for results
        $maxAttempts = 30
        for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
            Start-Sleep -Seconds 1
            
            try {
                $statusResponse = Invoke-WebRequest -Uri "http://localhost:5001/casestrainer/api/task_status/$taskId" -Method GET
                $statusData = $statusResponse.Content | ConvertFrom-Json
                
                if ($statusData.status -eq "completed") {
                    Write-Host "Task completed!" -ForegroundColor Green
                    
                    $citations = $statusData.citations
                    $clusters = $statusData.clusters
                    
                    Write-Host "Citations found: $($citations.Count)" -ForegroundColor Green
                    Write-Host "Clusters found: $($clusters.Count)" -ForegroundColor Green
                    
                    # Check for cluster metadata
                    $withMetadata = 0
                    $inClusters = 0
                    
                    foreach ($citation in $citations) {
                        if ($citation.metadata) {
                            $withMetadata++
                            if ($citation.metadata.is_in_cluster) {
                                $inClusters++
                                Write-Host "✅ Citation in cluster $($citation.metadata.cluster_id): $($citation.citation)" -ForegroundColor Green
                            } else {
                                Write-Host "❌ Citation not in cluster: $($citation.citation)" -ForegroundColor Red
                            }
                        } else {
                            Write-Host "❌ Citation has no metadata: $($citation.citation)" -ForegroundColor Red
                        }
                    }
                    
                    Write-Host "`nSummary:" -ForegroundColor Cyan
                    Write-Host "  Citations with metadata: $withMetadata/$($citations.Count)"
                    Write-Host "  Citations in clusters: $inClusters/$($citations.Count)"
                    
                    if ($inClusters -gt 0) {
                        Write-Host "`n🎉 SUCCESS: Clustering is working!" -ForegroundColor Green
                        Write-Host "✅ Frontend should now display clusters correctly" -ForegroundColor Green
                    } else {
                        Write-Host "`n❌ ISSUE: No citations have cluster metadata" -ForegroundColor Red
                    }
                    
                    break
                } elseif ($statusData.status -eq "failed") {
                    Write-Host "Task failed: $($statusData.error)" -ForegroundColor Red
                    break
                } else {
                    Write-Host "Status: $($statusData.status) (attempt $attempt/$maxAttempts)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "Error checking status: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        if ($attempt -gt $maxAttempts) {
            Write-Host "Polling timed out" -ForegroundColor Red
        }
    } else {
        Write-Host "Unexpected response format" -ForegroundColor Red
    }
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
} 