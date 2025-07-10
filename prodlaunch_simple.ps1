# Simplified CaseStrainer Docker Production Launcher
# Focuses on core functionality with real-time feedback

param(
    [ValidateSet("Production", "Diagnostics", "Menu")]
    [string]$Mode = "Menu",
    [switch]$Help
)

# Show help
if ($Help) {
    Write-Host @"
Simplified CaseStrainer Docker Production Launcher

Usage:
  .\prodlaunch_simple.ps1 [Options]

Options:
  -Mode Production    Start Docker Production Mode
  -Mode Diagnostics   Run Production Diagnostics
  -Mode Menu         Show interactive menu (default)
  -Help              Show this help

Examples:
  .\prodlaunch_simple.ps1                    # Show menu
  .\prodlaunch_simple.ps1 -Mode Production   # Start production directly
  .\prodlaunch_simple.ps1 -Mode Diagnostics  # Run diagnostics directly
"@ -ForegroundColor Cyan
    exit 0
}

function Test-DockerAvailability {
    try {
        $null = docker info --format "{{.ServerVersion}}" 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Show-Menu {
    Clear-Host
    Write-Host "`n" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " Simplified CaseStrainer Docker Launcher" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " 1. Docker Production Mode" -ForegroundColor Green
    Write-Host "    - Complete Docker Compose deployment" -ForegroundColor Gray
    Write-Host "    - Redis, Backend, RQ Workers, Frontend, Nginx" -ForegroundColor Gray
    Write-Host ""
    Write-Host " 2. Production Diagnostics" -ForegroundColor Cyan
    Write-Host "    - Container health checks" -ForegroundColor Gray
    Write-Host "    - Service status" -ForegroundColor Gray
    Write-Host ""
    Write-Host " 0. Exit" -ForegroundColor Gray
    Write-Host ""
    
    do {
        $selection = Read-Host "Select an option (0-2)"
        if ($selection -match "^[0-2]$") {
            return $selection
        } else {
            Write-Host "Invalid selection. Please enter a number between 0 and 2." -ForegroundColor Red
        }
    } while ($true)
}

function Start-DockerProduction {
    Write-Host "`n=== Starting Docker Production Mode ===`n" -ForegroundColor Green
    
    try {
        # Check Docker availability
        if (-not (Test-DockerAvailability)) {
            Write-Host "❌ Docker is not running or not available" -ForegroundColor Red
            Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
            return $false
        }
        Write-Host "✅ Docker is running" -ForegroundColor Green
        
        $dockerComposeFile = Join-Path $PSScriptRoot "docker-compose.prod.yml"
        
        # Build Vue frontend with real-time feedback
        Write-Host "`nBuilding Vue frontend..." -ForegroundColor Cyan
        $vueDir = Join-Path $PSScriptRoot "casestrainer-vue-new"
        
        if (-not (Test-Path $vueDir)) {
            Write-Host "❌ Vue directory not found: $vueDir" -ForegroundColor Red
            return $false
        }
        
        Push-Location $vueDir
        try {
            # Check if package.json exists
            if (-not (Test-Path "package.json")) {
                throw "package.json not found in Vue directory"
            }
            
            Write-Host "Running npm install..." -ForegroundColor Yellow
            Write-Host "This may take a few minutes. Please wait..." -ForegroundColor Gray
            
            # Run npm install with real-time output
            $installJob = Start-Job -ScriptBlock {
                param($VueDir)
                Set-Location $VueDir
                & npm install 2>&1
            } -ArgumentList $vueDir
            
            # Show progress while npm install runs
            $startTime = Get-Date
            $dots = 0
            
            while ($installJob.State -eq "Running") {
                $elapsed = (Get-Date) - $startTime
                $elapsedStr = "{0:mm}:{0:ss}" -f $elapsed
                $dotStr = "." * ($dots % 4)
                Write-Host "`rnpm install in progress$dotStr ($elapsedStr elapsed)" -NoNewline -ForegroundColor Yellow
                Start-Sleep -Seconds 1
                $dots++
            }
            
            Write-Host "`n" # New line after progress
            
            # Get the result
            $installResult = Receive-Job $installJob
            Remove-Job $installJob
            
            # Check for errors
            if ($installResult -match "error|Error|ERROR") {
                Write-Host "❌ npm install encountered errors:" -ForegroundColor Red
                $installResult | Where-Object { $_ -match "error|Error|ERROR" } | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
                throw "npm install failed"
            }
            
            Write-Host "✅ npm install completed successfully" -ForegroundColor Green
            
            Write-Host "Running npm build..." -ForegroundColor Yellow
            Write-Host "Building Vue frontend for production..." -ForegroundColor Gray
            
            # Run npm build with real-time output
            $buildJob = Start-Job -ScriptBlock {
                param($VueDir)
                Set-Location $VueDir
                & npm run build 2>&1
            } -ArgumentList $vueDir
            
            # Show progress while npm build runs
            $startTime = Get-Date
            $dots = 0
            
            while ($buildJob.State -eq "Running") {
                $elapsed = (Get-Date) - $startTime
                $elapsedStr = "{0:mm}:{0:ss}" -f $elapsed
                $dotStr = "." * ($dots % 4)
                Write-Host "`rnpm build in progress$dotStr ($elapsedStr elapsed)" -NoNewline -ForegroundColor Yellow
                Start-Sleep -Seconds 1
                $dots++
            }
            
            Write-Host "`n" # New line after progress
            
            # Get the result
            $buildResult = Receive-Job $buildJob
            Remove-Job $buildJob
            
            # Check for errors
            if ($buildResult -match "error|Error|ERROR") {
                Write-Host "❌ npm build encountered errors:" -ForegroundColor Red
                $buildResult | Where-Object { $_ -match "error|Error|ERROR" } | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
                throw "npm build failed"
            }
            
            Write-Host "✅ Vue frontend built successfully" -ForegroundColor Green
        } finally {
            Pop-Location
        }
        
        # Stop existing containers
        Write-Host "`nStopping existing containers..." -ForegroundColor Yellow
        $stopProcess = Start-Process -FilePath "docker-compose" -ArgumentList "-f", $dockerComposeFile, "down" -Wait -NoNewWindow -PassThru -WorkingDirectory $PSScriptRoot
        if ($stopProcess.ExitCode -ne 0) {
            Write-Warning "Failed to stop existing containers (they may not be running)"
        }
        
        # Start containers
        Write-Host "`nStarting Docker containers..." -ForegroundColor Cyan
        Write-Host "This will start: Redis, Backend, RQ Workers, Frontend, and Nginx" -ForegroundColor Gray
        
        # Start containers in background and show progress
        $startJob = Start-Job -ScriptBlock {
            param($DockerComposeFile, $WorkingDir)
            Set-Location $WorkingDir
            & docker-compose -f $DockerComposeFile up -d --build 2>&1
        } -ArgumentList $dockerComposeFile, $PSScriptRoot
        
        # Show progress while containers start
        $startTime = Get-Date
        $dots = 0
        
        while ($startJob.State -eq "Running") {
            $elapsed = (Get-Date) - $startTime
            $elapsedStr = "{0:mm}:{0:ss}" -f $elapsed
            $dotStr = "." * ($dots % 4)
            Write-Host "`rStarting Docker containers$dotStr ($elapsedStr elapsed)" -NoNewline -ForegroundColor Yellow
            Start-Sleep -Seconds 1
            $dots++
        }
        
        Write-Host "`n" # New line after progress
        
        # Get the result
        $startResult = Receive-Job $startJob
        Remove-Job $startJob
        
        # Check for errors
        if ($startResult -match "error|Error|ERROR") {
            Write-Host "❌ Docker container startup encountered errors:" -ForegroundColor Red
            $startResult | Where-Object { $_ -match "error|Error|ERROR" } | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
            throw "Docker container startup failed"
        }
        
        Write-Host "✅ Docker containers started successfully" -ForegroundColor Green
        Write-Host "Waiting for services to become healthy..." -ForegroundColor Yellow
        
        # Wait for services to be ready
        if (Wait-ForServices -TimeoutMinutes 5) {
            Show-ServiceUrls
            
            # Open browser
            try {
                Start-Process "https://localhost/casestrainer/"
            } catch {
                Write-Host "Could not open browser automatically" -ForegroundColor Yellow
            }
            
            return $true
        } else {
            Write-Host "❌ Services failed to become healthy within timeout period" -ForegroundColor Red
            return $false
        }
        
    } catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Wait-ForServices {
    param([int]$TimeoutMinutes = 5)
    
    Write-Host "`nWaiting for services to initialize..." -ForegroundColor Yellow
    $timeout = (Get-Date).AddMinutes($TimeoutMinutes)
    $allHealthy = $false
    $attempt = 0
    
    while ((Get-Date) -lt $timeout -and -not $allHealthy) {
        $attempt++
        Start-Sleep -Seconds 10
        
        try {
            # Test backend health
            $backendHealthy = Test-NetConnection -ComputerName localhost -Port 5001 -InformationLevel Quiet -WarningAction SilentlyContinue
            
            # Test Redis
            $redisHealthy = $false
            try {
                $redisPing = docker exec casestrainer-redis-prod redis-cli ping 2>$null
                $redisHealthy = ($LASTEXITCODE -eq 0 -and $redisPing -like "*PONG*")
            } catch {
                # Redis not ready yet
            }
            
            # Test API endpoint
            $apiHealthy = $false
            if ($backendHealthy) {
                try {
                    $healthResponse = Invoke-RestMethod -Uri "http://localhost:5001/casestrainer/api/health" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
                    $apiHealthy = $null -ne $healthResponse
                } catch {
                    # API not ready yet
                }
            }
            
            if ($backendHealthy -and $redisHealthy -and $apiHealthy) {
                Write-Host "✅ All services are healthy" -ForegroundColor Green
                $allHealthy = $true
            } else {
                $statusStr = "Backend: $(if($backendHealthy){'✅'}else{'❌'}), Redis: $(if($redisHealthy){'✅'}else{'❌'}), API: $(if($apiHealthy){'✅'}else{'❌'})"
                Write-Host "Services initializing (attempt $attempt)... $statusStr" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "Health check error (attempt $attempt): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    return $allHealthy
}

function Show-ServiceUrls {
    Write-Host "`n=== Docker Production Mode Ready ===`n" -ForegroundColor Green
    Write-Host "Backend API:    http://localhost:5001/casestrainer/api/" -ForegroundColor Green
    Write-Host "Frontend Prod:  http://localhost:8080/" -ForegroundColor Green
    Write-Host "Nginx (HTTP):   http://localhost:80/" -ForegroundColor Green
    Write-Host "Nginx (HTTPS):  https://localhost:443/" -ForegroundColor Green
    Write-Host "Main Frontend:  https://localhost/casestrainer/" -ForegroundColor Green
    Write-Host "API Health:     https://localhost/casestrainer/api/health" -ForegroundColor Green
}

function Show-Diagnostics {
    Write-Host "`n=== Production Diagnostics ===`n" -ForegroundColor Cyan
    
    # Check Docker status
    Write-Host "Checking Docker status..." -ForegroundColor Yellow
    if (-not (Test-DockerAvailability)) {
        Write-Host "❌ Docker is not available" -ForegroundColor Red
        return
    }
    
    try {
        $dockerVersion = docker --version
        Write-Host "✅ Docker is available: $dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker version check failed: $($_.Exception.Message)" -ForegroundColor Red
        return
    }
    
    # Container status
    Write-Host "`n=== Container Status ===" -ForegroundColor Cyan
    try {
        $containers = docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}\t{{.Health}}\t{{.Ports}}"
        if ($containers -and $containers.Count -gt 1) {
            Write-Host "Container Status:" -ForegroundColor Gray
            $containers | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
        } else {
            Write-Host "❌ No CaseStrainer containers are running" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Could not check container status: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # API health check
    Write-Host "`n=== API Health Check ===" -ForegroundColor Cyan
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:5001/casestrainer/api/health" -Method GET -TimeoutSec 5
        Write-Host "✅ API is healthy: $($healthResponse.status)" -ForegroundColor Green
    } catch {
        Write-Host "❌ API health check failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host "`n=== Diagnostics Complete ===`n" -ForegroundColor Green
}

# Main execution
try {
    switch ($Mode) {
        "Production" {
            Start-DockerProduction
        }
        "Diagnostics" {
            Show-Diagnostics
        }
        "Menu" {
            do {
                $selection = Show-Menu
                switch ($selection) {
                    "1" { Start-DockerProduction }
                    "2" { Show-Diagnostics }
                    "0" { 
                        Write-Host "`nShutting down..." -ForegroundColor Yellow
                        exit 0 
                    }
                }
                
                if ($selection -ne "0") {
                    Write-Host "`nPress any key to return to menu..." -NoNewline
                    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                }
            } while ($selection -ne "0")
        }
    }
} catch {
    Write-Host "❌ Script error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} 