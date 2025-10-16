# CaseStrainer WSL 2 Launcher
# Uses WSL 2 to run Linux containers on Windows Server 2022
# Based on Microsoft Tech Community guidance

param(
    [switch]$Help,
    [switch]$Status,
    [switch]$Stop
)

if ($Help) {
    Write-Host "CaseStrainer WSL 2 Launcher" -ForegroundColor Cyan
    Write-Host "===========================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This launcher uses WSL 2 to run Linux containers on Windows Server 2022." -ForegroundColor White
    Write-Host "It provides better compatibility than Windows containers." -ForegroundColor White
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  .\cslaunch_wsl2.ps1        # Start CaseStrainer using WSL 2" -ForegroundColor Green
    Write-Host "  .\cslaunch_wsl2.ps1 -Status # Show status" -ForegroundColor Yellow
    Write-Host "  .\cslaunch_wsl2.ps1 -Stop   # Stop containers" -ForegroundColor Red
    Write-Host "  .\cslaunch_wsl2.ps1 -Help   # Show this help" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Requirements:" -ForegroundColor White
    Write-Host "  - Windows Server 2022 with June 2022 patches or later" -ForegroundColor Yellow
    Write-Host "  - WSL 2 installed (wsl --install)" -ForegroundColor Yellow
    Write-Host "  - Ubuntu distribution in WSL 2" -ForegroundColor Yellow
    Write-Host "  - Docker installed in Ubuntu WSL" -ForegroundColor Yellow
    exit
}

function Test-WSL2Availability {
    Write-Host "Checking WSL 2 availability..." -ForegroundColor Yellow
    try {
        $wslVersion = wsl --version 2>$null
        if ($wslVersion) {
            Write-Host "✅ WSL is available: $wslVersion" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ WSL is not available" -ForegroundColor Red
            Write-Host "💡 Install WSL 2 with: wsl --install" -ForegroundColor Yellow
            Write-Host "   Requires Windows Server 2022 with June 2022 patches or later" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "❌ Error checking WSL: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-UbuntuDistribution {
    Write-Host "Checking WSL distributions..." -ForegroundColor Yellow
    try {
        $distros = wsl --list --verbose 2>$null
        if ($distros -match "Ubuntu") {
            Write-Host "✅ Ubuntu distribution found in WSL" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠️ Ubuntu not found in WSL. Installing..." -ForegroundColor Yellow
            Write-Host "   This may take a few minutes..." -ForegroundColor White
            wsl --install -d Ubuntu
            Start-Sleep -Seconds 30
            return $true
        }
    } catch {
        Write-Host "❌ Error checking WSL distributions: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-DockerInWSL {
    Write-Host "Checking Docker in WSL..." -ForegroundColor Yellow
    try {
        $dockerStatus = wsl -d Ubuntu -- docker info 2>$null
        if ($dockerStatus -match "Server Version") {
            Write-Host "✅ Docker is running in WSL" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠️ Docker not running in WSL. Starting..." -ForegroundColor Yellow
            wsl -d Ubuntu -- sudo service docker start
            Start-Sleep -Seconds 5
            return $true
        }
    } catch {
        Write-Host "❌ Error checking Docker in WSL: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Start-CaseStrainerWSL2 {
    Write-Host "Starting CaseStrainer using WSL 2 on Windows Server 2022..." -ForegroundColor Green
    Write-Host "This mode uses WSL 2 to run Linux containers, providing better compatibility." -ForegroundColor Cyan
    
    # Check prerequisites
    if (-not (Test-WSL2Availability)) { return }
    if (-not (Test-UbuntuDistribution)) { return }
    if (-not (Test-DockerInWSL)) { return }
    
    # Start CaseStrainer using WSL 2
    Write-Host "Starting CaseStrainer in WSL 2..." -ForegroundColor Cyan
    
    # Use the original docker-compose.prodbuild.yml which is designed for Linux containers
    $composeFile = "docker-compose.prebuild.yml"
    
    if (-not (Test-Path $composeFile)) {
        Write-Host "❌ Docker Compose file not found: $composeFile" -ForegroundColor Red
        Write-Host "💡 Make sure you're in the CaseStrainer directory" -ForegroundColor Yellow
        return
    }
    
    # Start containers using WSL
    Write-Host "Starting CaseStrainer containers in WSL 2..." -ForegroundColor Cyan
    try {
        Write-Host "Stopping any existing containers..." -ForegroundColor Yellow
        wsl -d Ubuntu -- docker compose -f $composeFile down
        
        Write-Host "Starting containers..." -ForegroundColor Yellow
        wsl -d Ubuntu -- docker compose -f $composeFile up -d
        
        # Wait for containers to start
        Write-Host "Waiting for containers to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 15
        
        # Check container status
        $containers = wsl -d Ubuntu -- docker ps --filter "name=casestrainer" --format "{{.Names}}" 2>$null
        if ($containers) {
            Write-Host "✅ CaseStrainer containers started successfully in WSL 2!" -ForegroundColor Green
            Write-Host ""
            Write-Host "🌐 Access URLs:" -ForegroundColor Green
            Write-Host "   Local: http://localhost:5000/casestrainer/" -ForegroundColor Cyan
            Write-Host "   Health: http://localhost:5000/casestrainer/api/health" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "📋 Next steps to make it accessible at https://wolf.law.uw.edu/casestrainer/:" -ForegroundColor Yellow
            Write-Host "   1. Configure your web server to proxy /casestrainer/ to localhost:5000" -ForegroundColor White
            Write-Host "   2. Set up SSL certificates for HTTPS" -ForegroundColor White
            Write-Host "   3. Configure firewall rules to allow external access" -ForegroundColor White
            Write-Host ""
            Write-Host "🔧 Management commands:" -ForegroundColor Blue
            Write-Host "   Status: .\cslaunch_wsl2.ps1 -Status" -ForegroundColor White
            Write-Host "   Stop:   .\cslaunch_wsl2.ps1 -Stop" -ForegroundColor White
        } else {
            Write-Host "❌ Failed to start containers in WSL 2" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Error starting containers in WSL: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Get-WSL2Status {
    Write-Host "CaseStrainer WSL 2 Status:" -ForegroundColor Yellow
    Write-Host ""
    
    # Check WSL 2
    Write-Host "WSL 2 Status:" -ForegroundColor Cyan
    try {
        $wslVersion = wsl --version 2>$null
        if ($wslVersion) {
            Write-Host "  ✅ WSL: $wslVersion" -ForegroundColor Green
        } else {
            Write-Host "  ❌ WSL: Not available" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ WSL: Error checking" -ForegroundColor Red
    }
    
    # Check Ubuntu distribution
    Write-Host ""
    Write-Host "WSL Distribution:" -ForegroundColor Cyan
    try {
        $distros = wsl --list --verbose 2>$null
        if ($distros -match "Ubuntu") {
            Write-Host "  ✅ Ubuntu: Found in WSL" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Ubuntu: Not found in WSL" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ Ubuntu: Error checking" -ForegroundColor Red
    }
    
    # Check Docker in WSL
    Write-Host ""
    Write-Host "Docker in WSL:" -ForegroundColor Cyan
    try {
        $dockerStatus = wsl -d Ubuntu -- docker info 2>$null
        if ($dockerStatus -match "Server Version") {
            Write-Host "  ✅ Docker: Running in WSL" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Docker: Not running in WSL" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ Docker: Error checking" -ForegroundColor Red
    }
    
    # Check containers
    Write-Host ""
    Write-Host "Container Status:" -ForegroundColor Cyan
    try {
        $containers = wsl -d Ubuntu -- docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
        if ($containers) {
            Write-Host $containers -ForegroundColor Green
        } else {
            Write-Host "  ❌ No CaseStrainer containers running" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ Error checking containers" -ForegroundColor Red
    }
    
    # Check application health
    Write-Host ""
    Write-Host "Application Health:" -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ Backend API: Healthy" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️ Backend API: Status $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ❌ Backend API: Not responding" -ForegroundColor Red
    }
}

function Stop-CaseStrainerWSL2 {
    Write-Host "Stopping CaseStrainer containers in WSL 2..." -ForegroundColor Red
    try {
        wsl -d Ubuntu -- docker compose -f "docker-compose.prebuild.yml" down
        Write-Host "✅ Containers stopped" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error stopping containers: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Main execution
if ($Status) {
    Get-WSL2Status
} elseif ($Stop) {
    Stop-CaseStrainerWSL2
} elseif ($Help) {
    # Help is handled at the top
} else {
    Start-CaseStrainerWSL2
}
