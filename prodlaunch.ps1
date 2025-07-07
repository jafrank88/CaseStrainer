# Enhanced CaseStrainer Docker Production Launcher - Complete Improved Version
# Includes better error handling, security, and full implementation

param(
    [ValidateSet("Production", "Diagnostics", "Menu", "Cache")]
    [string]$Mode = "Menu",
    [switch]$Help,
    [switch]$AutoRestart
)

# Input validation
if (-not $PSScriptRoot) {
    throw "Script must be run from a file, not from command line"
}

# Global variables for auto-restart
$script:AutoRestartEnabled = $AutoRestart.IsPresent
$script:RestartCount = 0
$script:MaxRestartAttempts = 3
$script:CrashLogFile = Join-Path $PSScriptRoot "logs\crash.log"
$script:MonitoringJob = $null

# Show help
if ($Help) {
    Write-Host @"
Enhanced CaseStrainer Docker Production Launcher - Help

Usage:
  .\prodlaunch.ps1 [Options]

Options:
  -Mode Production    Start Docker Production Mode
  -Mode Diagnostics   Run Advanced Production Diagnostics
  -Mode Cache         Manage Citation Caches
  -Mode Menu         Show interactive menu (default)
  -AutoRestart       Enable auto-restart monitoring
  -Help              Show this help

Examples:
  .\prodlaunch.ps1                           # Show menu
  .\prodlaunch.ps1 -Mode Production          # Start production directly
  .\prodlaunch.ps1 -Mode Diagnostics         # Run diagnostics directly
  .\prodlaunch.ps1 -Mode Cache               # Manage caches
  .\prodlaunch.ps1 -Mode Production -AutoRestart  # Start with auto-restart
"@ -ForegroundColor Cyan
    exit 0
}

# Validate script environment
function Test-ScriptEnvironment {
    [CmdletBinding()]
    param()
    
    $requiredFiles = @(
        "docker-compose.prod.yml",
        "casestrainer-vue-new"
    )
    
    foreach ($file in $requiredFiles) {
        $path = Join-Path $PSScriptRoot $file
        if (-not (Test-Path $path)) {
            throw "Required file/directory not found: $file"
        }
    }
}

function Write-CrashLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        [ValidateSet("INFO", "WARN", "ERROR", "DEBUG")]
        [string]$Level = "INFO",
        [System.Management.Automation.ErrorRecord]$Exception = $null
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    if ($Exception) {
        $logEntry += " - Exception: $($Exception.Exception.Message)"
        $logEntry += " - StackTrace: $($Exception.ScriptStackTrace)"
    }
    
    try {
        $logDir = Split-Path $script:CrashLogFile -Parent
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        }
        Add-Content -Path $script:CrashLogFile -Value $logEntry -ErrorAction Stop
    } catch {
        Write-Warning "Could not write to crash log: $($_.Exception.Message)"
    }
}

function Initialize-LogDirectory {
    [CmdletBinding()]
    param()
    
    $logDir = Join-Path $PSScriptRoot "logs"
    if (-not (Test-Path $logDir)) {
        try {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        } catch {
            Write-Warning "Could not create log directory: $($_.Exception.Message)"
        }
    }
}

function Show-NpmProgress {
    [CmdletBinding()]
    param(
        [string]$ProcessName,
        [string]$LogFile,
        [string]$ErrorLogFile
    )
    
    $startTime = Get-Date
    $dots = 0
    
    while ($true) {
        $elapsed = (Get-Date) - $startTime
        $elapsedStr = "{0:mm}:{0:ss}" -f $elapsed
        
        # Show animated dots
        $dotStr = "." * ($dots % 4)
        Write-Host "`r$ProcessName in progress$dotStr ($elapsedStr elapsed)" -NoNewline -ForegroundColor Yellow
        
        # Check if process is still running by looking for the log file
        if (Test-Path $LogFile) {
            $lastModified = (Get-Item $LogFile).LastWriteTime
            if ((Get-Date) - $lastModified -gt [TimeSpan]::FromMinutes(5)) {
                # Process seems to have stopped
                break
            }
        }
        
        # Check for errors
        if (Test-Path $ErrorLogFile) {
            $errorContent = Get-Content $ErrorLogFile -ErrorAction SilentlyContinue
            if ($errorContent -and $errorContent.Count -gt 0) {
                Write-Host "`n❌ Error detected in $ProcessName" -ForegroundColor Red
                $errorContent | Select-Object -Last 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
                return $false
            }
        }
        
        Start-Sleep -Seconds 1
        $dots++
    }
    
    Write-Host "`n" # New line after progress
    return $true
}

function Test-DockerAvailability {
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    
    try {
        $null = docker info --format "{{.ServerVersion}}" 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        Write-CrashLog "Docker availability check failed" -Level "ERROR" -Exception $_
        return $false
    }
}

function Show-Menu {
    [CmdletBinding()]
    [OutputType([string])]
    param()
    
    Clear-Host
    Write-Host "`n" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " Enhanced CaseStrainer Docker Launcher" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " 1. Docker Production Mode" -ForegroundColor Green
    Write-Host "    - Complete Docker Compose deployment"
    Write-Host "    - Redis, Backend, RQ Worker, Frontend, Nginx"
    Write-Host "    - Production-ready with SSL support"
    Write-Host ""
    Write-Host " 2. Advanced Production Diagnostics" -ForegroundColor Cyan
    Write-Host "    - Comprehensive system checks"
    Write-Host "    - Container health analysis"
    Write-Host "    - Performance monitoring"
    Write-Host "    - Network connectivity tests"
    Write-Host ""
    Write-Host " 3. Citation Cache Management" -ForegroundColor Yellow
    Write-Host "    - View cache information"
    Write-Host "    - Clear unverified citations"
    Write-Host "    - Clear all citation cache"
    Write-Host "    - Show cache statistics"
    Write-Host ""
    Write-Host " 4. Stop All Services" -ForegroundColor Red
    Write-Host " 5. View Container Status" -ForegroundColor Yellow
    Write-Host " 6. View Logs" -ForegroundColor Yellow
    Write-Host " 7. Auto-Restart Monitoring" -ForegroundColor Magenta
    Write-Host " 0. Exit" -ForegroundColor Gray
    Write-Host ""
    
    do {
        $selection = Read-Host "Select an option (0-7)"
        if ($selection -match "^[0-7]$") {
            return $selection
        } else {
            Write-Host "Invalid selection. Please enter a number between 0 and 7." -ForegroundColor Red
        }
    } while ($true)
}

function Start-DockerProduction {
    [CmdletBinding(SupportsShouldProcess)]
    [OutputType([bool])]
    param()
    
    Write-Host "`n=== Starting Docker Production Mode ===`n" -ForegroundColor Green
    
    try {
        # Validate environment first
        Test-ScriptEnvironment
        
        if (-not (Test-DockerAvailability)) {
            Write-Host "❌ Docker is not running or not available" -ForegroundColor Red
            Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
            return $false
        }
        Write-Host "✅ Docker is running" -ForegroundColor Green
        
        $dockerComposeFile = Join-Path $PSScriptRoot "docker-compose.prod.yml"
        
        # Build Vue frontend with better error handling
        Write-Host "`nBuilding Vue frontend..." -ForegroundColor Cyan
        $vueDir = Join-Path $PSScriptRoot "casestrainer-vue-new"
        
        Push-Location $vueDir
        try {
            # Check if package.json exists
            if (-not (Test-Path "package.json")) {
                throw "package.json not found in Vue directory"
            }
            
            Write-Host "Running npm install..." -ForegroundColor Yellow
            Write-Host "This may take a few minutes. Please wait..." -ForegroundColor Gray
            
            # Start npm install in background and show progress
            $installJob = Start-Job -ScriptBlock {
                param($VueDir)
                Set-Location $VueDir
                & npm install 2>&1
            } -ArgumentList $vueDir
            
            # Show progress while npm install runs
            $installLogFile = Join-Path $PSScriptRoot "logs\npm_install.log"
            $installErrorFile = Join-Path $PSScriptRoot "logs\npm_install_error.log"
            
            # Monitor the job and show progress
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
                $installResult | Where-Object { $_ -match "error|Error|ERROR" } | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
                throw "npm install failed"
            }
            
            Write-Host "✅ npm install completed successfully" -ForegroundColor Green
            
            Write-Host "Running npm build..." -ForegroundColor Yellow
            Write-Host "Building Vue frontend for production..." -ForegroundColor Gray
            
            # Start npm build in background and show progress
            $buildJob = Start-Job -ScriptBlock {
                param($VueDir)
                Set-Location $VueDir
                & npm run build 2>&1
            } -ArgumentList $vueDir
            
            # Monitor the job and show progress
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
                $buildResult | Where-Object { $_ -match "error|Error|ERROR" } | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
                throw "npm build failed"
            }
            
            Write-Host "✅ Vue frontend built successfully" -ForegroundColor Green
        } finally {
            Pop-Location
        }
        
        # Stop existing containers with proper error handling
        if ($PSCmdlet.ShouldProcess("Docker containers", "Stop existing")) {
            Write-Host "`nStopping existing containers..." -ForegroundColor Yellow
            $stopProcess = Start-Process -FilePath "docker-compose" -ArgumentList "-f", $dockerComposeFile, "down" -Wait -NoNewWindow -PassThru -WorkingDirectory $PSScriptRoot
            if ($stopProcess.ExitCode -ne 0) {
                Write-Warning "Failed to stop existing containers (they may not be running)"
            }
        }
        
        # Start containers
        if ($PSCmdlet.ShouldProcess("Docker containers", "Start")) {
            Write-Host "`nStarting Docker containers..." -ForegroundColor Cyan
            Write-Host "This will start: Redis, Backend, RQ Workers, Frontend, and Nginx" -ForegroundColor Gray
            
            # Start containers in background and show progress
            $startJob = Start-Job -ScriptBlock {
                param($DockerComposeFile, $WorkingDir)
                Set-Location $WorkingDir
                & docker-compose -f $DockerComposeFile up -d 2>&1
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
                $startResult | Where-Object { $_ -match "error|Error|ERROR" } | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
                throw "Docker container startup failed"
            }
            
            Write-Host "✅ Docker containers started successfully" -ForegroundColor Green
            Write-Host "Waiting for services to become healthy..." -ForegroundColor Yellow
                
                # Enhanced health checks with timeout
                if (Wait-ForServices -TimeoutMinutes 5) {
                    Show-ServiceUrls
                    
                    # Start auto-restart monitoring if enabled
                    if ($script:AutoRestartEnabled) {
                        Start-ServiceMonitoring
                        Write-Host "`n🔄 Auto-restart monitoring enabled" -ForegroundColor Magenta
                    }
                    
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
            }
        }
    } catch {
        Write-CrashLog "Error in Start-DockerProduction" -Level "ERROR" -Exception $_
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Wait-ForServices {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [int]$TimeoutMinutes = 5
    )
    
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

function Start-ServiceMonitoring {
    [CmdletBinding()]
    param()
    
    if ($script:MonitoringJob) {
        Stop-Job $script:MonitoringJob -ErrorAction SilentlyContinue
        Remove-Job $script:MonitoringJob -ErrorAction SilentlyContinue
    }
    
    $monitoringScript = {
        param($ScriptRoot, $LogFile, $MaxAttempts)
        
        $restartCount = 0
        while ($restartCount -lt $MaxAttempts) {
            Start-Sleep -Seconds 30
            
            try {
                # Check container health
                $containers = docker ps --filter "name=casestrainer" --format "{{.Names}},{{.Status}}" 2>$null
                if ($LASTEXITCODE -ne 0) { continue }
                
                $unhealthyContainers = @()
                foreach ($container in $containers) {
                    if ($container -and $container -notlike "*Up*") {
                        $containerName = $container.Split(',')[0]
                        $unhealthyContainers += $containerName
                    }
                }
                
                if ($unhealthyContainers.Count -gt 0) {
                    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                    $logEntry = "[$timestamp] [MONITOR] Unhealthy containers detected: $($unhealthyContainers -join ', ')"
                    Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
                    
                    # Attempt restart
                    docker-compose -f "$ScriptRoot\docker-compose.prod.yml" restart $unhealthyContainers[0] 2>$null
                    $restartCount++
                    
                    $logEntry = "[$timestamp] [MONITOR] Restart attempt $restartCount for $($unhealthyContainers[0])"
                    Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
                }
            } catch {
                $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                $logEntry = "[$timestamp] [MONITOR] Monitoring error: $($_.Exception.Message)"
                Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
            }
        }
    }
    
    $script:MonitoringJob = Start-Job -ScriptBlock $monitoringScript -ArgumentList $PSScriptRoot, $script:CrashLogFile, $script:MaxRestartAttempts
}

function Show-ServiceUrls {
    Write-Host "`n=== Docker Production Mode Ready ===`n" -ForegroundColor Green
    Write-Host "Backend API:    http://localhost:5001/casestrainer/api/" -ForegroundColor Green
    Write-Host "Frontend Prod:  http://localhost:8080/" -ForegroundColor Green
    Write-Host "Nginx (HTTP):   http://localhost:80/" -ForegroundColor Green
    Write-Host "Nginx (HTTPS):  https://localhost:443/" -ForegroundColor Green
    Write-Host "Main Frontend:  https://localhost/casestrainer/" -ForegroundColor Green
    Write-Host "API Health:     https://localhost/casestrainer/api/health" -ForegroundColor Green
    
    Write-Host "`nDocker Commands:" -ForegroundColor Cyan
    Write-Host "  View logs:    docker-compose -f docker-compose.prod.yml logs [service]" -ForegroundColor Gray
    Write-Host "  Stop all:     docker-compose -f docker-compose.prod.yml down" -ForegroundColor Gray
    Write-Host "  Restart:      docker-compose -f docker-compose.prod.yml restart [service]" -ForegroundColor Gray
}

function Show-AdvancedDiagnostics {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Advanced Production Diagnostics ===`n" -ForegroundColor Cyan
    
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
    
    # Enhanced container status
    Write-Host "`n=== Enhanced Container Status ===" -ForegroundColor Cyan
    try {
        $containers = docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}\t{{.Health}}\t{{.Ports}}"
        if ($containers -and $containers.Count -gt 1) {
            Write-Host "Container Status:" -ForegroundColor Gray
            $containers | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
            
            # Analyze container health
            $containerLines = $containers -split "`n" | Where-Object { $_ -match "casestrainer" }
            $runningCount = ($containerLines | Where-Object { $_ -match "Up" }).Count
            $healthyCount = ($containerLines | Where-Object { $_ -match "healthy" }).Count
            $unhealthyCount = ($containerLines | Where-Object { $_ -match "unhealthy" }).Count
            
            Write-Host "`nContainer Summary:" -ForegroundColor Green
            Write-Host "  Running: $runningCount" -ForegroundColor Green
            Write-Host "  Healthy: $healthyCount" -ForegroundColor Green
            Write-Host "  Unhealthy: $unhealthyCount" -ForegroundColor $(if ($unhealthyCount -gt 0) { "Red" } else { "Green" })
            
            if ($unhealthyCount -gt 0) {
                Write-Host "`n⚠️  UNHEALTHY CONTAINERS DETECTED!" -ForegroundColor Yellow
            }
        } else {
            Write-Host "❌ No CaseStrainer containers are running" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Could not check container status: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # API endpoint tests
    Write-Host "`n=== API Endpoint Tests ===" -ForegroundColor Cyan
    Test-ApiEndpoints
    
    # Redis tests
    Write-Host "`n=== Redis Tests ===" -ForegroundColor Cyan
    Test-RedisHealth
    
    # System resource monitoring
    Write-Host "`n=== System Resources ===" -ForegroundColor Cyan
    Show-SystemResources
    
    Write-Host "`n=== Advanced Diagnostics Complete ===`n" -ForegroundColor Green
}

function Test-ApiEndpoints {
    [CmdletBinding()]
    param()
    
    # Health endpoint
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:5001/casestrainer/api/health" -Method GET -TimeoutSec 10 -ErrorAction Stop
        Write-Host "✅ Health endpoint: Working" -ForegroundColor Green
    } catch {
        Write-Host "❌ Health endpoint: Error - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Analyze endpoint (light test)
    try {
        $testData = @{ type = "text"; text = "Test citation" } | ConvertTo-Json
        $analyzeResponse = Invoke-RestMethod -Uri "http://localhost:5001/casestrainer/api/analyze" -Method POST -Body $testData -ContentType "application/json" -TimeoutSec 15 -ErrorAction Stop
        Write-Host "✅ Analyze endpoint: Working" -ForegroundColor Green
    } catch {
        Write-Host "❌ Analyze endpoint: Error - $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Test-RedisHealth {
    [CmdletBinding()]
    param()
    
    try {
        $redisPing = docker exec casestrainer-redis-prod redis-cli ping 2>$null
        if ($LASTEXITCODE -eq 0 -and $redisPing -like "*PONG*") {
            Write-Host "✅ Redis is responding" -ForegroundColor Green
            
            # Get Redis memory info
            try {
                $redisMemory = docker exec casestrainer-redis-prod redis-cli info memory 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $usedMemoryLine = $redisMemory | Select-String "used_memory_human:"
                    $peakMemoryLine = $redisMemory | Select-String "used_memory_peak_human:"
                    
                    if ($usedMemoryLine) {
                        $usedMemory = $usedMemoryLine.ToString().Split(":")[1].Trim()
                        Write-Host "  Current memory usage: $usedMemory" -ForegroundColor Gray
                    }
                    if ($peakMemoryLine) {
                        $peakMemory = $peakMemoryLine.ToString().Split(":")[1].Trim()
                        Write-Host "  Peak memory usage: $peakMemory" -ForegroundColor Gray
                    }
                }
            } catch {
                Write-Host "⚠️  Could not get Redis memory info" -ForegroundColor Yellow
            }
        } else {
            Write-Host "❌ Redis connectivity failed" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Redis check failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Show-SystemResources {
    [CmdletBinding()]
    param()
    
    # Check disk space
    try {
        $diskSpace = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='C:'" -ErrorAction Stop
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
    try {
        $memory = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
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
}

function Show-CacheManagement {
    [CmdletBinding()]
    param()
    
    do {
        Write-Host "`n=== Citation Cache Management ===`n" -ForegroundColor Cyan
        
        Write-Host "Cache Management Options:" -ForegroundColor Yellow
        Write-Host "1. View Cache Information" -ForegroundColor Green
        Write-Host "2. Clear Unverified Citation Cache" -ForegroundColor Yellow
        Write-Host "3. Clear All Citation Cache" -ForegroundColor Red
        Write-Host "4. Show Cache Statistics" -ForegroundColor Cyan
        Write-Host "5. Backup Cache Data" -ForegroundColor Blue
        Write-Host "0. Return to Main Menu" -ForegroundColor Gray
        Write-Host ""
        
        do {
            $selection = Read-Host "Select an option (0-5)"
            if ($selection -match "^[0-5]$") {
                break
            } else {
                Write-Host "Invalid selection. Please enter a number between 0 and 5." -ForegroundColor Red
            }
        } while ($true)
        
        switch ($selection) {
            "1" { Show-CacheInfo }
            "2" { Clear-UnverifiedCitationCache }
            "3" { Clear-AllCitationCache }
            "4" { Show-CacheStatistics }
            "5" { Backup-CacheData }
            "0" { return }
        }
        
        if ($selection -ne "0") {
            Write-Host "`nPress any key to continue..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
    } while ($selection -ne "0")
}

function Show-CacheInfo {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Cache Information ===`n" -ForegroundColor Cyan
    
    # Citation database
    $citationDbPath = Join-Path $PSScriptRoot "data\citations.db"
    if (Test-Path $citationDbPath) {
        try {
            $dbSize = (Get-Item $citationDbPath).Length
            $dbSizeMB = [math]::Round($dbSize / 1MB, 2)
            Write-Host "Citation Database:" -ForegroundColor Green
            Write-Host "  Path: $citationDbPath" -ForegroundColor Gray
            Write-Host "  Size: $dbSizeMB MB" -ForegroundColor Gray
        } catch {
            Write-Host "Citation Database: Error reading file info" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Citation Database: Not found" -ForegroundColor Yellow
    }
    
    # Citation cache
    $citationCachePath = Join-Path $PSScriptRoot "citation_cache"
    if (Test-Path $citationCachePath) {
        try {
            $cacheItems = Get-ChildItem $citationCachePath -Recurse -File
            $cacheSize = ($cacheItems | Measure-Object -Property Length -Sum).Sum
            $cacheSizeMB = [math]::Round($cacheSize / 1MB, 2)
            Write-Host "`nCitation Cache:" -ForegroundColor Green
            Write-Host "  Path: $citationCachePath" -ForegroundColor Gray
            Write-Host "  Items: $($cacheItems.Count)" -ForegroundColor Gray
            Write-Host "  Size: $cacheSizeMB MB" -ForegroundColor Gray
        } catch {
            Write-Host "`nCitation Cache: Error reading cache info" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`nCitation Cache: Not found" -ForegroundColor Yellow
    }
    
    # Correction cache
    $correctionCachePath = Join-Path $PSScriptRoot "correction_cache"
    if (Test-Path $correctionCachePath) {
        try {
            $correctionItems = Get-ChildItem $correctionCachePath -Recurse -File
            $correctionSize = ($correctionItems | Measure-Object -Property Length -Sum).Sum
            $correctionSizeMB = [math]::Round($correctionSize / 1MB, 2)
            Write-Host "`nCorrection Cache:" -ForegroundColor Green
            Write-Host "  Path: $correctionCachePath" -ForegroundColor Gray
            Write-Host "  Items: $($correctionItems.Count)" -ForegroundColor Gray
            Write-Host "  Size: $correctionSizeMB MB" -ForegroundColor Gray
        } catch {
            Write-Host "`nCorrection Cache: Error reading cache info" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`nCorrection Cache: Not found" -ForegroundColor Yellow
    }
}

function Clear-UnverifiedCitationCache {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Host "`n=== Clear Unverified Citation Cache ===`n" -ForegroundColor Yellow
    Write-Host "This will remove citations that haven't been verified yet." -ForegroundColor Yellow
    Write-Host "This action cannot be undone!" -ForegroundColor Red
    
    $confirm = Read-Host "`nAre you sure you want to continue? (y/N)"
    if ($confirm -notmatch "^[Yy]") {
        Write-Host "Operation cancelled" -ForegroundColor Yellow
        return
    }
    
    if ($PSCmdlet.ShouldProcess("Unverified citation cache", "Clear")) {
        try {
            # Check if backend is available
            if (Test-NetConnection -ComputerName localhost -Port 5001 -InformationLevel Quiet -WarningAction SilentlyContinue) {
                Write-Host "Clearing unverified citation cache via API..." -ForegroundColor Yellow
                
                try {
                    $apiUrl = "http://localhost:5001/casestrainer/api/cache/clear-unverified"
                    $response = Invoke-RestMethod -Uri $apiUrl -Method POST -TimeoutSec 30
                    Write-Host "✅ Unverified citation cache cleared successfully via API" -ForegroundColor Green
                    return
                } catch {
                    Write-Host "⚠️  API call failed, attempting manual cleanup..." -ForegroundColor Yellow
                    Write-CrashLog "API cache clear failed" -Level "WARN" -Exception $_
                }
            }
            
            # Fallback to manual file cleanup
            Write-Host "Attempting manual cleanup..." -ForegroundColor Yellow
            $cachePattern = Join-Path $PSScriptRoot "citation_cache\*unverified*"
            $unverifiedFiles = Get-ChildItem $cachePattern -ErrorAction SilentlyContinue
            if ($unverifiedFiles) {
                Remove-Item $unverifiedFiles -Force
                Write-Host "✅ Manual cleanup completed ($($unverifiedFiles.Count) files removed)" -ForegroundColor Green
            } else {
                Write-Host "No unverified cache files found" -ForegroundColor Gray
            }
        } catch {
            Write-CrashLog "Error clearing unverified cache" -Level "ERROR" -Exception $_
            Write-Host "❌ Error clearing unverified cache: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

function Clear-AllCitationCache {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Host "`n=== Clear All Citation Cache ===`n" -ForegroundColor Red
    Write-Host "This will remove ALL citation cache data." -ForegroundColor Red
    Write-Host "This will force fresh API calls and may slow down initial requests." -ForegroundColor Yellow
    Write-Host "This action cannot be undone!" -ForegroundColor Red
    
    $confirm = Read-Host "`nAre you ABSOLUTELY sure you want to continue? (y/N)"
    if ($confirm -notmatch "^[Yy]") {
        Write-Host "Operation cancelled" -ForegroundColor Yellow
        return
    }
    
    if ($PSCmdlet.ShouldProcess("All citation cache data", "Clear")) {
        try {
            Write-Host "Clearing all citation cache..." -ForegroundColor Yellow
            
            # Clear citation cache directory
            $citationCachePath = Join-Path $PSScriptRoot "citation_cache"
            if (Test-Path $citationCachePath) {
                $itemCount = (Get-ChildItem $citationCachePath -Recurse -File).Count
                Remove-Item $citationCachePath -Recurse -Force
                Write-Host "✅ Citation cache directory cleared ($itemCount files)" -ForegroundColor Green
            }
            
            # Clear correction cache directory
            $correctionCachePath = Join-Path $PSScriptRoot "correction_cache"
            if (Test-Path $correctionCachePath) {
                $itemCount = (Get-ChildItem $correctionCachePath -Recurse -File).Count
                Remove-Item $correctionCachePath -Recurse -Force
                Write-Host "✅ Correction cache directory cleared ($itemCount files)" -ForegroundColor Green
            }
            
            Write-Host "✅ All citation cache cleared successfully" -ForegroundColor Green
        } catch {
            Write-CrashLog "Error clearing all cache" -Level "ERROR" -Exception $_
            Write-Host "❌ Error clearing cache: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

function Show-CacheStatistics {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Cache Statistics ===`n" -ForegroundColor Cyan
    
    try {
        # Citation cache statistics
        $citationCachePath = Join-Path $PSScriptRoot "citation_cache"
        if (Test-Path $citationCachePath) {
            $cacheFiles = Get-ChildItem $citationCachePath -Recurse -File
            if ($cacheFiles.Count -gt 0) {
                $totalSize = ($cacheFiles | Measure-Object -Property Length -Sum).Sum
                $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
                $avgFileSize = [math]::Round($totalSize / $cacheFiles.Count / 1KB, 2)
                
                Write-Host "Citation Cache Statistics:" -ForegroundColor Green
                Write-Host "  Total files: $($cacheFiles.Count)" -ForegroundColor Gray
                Write-Host "  Total size: $totalSizeMB MB" -ForegroundColor Gray
                Write-Host "  Average file size: $avgFileSize KB" -ForegroundColor Gray
                
                # Show file age distribution
                $now = Get-Date
                $recent = ($cacheFiles | Where-Object { $_.LastWriteTime -gt $now.AddDays(-7) }).Count
                $old = ($cacheFiles | Where-Object { $_.LastWriteTime -lt $now.AddDays(-30) }).Count
                
                Write-Host "  Files newer than 7 days: $recent" -ForegroundColor Gray
                Write-Host "  Files older than 30 days: $old" -ForegroundColor Gray
            } else {
                Write-Host "Citation cache is empty" -ForegroundColor Yellow
            }
        } else {
            Write-Host "Citation cache directory not found" -ForegroundColor Yellow
        }
        
        # Correction cache statistics
        $correctionCachePath = Join-Path $PSScriptRoot "correction_cache"
        if (Test-Path $correctionCachePath) {
            $correctionFiles = Get-ChildItem $correctionCachePath -Recurse -File
            if ($correctionFiles.Count -gt 0) {
                $totalSize = ($correctionFiles | Measure-Object -Property Length -Sum).Sum
                $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
                
                Write-Host "`nCorrection Cache Statistics:" -ForegroundColor Green
                Write-Host "  Total files: $($correctionFiles.Count)" -ForegroundColor Gray
                Write-Host "  Total size: $totalSizeMB MB" -ForegroundColor Gray
            }
        }
    } catch {
        Write-Host "❌ Error getting cache statistics: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Backup-CacheData {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Backup Cache Data ===`n" -ForegroundColor Blue
    
    try {
        $backupDir = Join-Path $PSScriptRoot "data\backups"
        if (-not (Test-Path $backupDir)) {
            New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        }
        
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupPath = Join-Path $backupDir "cache_backup_$timestamp"
        New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
        
        Write-Host "Creating backup at: $backupPath" -ForegroundColor Yellow
        
        $backupSize = 0
        $fileCount = 0
        
        # Backup citation cache
        $citationCachePath = Join-Path $PSScriptRoot "citation_cache"
        if (Test-Path $citationCachePath) {
            $destPath = Join-Path $backupPath "citation_cache"
            Copy-Item $citationCachePath -Destination $destPath -Recurse
            $files = Get-ChildItem $destPath -Recurse -File
            $size = ($files | Measure-Object -Property Length -Sum).Sum
            $backupSize += $size
            $fileCount += $files.Count
            Write-Host "✅ Citation cache backed up ($($files.Count) files)" -ForegroundColor Green
        }
        
        # Backup correction cache
        $correctionCachePath = Join-Path $PSScriptRoot "correction_cache"
        if (Test-Path $correctionCachePath) {
            $destPath = Join-Path $backupPath "correction_cache"
            Copy-Item $correctionCachePath -Destination $destPath -Recurse
            $files = Get-ChildItem $destPath -Recurse -File
            $size = ($files | Measure-Object -Property Length -Sum).Sum
            $backupSize += $size
            $fileCount += $files.Count
            Write-Host "✅ Correction cache backed up ($($files.Count) files)" -ForegroundColor Green
        }
        
        # Backup citation database
        $citationDbPath = Join-Path $PSScriptRoot "data\citations.db"
        if (Test-Path $citationDbPath) {
            $destPath = Join-Path $backupPath "citations.db"
            Copy-Item $citationDbPath -Destination $destPath
            $size = (Get-Item $destPath).Length
            $backupSize += $size
            $fileCount++
            Write-Host "✅ Citation database backed up" -ForegroundColor Green
        }
        
        $backupSizeMB = [math]::Round($backupSize / 1MB, 2)
        Write-Host "✅ Cache backup completed successfully" -ForegroundColor Green
        Write-Host "  Total files: $fileCount" -ForegroundColor Gray
        Write-Host "  Total size: $backupSizeMB MB" -ForegroundColor Gray
        Write-Host "  Location: $backupPath" -ForegroundColor Gray
        
    } catch {
        Write-CrashLog "Error creating backup" -Level "ERROR" -Exception $_
        Write-Host "❌ Error creating backup: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Stop-AllServices {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Host "`n=== Stopping All Services ===`n" -ForegroundColor Red
    
    if ($PSCmdlet.ShouldProcess("All Docker services", "Stop")) {
        try {
            # Stop monitoring first
            Stop-ServiceMonitoring
            
            $dockerComposeFile = Join-Path $PSScriptRoot "docker-compose.prod.yml"
            $stopProcess = Start-Process -FilePath "docker-compose" -ArgumentList "-f", $dockerComposeFile, "down" -Wait -NoNewWindow -PassThru -WorkingDirectory $PSScriptRoot
            
            if ($stopProcess.ExitCode -eq 0) {
                Write-Host "✅ All Docker services stopped successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠️  Docker services may not have stopped cleanly (exit code: $($stopProcess.ExitCode))" -ForegroundColor Yellow
            }
        } catch {
            Write-CrashLog "Error stopping services" -Level "ERROR" -Exception $_
            Write-Host "❌ Error stopping services: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "Operation cancelled by user" -ForegroundColor Yellow
    }
}

function Show-ContainerStatus {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Container Status ===`n" -ForegroundColor Cyan
    
    try {
        if (-not (Test-DockerAvailability)) {
            Write-Host "❌ Docker is not available" -ForegroundColor Red
            return
        }
        
        $containers = docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        if ($containers -and $containers.Count -gt 1) {
            $containers | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
            
            # Show additional details
            Write-Host "`nDetailed Container Information:" -ForegroundColor Cyan
            $containerNames = docker ps --filter "name=casestrainer" --format "{{.Names}}"
            foreach ($name in $containerNames) {
                if ($name) {
                    $inspect = docker inspect $name --format "{{.State.Health.Status}},{{.State.StartedAt}}" 2>$null
                    if ($LASTEXITCODE -eq 0 -and $inspect) {
                        $parts = $inspect.Split(',')
                        $health = if ($parts[0]) { $parts[0] } else { "No health check" }
                        $started = if ($parts[1]) { 
                            try {
                                $startTime = [DateTime]::Parse($parts[1])
                                $uptime = (Get-Date) - $startTime
                                "Up for $([math]::Floor($uptime.TotalHours))h $($uptime.Minutes)m"
                            } catch {
                                $parts[1]
                            }
                        } else { "Unknown" }
                        Write-Host "  $name`: Health=$health, $started" -ForegroundColor Gray
                    }
                }
            }
        } else {
            Write-Host "❌ No CaseStrainer containers are running" -ForegroundColor Red
        }
    } catch {
        Write-CrashLog "Error getting container status" -Level "ERROR" -Exception $_
        Write-Host "❌ Could not get container status: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Show-Logs {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Docker Logs ===`n" -ForegroundColor Cyan
    
    if (-not (Test-DockerAvailability)) {
        Write-Host "❌ Docker is not available" -ForegroundColor Red
        return
    }
    
    Write-Host "Available containers:" -ForegroundColor Yellow
    Write-Host "1. Backend (casestrainer-backend-prod)"
    Write-Host "2. Frontend (casestrainer-frontend-prod)"
    Write-Host "3. Nginx (casestrainer-nginx-prod)"
    Write-Host "4. Redis (casestrainer-redis-prod)"
    Write-Host "5. RQ Worker (casestrainer-rqworker-prod)"
    Write-Host "6. All containers"
    Write-Host "0. Return"
    Write-Host ""
    
    do {
        $selection = Read-Host "Select container (0-6)"
        if ($selection -match "^[0-6]$") {
            break
        } else {
            Write-Host "Invalid selection. Please enter a number between 0 and 6." -ForegroundColor Red
        }
    } while ($true)
    
    if ($selection -eq "0") { return }
    
    try {
        $dockerComposeFile = Join-Path $PSScriptRoot "docker-compose.prod.yml"
        
        switch ($selection) {
            "1" { 
                Write-Host "`nBackend logs (last 50 lines):" -ForegroundColor Cyan
                docker logs casestrainer-backend-prod --tail 50 
            }
            "2" { 
                Write-Host "`nFrontend logs (last 50 lines):" -ForegroundColor Cyan
                docker logs casestrainer-frontend-prod --tail 50 
            }
            "3" { 
                Write-Host "`nNginx logs (last 50 lines):" -ForegroundColor Cyan
                docker logs casestrainer-nginx-prod --tail 50 
            }
            "4" { 
                Write-Host "`nRedis logs (last 50 lines):" -ForegroundColor Cyan
                docker logs casestrainer-redis-prod --tail 50 
            }
            "5" { 
                Write-Host "`nRQ Worker logs (last 50 lines):" -ForegroundColor Cyan
                docker logs casestrainer-rqworker-prod --tail 50 
            }
            "6" { 
                Write-Host "`nAll container logs (last 20 lines each):" -ForegroundColor Cyan
                docker-compose -f $dockerComposeFile logs --tail 20 
            }
        }
    } catch {
        Write-Host "❌ Error retrieving logs: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Start-AutoRestartMonitoring {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Host "`n=== Auto-Restart Monitoring ===`n" -ForegroundColor Magenta
    
    if ($script:AutoRestartEnabled) {
        Write-Host "Auto-restart monitoring is already enabled" -ForegroundColor Green
        
        # Show monitoring status
        if ($script:MonitoringJob -and $script:MonitoringJob.State -eq "Running") {
            Write-Host "✅ Monitoring job is running" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Monitoring job is not running" -ForegroundColor Yellow
        }
    } else {
        $confirm = Read-Host "Enable auto-restart monitoring? (y/N)"
        if ($confirm -match "^[Yy]") {
            if ($PSCmdlet.ShouldProcess("Auto-restart monitoring", "Enable")) {
                $script:AutoRestartEnabled = $true
                Start-ServiceMonitoring
                Write-Host "✅ Auto-restart monitoring enabled" -ForegroundColor Green
            }
        } else {
            Write-Host "Auto-restart monitoring not enabled" -ForegroundColor Yellow
            return
        }
    }
    
    Write-Host "`nAuto-restart will:" -ForegroundColor Yellow
    Write-Host "- Monitor service health every 30 seconds" -ForegroundColor Gray
    Write-Host "- Automatically restart failed services" -ForegroundColor Gray
    Write-Host "- Log all restart attempts to: $($script:CrashLogFile)" -ForegroundColor Gray
    Write-Host "- Stop after $($script:MaxRestartAttempts) failed attempts" -ForegroundColor Gray
    
    if ($script:MonitoringJob) {
        Write-Host "`nMonitoring job ID: $($script:MonitoringJob.Id)" -ForegroundColor Gray
        Write-Host "Restart count: $($script:RestartCount)/$($script:MaxRestartAttempts)" -ForegroundColor Gray
    }
}

function Stop-ServiceMonitoring {
    [CmdletBinding()]
    param()
    
    if ($script:MonitoringJob) {
        try {
            Stop-Job $script:MonitoringJob -ErrorAction SilentlyContinue
            Remove-Job $script:MonitoringJob -ErrorAction SilentlyContinue
            $script:MonitoringJob = $null
            Write-CrashLog "Service monitoring stopped" -Level "INFO"
        } catch {
            Write-CrashLog "Error stopping service monitoring" -Level "WARN" -Exception $_
        }
    }
}

# Cleanup function for graceful shutdown
function Stop-AllMonitoring {
    [CmdletBinding()]
    param()
    
    Stop-ServiceMonitoring
    $script:AutoRestartEnabled = $false
}

# Register cleanup on script exit
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Stop-AllMonitoring
} | Out-Null

# Main execution
try {
    Initialize-LogDirectory
    Write-CrashLog "Script started with Mode: $Mode, AutoRestart: $($script:AutoRestartEnabled)" -Level "INFO"
    
    if ($Mode -ne "Menu") {
        # Direct mode execution
        switch ($Mode) {
            "Production" { 
                $result = Start-DockerProduction
                if (-not $result) {
                    exit 1
                }
            }
            "Diagnostics" { Show-AdvancedDiagnostics }
            "Cache" { Show-CacheManagement }
        }
    } else {
        # Interactive menu
        do {
            $selection = Show-Menu
            
            switch ($selection) {
                "1" { Start-DockerProduction }
                "2" { Show-AdvancedDiagnostics }
                "3" { Show-CacheManagement }
                "4" { Stop-AllServices }
                "5" { Show-ContainerStatus }
                "6" { Show-Logs }
                "7" { Start-AutoRestartMonitoring }
                "0" { 
                    Write-Host "`nShutting down..." -ForegroundColor Yellow
                    Stop-AllMonitoring
                    Write-CrashLog "Script exiting normally" -Level "INFO"
                    exit 0 
                }
                default { 
                    Write-Host "`nInvalid selection. Please try again." -ForegroundColor Red
                    Start-Sleep -Seconds 1
                }
            }
            
            if ($selection -ne "0") {
                Write-Host "`nPress any key to return to menu..." -NoNewline
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
        } while ($selection -ne "0")
    }
} catch {
    Write-CrashLog "Fatal error in main execution" -Level "ERROR" -Exception $_
    Write-Host "`nFatal Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check log file: $($script:CrashLogFile)" -ForegroundColor Yellow
    Stop-AllMonitoring
    exit 1
} finally {
    # Ensure cleanup happens
    Stop-AllMonitoring
}