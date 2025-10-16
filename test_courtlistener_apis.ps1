# Test CourtListener APIs for "934 F.2d 401"

$apiKey = "***REDACTED_COURTLISTENER_KEY***"
$headers = @{ 
    Authorization = "Token $apiKey"
    "Content-Type" = "application/json"
}

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "TEST 1: Citation Lookup API (Batch)" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

$body = @{
    citations = @("934 F.2d 401")
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "https://www.courtlistener.com/api/rest/v4/citation-lookup/" `
        -Method POST `
        -Headers $headers `
        -Body $body

    Write-Host "`nFound $($response.Count) result(s):`n" -ForegroundColor Yellow
    
    $response | ForEach-Object {
        Write-Host "Case Name: $($_.cluster_case_names)" -ForegroundColor Green
        Write-Host "  Date Filed: $($_.date_filed)"
        Write-Host "  Court: $($_.court_citation_string)"
        Write-Host "  Citations: $($_.citations -join ', ')"
        Write-Host "  URL: https://www.courtlistener.com$($_.absolute_url)"
        Write-Host ""
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n" + "=" * 80 -ForegroundColor Cyan
Write-Host "TEST 2: Search API" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

try {
    $searchUrl = "https://www.courtlistener.com/api/rest/v4/search/?q=934%20F.2d%20401&type=o"
    $searchResponse = Invoke-RestMethod -Uri $searchUrl -Headers $headers
    
    Write-Host "`nSearch found $($searchResponse.count) result(s):`n" -ForegroundColor Yellow
    
    $searchResponse.results | Select-Object -First 5 | ForEach-Object {
        Write-Host "Case Name: $($_.caseName)" -ForegroundColor Green
        Write-Host "  Date: $($_.dateFiled)"
        Write-Host "  Court: $($_.court)"
        Write-Host "  Citations: $($_.citation -join ', ')"
        Write-Host "  URL: https://www.courtlistener.com$($_.absolute_url)"
        Write-Host ""
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n" + "=" * 80 -ForegroundColor Cyan
Write-Host "TEST 3: Direct Opinion Lookup - In Re Novak" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

try {
    $opinionUrl = "https://www.courtlistener.com/api/rest/v4/opinions/613867/"
    $opinionResponse = Invoke-RestMethod -Uri $opinionUrl -Headers $headers
    
    Write-Host "`nDirect lookup of opinion ID 613867:`n" -ForegroundColor Yellow
    Write-Host "Opinion ID: $($opinionResponse.id)" -ForegroundColor Green
    Write-Host "  Cluster: $($opinionResponse.cluster)"
    Write-Host "  Author: $($opinionResponse.author_str)"
    Write-Host "  Type: $($opinionResponse.type)"
    Write-Host ""
    
    # Get the cluster details
    $clusterResponse = Invoke-RestMethod -Uri $opinionResponse.cluster -Headers $headers
    Write-Host "Cluster Details:" -ForegroundColor Green
    Write-Host "  Case Name: $($clusterResponse.case_name)"
    Write-Host "  Date Filed: $($clusterResponse.date_filed)"
    Write-Host "  Citations: $($clusterResponse.citations -join ', ')"
    Write-Host "  URL: https://www.courtlistener.com$($clusterResponse.absolute_url)"
    
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
