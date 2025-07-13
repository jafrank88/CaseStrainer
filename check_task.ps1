# Check async task status and analyze clustering
$taskId = "00327804-6013-4dbe-a775-715575f0a2c9"
$url = "http://localhost:5001/casestrainer/api/task_status/$taskId"

Write-Host "Checking task status for: $taskId" -ForegroundColor Green

try {
    $response = Invoke-WebRequest -Uri $url -Method GET
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "Task Status: $($data.status)" -ForegroundColor Yellow
    
    if ($data.status -eq "completed") {
        $citations = $data.citations
        $clusters = $data.clusters
        
        Write-Host "Citations found: $($citations.Count)" -ForegroundColor Green
        Write-Host "Clusters found: $($clusters.Count)" -ForegroundColor Green
        
        # Check for cluster metadata in citations
        $citationsWithMetadata = 0
        $citationsInClusters = 0
        
        foreach ($citation in $citations) {
            if ($citation.metadata) {
                $citationsWithMetadata++
                if ($citation.metadata.is_in_cluster) {
                    $citationsInClusters++
                    Write-Host "✅ Citation in cluster $($citation.metadata.cluster_id): $($citation.citation)" -ForegroundColor Green
                } else {
                    Write-Host "❌ Citation not in cluster: $($citation.citation)" -ForegroundColor Red
                }
            } else {
                Write-Host "❌ Citation has no metadata: $($citation.citation)" -ForegroundColor Red
            }
        }
        
        Write-Host "`nSummary:" -ForegroundColor Cyan
        Write-Host "  Citations with metadata: $citationsWithMetadata/$($citations.Count)"
        Write-Host "  Citations in clusters: $citationsInClusters/$($citations.Count)"
        
        if ($clusters) {
            Write-Host "`nCluster Details:" -ForegroundColor Cyan
            for ($i = 0; $i -lt $clusters.Count; $i++) {
                $cluster = $clusters[$i]
                Write-Host "  Cluster $($i+1): $($cluster.canonical_name) - $($cluster.citations.Count) citations"
            }
        }
        
        if ($citationsInClusters -gt 0) {
            Write-Host "`n🎉 SUCCESS: Clustering is working!" -ForegroundColor Green
        } else {
            Write-Host "`n❌ ISSUE: No citations have cluster metadata" -ForegroundColor Red
        }
    } else {
        Write-Host "Task not completed yet. Status: $($data.status)" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
} 