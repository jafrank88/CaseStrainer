# CaseStrainer Image Pre-builder
# This script builds all Docker images in advance for faster container startup

Write-Host "CaseStrainer Image Pre-builder" -ForegroundColor Cyan
Write-Host "Building all images in advance for instant startup..." -ForegroundColor Yellow
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "Docker is running" -ForegroundColor Green
} catch {
    Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Building Backend Image..." -ForegroundColor Blue
docker build -t casestrainer-backend:latest -f docker/Dockerfile .

if ($LASTEXITCODE -eq 0) {
    Write-Host "Backend image built successfully" -ForegroundColor Green
} else {
    Write-Host "Backend image build failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "Building Frontend Image..." -ForegroundColor Blue
docker build -t casestrainer-frontend:latest -f casestrainer-vue-new/Dockerfile.prod ./casestrainer-vue-new

if ($LASTEXITCODE -eq 0) {
    Write-Host "Frontend image built successfully" -ForegroundColor Green
} else {
    Write-Host "Frontend image build failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "Building Nginx Image..." -ForegroundColor Blue
docker build -t casestrainer-nginx:latest -f nginx/Dockerfile ./nginx

if ($LASTEXITCODE -eq 0) {
    Write-Host "Nginx image built successfully" -ForegroundColor Green
} else {
    Write-Host "Nginx image build failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "Building RQ Worker Images..." -ForegroundColor Blue
docker build -t casestrainer-rqworker:latest -f docker/Dockerfile .

if ($LASTEXITCODE -eq 0) {
    Write-Host "RQ Worker image built successfully" -ForegroundColor Green
} else {
    Write-Host "RQ Worker image build failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "Summary of Built Images:" -ForegroundColor Cyan
docker images | findstr casestrainer

Write-Host ""
Write-Host "Now you can start CaseStrainer instantly with:" -ForegroundColor Green
Write-Host "   .\fast_start.ps1" -ForegroundColor White
Write-Host ""
Write-Host "The containers will start in seconds instead of minutes!" -ForegroundColor Yellow
