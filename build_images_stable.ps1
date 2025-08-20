# CaseStrainer Stable Image Builder
# Builds images one by one with pauses to avoid connection issues

Write-Host "CaseStrainer Stable Image Builder" -ForegroundColor Cyan
Write-Host "Building images one by one with stability checks..." -ForegroundColor Yellow
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "Docker is running" -ForegroundColor Green
} catch {
    Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Function to check Docker stability
function Test-DockerStability {
    try {
        docker info | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to build image with retry logic
function Build-Image {
    param(
        [string]$ImageName,
        [string]$DockerfilePath,
        [string]$BuildContext = "."
    )
    
    Write-Host "Building $ImageName..." -ForegroundColor Blue
    
    # Wait for Docker to be stable
    $attempts = 0
    $maxAttempts = 3
    
    while ($attempts -lt $maxAttempts) {
        $attempts++
        Write-Host "Attempt $attempts of $maxAttempts..." -ForegroundColor Yellow
        
        if (-not (Test-DockerStability)) {
            Write-Host "Docker not stable, waiting 30 seconds..." -ForegroundColor Red
            Start-Sleep -Seconds 30
            continue
        }
        
        # Try to build
        if ($BuildContext -eq ".") {
            docker build -t $ImageName -f $DockerfilePath .
        } else {
            docker build -t $ImageName -f $DockerfilePath $BuildContext
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "$ImageName built successfully!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "$ImageName build failed on attempt $attempts" -ForegroundColor Red
            if ($attempts -lt $maxAttempts) {
                Write-Host "Waiting 60 seconds before retry..." -ForegroundColor Yellow
                Start-Sleep -Seconds 60
            }
        }
    }
    
    Write-Host "$ImageName build failed after $maxAttempts attempts" -ForegroundColor Red
    return $false
}

# Build images one by one with stability checks
$successCount = 0
$totalImages = 4

Write-Host "Starting image builds with stability checks..." -ForegroundColor Green
Write-Host ""

# 1. Backend Image
if (Build-Image -ImageName "casestrainer-backend:latest" -DockerfilePath "docker/Dockerfile") {
    $successCount++
}
Write-Host "Waiting 30 seconds for Docker to stabilize..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 2. Frontend Image
if (Build-Image -ImageName "casestrainer-frontend:latest" -DockerfilePath "casestrainer-vue-new/Dockerfile.prod" -BuildContext "./casestrainer-vue-new") {
    $successCount++
}
Write-Host "Waiting 30 seconds for Docker to stabilize..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 3. Nginx Image
if (Build-Image -ImageName "casestrainer-nginx:latest" -DockerfilePath "nginx/Dockerfile" -BuildContext "./nginx") {
    $successCount++
}
Write-Host "Waiting 30 seconds for Docker to stabilize..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 4. RQ Worker Image
if (Build-Image -ImageName "casestrainer-rqworker:latest" -DockerfilePath "docker/Dockerfile") {
    $successCount++
}

Write-Host ""
Write-Host "Build Summary:" -ForegroundColor Cyan
Write-Host "Successfully built: $successCount of $totalImages images" -ForegroundColor $(if ($successCount -eq $totalImages) { "Green" } else { "Yellow" })

if ($successCount -gt 0) {
    Write-Host ""
    Write-Host "Built Images:" -ForegroundColor Cyan
    docker images | findstr casestrainer
    
    Write-Host ""
    Write-Host "You can now start CaseStrainer with:" -ForegroundColor Green
    Write-Host "   .\fast_start.ps1" -ForegroundColor White
}

if ($successCount -eq $totalImages) {
    Write-Host ""
    Write-Host "All images built successfully! CaseStrainer will start in seconds!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Some images failed to build. You may need to:" -ForegroundColor Yellow
    Write-Host "1. Wait for Docker to fully stabilize" -ForegroundColor White
    Write-Host "2. Run this script again" -ForegroundColor White
    Write-Host "3. Or try building individual images manually" -ForegroundColor White
}


