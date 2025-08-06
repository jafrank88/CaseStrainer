param([switch]$Quick, [switch]$Fast, [switch]$Full, [switch]$Help)

if ($Help) { 
    Write-Host "CaseStrainer Launcher" -ForegroundColor Cyan
    Write-Host "  .\cslaunch.ps1              # Intelligent auto-detect (recommended)" -ForegroundColor Green
    Write-Host "  .\cslaunch.ps1 -Fast        # Fast Start (restart with latest code)" -ForegroundColor Cyan
    Write-Host "  .\cslaunch.ps1 -Quick       # Quick Start (when everything is ready)" -ForegroundColor Green
    Write-Host "  .\cslaunch.ps1 -Full        # Full Rebuild (complete reset)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Auto-detection logic:" -ForegroundColor White
    Write-Host "  • No containers exist → Full Rebuild" -ForegroundColor Gray
    Write-Host "  • Containers stopped → Fast Start" -ForegroundColor Gray
    Write-Host "  • Code changes detected → Fast Start" -ForegroundColor Gray
    Write-Host "  • No changes, running → Quick Start" -ForegroundColor Gray
}
elseif ($Quick) { 
    Write-Host "Quick Start" -ForegroundColor Green
    docker-compose -f docker-compose.prod.yml up -d
    Write-Host "Quick Start completed!" -ForegroundColor Green
}
elseif ($Fast) { 
    Write-Host "Fast Start" -ForegroundColor Cyan
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml up -d
    Write-Host "Fast Start completed!" -ForegroundColor Green
}
elseif ($Full) { 
    Write-Host "Full Rebuild" -ForegroundColor Yellow
    docker-compose -f docker-compose.prod.yml down
    docker system prune -af --volumes
    docker-compose -f docker-compose.prod.yml build --no-cache
    docker-compose -f docker-compose.prod.yml up -d
    Write-Host "Full Rebuild completed!" -ForegroundColor Green
}
else { 
    Write-Host "Intelligent Auto-Detection..." -ForegroundColor Magenta
    
    # Check if Docker is running
    $dockerVersion = docker --version 2>$null
    if (-not $dockerVersion) {
        Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
        exit 1
    }
    
    # Check if containers exist and are running
    $containers = docker ps --filter "name=casestrainer" --format "table" 2>$null
    $allContainers = docker ps -a --filter "name=casestrainer" --format "table" 2>$null
    
    # Check for recent code changes (last 30 minutes)
    $recentChanges = $false
    
    # Check frontend changes
    $vueFiles = Get-ChildItem -Path "casestrainer-vue-new" -Recurse -Include "*.vue", "*.js", "*.css" -ErrorAction SilentlyContinue | 
               Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-30) }
    if ($vueFiles) {
        $recentChanges = $true
        Write-Host "Frontend files changed recently" -ForegroundColor Yellow
    }
    
    # Check backend changes
    $backendFiles = Get-ChildItem -Path "src" -Recurse -Include "*.py" -ErrorAction SilentlyContinue | 
                   Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-30) }
    if ($backendFiles) {
        $recentChanges = $true
        Write-Host "Backend files changed recently" -ForegroundColor Yellow
    }
    
    # Check Docker compose changes
    $composeFile = Get-ChildItem "docker-compose.prod.yml" -ErrorAction SilentlyContinue
    if ($composeFile -and $composeFile.LastWriteTime -gt (Get-Date).AddMinutes(-30)) {
        $recentChanges = $true
        Write-Host "Docker configuration changed recently" -ForegroundColor Yellow
    }
    
    # Determine the best action
    if (-not $allContainers) {
        Write-Host "No containers exist - using Full Rebuild" -ForegroundColor Yellow
        Write-Host "Full Rebuild" -ForegroundColor Yellow
        docker-compose -f docker-compose.prod.yml down
        docker system prune -af --volumes
        docker-compose -f docker-compose.prod.yml build --no-cache
        docker-compose -f docker-compose.prod.yml up -d
        Write-Host "Full Rebuild completed!" -ForegroundColor Green
    } elseif (-not $containers) {
        Write-Host "Containers exist but not running - using Fast Start" -ForegroundColor Cyan
        Write-Host "Fast Start" -ForegroundColor Cyan
        docker-compose -f docker-compose.prod.yml down
        docker-compose -f docker-compose.prod.yml up -d
        Write-Host "Fast Start completed!" -ForegroundColor Green
    } elseif ($recentChanges) {
        Write-Host "Code changes detected - using Fast Start" -ForegroundColor Cyan
        Write-Host "Fast Start" -ForegroundColor Cyan
        docker-compose -f docker-compose.prod.yml down
        docker-compose -f docker-compose.prod.yml up -d
        Write-Host "Fast Start completed!" -ForegroundColor Green
    } else {
        Write-Host "No recent changes, containers running - using Quick Start" -ForegroundColor Green
        Write-Host "Quick Start" -ForegroundColor Green
        docker-compose -f docker-compose.prod.yml up -d
        Write-Host "Quick Start completed!" -ForegroundColor Green
    }
}
