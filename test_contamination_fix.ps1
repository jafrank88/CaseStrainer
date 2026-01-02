# Test script to verify data contamination fix
$body = @{
    text = "This document discusses Fake Test Case v. Example Corporation, 2023. The citation 999 F.3d 123 is mentioned."
    enable_verification = $true
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5000/casestrainer/api/analyze" -Method Post -Body $body -ContentType "application/json"

Write-Host "Response:"
$response | ConvertTo-Json -Depth 10
