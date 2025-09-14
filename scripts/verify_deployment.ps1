# CaseStrainer Deployment Verification Script
# This script ensures all components are working correctly after deployment

param(
    [switch]$SkipFrontendRebuild,
    [switch]$SkipBackendRestart
)

Write-Host "=== CASESTRAINER DEPLOYMENT VERIFICATION ===" -ForegroundColor Green

# Test data
$testText = "Certified questions are questions of law that this court reviews de novo and in light`nof the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183`nWn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we`nreview de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018)."

$expectedResults = @{
    "183 Wn.2d 649" = "Lopez Demetrio v. Sakuma Bros. Farms"
    "192 Wn.2d 453" = "Spokane County v. Dep't of Fish & Wildlife"
    "355 P.3d 258" = "Lopez Demetrio v. Sakuma Bros. Farms"
    "430 P.3d 655" = "Spokane County v. Dep't of Fish & Wildlife"
}

# Step 1: Ensure containers are running
Write-Host "`n1. Checking container status..." -ForegroundColor Yellow
$containers = docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}"
Write-Host $containers

# Step 2: Restart backend if needed
if (-not $SkipBackendRestart) {
    Write-Host "`n2. Restarting backend to ensure latest code..." -ForegroundColor Yellow
    docker compose -f docker-compose.prod.yml restart backend
    Start-Sleep -Seconds 5
}

# Step 3: Rebuild frontend if needed
if (-not $SkipFrontendRebuild) {
    Write-Host "`n3. Rebuilding frontend to clear cache..." -ForegroundColor Yellow
    docker compose -f docker-compose.prod.yml build frontend-prod
    docker compose -f docker-compose.prod.yml restart frontend-prod
    Start-Sleep -Seconds 10
}

# Step 4: Test API directly
Write-Host "`n4. Testing API directly..." -ForegroundColor Yellow
$body = @{ type = "text"; text = $testText } | ConvertTo-Json
try {
    $response = Invoke-RestMethod -Uri "https://wolf.law.uw.edu/casestrainer/api/analyze" -Method POST -Body $body -ContentType "application/json"
    
    Write-Host "API Response:" -ForegroundColor Green
    $response.result.citations | ForEach-Object {
        $citation = $_.citation
        $caseName = $_.extracted_case_name
        $expected = $expectedResults[$citation]
        
        if ($caseName -eq $expected) {
            Write-Host "✅ $citation : $caseName" -ForegroundColor Green
        } else {
            Write-Host "❌ $citation : $caseName (Expected: $expected)" -ForegroundColor Red
        }
    }
    
    # Check clustering
    Write-Host "`nClustering Results:" -ForegroundColor Green
    $response.result.clusters | ForEach-Object {
        Write-Host "Cluster: '$($_.extracted_case_name)' | Size: $($_.size) | Citations: $($_.citations -join ', ')"
    }
    
} catch {
    Write-Host "❌ API Test Failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 5: Check backend logs for errors
Write-Host "`n5. Checking backend logs for errors..." -ForegroundColor Yellow
$logs = docker logs casestrainer-backend-prod --tail 20
if ($logs -match "ERROR|Exception|Failed") {
    Write-Host "❌ Backend errors detected:" -ForegroundColor Red
    Write-Host $logs
} else {
    Write-Host "✅ Backend logs look clean" -ForegroundColor Green
}

Write-Host "`n=== VERIFICATION COMPLETE ===" -ForegroundColor Green
Write-Host "If all tests passed, the deployment is working correctly." -ForegroundColor Green
Write-Host "If any tests failed, check the logs and fix the issues." -ForegroundColor Yellow
