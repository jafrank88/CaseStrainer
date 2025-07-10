# Test the Docker production API to see if the extraction is working

$possibleUrls = @(
    "http://localhost:5000/casestrainer/api/analyze_enhanced",
    "http://localhost:80/casestrainer/api/analyze_enhanced", 
    "http://localhost/casestrainer/api/analyze_enhanced",
    "http://127.0.0.1:5000/casestrainer/api/analyze_enhanced"
)

$data = @{
    type = "text"
    text = "The court considered the case of Doe v. Wdae, 410 U.S. 113 (1901) in determining the outcome."
    citations = @("Doe v. Wdae, 410 U.S. 113 (1901)")
} | ConvertTo-Json

Write-Host "Testing Docker Production API..."
Write-Host "Data: $data"
Write-Host ""

foreach ($url in $possibleUrls) {
    Write-Host "Testing URL: $url"
    try {
        $response = Invoke-WebRequest -Uri $url -Method POST -Body $data -ContentType "application/json" -TimeoutSec 10
        
        Write-Host "✅ SUCCESS! Status: $($response.StatusCode)"
        
        if ($response.Content) {
            try {
                $responseJson = $response.Content | ConvertFrom-Json
                Write-Host "Response JSON:"
                Write-Host ($responseJson | ConvertTo-Json -Depth 10)
                
                # Check specific fields
                if ($responseJson.citations -and $responseJson.citations.Count -gt 0) {
                    $citation = $responseJson.citations[0]
                    Write-Host "`n🔍 FIELD ANALYSIS:"
                    Write-Host "  extracted_case_name: '$($citation.extracted_case_name)'"
                    Write-Host "  extracted_date: '$($citation.extracted_date)'"
                    Write-Host "  canonical_name: '$($citation.canonical_name)'"
                    Write-Host "  canonical_date: '$($citation.canonical_date)'"
                    
                    # Check if the mapping worked
                    if ($citation.extracted_case_name -eq 'EXTRACTED_FAKE_NAME_Y') {
                        Write-Host "✅ SUCCESS: extracted_case_name mapped correctly!"
                    } else {
                        Write-Host "❌ FAILED: extracted_case_name is '$($citation.extracted_case_name)' instead of 'EXTRACTED_FAKE_NAME_Y'"
                    }
                        
                    if ($citation.extracted_date -eq '2099-12-31') {
                        Write-Host "✅ SUCCESS: extracted_date mapped correctly!"
                    } else {
                        Write-Host "❌ FAILED: extracted_date is '$($citation.extracted_date)' instead of '2099-12-31'"
                    }
                } else {
                    Write-Host "❌ No citations found in response"
                }
                    
            } catch {
                Write-Host "Response Text: $($response.Content)"
            }
        } else {
            Write-Host "Empty response"
        }
        
        # If we get here, we found a working URL
        break
        
    } catch {
        Write-Host "❌ Error: $($_.Exception.Message)"
    }
    
    Write-Host ""
} 