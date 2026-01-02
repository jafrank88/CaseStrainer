$body = @{
    type = "url"
    url = "https://www.courts.wa.gov/opinions/pdf/D2%2060382-9-II%20Published%20Opinion.pdf"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "https://wolf.law.uw.edu/casestrainer/api/analyze" -Method Post -ContentType "application/json" -Body $body
    Write-Host "Response received:"
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error occurred:"
    Write-Host "Status Code:" $_.Exception.Response.StatusCode
    Write-Host "Status Description:" $_.Exception.Response.StatusDescription
    Write-Host "Error Message:" $_.Exception.Message
    $errorResponse = $_.Exception.Response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($errorResponse)
    $reader.BaseStream.Position = 0
    $errorBody = $reader.ReadToEnd()
    Write-Host "Error Body:" $errorBody
}
