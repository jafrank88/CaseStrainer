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
    [switch]$Direct
)

function Get-CodeChecksum {
    <#
    .SYNOPSIS
    Generates a checksum of key source code files to detect changes
    #>
    $sourcePaths = @(
        "src/",
        "casestrainer-vue-new/src/",
        "casestrainer-vue-new/package.json",
        "docker/",
        "docker-compose.prod.yml"
    )
    
    $checksum = ""
    foreach ($path in $sourcePaths) {
        if (Test-Path $path) {
            if (Test-Path $path -PathType Leaf) {
                # Single file
                $checksum += (Get-FileHash -Path $path -Algorithm MD5).Hash
            } else {
                # Directory - get all files recursively
                Get-ChildItem -Path $path -Recurse -File | 
                Where-Object { $_.Extension -match "\.(py|js|vue|css|html|yml|yaml|dockerfile|conf)$" } |
                Sort-Object FullName |
                ForEach-Object { $checksum += (Get-FileHash -Path $_.FullName -Algorithm MD5).Hash }
            }
        }
    }
    
    # Generate final checksum
    $finalChecksum = (Get-FileHash -String $checksum -Algorithm MD5).Hash
    return $finalChecksum
}

function Test-CodeChanged {
    <#
    .SYNOPSIS
    Tests if source code has changed since last build
    #>
    $checksumFile = ".code_checksum"
    $currentChecksum = Get-CodeChecksum
    
    if (-not (Test-Path $checksumFile)) {
        # First time running - save checksum and return true
        $currentChecksum | Out-File -FilePath $checksumFile -Encoding UTF8
        Write-Host "First run detected - will perform full build" -ForegroundColor Yellow
        return $true
    }
    
    $savedChecksum = Get-Content $checksumFile -ErrorAction SilentlyContinue
    if ($currentChecksum -eq $savedChecksum) {
        Write-Host "Code unchanged - using existing containers" -ForegroundColor Green
        return $false
    } else {
        Write-Host "Code has changed - rebuilding containers" -ForegroundColor Yellow
        # Update saved checksum
        $currentChecksum | Out-File -FilePath $checksumFile -Encoding UTF8
        return $true
    }
}

function Start-DirectMode {
    Write-Host "Starting CaseStrainer with all components (Flask + Redis + RQ Workers)..." -ForegroundColor Green
    
    # Create logs directory if it doesn't exist
    if (-not (Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    }
    
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
                Write-Host "Redis service started" -ForegroundColor Green
            } else {
                Write-Host "Redis service already running" -ForegroundColor Green
            }
        } else {
            Write-Host "Redis service not found. You may need to install Redis for Windows." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Failed to start Redis: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Wait for Redis to be ready
    Start-Sleep -Seconds 3
    
    # 2. Start RQ worker
    Write-Host "Starting RQ worker..." -ForegroundColor Cyan
    try {
        $workerProcess = Start-Process -FilePath "python" -ArgumentList "-m", "rq", "worker", "casestrainer" -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru
        $workerProcess.Id | Out-File -FilePath "logs\rq_worker.pid" -Encoding UTF8
        Write-Host "RQ worker started (PID: $($workerProcess.Id))" -ForegroundColor Green
    } catch {
        Write-Host "Failed to start RQ worker: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Wait for worker to start
    Start-Sleep -Seconds 5
    
    # 3. Start Flask app
    Write-Host "Starting Flask app..." -ForegroundColor Cyan
    try {
        $flaskProcess = Start-Process -FilePath "python" -ArgumentList "src\app_final_vue.py" -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru
        $flaskProcess.Id | Out-File -FilePath "logs\casestrainer.pid" -Encoding UTF8
        Write-Host "Flask app started (PID: $($flaskProcess.Id))" -ForegroundColor Green
    } catch {
        Write-Host "Failed to start Flask app: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Wait for Flask to start
    Write-Host "Waiting for Flask app to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    # 4. Test all components
    Write-Host "Testing all components..." -ForegroundColor Cyan
    
    # Check Flask
    $flaskRunning = $false
    if (Test-Path "logs\casestrainer.pid") {
        $processId = Get-Content "logs\casestrainer.pid" -ErrorAction SilentlyContinue
        if ($processId -and (Get-Process -Id $processId -ErrorAction SilentlyContinue)) {
            $flaskRunning = $true
            Write-Host "Flask app is running (PID: $processId)" -ForegroundColor Green
            
            # Test health endpoint
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -UseBasicParsing -TimeoutSec 10
                Write-Host "Flask health check: OK (Status: $($response.StatusCode))" -ForegroundColor Green
            } catch {
                Write-Host "Flask health check failed: $($_.Exception.Message)" -ForegroundColor Red
                $flaskRunning = $false
            }
        } else {
            Write-Host "Flask app is not running" -ForegroundColor Red
        }
    }
    
    if ($flaskRunning) {
        Write-Host "CaseStrainer is running successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Access URLs:" -ForegroundColor Green
        Write-Host "   Local: http://localhost:5000/casestrainer/" -ForegroundColor Cyan
        Write-Host "   Health: http://localhost:5000/casestrainer/api/health" -ForegroundColor Cyan
    } else {
        Write-Host "Some components failed to start. Check the logs above." -ForegroundColor Red
    }
}

if ($Help) { 
    Write-Host "CaseStrainer Enhanced Launcher" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Basic Commands:" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1              # Smart auto-detect (recommended)" -ForegroundColor Green
    Write-Host "  .\cslaunch.ps1 -Quick       # Quick Start (when code unchanged)" -ForegroundColor Green
    Write-Host "  .\cslaunch.ps1 -Fast        # Fast Start (restart containers)" -ForegroundColor Cyan
    Write-Host "  .\cslaunch.ps1 -Full        # Force Full Rebuild (ignore checksums)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Smart Features:" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1              # Automatically detects code changes" -ForegroundColor Green
    Write-Host "  .\cslaunch.ps1 -ForceRebuild # Force rebuild even if code unchanged" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Monitoring & Prevention:" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1 -HealthCheck # Run Docker health check with auto-recovery" -ForegroundColor Magenta
    Write-Host "  .\cslaunch.ps1 -Prevent     # Run Docker prevention and optimization" -ForegroundColor Blue
    Write-Host "  .\cslaunch.ps1 -Monitor     # Show current monitoring status" -ForegroundColor Cyan
    Write-Host "  .\cslaunch.ps1 -StartMonitoring # Start background monitoring systems" -ForegroundColor Green
    Write-Host "  .\cslaunch.ps1 -StopMonitoring  # Stop background monitoring systems" -ForegroundColor Red
    Write-Host "  .\cslaunch.ps1 -Status      # Show comprehensive system status" -ForegroundColor Yellow
    Write-Host "  .\cslaunch.ps1 -StartRecovery # Start Docker auto-recovery monitoring in background" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Windows Direct Mode:" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1 -Windows      # Run CaseStrainer directly on Windows (no Docker)" -ForegroundColor Green
    Write-Host "  .\cslaunch.ps1 -Direct       # Run CaseStrainer with all components (Flask + Redis + RQ Workers)" -ForegroundColor Green
}
elseif ($OptimizeDocker) {
    Write-Host "Optimizing Docker Desktop for Maximum Performance..." -ForegroundColor Blue
    
    # Clean up zombie Docker processes
    Write-Host "Cleaning up zombie Docker processes..." -ForegroundColor Yellow
    $dockerProcesses = Get-Process *docker* -ErrorAction SilentlyContinue
    $zombieCount = 0
    
    foreach ($proc in $dockerProcesses) {
        if ($proc.ProcessName -notmatch "com\.docker\.service|Docker Desktop" -and $proc.CPU -lt 1.0) {
            Write-Host "Killing zombie process: $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Red
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                $zombieCount++
            }
            catch {
                Write-Host "Could not stop process $($proc.Id): $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
    
    Write-Host "Killed $zombieCount zombie Docker processes" -ForegroundColor Green
}
elseif ($StartMonitoring) {
    Write-Host "Starting Background Monitoring Systems..." -ForegroundColor Green
    Start-Job -ScriptBlock { 
        while ($true) { 
            Start-Sleep -Seconds 60
            docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}" 
        } 
    } -Name "BasicMonitoring" | Out-Null
    Write-Host "Monitoring systems started in background!" -ForegroundColor Green
    Write-Host "Use '.\cslaunch.ps1 -Monitor' to check status" -ForegroundColor Cyan
}
elseif ($StopMonitoring) {
    Write-Host "Stopping Background Monitoring Systems..." -ForegroundColor Red
    Get-Job | Where-Object { $_.Name -like "*monitoring*" -or $_.Name -like "*recovery*" -or $_.Name -like "*resource*" } | Stop-Job
    Get-Job | Where-Object { $_.Name -like "*monitoring*" -or $_.Name -like "*recovery*" -or $_.Name -like "*resource*" } | Stop-Job
    Remove-Job
    Write-Host "Monitoring systems stopped!" -ForegroundColor Green
}
elseif ($Monitor) {
    Write-Host "Monitoring System Status:" -ForegroundColor Cyan
    Write-Host ""
    
    # Check monitoring jobs
    $monitoringJobs = Get-Job | Where-Object { $_.State -eq "Running" }
    if ($monitoringJobs) {
        Write-Host "Active Monitoring Jobs:" -ForegroundColor Green
        $monitoringJobs | Format-Table Id, Name, State, HasMoreData -AutoSize
    } else {
        Write-Host "No monitoring jobs running" -ForegroundColor Yellow
        Write-Host "Use '.\cslaunch.ps1 -StartMonitoring' to start monitoring" -ForegroundColor Cyan
    }
}
elseif ($Status) {
    Write-Host "Comprehensive System Status:" -ForegroundColor Yellow
    Write-Host ""
    
    # Docker status
    Write-Host "Docker Status:" -ForegroundColor Cyan
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Host "  Docker: $dockerVersion" -ForegroundColor Green
        } else {
            Write-Host "  Docker: Not responding" -ForegroundColor Red
        }
    } catch {
        Write-Host "  Docker: Error checking version" -ForegroundColor Red
    }
    
    # Container status
    Write-Host ""
    Write-Host "Container Status:" -ForegroundColor Cyan
    try {
        $containers = docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
        if ($containers) {
            Write-Host $containers -ForegroundColor Green
        } else {
            Write-Host "  No CaseStrainer containers running" -ForegroundColor Red
        }
    } catch {
        Write-Host "  Error checking containers" -ForegroundColor Red
    }
    
    # Application health
    Write-Host ""
    Write-Host "Application Health:" -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "  Backend API: Healthy" -ForegroundColor Green
        } else {
            Write-Host "  Backend API: Status $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  Backend API: Not responding" -ForegroundColor Red
    }
    
    # Code change status
    Write-Host ""
    Write-Host "Code Change Status:" -ForegroundColor Cyan
    if (Test-CodeChanged) {
        Write-Host "  Code has changed since last build" -ForegroundColor Yellow
    } else {
        Write-Host "  Code unchanged since last build" -ForegroundColor Green
    }
}
elseif ($StartRecovery) {
    Write-Host "Starting Docker Auto-Recovery monitoring in background..." -ForegroundColor Cyan
    Start-Job -ScriptBlock {
        while ($true) {
            Start-Sleep -Seconds 60
            $containers = docker ps --filter "name=casestrainer" --format "{{.Names}}" 2>$null
            if (-not $containers) {
                Write-Host "$(Get-Date): No CaseStrainer containers running - attempting restart" -ForegroundColor Yellow
                docker compose -f docker-compose.prod.yml up -d 2>$null
            }
        }
    } -Name "DockerAutoRecovery" | Out-Null
    Write-Host "Docker Auto-Recovery job started." -ForegroundColor Green
}
elseif ($Windows) {
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
            Write-Host "CaseStrainer started successfully with PID: $($process.Id)" -ForegroundColor Green
            Write-Host "Access URL: http://localhost:5000/casestrainer/" -ForegroundColor Cyan
            Write-Host "API Health: http://localhost:5000/casestrainer/api/health" -ForegroundColor Cyan
        } else {
            Write-Host "CaseStrainer started but health check failed: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Failed to start CaseStrainer: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Check the logs for more details" -ForegroundColor Yellow
    }
}
elseif ($Direct) {
    Start-DirectMode
}
elseif ($HealthCheck) {
    Write-Host "Running Enhanced Docker Health Check..." -ForegroundColor Magenta
    Write-Host "Performing basic Docker health check..." -ForegroundColor Cyan
    docker system df
    docker ps -a
    docker version
}
elseif ($Prevent) {
    Write-Host "Running Docker Prevention and Optimization..." -ForegroundColor Blue
    Write-Host "Performing basic Docker cleanup..." -ForegroundColor Yellow
    docker system prune -f
    Write-Host "Prevention and optimization completed!" -ForegroundColor Green
}
elseif ($Quick) { 
    Write-Host "Quick Start" -ForegroundColor Green
    # Detect container type and set compose file
    $dockerInfo = docker info 2>$null
    if ($dockerInfo -match "OSType: windows") {
        $composeFile = "docker-compose.windows-working.yml"
    } else {
        $composeFile = "docker-compose.prod.yml"
    }
    docker compose -f $composeFile up -d
    Write-Host "Quick Start completed!" -ForegroundColor Green
}
elseif ($Fast) { 
    Write-Host "Fast Start" -ForegroundColor Cyan
    # Detect container type and set compose file
    $dockerInfo = docker info 2>$null
    if ($dockerInfo -match "OSType: windows") {
        $composeFile = "docker-compose.windows-working.yml"
    } else {
        $composeFile = "docker-compose.prod.yml"
    }
    docker compose -f $composeFile down
    docker compose -f $composeFile up -d
    Write-Host "Fast Start completed!" -ForegroundColor Green
}
elseif ($Full) { 
    Write-Host "Full Rebuild" -ForegroundColor Yellow
    # Detect container type and set compose file
    $dockerInfo = docker info 2>$null
    if ($dockerInfo -match "OSType: windows") {
        $composeFile = "docker-compose.windows-working.yml"
    } else {
        $composeFile = "docker-compose.prod.yml"
    }
    docker compose -f $composeFile down
    docker system prune -af --volumes
    docker compose -f $composeFile build --no-cache
    docker compose -f $composeFile up -d
    Write-Host "Full Rebuild completed!" -ForegroundColor Green
}
else {
    Write-Host "Smart Auto-Detection with Code Change Detection..." -ForegroundColor Magenta
    
    # Check if Docker is running
    $dockerVersion = docker --version 2>$null
    if (-not $dockerVersion) {
        Write-Host "Docker is not running. Please start Docker Engine first." -ForegroundColor Red
        Write-Host "Try: .\cslaunch.ps1 -HealthCheck" -ForegroundColor Yellow
        exit 1
    }
    
    # Detect container type
    $containerType = "linux"
    try {
        $dockerInfo = docker info 2>$null
        if ($dockerInfo -match "OSType: windows") {
            $containerType = "windows"
            Write-Host "Detected Windows containers" -ForegroundColor Cyan
        } else {
            Write-Host "Detected Linux containers" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "Could not determine container type, assuming Linux" -ForegroundColor Yellow
    }
    
    # Set compose file
    if ($containerType -eq "windows") {
        $composeFile = "docker-compose.windows-working.yml"
    } else {
        $composeFile = "docker-compose.prod.yml"
    }
    Write-Host "Using compose file: $composeFile" -ForegroundColor Green
    
    # Check container status
    $containers = docker ps --filter "name=casestrainer" --format "table" 2>$null
    $allContainers = docker ps -a --filter "name=casestrainer" --format "table" 2>$null
    
    # Determine action based on code changes
    $codeChanged = Test-CodeChanged
    
    if (-not $allContainers) {
        Write-Host "No containers exist - performing Full Rebuild..." -ForegroundColor Yellow
        docker compose -f $composeFile down
        docker compose -f $composeFile build --no-cache
        docker compose -f $composeFile up -d
        Write-Host "Full Rebuild completed!" -ForegroundColor Green
    } elseif ($codeChanged) {
        Write-Host "Code has changed - performing Full Rebuild..." -ForegroundColor Yellow
        docker compose -f $composeFile down
        docker compose -f $composeFile build --no-cache
        docker compose -f $composeFile up -d
        Write-Host "Full Rebuild completed!" -ForegroundColor Green
    } elseif (-not $containers) {
        Write-Host "Containers exist but not running - performing Fast Start..." -ForegroundColor Cyan
        docker compose -f $composeFile down
        docker compose -f $composeFile up -d
        Write-Host "Fast Start completed!" -ForegroundColor Green
    } else {
        Write-Host "Containers running and code unchanged - performing Quick Start..." -ForegroundColor Green
        docker compose -f $composeFile up -d
        Write-Host "Quick Start completed!" -ForegroundColor Green
    }
    
    # Display final status
    Write-Host ""
    Write-Host "CaseStrainer is ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Cyan
    Write-Host "  .\cslaunch.ps1        # Smart auto-detect (recommended)" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1 -Quick # Quick start (no rebuild)" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1 -Fast  # Fast start (restart containers)" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1 -Full  # Force full rebuild" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1 -Status # Check status and code changes" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1 -Windows # Direct Windows mode" -ForegroundColor White
}