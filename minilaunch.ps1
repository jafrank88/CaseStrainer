# Minimal CaseStrainer Docker Production Launcher
# Focuses on Docker Production Mode and Diagnostics

param(
    [ValidateSet("Production", "Diagnostics", "Menu")]
    [string]$Mode = "Menu",
    [switch]$Help
)

# Show help
if ($Help) {
    Write-Host @"
CaseStrainer Docker Launcher - Help

Usage:
  .\launcher-docker.ps1 [Options]

Options:
  -Mode Production    Start Docker Production Mode
  -Mode Diagnostics   Run Production Diagnostics
  -Mode Menu         Show interactive menu (default)
  -Help              Show this help

Examples:
  .\launcher-docker.ps1                    # Show menu
  .\launcher-docker.ps1 -Mode Production   # Start production directly
  .\launcher-docker.ps1 -Mode Diagnostics # Run diagnostics directly
"@ -ForegroundColor Cyan
    exit 0
}

function Show-Menu {
    Clear-Host
    Write-Host "`n" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " CaseStrainer Docker Launcher" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " 1. Docker Production Mode" -ForegroundColor Green
    Write-Host "    - Complete Docker Compose deployment"
    Write-Host "    - Redis, Backend, RQ Worker, Frontend, Nginx"
    Write-Host "    - Production-ready with SSL support"
    Write-Host ""
    Write-Host " 2. Production Diagnostics" -ForegroundColor Cyan
    Write-Host "    - Comprehensive system checks"
    Write-Host "    - Container health analysis"
    Write-Host "    - Performance monitoring"
    Write-Host ""
    Write-Host " 3. Stop All Services" -ForegroundColor Red
    Write-Host " 4. View Container Status" -ForegroundColor Yellow
    Write-Host " 5. View Logs" -ForegroundColor Yellow
    Write-Host " 0. Exit" -ForegroundColor Gray
    Write-Host ""
    
    $selection = Read-Host "Select an option (0-5)"
    return $selection
}

function Start-DockerProduction {
    Write-Host "`n=== Starting Docker Production Mode ===`n" -ForegroundColor Green
    
    $dockerComposeFile = "docker-compose.prod.yml"
    
    # Check if Docker is running
    Write-Host "Checking Docker status..." -ForegroundColor Yellow
    try {
        docker info 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
            return $false
        }
        Write-Host "✅ Docker is running" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker is not available: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    # Check if docker-compose.prod.yml exists
    if (-not (Test-Path $dockerComposeFile)) {
        Write-Host "❌ $dockerComposeFile not found" -ForegroundColor Red
        return $false
    }
    
    # Build Vue frontend
    Write-Host "`nBuilding Vue frontend..." -ForegroundColor Cyan
    Push-Location "casestrainer-vue-new"
    try {
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ npm install failed" -ForegroundColor Red
            return $false
        }
        
        npm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ npm build failed" -ForegroundColor Red
            return $false
        }
        Write-Host "✅ Vue frontend built successfully" -ForegroundColor Green
    } finally {
        Pop-Location
    }
    
    # Stop any existing containers
    Write-Host "`nStopping existing containers..." -ForegroundColor Yellow
    docker-compose -f $dockerComposeFile down 2>&1 | Out-Null
    
    # Start containers
    Write-Host "`nStarting Docker containers..." -ForegroundColor Cyan
    $startResult = Start-Process -FilePath "docker-compose" -ArgumentList "-f", $dockerComposeFile, "up", "-d", "--build" -WorkingDirectory $PSScriptRoot -NoNewWindow -PassThru -Wait
    
    if ($startResult.ExitCode -eq 0) {
        Write-Host "✅ Docker containers started successfully" -ForegroundColor Green
        
        # Wait for services to initialize
        Write-Host "`nWaiting for services to initialize..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        
        # Test backend health
        Write-Host "`nTesting backend health..." -ForegroundColor Yellow
        for ($i = 1; $i -le 8; $i++) {
            try {
                $result = Test-NetConnection -ComputerName localhost -Port 5001 -InformationLevel Quiet -WarningAction SilentlyContinue
                if ($result) {
                    Write-Host "✅ Backend is healthy and responding!" -ForegroundColor Green
                    break
                }
            } catch {}
            if ($i -lt 8) {
                Write-Host "Backend not ready yet, waiting... (attempt $i/8)" -ForegroundColor Yellow
                Start-Sleep -Seconds 5
            } else {
                Write-Host "⚠️  Backend health check failed after 8 attempts" -ForegroundColor Yellow
            }
        }
        
        # Show URLs
        Write-Host "`n=== Docker Production Mode Ready ===`n" -ForegroundColor Green
        Write-Host "Backend API:    http://localhost:5001/casestrainer/api/" -ForegroundColor Green
        Write-Host "Frontend Prod:  http://localhost:8080/" -ForegroundColor Green
        Write-Host "Nginx (HTTP):   http://localhost:80/" -ForegroundColor Green
        Write-Host "Nginx (HTTPS):  https://localhost:443/" -ForegroundColor Green
        Write-Host "Main Frontend:  https://localhost/casestrainer/" -ForegroundColor Green
        Write-Host "API Health:     https://localhost/casestrainer/api/health" -ForegroundColor Green
        
        Write-Host "`nDocker Commands:" -ForegroundColor Cyan
        Write-Host "  View logs:    docker-compose -f $dockerComposeFile logs [service]" -ForegroundColor Gray
        Write-Host "  Stop all:     docker-compose -f $dockerComposeFile down" -ForegroundColor Gray
        Write-Host "  Restart:      docker-compose -f $dockerComposeFile restart [service]" -ForegroundColor Gray
        
        # Open browser
        try {
            Start-Process "https://localhost/casestrainer/"
        } catch {
            Write-Host "Could not open browser automatically" -ForegroundColor Yellow
        }
        
        return $true
    } else {
        Write-Host "❌ Failed to start Docker containers" -ForegroundColor Red
        return $false
    }
}

function Show-ProductionDiagnostics {
    Write-Host "`n=== Production Diagnostics ===`n" -ForegroundColor Cyan
    
    # Check Docker status
    Write-Host "Checking Docker status..." -ForegroundColor Yellow
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker is available: $dockerVersion" -ForegroundColor Green
        } else {
            Write-Host "❌ Docker is not available" -ForegroundColor Red
            return
        }
    } catch {
        Write-Host "❌ Docker is not available: $($_.Exception.Message)" -ForegroundColor Red
        return
    }
    
    # Check container status
    Write-Host "`nChecking container status..." -ForegroundColor Yellow
    try {
        $containerStatus = docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        if ($containerStatus) {
            Write-Host "Container Status:" -ForegroundColor Gray
            Write-Host $containerStatus -ForegroundColor Gray
            
            # Count containers
            $containers = $containerStatus -split "`n" | Where-Object { $_ -match "casestrainer" }
            $runningCount = ($containers | Where-Object { $_ -match "Up" }).Count
            Write-Host "`nRunning containers: $runningCount" -ForegroundColor Green
        } else {
            Write-Host "❌ No CaseStrainer containers are running" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Could not check container status: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test API endpoints
    Write-Host "`nTesting API endpoints..." -ForegroundColor Yellow
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:5001/casestrainer/api/health" -Method GET -TimeoutSec 10 -ErrorAction SilentlyContinue
        if ($healthResponse) {
            Write-Host "✅ Health endpoint: Working" -ForegroundColor Green
        } else {
            Write-Host "❌ Health endpoint: Not responding" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Health endpoint: Error - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Check Redis
    Write-Host "`nChecking Redis..." -ForegroundColor Yellow
    try {
        $redisPing = docker exec casestrainer-redis-prod redis-cli ping 2>&1
        if ($LASTEXITCODE -eq 0 -and $redisPing -like "*PONG*") {
            Write-Host "✅ Redis is responding" -ForegroundColor Green
        } else {
            Write-Host "❌ Redis connectivity failed: $redisPing" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Redis check failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Check disk space
    Write-Host "`nChecking disk space..." -ForegroundColor Yellow
    try {
        $diskSpace = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='C:'"
        $diskPercent = [math]::Round(($diskSpace.FreeSpace/$diskSpace.Size)*100, 2)
        $freeGB = [math]::Round($diskSpace.FreeSpace/1GB, 2)
        $totalGB = [math]::Round($diskSpace.Size/1GB, 2)
        Write-Host "Disk C: $totalGB GB total, $freeGB GB free ($diskPercent% free)" -ForegroundColor Gray
        if ($diskPercent -lt 10) {
            Write-Host "⚠️  Low disk space warning!" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Could not check disk space: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # Check memory usage
    Write-Host "`nChecking memory usage..." -ForegroundColor Yellow
    try {
        $memory = Get-CimInstance -ClassName Win32_OperatingSystem
        $memPercent = [math]::Round(($memory.FreePhysicalMemory/$memory.TotalVisibleMemorySize)*100, 2)
        $freeGB = [math]::Round($memory.FreePhysicalMemory/1MB, 2)
        $totalGB = [math]::Round($memory.TotalVisibleMemorySize/1MB, 2)
        Write-Host "Memory: $totalGB GB total, $freeGB GB free ($memPercent% free)" -ForegroundColor Gray
        if ($memPercent -lt 20) {
            Write-Host "⚠️  Low memory warning!" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Could not check memory usage: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host "`n=== Diagnostics Complete ===`n" -ForegroundColor Green
}

function Stop-AllServices {
    Write-Host "`n=== Stopping All Services ===`n" -ForegroundColor Red
    
    try {
        docker-compose -f docker-compose.prod.yml down 2>&1 | Out-Null
        Write-Host "✅ All Docker services stopped" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error stopping services: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Show-ContainerStatus {
    Write-Host "`n=== Container Status ===`n" -ForegroundColor Cyan
    
    try {
        docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    } catch {
        Write-Host "❌ Could not get container status: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host "`nPress any key to return..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Show-Logs {
    Write-Host "`n=== Docker Logs ===`n" -ForegroundColor Cyan
    Write-Host "Available containers:" -ForegroundColor Yellow
    Write-Host "1. Backend (casestrainer-backend-prod)"
    Write-Host "2. Frontend (casestrainer-frontend-prod)"
    Write-Host "3. Nginx (casestrainer-nginx-prod)"
    Write-Host "4. Redis (casestrainer-redis-prod)"
    Write-Host "5. RQ Worker (casestrainer-rqworker-prod)"
    Write-Host "6. All containers"
    Write-Host ""
    
    $selection = Read-Host "Select container (1-6)"
    
    switch ($selection) {
        "1" { docker logs casestrainer-backend-prod --tail 50 }
        "2" { docker logs casestrainer-frontend-prod --tail 50 }
        "3" { docker logs casestrainer-nginx-prod --tail 50 }
        "4" { docker logs casestrainer-redis-prod --tail 50 }
        "5" { docker logs casestrainer-rqworker-prod --tail 50 }
        "6" { docker-compose -f docker-compose.prod.yml logs --tail 20 }
        default { Write-Host "Invalid selection" -ForegroundColor Red }
    }
    
    Write-Host "`nPress any key to return..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

# Main execution
try {
    if ($Mode -ne "Menu") {
        # Direct mode execution
        switch ($Mode) {
            "Production" { Start-DockerProduction }
            "Diagnostics" { Show-ProductionDiagnostics }
        }
    } else {
        # Interactive menu
        do {
            $selection = Show-Menu
            
            switch ($selection) {
                '1' { Start-DockerProduction }
                '2' { Show-ProductionDiagnostics }
                '3' { Stop-AllServices }
                '4' { Show-ContainerStatus }
                '5' { Show-Logs }
                '0' { exit 0 }
                default { 
                    Write-Host "`nInvalid selection. Please try again." -ForegroundColor Red
                    Start-Sleep -Seconds 1
                }
            }
            
            if ($selection -ne '0') {
                Write-Host "`nPress any key to return to menu..." -NoNewline
                $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
            }
        } while ($selection -ne '0')
    }
} catch {
    Write-Host "`nError: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}