# Test script to verify that the frontend shows both extracted and canonical names/dates
# when they differ (e.g., "Doe v. Wdae (1901)" vs canonical "Doe v. Wade (1973)")

$testData = @{
    text = @"
The court considered the case of Doe v. Wdae (1901) in determining the outcome.
This case established important precedent for privacy rights.
"@
    document_type = "legal_brief"
} | ConvertTo-Json

Write-Host "Testing API with fake extraction data..."
Write-Host "Input text: $($testData | ConvertFrom-Json | Select-Object -ExpandProperty text)"
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/analyze_enhanced" -Method POST -Body $testData -ContentType "application/json" -TimeoutSec 30
    
    Write-Host "Response status: $($response.StatusCode)"
    
    if ($response.StatusCode -eq 200) {
        $result = $response.Content | ConvertFrom-Json
        Write-Host "✅ API call successful!"
        Write-Host ""
        
        # Check if we have citations
        if ($result.citations -and $result.citations.Count -gt 0) {
            Write-Host "Found $($result.citations.Count) citations:"
            Write-Host ""
            
            for ($i = 0; $i -lt $result.citations.Count; $i++) {
                $citation = $result.citations[$i]
                Write-Host "Citation $($i + 1):"
                Write-Host "  Citation text: $($citation.citation)"
                Write-Host "  Extracted case name: $($citation.extracted_case_name)"
                Write-Host "  Extracted date: $($citation.extracted_date)"
                Write-Host "  Canonical case name: $($citation.canonical_name)"
                Write-Host "  Canonical date: $($citation.canonical_date)"
                Write-Host "  Verified: $($citation.verified)"
                Write-Host "  Error: $($citation.error)"
                Write-Host ""
                
                # Verify that extracted fields are present
                $extractedName = $citation.extracted_case_name
                $extractedDate = $citation.extracted_date
                
                if ($extractedName -and $extractedName -ne "N/A") {
                    Write-Host "✅ Extracted case name is present: '$extractedName'"
                } else {
                    Write-Host "❌ Extracted case name is missing or 'N/A'"
                }
                    
                if ($extractedDate -and $extractedDate -ne "N/A") {
                    Write-Host "✅ Extracted date is present: '$extractedDate'"
                } else {
                    Write-Host "❌ Extracted date is missing or 'N/A'"
                }
                    
                Write-Host ""
            }
        } else {
            Write-Host "❌ No citations found in response"
            Write-Host "Response keys: $($result.PSObject.Properties.Name -join ', ')"
            if ($result.error) {
                Write-Host "Error: $($result.error)"
            }
        }
    } else {
        Write-Host "❌ API call failed with status $($response.StatusCode)"
        Write-Host "Response: $($response.Content)"
    }
        
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)"
    if ($_.Exception.InnerException) {
        Write-Host "Inner error: $($_.Exception.InnerException.Message)"
    }
} 