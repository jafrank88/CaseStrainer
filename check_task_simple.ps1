# Simple check for clustering
$taskId = "00327804-6013-4dbe-a775-715575f0a2c9"
$url = "http://localhost:5001/casestrainer/api/task_status/$taskId"

Write-Host "Checking clustering for task: $taskId"

$response = Invoke-WebRequest -Uri $url -Method GET
$data = $response.Content | ConvertFrom-Json

Write-Host "Status: $($data.status)"
Write-Host "Citations: $($data.citations.Count)"
Write-Host "Clusters: $($data.clusters.Count)"

# Check first citation for metadata
if ($data.citations.Count -gt 0) {
    $firstCitation = $data.citations[0]
    Write-Host "First citation: $($firstCitation.citation)"
    
    if ($firstCitation.metadata) {
        Write-Host "Has metadata: YES"
        Write-Host "Is in cluster: $($firstCitation.metadata.is_in_cluster)"
        Write-Host "Cluster ID: $($firstCitation.metadata.cluster_id)"
    } else {
        Write-Host "Has metadata: NO"
    }
}

# Check if any citations have cluster metadata
$withMetadata = 0
$inClusters = 0

foreach ($citation in $data.citations) {
    if ($citation.metadata) {
        $withMetadata++
        if ($citation.metadata.is_in_cluster) {
            $inClusters++
        }
    }
}

Write-Host "Citations with metadata: $withMetadata/$($data.citations.Count)"
Write-Host "Citations in clusters: $inClusters/$($data.citations.Count)"

if ($inClusters -gt 0) {
    Write-Host "SUCCESS: Clustering is working!"
} else {
    Write-Host "ISSUE: No citations have cluster metadata"
} 