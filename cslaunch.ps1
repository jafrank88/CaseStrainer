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
    [switch]$StartRecovery
)

if ($Help) { 
    Write-Host "CaseStrainer Enhanced Launcher" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Basic Commands:" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1              # Intelligent auto-detect (recommended)" -ForegroundColor Green
    Write-Host "  .\cslaunch.ps1 -Fast        # Fast Start (restart with latest code)" -ForegroundColor Cyan
    Write-Host "  .\cslaunch.ps1 -Quick       # Quick Start (when everything is ready)" -ForegroundColor Green
    Write-Host "  .\cslaunch.ps1 -Full        # Full Rebuild (complete reset)" -ForegroundColor Yellow
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
    Write-Host "Docker Optimization:" -ForegroundColor White
    Write-Host "  .\cslaunch.ps1 -OptimizeDocker # Configure Docker Desktop for maximum performance" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Auto-detection logic:" -ForegroundColor White
    Write-Host "  • No containers exist → Full Rebuild" -ForegroundColor Gray
    Write-Host "  • Containers stopped → Fast Start" -ForegroundColor Gray
    Write-Host "  • Code changes detected → Fast Start" -ForegroundColor Gray
    Write-Host "  • No changes, running → Quick Start" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Monitoring Features:" -ForegroundColor White
    Write-Host "  • Auto-restart Docker Desktop when it stops" -ForegroundColor Gray
    Write-Host "  • Smart resource management for Dify containers" -ForegroundColor Gray
    Write-Host "  • Prioritize CaseStrainer performance" -ForegroundColor Gray
    Write-Host "  • Comprehensive logging and alerting" -ForegroundColor Gray
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
    & .\optimize_docker_desktop.ps1 -MaxResources -AutoRestart -Verbose
}
elseif ($StartMonitoring) {
    Write-Host "Starting Background Monitoring Systems..." -ForegroundColor Green
    & .\start_monitoring.ps1 -Background -Verbose
    Write-Host "Monitoring systems started in background!" -ForegroundColor Green
    Write-Host "Use '.\cslaunch.ps1 -Monitor' to check status" -ForegroundColor Cyan
}
elseif ($StopMonitoring) {
    Write-Host "Stopping Background Monitoring Systems..." -ForegroundColor Red
    Get-Job | Where-Object { $_.Name -like "*monitoring*" -or $_.Name -like "*recovery*" -or $_.Name -like "*resource*" } | Stop-Job
    Get-Job | Where-Object { $_.Name -like "*monitoring*" -or $_.Name -like "*recovery*" -or $_.Name -like "*resource*" } | Remove-Job
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
        Write-Host ""
    } else {
        Write-Host "No monitoring jobs running" -ForegroundColor Yellow
        Write-Host "Use '.\cslaunch.ps1 -StartMonitoring' to start monitoring" -ForegroundColor Cyan
        Write-Host ""
    }
    
    # Check recent logs
    if (Test-Path "logs/docker_auto_recovery.log") {
        Write-Host "Recent Auto-Recovery Logs:" -ForegroundColor Green
        Get-Content "logs/docker_auto_recovery.log" -Tail 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        Write-Host ""
    }
    
    if (Test-Path "logs/smart_resource_manager.log") {
        Write-Host "Recent Resource Manager Logs:" -ForegroundColor Green
        Get-Content "logs/smart_resource_manager.log" -Tail 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        Write-Host ""
    }
}
elseif ($Status) {
    Write-Host "Comprehensive System Status:" -ForegroundColor Yellow
    Write-Host ""
    
    # Docker status and zombie process check
    Write-Host "Docker Process Status:" -ForegroundColor Cyan
    $dockerProcesses = Get-Process *docker* -ErrorAction SilentlyContinue
    Write-Host "  Total Docker processes: $($dockerProcesses.Count)" -ForegroundColor White
    
    $zombieProcesses = $dockerProcesses | Where-Object { $_.CPU -lt 1.0 -and $_.ProcessName -notmatch "com\.docker\.service|Docker Desktop" }
    if ($zombieProcesses.Count -gt 0) {
        Write-Host "  ⚠️  Zombie processes detected: $($zombieProcesses.Count)" -ForegroundColor Red
        $zombieProcesses | ForEach-Object {
            Write-Host "    - $($_.ProcessName) (PID: $($_.Id)) CPU: $($_.CPU)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✅ No zombie processes detected" -ForegroundColor Green
    }
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
    
    # Application health
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
    
    # Monitoring status
    Write-Host ""
    Write-Host "Monitoring Status:" -ForegroundColor Cyan
    $monitoringJobs = Get-Job | Where-Object { $_.State -eq "Running" }
    if ($monitoringJobs) {
        Write-Host "  ✅ Monitoring: Active ($($monitoringJobs.Count) jobs)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Monitoring: Not running" -ForegroundColor Red
    }
}
elseif ($StartRecovery) {
    Write-Host "Starting Docker Auto-Recovery monitoring in background..." -ForegroundColor Cyan
    # Start the auto-recovery script as a background job
    Start-Job -ScriptBlock { & "$PSScriptRoot\docker_auto_recovery.ps1" -CheckInterval 10 -Verbose } -Name "DockerAutoRecovery" | Out-Null
    Write-Host "Docker Auto-Recovery job started." -ForegroundColor Green
}
elseif ($HealthCheck) {
    Write-Host "Running Enhanced Docker Health Check with Auto-Recovery..." -ForegroundColor Magenta
    
    # Run the enhanced health check
    if (Test-Path ".\docker_auto_recovery.ps1") {
        & .\docker_auto_recovery.ps1 -Verbose -CheckInterval 10
    } else {
        Write-Host "Running basic health check..." -ForegroundColor Yellow
        & .\docker_health_check.ps1 -AutoRestart -DeepDiagnostics -CollectLogs
    }
}
elseif ($Prevent) {
    Write-Host "Running Comprehensive Docker Prevention and Optimization..." -ForegroundColor Blue
    
    # Run Docker optimization
    if (Test-Path ".\optimize_docker_desktop.ps1") {
        & .\optimize_docker_desktop.ps1 -MaxResources -AutoRestart -Verbose
    }
    
    # Run prevention scripts
    if (Test-Path ".\prevent_docker_issues.ps1") {
        & .\prevent_docker_issues.ps1 -AutoFix
    }
    
    # Start monitoring if not already running
    $monitoringJobs = Get-Job | Where-Object { $_.State -eq "Running" }
    if (-not $monitoringJobs) {
        Write-Host "Starting monitoring systems..." -ForegroundColor Green
        & .\start_monitoring.ps1 -Background -Verbose
    }
    
    Write-Host "Prevention and optimization completed!" -ForegroundColor Green
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
    Write-Host "Intelligent Auto-Detection with Enhanced Monitoring..." -ForegroundColor Magenta
    
    # Enhanced Docker health check and prevention before proceeding
    Write-Host "Pre-flight Docker health check and prevention..." -ForegroundColor Gray
    if (Test-Path "$PSScriptRoot\docker_prevention.ps1") {
        & "$PSScriptRoot\docker_prevention.ps1"
    } elseif (Test-Path "$PSScriptRoot\smart_docker_monitor.ps1") {
        & "$PSScriptRoot\smart_docker_monitor.ps1" -AutoFix
    } else {
        Write-Host "Using fallback health check..." -ForegroundColor Yellow
        docker system df
        docker ps -a
    }
    
    # Enhanced source change detection and rebuild logic
    Write-Host "Checking for source code changes..." -ForegroundColor Cyan
    
    $codeChanged = $false
    $changeDetails = @()
    
    # Check for uncommitted changes
    if (Test-Path "$PSScriptRoot\.git") {
        $gitStatus = git status --porcelain 2>$null
        if ($gitStatus) {
            $codeChanged = $true
            $changeDetails += "Git changes: $($gitStatus.Count) files"
            Write-Host "Git changes detected: $($gitStatus.Count) files" -ForegroundColor Yellow
        }
    }
    
    # Check file modification times against container images
    $sourceFiles = @(
        "$PSScriptRoot\src\app.py",
        "$PSScriptRoot\src\*.py",
        "$PSScriptRoot\frontend\src\main.js",
        "$PSScriptRoot\frontend\src\*.js",
        "$PSScriptRoot\frontend\src\*.vue",
        "$PSScriptRoot\backend\Dockerfile",
        "$PSScriptRoot\frontend\Dockerfile",
        "$PSScriptRoot\worker\Dockerfile",
        "$PSScriptRoot\docker-compose.yml"
    )
    
    $latestSourceTime = Get-Date "2000-01-01"
    foreach ($pattern in $sourceFiles) {
        Get-ChildItem -Path $pattern -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.LastWriteTime -gt $latestSourceTime) {
                $latestSourceTime = $_.LastWriteTime
            }
        }
    }
    
    # Check latest container build times
    $backendImageTime = $null
    $frontendImageTime = $null
    $workerImageTime = $null
    
    try {
        $backendImage = docker images --format "{{.CreatedAt}}" casestrainer-backend:latest 2>$null
        if ($backendImage) { $backendImageTime = [DateTime]::Parse($backendImage.Split()[0] + " " + $backendImage.Split()[1]) }
        
        $frontendImage = docker images --format "{{.CreatedAt}}" casestrainer-frontend:latest 2>$null
        if ($frontendImage) { $frontendImageTime = [DateTime]::Parse($frontendImage.Split()[0] + " " + $frontendImage.Split()[1]) }
        
        $workerImage = docker images --format "{{.CreatedAt}}" casestrainer-rqworker:latest 2>$null
        if ($workerImage) { $workerImageTime = [DateTime]::Parse($workerImage.Split()[0] + " " + $workerImage.Split()[1]) }
    } catch {
        Write-Host "Could not determine image build times - assuming rebuild needed" -ForegroundColor Yellow
        $codeChanged = $true
    }
    
    # Determine if rebuild is needed
    $rebuildNeeded = $false
    
    if ($backendImageTime -and $latestSourceTime -gt $backendImageTime) {
        $rebuildNeeded = $true
        $changeDetails += "Backend source newer than image"
    }
    
    if ($frontendImageTime -and $latestSourceTime -gt $frontendImageTime) {
        $rebuildNeeded = $true
        $changeDetails += "Frontend source newer than image"
    }
    
    if ($workerImageTime -and $latestSourceTime -gt $workerImageTime) {
        $rebuildNeeded = $true
        $changeDetails += "Worker source newer than image"
    }
    
    if ($changeDetails) {
        Write-Host "Source changes detected: $($changeDetails -join ', ')" -ForegroundColor Yellow
        Write-Host "Latest source: $latestSourceTime" -ForegroundColor Gray
    }
    
    # Check if containers exist
    $containersExist = docker ps -a --format "table {{.Names}}" | Select-String -Pattern "casestrainer" -Quiet
    
    # Determine action based on state and changes
    if (-not $containersExist) {
        Write-Host "No containers exist - performing Full Rebuild..." -ForegroundColor Magenta
        if (Test-Path "$PSScriptRoot\cslaunch_full.ps1") {
            & "$PSScriptRoot\cslaunch_full.ps1"
        } else {
            Write-Host "Running docker-compose up --build for full rebuild..." -ForegroundColor Magenta
            docker-compose down
            docker-compose build --no-cache
            docker-compose up -d
        }
    } elseif ($rebuildNeeded -or $codeChanged) {
        Write-Host "Source changes detected - performing Fast Start with rebuild..." -ForegroundColor Yellow
        if (Test-Path "$PSScriptRoot\cslaunch_fast.ps1") {
            & "$PSScriptRoot\cslaunch_fast.ps1"
        } else {
            Write-Host "Running docker-compose up --build for fast rebuild..." -ForegroundColor Yellow
            docker-compose down
            docker-compose build
            docker-compose up -d
        }
    } else {
        Write-Host "No source changes detected - performing Quick Start..." -ForegroundColor Green
        if (Test-Path "$PSScriptRoot\cslaunch_quick.ps1") {
            & "$PSScriptRoot\cslaunch_quick.ps1"
        } else {
            Write-Host "Running docker-compose up for quick start..." -ForegroundColor Green
            docker-compose up -d
        }
    }
    
    # Check if Docker is running
    $dockerVersion = docker --version 2>$null
    if (-not $dockerVersion) {
        Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
        Write-Host "Try: .\cslaunch.ps1 -HealthCheck" -ForegroundColor Yellow
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
    
    # Start monitoring systems if not already running
    $monitoringJobs = Get-Job | Where-Object { $_.State -eq "Running" }
    if (-not $monitoringJobs) {
        Write-Host "Starting background monitoring systems..." -ForegroundColor Green
        if (Test-Path ".\start_monitoring.ps1") {
            & .\start_monitoring.ps1 -Background -Verbose
        }
    }
    
    Write-Host ""
    Write-Host "✅ CaseStrainer is ready!" -ForegroundColor Green
    Write-Host "🧟 Zombie Process Monitor: Run 'docker_zombie_monitor.ps1' for continuous monitoring" -ForegroundColor Magenta
    Write-Host "🌐 Access at: https://wolf.law.uw.edu/casestrainer/" -ForegroundColor Cyan
    Write-Host "📊 Status: .\cslaunch.ps1 -Status" -ForegroundColor Yellow
    Write-Host "🔍 Monitor: .\cslaunch.ps1 -Monitor" -ForegroundColor Yellow
}
