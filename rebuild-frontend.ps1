# rebuild-frontend.ps1 - Rebuild Vue.js frontend only
# Use this when you've made changes to Vue components but don't need to rebuild backend

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Rebuilding Frontend (Vue.js)" -ForegroundColor Cyan  
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "[Step 1/3] Building Vue production bundle..." -ForegroundColor Yellow
Push-Location casestrainer-vue-new
try {
    # Build the Vue app
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n[ERROR] Vue build failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Vue build complete" -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host "`n[Step 2/3] Rebuilding frontend Docker container..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml up -d --build frontend-prod

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Frontend container rebuilt" -ForegroundColor Green
    
    Write-Host "`n[Step 3/3] Waiting for frontend to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "✅ FRONTEND REBUILD COMPLETE!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Frontend is now serving updated Vue files" -ForegroundColor Cyan
    Write-Host "Application: http://localhost" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "`n[ERROR] Frontend container build failed" -ForegroundColor Red
    exit 1
}
