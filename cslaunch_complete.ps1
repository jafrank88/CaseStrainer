# Complete CaseStrainer Launcher
# This launcher handles both Docker containers and direct Windows execution

param(
    [switch]$Quick, 
    [switch]$Fast, 
    [switch]$Full, 
    [switch]$Help, 
    [switch]$HealthCheck, 
    [switch]$Prevent,
    [switch]$Monitor,
    [switch]$OptimizeDocker,
    [switch]$StartMonitoring,
    [switch]$StopMonitoring,
    [switch]$Status,
    [switch]$StartRecovery,
    [switch]$Windows,
    [switch]$Direct,
    [switch]$WSL2
)

if ($Help) {
    Write-Host "CaseStrainer Complete Launcher" -ForegroundColor Cyan
    Write-Host "=============================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Docker Container Management:" -ForegroundColor White
    Write-Host "  .\cslaunch_complete.ps1              # Intelligent auto-detection" -ForegroundColor Green
    Write-Host "  .\cslaunch_complete.ps1 -Quick       # Quick start (existing containers)" -ForegroundColor Green
    Write-Host "  .\cslaunch_complete.ps1 -Fast        # Fast rebuild (stop + start)" -ForegroundColor Green
    Write-Host "  .\cslaunch_complete.ps1 -Full        # Full rebuild (clean + build)" -ForegroundColor Green
    Write-Host ""
    Write-Host "System Management:" -ForegroundColor White
    Write-Host "  .\cslaunch_complete.ps1 -Status      # Show comprehensive system status" -ForegroundColor Yellow
    Write-Host "  .\cslaunch_complete.ps1 -HealthCheck # Run Docker health check" -ForegroundColor Yellow
    Write-Host "  .\cslaunch_complete.ps1 -Prevent     # Run prevention and optimization" -ForegroundColor Yellow
    Write-Host "  .\cslaunch_complete.ps1 -Monitor     # Start monitoring systems" -ForegroundColor Yellow
    Write-Host "  .\cslaunch_complete.ps1 -StartMonitoring    # Start background monitoring" -ForegroundColor Yellow
    Write-Host "  .\cslaunch_complete.ps1 -StopMonitoring     # Stop background monitoring" -ForegroundColor Red
    Write-Host "  .\cslaunch_complete.ps1 -StartRecovery      # Start Docker auto-recovery" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Windows Direct Mode:" -ForegroundColor White
    Write-Host "  .\cslaunch_complete.ps1 -Windows     # Run CaseStrainer directly on Windows (no Docker)" -ForegroundColor Green
    Write-Host "  .\cslaunch_complete.ps1 -Direct      # Run CaseStrainer with all components (Flask + Redis + RQ Workers)" -ForegroundColor Green
    Write-Host ""
    Write-Host "WSL 2 Mode (Recommended for Windows Server 2022):" -ForegroundColor White
    Write-Host "  .\cslaunch_complete.ps1 -WSL2        # Use WSL 2 to run Linux containers on Windows Server" -ForegroundColor Green
    Write-Host ""
    Write-Host "Docker Optimization:" -ForegroundColor White
    Write-Host "  .\cslaunch_complete.ps1 -OptimizeDocker # Configure Docker for maximum performance" -ForegroundColor Blue
    exit
}

# Configuration
$LogFile = "logs\cslaunch_complete.log"
$PidFile = "logs\casestrainer.pid"
$WorkerPidFile = "logs\rq_worker.pid"

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    Write-Host "[$timestamp] $Message"
}

function Stop-AllComponents {
    Write-Log "Stopping all CaseStrainer components..."
    
    # Stop Flask app
    if (Test-Path $PidFile) {
        $processId = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($processId) {
            try {
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                Write-Log "✅ Stopped Flask app (PID: $processId)"
            } catch {
                Write-Log "⚠️ Could not stop Flask process $processId"
            }
        }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    }
    
    # Stop RQ worker
    if (Test-Path $WorkerPidFile) {
        $workerId = Get-Content $WorkerPidFile -ErrorAction SilentlyContinue
        if ($workerId) {
            try {
                Stop-Process -Id $workerId -Force -ErrorAction SilentlyContinue
                Write-Log "✅ Stopped RQ worker (PID: $workerId)"
            } catch {
                Write-Log "⚠️ Could not stop RQ worker $workerId"
            }
        }
        Remove-Item $WorkerPidFile -Force -ErrorAction SilentlyContinue
    }
    
    # Stop Redis (if running as Windows service)
    try {
        $redisService = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
        if ($redisService -and $redisService.Status -eq "Running") {
            Stop-Service -Name "Redis" -Force
            Write-Log "✅ Stopped Redis service"
        }
    } catch {
        Write-Log "Redis service not found or already stopped"
    }
    
    # Stop any remaining Python processes
    Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
        $_.ProcessName -eq "python" 
    } | ForEach-Object {
        try {
            Stop-Process -Id $_.Id -Force
            Write-Log "Stopped Python process: $($_.Id)"
        } catch {
            Write-Log "Could not stop Python process $($_.Id)"
        }
    }
    
    Write-Log "All components stopped"
}

function Start-DirectMode {
    Write-Log "Starting CaseStrainer with all components (Flask + Redis + RQ Workers)..."
    
    # Stop any existing components first
    Write-Host "Stopping any existing components..." -ForegroundColor Yellow
    Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
        $_.ProcessName -eq "python" 
    } | ForEach-Object {
        try { 
            Stop-Process -Id $_.Id -Force 
            Write-Host "Stopped Python process: $($_.Id)" -ForegroundColor Green
        } catch {
            Write-Host "Could not stop Python process $($_.Id)" -ForegroundColor Red
        }
    }
    Start-Sleep -Seconds 2
    
    # 1. Start Redis (if not already running)
    Write-Host "Starting Redis..." -ForegroundColor Cyan
    try {
        $redisService = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
        if ($redisService) {
            if ($redisService.Status -ne "Running") {
                Start-Service -Name "Redis"
                Write-Host "✅ Redis service started" -ForegroundColor Green
            } else {
                Write-Host "✅ Redis service already running" -ForegroundColor Green
            }
        } else {
            Write-Host "⚠️ Redis service not found. You may need to install Redis for Windows." -ForegroundColor Yellow
            Write-Host "   Download from: https://github.com/microsoftarchive/redis/releases" -ForegroundColor White
            Write-Host "   Or use: winget install Redis.Redis" -ForegroundColor White
        }
    } catch {
        Write-Host "❌ Failed to start Redis: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Wait for Redis to be ready
    Start-Sleep -Seconds 3
    
    # 2. Start RQ worker
    Write-Host "Starting RQ worker..." -ForegroundColor Cyan
    try {
        $workerProcess = Start-Process -FilePath "python" -ArgumentList "-m", "rq", "worker", "casestrainer" -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru
        $workerProcess.Id | Out-File -FilePath $WorkerPidFile -Encoding UTF8
        Write-Host "✅ RQ worker started (PID: $($workerProcess.Id))" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to start RQ worker: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Wait for worker to start
    Start-Sleep -Seconds 5
    
    # 3. Start Flask app
    Write-Host "Starting Flask app..." -ForegroundColor Cyan
    try {
        $flaskProcess = Start-Process -FilePath "python" -ArgumentList "src\app_final_vue.py" -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru
        $flaskProcess.Id | Out-File -FilePath $PidFile -Encoding UTF8
        Write-Host "✅ Flask app started (PID: $($flaskProcess.Id))" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to start Flask app: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Wait for Flask to start
    Write-Host "Waiting for Flask app to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    # 4. Test all components
    Write-Host "Testing all components..." -ForegroundColor Cyan
    
    # Check Redis
    $redisRunning = $false
    try {
        $redisService = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
        if ($redisService -and $redisService.Status -eq "Running") {
            $redisRunning = $true
            Write-Host "✅ Redis service is running" -ForegroundColor Green
        } else {
            Write-Host "❌ Redis service is not running" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Redis service not found" -ForegroundColor Red
    }
    
    # Check Flask
    $flaskRunning = $false
    if (Test-Path $PidFile) {
        $processId = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($processId -and (Get-Process -Id $processId -ErrorAction SilentlyContinue)) {
            $flaskRunning = $true
            Write-Host "✅ Flask app is running (PID: $processId)" -ForegroundColor Green
            
            # Test health endpoint
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -UseBasicParsing -TimeoutSec 10
                Write-Host "🌐 Flask health check: OK (Status: $($response.StatusCode))" -ForegroundColor Green
            } catch {
                Write-Host "❌ Flask health check failed: $($_.Exception.Message)" -ForegroundColor Red
                $flaskRunning = $false
            }
        } else {
            Write-Host "❌ Flask app is not running" -ForegroundColor Red
        }
    }
    
    if ($flaskRunning -and $redisRunning) {
        Write-Host "✅ CaseStrainer is running successfully with all components!" -ForegroundColor Green
        Write-Host ""
        Write-Host "🌐 Access URLs:" -ForegroundColor Green
        Write-Host "   Local: http://localhost:5000/casestrainer/" -ForegroundColor Cyan
        Write-Host "   Health: http://localhost:5000/casestrainer/api/health" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "📋 Next steps to make it accessible at https://wolf.law.uw.edu/casestrainer/:" -ForegroundColor Yellow
        Write-Host "   1. Install and configure Nginx to proxy /casestrainer/ to localhost:5000" -ForegroundColor White
        Write-Host "   2. Set up SSL certificates for HTTPS" -ForegroundColor White
        Write-Host "   3. Configure firewall rules to allow external access" -ForegroundColor White
        Write-Host ""
        Write-Host "🔧 Management commands:" -ForegroundColor Blue
        Write-Host "   Status: .\cslaunch_complete.ps1 -Status" -ForegroundColor White
        Write-Host "   Stop:   .\cslaunch_complete.ps1 -StopMonitoring" -ForegroundColor White
    } else {
        Write-Host "❌ Some components failed to start. Check the logs above." -ForegroundColor Red
    }
}

function Start-WSL2Mode {
    Write-Host "Starting CaseStrainer using WSL 2 on Windows Server 2022..." -ForegroundColor Green
    Write-Host "This mode uses WSL 2 to run Linux containers, providing better compatibility." -ForegroundColor Cyan
    
    # Check if WSL 2 is available
    Write-Host "Checking WSL 2 availability..." -ForegroundColor Yellow
    try {
        $wslVersion = wsl --version 2>$null
        if ($wslVersion) {
            Write-Host "✅ WSL is available: $wslVersion" -ForegroundColor Green
        } else {
            Write-Host "❌ WSL is not available" -ForegroundColor Red
            Write-Host "💡 Install WSL 2 with: wsl --install" -ForegroundColor Yellow
            Write-Host "   Requires Windows Server 2022 with June 2022 patches or later" -ForegroundColor Yellow
            return
        }
    } catch {
        Write-Host "❌ Error checking WSL: $($_.Exception.Message)" -ForegroundColor Red
        return
    }
    
    # Check if Ubuntu is available in WSL
    Write-Host "Checking WSL distributions..." -ForegroundColor Yellow
    try {
        $distros = wsl --list --verbose 2>$null
        if ($distros -match "Ubuntu") {
            Write-Host "✅ Ubuntu distribution found in WSL" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Ubuntu not found in WSL. Installing..." -ForegroundColor Yellow
            Write-Host "   This may take a few minutes..." -ForegroundColor White
            wsl --install -d Ubuntu
            Start-Sleep -Seconds 30
        }
    } catch {
        Write-Host "❌ Error checking WSL distributions: $($_.Exception.Message)" -ForegroundColor Red
        return
    }
    
    # Start CaseStrainer using WSL 2
    Write-Host "Starting CaseStrainer in WSL 2..." -ForegroundColor Cyan
    
    # Use the original docker-compose.prodbuild.yml which is designed for Linux containers
    $composeFile = "docker-compose.prebuild.yml"
    
    if (-not (Test-Path $composeFile)) {
        Write-Host "❌ Docker Compose file not found: $composeFile" -ForegroundColor Red
        return
    }
    
    # Check if Docker is running in WSL
    Write-Host "Checking Docker in WSL..." -ForegroundColor Yellow
    try {
        $dockerStatus = wsl -d Ubuntu -- docker info 2>$null
        if ($dockerStatus -match "Server Version") {
            Write-Host "✅ Docker is running in WSL" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Docker not running in WSL. Starting..." -ForegroundColor Yellow
            wsl -d Ubuntu -- sudo service docker start
            Start-Sleep -Seconds 5
        }
    } catch {
        Write-Host "❌ Error checking Docker in WSL: $($_.Exception.Message)" -ForegroundColor Red
        return
    }
    
    # Start containers using WSL
    Write-Host "Starting CaseStrainer containers in WSL 2..." -ForegroundColor Cyan
    try {
        wsl -d Ubuntu -- docker compose -f $composeFile down
        wsl -d Ubuntu -- docker compose -f $composeFile up -d
        
        # Wait for containers to start
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
            Write-Host "   Status: .\cslaunch_complete.ps1 -Status" -ForegroundColor White
            Write-Host "   Stop:   .\cslaunch_complete.ps1 -StopMonitoring" -ForegroundColor White
        } else {
            Write-Host "❌ Failed to start containers in WSL 2" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Error starting containers in WSL: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Start-WindowsMode {
    Write-Host "Starting CaseStrainer directly on Windows..." -ForegroundColor Green
    
    # Check if already running
    $existingProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
        $_.ProcessName -eq "python" 
    }
    
    if ($existingProcess) {
        Write-Host "Python processes found. Stopping existing processes..." -ForegroundColor Yellow
        $existingProcess | ForEach-Object { 
            try { 
                Stop-Process -Id $_.Id -Force 
                Write-Host "Stopped Python process: $($_.Id)" -ForegroundColor Green
            } catch {
                Write-Host "Could not stop Python process $($_.Id)" -ForegroundColor Red
            }
        }
        Start-Sleep -Seconds 2
    }
    
    # Start CaseStrainer
    Write-Host "Starting CaseStrainer Flask app..." -ForegroundColor Cyan
    $process = Start-Process -FilePath "python" -ArgumentList "src\app_final_vue.py" -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru
    
    # Wait for startup
    Write-Host "Waiting for CaseStrainer to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Test if it's responding
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ CaseStrainer started successfully with PID: $($process.Id)" -ForegroundColor Green
            Write-Host "🌐 Access URL: http://localhost:5000/casestrainer/" -ForegroundColor Cyan
            Write-Host "🔧 API Health: http://localhost:5000/casestrainer/api/health" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "To make it accessible at https://wolf.law.uw.edu/casestrainer/:" -ForegroundColor Yellow
            Write-Host "1. Configure your web server to proxy /casestrainer/ to localhost:5000" -ForegroundColor White
            Write-Host "2. Set up SSL certificates for HTTPS" -ForegroundColor White
            Write-Host "3. Configure firewall rules to allow external access" -ForegroundColor White
        } else {
            Write-Host "⚠️ CaseStrainer started but health check failed: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Failed to start CaseStrainer: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Check the logs for more details" -ForegroundColor Yellow
    }
}

function Get-ComponentStatus {
    Write-Host "Comprehensive System Status:" -ForegroundColor Yellow
    Write-Host ""
    
    # Docker status
    Write-Host "Docker Status:" -ForegroundColor Cyan
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Host "  ✅ Docker: $dockerVersion" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Docker: Not responding" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ Docker: Error checking version" -ForegroundColor Red
    }
    
    # Container status
    Write-Host ""
    Write-Host "Container Status:" -ForegroundColor Cyan
    try {
        $containers = docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
        if ($containers) {
            Write-Host $containers -ForegroundColor Green
        } else {
            Write-Host "  ❌ No CaseStrainer containers running" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ Error checking containers" -ForegroundColor Red
    }
    
    # Direct Mode components
    Write-Host ""
    Write-Host "Direct Mode Components:" -ForegroundColor Cyan
    
    # Check Flask app
    if (Test-Path $PidFile) {
        $processId = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($processId -and (Get-Process -Id $processId -ErrorAction SilentlyContinue)) {
            Write-Host "  ✅ Flask app: Running (PID: $processId)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Flask app: Not running (stale PID file)" -ForegroundColor Red
        }
    } else {
        Write-Host "  ❌ Flask app: Not running (no PID file)" -ForegroundColor Red
    }
    
    # Check RQ worker
    if (Test-Path $WorkerPidFile) {
        $workerId = Get-Content $WorkerPidFile -ErrorAction SilentlyContinue
        if ($workerId -and (Get-Process -Id $workerId -ErrorAction SilentlyContinue)) {
            Write-Host "  ✅ RQ worker: Running (PID: $workerId)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ RQ worker: Not running (stale PID file)" -ForegroundColor Red
        }
    } else {
        Write-Host "  ❌ RQ worker: Not running (no PID file)" -ForegroundColor Red
    }
    
    # Check Redis
    try {
        $redisService = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
        if ($redisService -and $redisService.Status -eq "Running") {
            Write-Host "  ✅ Redis service: Running" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Redis service: Not running" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ Redis service: Not found" -ForegroundColor Red
    }
    
    # System resources
    Write-Host ""
    Write-Host "System Resources:" -ForegroundColor Cyan
    try {
        $cpu = (Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples[0].CookedValue
        $memory = (Get-Counter "\Memory\% Committed Bytes In Use").CounterSamples[0].CookedValue
        Write-Host "  CPU: $([math]::Round($cpu, 1))%" -ForegroundColor $(if ($cpu -gt 80) { "Red" } elseif ($cpu -gt 60) { "Yellow" } else { "Green" })
        Write-Host "  Memory: $([math]::Round($memory, 1))%" -ForegroundColor $(if ($memory -gt 80) { "Red" } elseif ($memory -gt 60) { "Yellow" } else { "Green" })
    } catch {
        Write-Host "  ❌ Error getting system resources" -ForegroundColor Red
    }
}

# Main execution
if ($WSL2) {
    Start-WSL2Mode
} elseif ($Direct) {
    Start-DirectMode
} elseif ($Windows) {
    Start-WindowsMode
} elseif ($Status) {
    Get-ComponentStatus
} elseif ($StopMonitoring) {
    Stop-AllComponents
} else {
    Write-Host "Intelligent Auto-Detection with Enhanced Monitoring..." -ForegroundColor Magenta
    
    # Detect container type and set compose file
    $dockerInfo = docker info 2>$null
    if ($dockerInfo -match "OSType: windows") {
        $composeFile = "docker-compose.windows-working.yml"
    } else {
        $composeFile = "docker-compose.prebuild.yml"
    }
    
    # Check if compose file exists
    if (-not (Test-Path $composeFile)) {
        Write-Host "❌ Docker Compose file not found: $composeFile" -ForegroundColor Red
        Write-Host "💡 Try using -Direct mode instead: .\cslaunch_complete.ps1 -Direct" -ForegroundColor Yellow
        exit 1
    }
    
    # Check for existing containers
    $allContainers = docker ps -a --filter "name=casestrainer" --format "{{.Names}}" 2>$null
    $containers = docker ps --filter "name=casestrainer" --format "{{.Names}}" 2>$null
    
    # Check for recent changes
    $recentChanges = $false
    $changeDetails = @()
    
    # Check frontend changes
    $frontendFiles = Get-ChildItem -Path "casestrainer-vue-new\dist-minimal" -Recurse -Include "*.js", "*.css", "*.html" -ErrorAction SilentlyContinue | 
                     Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-30) }
    if ($frontendFiles) {
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
    
    # Determine the best action
    if (-not $allContainers) {
        Write-Host "No containers exist - using Full Rebuild" -ForegroundColor Yellow
        docker compose -f $composeFile down
        docker compose -f $composeFile build --no-cache
        docker compose -f $composeFile up -d
        Write-Host "Full Rebuild completed!" -ForegroundColor Green
    } elseif (-not $containers) {
        Write-Host "Containers exist but not running - using Fast Start" -ForegroundColor Cyan
        docker compose -f $composeFile down
        docker compose -f $composeFile up -d
        Write-Host "Fast Start completed!" -ForegroundColor Green
    } elseif ($recentChanges) {
        Write-Host "Code changes detected - using Fast Start" -ForegroundColor Cyan
        docker compose -f $composeFile down
        docker compose -f $composeFile up -d
        Write-Host "Fast Start completed!" -ForegroundColor Green
    } else {
        Write-Host "No recent changes, containers running - using Quick Start" -ForegroundColor Green
        docker compose -f $composeFile up -d
        Write-Host "Quick Start completed!" -ForegroundColor Green
    }
    
    # Display final status
    Write-Host "`n[SUCCESS] CaseStrainer is ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "[RESTART] .\cslaunch_complete.ps1" -ForegroundColor Cyan
    Write-Host "[QUICK]   .\cslaunch_complete.ps1 -Quick" -ForegroundColor Cyan
    Write-Host "[FAST]    .\cslaunch_complete.ps1 -Fast" -ForegroundColor Cyan
    Write-Host "[FULL]    .\cslaunch_complete.ps1 -Full" -ForegroundColor Yellow
    Write-Host "[STATUS]  .\cslaunch_complete.ps1 -Status" -ForegroundColor Yellow
    Write-Host "[WSL2]    .\cslaunch_complete.ps1 -WSL2" -ForegroundColor Green
    Write-Host "[DIRECT]  .\cslaunch_complete.ps1 -Direct" -ForegroundColor Green
}
