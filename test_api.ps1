# Test API endpoints
Write-Host "Testing API endpoints..." -ForegroundColor Green

# Test 1: Health endpoint
Write-Host "`n1. Testing health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:5000/casestrainer/api/health" -Method GET
    Write-Host "✅ Health endpoint: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Health endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Version endpoint
Write-Host "`n2. Testing version endpoint..." -ForegroundColor Yellow
try {
    $version = Invoke-RestMethod -Uri "http://localhost:5000/casestrainer/api/version" -Method GET
    Write-Host "✅ Version endpoint: $($version.version)" -ForegroundColor Green
} catch {
    Write-Host "❌ Version endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Process text endpoint
Write-Host "`n3. Testing process-text endpoint..." -ForegroundColor Yellow
$body = @{
    text = "See State v. Lewis, 115 Wn.2d 294, 298-99, 797 P.2d 1141 (1990)."
    extract_case_names = $true
    include_context = $true
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "http://localhost:5000/casestrainer/api/process-text" -Method POST -ContentType "application/json" -Body $body
    Write-Host "✅ Process-text endpoint: Success" -ForegroundColor Green
    Write-Host "   Citations found: $($result.citations.Count)" -ForegroundColor Cyan
    Write-Host "   Case names found: $($result.case_names.Count)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Process-text endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nAPI testing completed!" -ForegroundColor Green 