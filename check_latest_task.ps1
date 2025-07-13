# Check the latest task for clustering
$taskId = "14a37f49-1784-4026-9f2e-9b26e05a6d0f"
$url = "http://localhost:5001/casestrainer/api/task_status/$taskId"

Write-Host "Checking latest task: $taskId"

$response = Invoke-WebRequest -Uri $url -Method GET
$data = $response.Content | ConvertFrom-Json

Write-Host "Status: $($data.status)"
Write-Host "Citations: $($data.citations.Count)"
Write-Host "Clusters: $($data.clusters.Count)"

# Check first few citations for metadata
$withMetadata = 0
$inClusters = 0

foreach ($citation in $data.citations) {
    if ($citation.metadata) {
        $withMetadata++
        if ($citation.metadata.is_in_cluster) {
            $inClusters++
            Write-Host "✅ IN CLUSTER: $($citation.citation)"
        } else {
            Write-Host "❌ NO CLUSTER: $($citation.citation)"
        }
    } else {
        Write-Host "❌ NO METADATA: $($citation.citation)"
    }
}

Write-Host "`nSummary:"
Write-Host "  With metadata: $withMetadata/$($data.citations.Count)"
Write-Host "  In clusters: $inClusters/$($data.citations.Count)"

if ($inClusters -gt 0) {
    Write-Host "`n🎉 SUCCESS: Clustering is working!"
} else {
    Write-Host "`n❌ ISSUE: No citations have cluster metadata"
} 