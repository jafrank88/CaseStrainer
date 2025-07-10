# Test the actual API endpoint to see if the extraction is working

$url = "http://localhost:5000/casestrainer/api/analyze_enhanced"
$data = @{
    type = "text"
    text = "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions"
    citations = @("200 Wn.2d 72, 73, 514 P.3d 643")
} | ConvertTo-Json

Write-Host "Testing API endpoint..."
Write-Host "URL: $url"
Write-Host "Data: $data"

try {
    $response = Invoke-WebRequest -Uri $url -Method POST -Body $data -ContentType "application/json" -TimeoutSec 30
    
    Write-Host "`nResponse Status: $($response.StatusCode)"
    Write-Host "Response Headers: $($response.Headers)"
    
    if ($response.Content) {
        try {
            $responseJson = $response.Content | ConvertFrom-Json
            Write-Host "`nResponse JSON:"
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
        
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)"
    if ($_.Exception.InnerException) {
        Write-Host "Inner error: $($_.Exception.InnerException.Message)"
    }
} 