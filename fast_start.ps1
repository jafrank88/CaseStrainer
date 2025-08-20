# CaseStrainer Fast Start Script
# Uses pre-built images for instant startup (no building required)

param(
    [switch]$Help,
    [switch]$Status,
    [switch]$Stop
)

if ($Help) {
    Write-Host "CaseStrainer Fast Start Script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  .\fast_start.ps1              # Start CaseStrainer instantly" -ForegroundColor Green
    Write-Host "  .\fast_start.ps1 -Status      # Check container status" -ForegroundColor Cyan
    Write-Host "  .\fast_start.ps1 -Stop        # Stop all containers" -ForegroundColor Red
    Write-Host "  .\fast_start.ps1 -Help        # Show this help" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Prerequisites:" -ForegroundColor White
    Write-Host "  • Run .\prebuild_images.ps1 first to build all images" -ForegroundColor Gray
    Write-Host "  • Docker Desktop must be running" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Benefits:" -ForegroundColor White
    Write-Host "  • Starts in seconds instead of minutes" -ForegroundColor Green
    Write-Host "  • No build time on startup" -ForegroundColor Green
    Write-Host "  • Consistent startup times" -ForegroundColor Green
    exit 0
}

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "Docker is running" -ForegroundColor Green
} catch {
    Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

if ($Status) {
    Write-Host "CaseStrainer Container Status:" -ForegroundColor Cyan
    Write-Host ""
    docker ps -a --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    exit 0
}

if ($Stop) {
    Write-Host "Stopping CaseStrainer containers..." -ForegroundColor Red
    docker-compose -f docker-compose.prebuild.yml down
    Write-Host "All containers stopped" -ForegroundColor Green
    exit 0
}

# Check if pre-built images exist
Write-Host "Checking for pre-built images..." -ForegroundColor Blue
$requiredImages = @("casestrainer-backend:latest", "casestrainer-frontend:latest", "casestrainer-nginx:latest", "casestrainer-rqworker:latest")
$missingImages = @()

foreach ($image in $requiredImages) {
    $exists = docker images --format "{{.Repository}}:{{.Tag}}" | Select-String -Pattern "^$image$"
    if ($exists) {
        Write-Host "$image found" -ForegroundColor Green
    } else {
        Write-Host "$image missing" -ForegroundColor Red
        $missingImages += $image
    }
}

if ($missingImages.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing required images. Please run the pre-builder first:" -ForegroundColor Red
    Write-Host "   .\prebuild_images.ps1" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "Starting CaseStrainer with pre-built images..." -ForegroundColor Green
Write-Host "   This will start in seconds instead of minutes!" -ForegroundColor Yellow

# Start containers using pre-built images
docker-compose -f docker-compose.prebuild.yml up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "CaseStrainer started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Container Status:" -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Host ""
    Write-Host "Access URLs:" -ForegroundColor Cyan
    Write-Host "   • Backend API: http://localhost:5000" -ForegroundColor White
    Write-Host "   • Frontend: http://localhost:8080" -ForegroundColor White
    Write-Host "   • Nginx: http://localhost:80" -ForegroundColor White
    Write-Host "   • Redis: localhost:6380" -ForegroundColor White
    
    Write-Host ""
    Write-Host "Management Commands:" -ForegroundColor Cyan
    Write-Host "   • Check status: .\fast_start.ps1 -Status" -ForegroundColor White
    Write-Host "   • Stop all: .\fast_start.ps1 -Stop" -ForegroundColor White
    Write-Host "   • View logs: docker-compose -f docker-compose.prebuild.yml logs -f" -ForegroundColor White
} else {
    Write-Host "Failed to start CaseStrainer" -ForegroundColor Red
    exit 1
}
