Write-Host "🔧 Fixing Docker Production Services" -ForegroundColor Green
Write-Host "=" * 50

# Step 1: Stop all services
Write-Host "`n📋 Step 1: Stopping all services..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml down

# Step 2: Stop Flask development server
Write-Host "`n📋 Step 2: Stopping Flask development server..." -ForegroundColor Yellow
Write-Host "Looking for processes using port 5000..." -ForegroundColor Cyan
$portProcess = netstat -ano | findstr :5000
if ($portProcess) {
    Write-Host "Found process using port 5000:" -ForegroundColor Yellow
    Write-Host $portProcess -ForegroundColor Gray
    $pid = ($portProcess -split '\s+')[4]
    Write-Host "Killing process PID: $pid" -ForegroundColor Yellow
    taskkill /F /PID $pid
} else {
    Write-Host "No process found using port 5000" -ForegroundColor Green
}

# Step 3: Clean up Docker resources
Write-Host "`n📋 Step 3: Cleaning up Docker resources..." -ForegroundColor Yellow
docker container prune -f
docker network prune -f

# Step 4: Start Redis first
Write-Host "`n📋 Step 4: Starting Redis..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml up -d redis

# Wait for Redis to be ready
Write-Host "Waiting for Redis to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Check Redis status
Write-Host "`n📋 Checking Redis status..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml logs redis

# Step 5: Start backend
Write-Host "`n📋 Step 5: Starting backend..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml up -d backend

# Wait for backend to be ready
Write-Host "Waiting for backend to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 15

# Check backend status
Write-Host "`n📋 Checking backend status..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml logs backend

# Step 6: Start all services
Write-Host "`n📋 Step 6: Starting all services..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml up -d

# Step 7: Check final status
Write-Host "`n📋 Step 7: Checking final status..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml ps

Write-Host "`n✅ Docker production services fix completed!" -ForegroundColor Green
Write-Host "`n🌐 Services should be available at:" -ForegroundColor Cyan
Write-Host "   Backend API: http://localhost:5001" -ForegroundColor White
Write-Host "   Frontend: http://localhost:8080" -ForegroundColor White
Write-Host "   Nginx: http://localhost:80" -ForegroundColor White

Write-Host "`nPress any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 