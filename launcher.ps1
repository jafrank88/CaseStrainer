<# : Begin batch (batch script header for PowerShell)
@echo off
title CaseStrainer Launcher

:: Check if running from CMD or PowerShell
set "POWERSHELL_BITS=%PROCESSOR_ARCHITEW6432%"
if not defined POWERSHELL_BITS set "POWERSHELL_BITS=%PROCESSOR_ARCHITECTURE%"

:: If running from CMD, restart with PowerShell
if "%POWERSHELL_BITS%" neq "" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& '%~dpn0.ps1' %*"
    exit /b %ERRORLEVEL%
)

echo This should not be reached if PowerShell is available
exit /b 1

#>
# Final Working CaseStrainer Launcher - All fixes integrated

param(
    [ValidateSet("Development", "Production", "Menu")]
    [string]$Environment = "Menu",
    [switch]$NoMenu,
    [switch]$Help,
    [switch]$SkipBuild,
    [switch]$VerboseLogging
)

# Global variables for process tracking
$script:BackendProcess = $null
$script:FrontendProcess = $null
$script:NginxProcess = $null
$script:RedisProcess = $null
$script:RQWorkerProcess = $null
$script:LogDirectory = "logs"
$script:AutoRestartEnabled = $true
$script:MaxRestartAttempts = 5
$script:RestartDelaySeconds = 10
$script:HealthCheckInterval = 30
$script:RestartCount = 0
$script:LastRestartTime = $null
$script:MonitoringEnabled = $false
$script:CrashLogFile = $null

# Configuration
$config = @{
    # Paths
    BackendPath = "src/app_final_vue.py"
    FrontendPath = "casestrainer-vue-new"
    NginxPath = "nginx-1.27.5"
    NginxExe = "nginx.exe"
    
    # SSL Configuration
    SSL_CERT = "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\ssl\WolfCertBundle.crt"
    SSL_KEY = "C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\ssl\wolf.law.uw.edu.key"
    
    # Ports
    BackendPort = 5000
    FrontendDevPort = 5173
    ProductionPort = 443
    
    # URLs
    CORS_ORIGINS = "https://wolf.law.uw.edu"
    DatabasePath = "data/citations.db"
    
    # Redis
    RedisExe = "C:\Program Files\Redis\redis-server.exe"  # Update this path if your redis-server.exe is elsewhere
    RedisPort = 6379
}

# Define venv Python and Waitress paths
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$waitressExe = Join-Path $PSScriptRoot ".venv\Scripts\waitress-serve.exe"

# Ensure venv exists
if (!(Test-Path $venvPython)) {
    Write-Host "Virtual environment not found. Creating one..." -ForegroundColor Yellow
    python -m venv .venv
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r requirements.txt
}

# Docker Desktop helper functions
function Test-DockerDesktopStatus {
    # Check if Docker Desktop is running
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            return @{ Running = $true; Message = "Docker Desktop is running and accessible" }
        } else {
            return @{ Running = $false; Message = "Docker Desktop is not responding" }
        }
    } catch {
        return @{ Running = $false; Message = "Docker Desktop is not available" }
    }
}

function Start-DockerDesktop {
    Write-Host "Attempting to start Docker Desktop..." -ForegroundColor Cyan
    
    # Check if Docker Desktop is already running
    $dockerStatus = Test-DockerDesktopStatus
    if ($dockerStatus.Running) {
        Write-Host "Docker Desktop is already running!" -ForegroundColor Green
        return $true
    }
    
    # Try to start Docker Desktop
    try {
        # Method 1: Try to start Docker Desktop via Start-Process
        $dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $dockerDesktopPath) {
            Write-Host "Starting Docker Desktop from: $dockerDesktopPath" -ForegroundColor Yellow
            Start-Process -FilePath $dockerDesktopPath -WindowStyle Minimized
            Write-Host "Docker Desktop startup initiated. Please wait for it to fully load..." -ForegroundColor Green
            Write-Host "This may take 30-60 seconds depending on your system." -ForegroundColor Yellow
            
            # Wait and check if Docker becomes available
            $maxWaitTime = 60  # seconds
            $waitInterval = 5  # seconds
            $elapsedTime = 0
            
            Write-Host "`nWaiting for Docker to become available..." -ForegroundColor Cyan
            while ($elapsedTime -lt $maxWaitTime) {
                Start-Sleep -Seconds $waitInterval
                $elapsedTime += $waitInterval
                
                # Test Docker availability
                $dockerStatus = Test-DockerDesktopStatus
                if ($dockerStatus.Running) {
                    Write-Host "Docker is now available! $($dockerStatus.Message)" -ForegroundColor Green
                    return $true
                }
                
                Write-Host "Still waiting... ($elapsedTime/$maxWaitTime seconds)" -ForegroundColor Yellow
            }
            
            Write-Host "Docker did not become available within $maxWaitTime seconds." -ForegroundColor Red
            Write-Host "Please start Docker Desktop manually and try again." -ForegroundColor Yellow
            return $false
            
        } else {
            # Method 2: Try to find Docker Desktop in other common locations
            $possiblePaths = @(
                "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe",
                "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
                "${env:LOCALAPPDATA}\Docker\Docker Desktop.exe"
            )
            
            $foundPath = $null
            foreach ($path in $possiblePaths) {
                if (Test-Path $path) {
                    $foundPath = $path
                    break
                }
            }
            
            if ($foundPath) {
                Write-Host "Starting Docker Desktop from: $foundPath" -ForegroundColor Yellow
                Start-Process -FilePath $foundPath -WindowStyle Minimized
                Write-Host "Docker Desktop startup initiated. Please wait for it to fully load..." -ForegroundColor Green
                return $true
            } else {
                Write-Host "Docker Desktop not found in common locations." -ForegroundColor Red
                Write-Host "Please ensure Docker Desktop is installed and try starting it manually." -ForegroundColor Yellow
                return $false
            }
        }
        
    } catch {
        Write-Host "Error starting Docker Desktop: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Please start Docker Desktop manually and try again." -ForegroundColor Yellow
        return $false
    }
}

# Redis Docker helper functions
function Stop-RedisDocker {
    Write-Host "Attempting to stop Redis Docker container..." -ForegroundColor Cyan
    try {
        $container = docker ps -a --filter "name=redis" --format "{{.ID}}"
        if ($container) {
            docker stop redis | Out-Null
            Write-Host "Redis Docker container stopped." -ForegroundColor Green
            return $true
        } else {
            Write-Host "No Redis Docker container found to stop." -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "Error stopping Redis Docker container: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Start-RedisDocker {
    Write-Host "Attempting to start Redis Docker container..." -ForegroundColor Cyan
    try {
        $container = docker ps -a --filter "name=redis" --format "{{.ID}}"
        if ($container) {
            docker start redis | Out-Null
            Write-Host "Redis Docker container started." -ForegroundColor Green
            return $true
        } else {
            Write-Host "No Redis Docker container found to start. Please create one with: docker run --name redis -d -p 6379:6379 redis" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "Error starting Redis Docker container: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Start-RQWorker {
    Write-Host "Starting RQ worker..." -ForegroundColor Cyan
    try {
        # Check if Redis is available
        $redisTest = docker ps --filter "name=redis" --format "{{.Status}}" 2>$null
        if (-not $redisTest) {
            Write-Host "Redis container not running. Starting Redis first..." -ForegroundColor Yellow
            if (-not (Start-RedisDocker)) {
                Write-Host "Failed to start Redis. RQ worker cannot start." -ForegroundColor Red
                return $false
            }
            Start-Sleep -Seconds 3
        }
        
        # Start RQ worker using the Windows-compatible script
        $rqWorkerScript = Join-Path $PSScriptRoot "src\rq_worker_windows.py"
        if (Test-Path $rqWorkerScript) {
            $script:RQWorkerProcess = Start-Process -FilePath $venvPython -ArgumentList $rqWorkerScript, "worker", "casestrainer" -NoNewWindow -PassThru
            Write-Host "RQ worker started (PID: $($script:RQWorkerProcess.Id))" -ForegroundColor Green
            return $true
        } else {
            Write-Host "RQ worker script not found at: $rqWorkerScript" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "Failed to start RQ worker: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Auto-restart and monitoring functions (must be defined before other functions)
function Initialize-CrashLogging {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $script:CrashLogFile = Join-Path $script:LogDirectory "crash_log_$timestamp.log"
    
    # Create log directory if it doesn't exist
    if (!(Test-Path $script:LogDirectory)) {
        New-Item -ItemType Directory -Path $script:LogDirectory -Force | Out-Null
    }
    
    Write-Host "Crash logging enabled: $($script:CrashLogFile)" -ForegroundColor Cyan
}

function Write-CrashLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [System.Exception]$Exception = $null
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    if ($Exception) {
        $logEntry += "`nException: $($Exception.Message)"
        $logEntry += "`nStackTrace: $($Exception.StackTrace)"
    }
    
    # Write to crash log file
    if ($script:CrashLogFile) {
        Add-Content -Path $script:CrashLogFile -Value $logEntry -ErrorAction SilentlyContinue
    }
    
    # Also write to console with colors
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARN"  { Write-Host $logEntry -ForegroundColor Yellow }
        "INFO"  { Write-Host $logEntry -ForegroundColor White }
        "DEBUG" { Write-Host $logEntry -ForegroundColor Gray }
        default { Write-Host $logEntry }
    }
}

function Stop-Monitoring {
    if ($script:MonitoringEnabled) {
        Write-CrashLog "Stopping service monitoring" -Level "INFO"
        $script:MonitoringEnabled = $false
        
        # Stop any monitoring jobs
        Get-Job -Name "*monitor*" -ErrorAction SilentlyContinue | Stop-Job -ErrorAction SilentlyContinue
        Get-Job -Name "*monitor*" -ErrorAction SilentlyContinue | Remove-Job -ErrorAction SilentlyContinue
    }
}

function Start-AutoRestartServices {
    param(
        [string]$Environment = "Development"
    )
    
    Write-CrashLog "Starting auto-restart recovery for $Environment mode" -Level "INFO"
    Write-Host "`n=== Auto-Restart Recovery ===`n" -ForegroundColor Cyan
    
    $success = $false
    $restartSteps = @()
    
    try {
        # Step 1: Check and start Docker Desktop if needed
        Write-Host "Step 1: Checking Docker Desktop..." -ForegroundColor Yellow
        $dockerStatus = Test-DockerDesktopStatus
        if (-not $dockerStatus.Running) {
            Write-Host "Docker Desktop is not running. Attempting to start..." -ForegroundColor Yellow
            if (Start-DockerDesktop) {
                Write-Host "✅ Docker Desktop started successfully" -ForegroundColor Green
                $restartSteps += "Docker Desktop"
                Start-Sleep -Seconds 10  # Wait for Docker to fully initialize
            } else {
                Write-Host "❌ Failed to start Docker Desktop automatically" -ForegroundColor Red
                Write-CrashLog "Auto-restart failed: Could not start Docker Desktop" -Level "ERROR"
                return $false
            }
        } else {
            Write-Host "✅ Docker Desktop is already running" -ForegroundColor Green
        }
        
        # Step 2: Check and start Redis
        Write-Host "`nStep 2: Checking Redis..." -ForegroundColor Yellow
        if (Start-RedisDocker) {
            Write-Host "✅ Redis started successfully" -ForegroundColor Green
            $restartSteps += "Redis"
        } else {
            Write-Host "❌ Failed to start Redis" -ForegroundColor Red
            Write-CrashLog "Auto-restart failed: Could not start Redis" -Level "ERROR"
            return $false
        }
        
        # Step 3: Start RQ Worker
        Write-Host "`nStep 3: Starting RQ Worker..." -ForegroundColor Yellow
        if (Start-RQWorker) {
            Write-Host "✅ RQ Worker started successfully" -ForegroundColor Green
            $restartSteps += "RQ Worker"
        } else {
            Write-Host "⚠️  RQ Worker failed to start (continuing anyway)" -ForegroundColor Yellow
            Write-CrashLog "Auto-restart warning: RQ Worker failed to start" -Level "WARN"
        }
        
        # Step 4: Restart main application services
        Write-Host "`nStep 4: Restarting main services..." -ForegroundColor Yellow
        
        # Clean up existing services before restarting
        Cleanup-ServicesForRestart
        
        if ($Environment -eq "Development") {
            # Restart development services
            if (Start-DevelopmentMode) {
                Write-Host "✅ Development services restarted successfully" -ForegroundColor Green
                $restartSteps += "Development Services"
                $success = $true
            } else {
                Write-Host "❌ Failed to restart development services" -ForegroundColor Red
                Write-CrashLog "Auto-restart failed: Could not restart development services" -Level "ERROR"
            }
        } elseif ($Environment -eq "Production") {
            # Restart production services
            if (Start-ProductionMode) {
                Write-Host "✅ Production services restarted successfully" -ForegroundColor Green
                $restartSteps += "Production Services"
                $success = $true
            } else {
                Write-Host "❌ Failed to restart production services" -ForegroundColor Red
                Write-CrashLog "Auto-restart failed: Could not restart production services" -Level "ERROR"
            }
        }
        
        if ($success) {
            Write-Host "`n=== Auto-Restart Recovery Complete ===" -ForegroundColor Green
            Write-Host "Successfully restarted: $($restartSteps -join ', ')" -ForegroundColor Green
            Write-CrashLog "Auto-restart recovery completed successfully: $($restartSteps -join ', ')" -Level "INFO"
            
            # Update restart tracking
            $script:RestartCount++
            $script:LastRestartTime = Get-Date
            
            return $true
        } else {
            Write-Host "`n=== Auto-Restart Recovery Failed ===" -ForegroundColor Red
            Write-CrashLog "Auto-restart recovery failed" -Level "ERROR"
            return $false
        }
        
    } catch {
        Write-Host "`n❌ Auto-restart recovery error: $($_.Exception.Message)" -ForegroundColor Red
        Write-CrashLog "Auto-restart recovery error: $($_.Exception.Message)" -Level "ERROR" -Exception $_
        return $false
    }
}

function Test-ServiceHealth {
    param(
        [string]$Environment = "Development"
    )
    
    $healthStatus = @{
        Backend = $false
        Frontend = $false
        Nginx = $false
        Redis = $false
        RQWorker = $false
        Overall = $false
    }
    
    try {
        # Test backend health
        if ($script:BackendProcess -and !$script:BackendProcess.HasExited) {
            # Retry logic for backend health check
            for ($i = 1; $i -le 3; $i++) {
                try {
                    $response = Invoke-RestMethod -Uri "http://127.0.0.1:$($config.BackendPort)/casestrainer/api/health" -TimeoutSec 5
                    if ($response.status -eq "healthy") {
                        $healthStatus.Backend = $true
                        break # Exit loop on success
                    }
                } catch {
                    # Ignore error and retry
                }
                if ($i -lt 3) { Start-Sleep -Seconds 5 }
            }
        }
        
        # Test frontend (development mode only)
        if ($Environment -eq "Development") {
            if ($script:FrontendProcess -and !$script:FrontendProcess.HasExited) {
                # Retry logic for frontend health check
                for ($i = 1; $i -le 3; $i++) {
                    try {
                        $response = Invoke-WebRequest -Uri "http://localhost:$($config.FrontendDevPort)" -TimeoutSec 5
                        if ($response.StatusCode -eq 200) {
                            $healthStatus.Frontend = $true
                            break # Exit loop on success
                        }
                    } catch {
                        # Ignore error and retry
                    }
                    if ($i -lt 3) { Start-Sleep -Seconds 5 }
                }
            }
        }
        
        # Test Nginx (production mode only)
        if ($Environment -eq "Production") {
            if ($script:NginxProcess -and !$script:NginxProcess.HasExited) {
                # Check if Nginx is listening on port 443
                try {
                    $listening = netstat -ano | findstr ":443" | findstr "LISTENING"
                    if ($listening) {
                        $healthStatus.Nginx = $true
                    } else {
                        $healthStatus.Nginx = $false
                    }
                } catch {
                    $healthStatus.Nginx = $false
                }
            }
        }
        
        # Test Redis
        try {
            $testConnection = python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping(); print('OK')" 2>&1
            $healthStatus.Redis = $LASTEXITCODE -eq 0
        } catch {
            $healthStatus.Redis = $false
        }
        
        # Test RQ Worker
        $rqWorkerProcesses = Get-Process python -ErrorAction SilentlyContinue | 
            Where-Object { $_.CommandLine -like '*rq worker*' }
        $healthStatus.RQWorker = $rqWorkerProcesses.Count -gt 0
        
        # Overall health (all critical services must be healthy)
        $criticalServices = @($healthStatus.Backend)
        if ($Environment -eq "Development") {
            $criticalServices += $healthStatus.Frontend
        } elseif ($Environment -eq "Production") {
            $criticalServices += $healthStatus.Nginx
        }
        
        $healthStatus.Overall = $criticalServices -notcontains $false
        
        return $healthStatus
        
    } catch {
        Write-CrashLog "Health check error: $($_.Exception.Message)" -Level "ERROR" -Exception $_
        return $healthStatus
    }
}

function Show-MonitoringStatus {
    Clear-Host
    Write-Host "`n=== Service Monitoring Status ===`n" -ForegroundColor Cyan
    
    Write-Host "Auto-Restart:" -NoNewline
    if ($script:AutoRestartEnabled) {
        Write-Host " ENABLED" -ForegroundColor Green
    } else {
        Write-Host " DISABLED" -ForegroundColor Red
    }
    
    Write-Host "Monitoring:" -NoNewline
    if ($script:MonitoringEnabled) {
        Write-Host " ACTIVE" -ForegroundColor Green
    } else {
        Write-Host " INACTIVE" -ForegroundColor Red
    }
    
    Write-Host "Restart Count: $($script:RestartCount) / $($script:MaxRestartAttempts)" -ForegroundColor Yellow
    
    if ($script:LastRestartTime) {
        Write-Host "Last Restart: $($script:LastRestartTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Yellow
    }
    
    # Show crash log info
    if ($script:CrashLogFile -and (Test-Path $script:CrashLogFile)) {
        $logSize = (Get-Item $script:CrashLogFile).Length
        $logSizeKB = [Math]::Round($logSize / 1KB, 2)
        Write-Host "`nCrash Log: $($script:CrashLogFile) ($logSizeKB KB)" -ForegroundColor Cyan
    }
    
    Write-Host "`nOptions:" -ForegroundColor Yellow
    Write-Host " 1. Enable Auto-Restart" -ForegroundColor Green
    Write-Host " 2. Disable Auto-Restart" -ForegroundColor Red
    Write-Host " 3. View Crash Log" -ForegroundColor Yellow
    Write-Host " 4. Clear Crash Log" -ForegroundColor Yellow
    Write-Host " 5. Test Service Health" -ForegroundColor Blue
    Write-Host " 6. Force Auto-Restart Recovery" -ForegroundColor Magenta
    Write-Host " 0. Back to Menu" -ForegroundColor Gray
    Write-Host ""
    
    $selection = Read-Host "Select an option (0-6)"
    
    switch ($selection) {
        '1' { 
            $script:AutoRestartEnabled = $true
            Write-Host "Auto-restart enabled!" -ForegroundColor Green
        }
        '2' { 
            $script:AutoRestartEnabled = $false
            Write-Host "Auto-restart disabled!" -ForegroundColor Yellow
        }
        '3' { 
            if ($script:CrashLogFile -and (Test-Path $script:CrashLogFile)) {
                Clear-Host
                Write-Host "`n=== Crash Log ===`n" -ForegroundColor Cyan
                Get-Content $script:CrashLogFile -Tail 50
                Write-Host "`nPress any key to return..." -NoNewline
                $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
            } else {
                Write-Host "No crash log file found" -ForegroundColor Yellow
            }
        }
        '4' { 
            if ($script:CrashLogFile -and (Test-Path $script:CrashLogFile)) {
                Clear-Content $script:CrashLogFile
                Write-Host "Crash log cleared!" -ForegroundColor Green
            } else {
                Write-Host "No crash log file to clear" -ForegroundColor Yellow
            }
        }
        '5' {
            Clear-Host
            Write-Host "`n=== Service Health Check ===`n" -ForegroundColor Cyan
            
            # Determine current environment
            $currentEnv = "Development"
            if ($script:NginxProcess -and !$script:NginxProcess.HasExited) {
                $currentEnv = "Production"
            }
            
            $health = Test-ServiceHealth -Environment $currentEnv
            
            Write-Host "Environment: $currentEnv" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Backend:" -NoNewline
            if ($health.Backend) { Write-Host " HEALTHY" -ForegroundColor Green } else { Write-Host " UNHEALTHY" -ForegroundColor Red }
            
            if ($currentEnv -eq "Development") {
                Write-Host "Frontend:" -NoNewline
                if ($health.Frontend) { Write-Host " HEALTHY" -ForegroundColor Green } else { Write-Host " UNHEALTHY" -ForegroundColor Red }
            } else {
                Write-Host "Nginx:" -NoNewline
                if ($health.Nginx) { Write-Host " HEALTHY" -ForegroundColor Green } else { Write-Host " UNHEALTHY" -ForegroundColor Red }
            }
            
            Write-Host "Redis:" -NoNewline
            if ($health.Redis) { Write-Host " HEALTHY" -ForegroundColor Green } else { Write-Host " UNHEALTHY" -ForegroundColor Red }
            
            Write-Host "RQ Worker:" -NoNewline
            if ($health.RQWorker) { Write-Host " HEALTHY" -ForegroundColor Green } else { Write-Host " UNHEALTHY" -ForegroundColor Red }
            
            Write-Host ""
            Write-Host "Overall Status:" -NoNewline
            if ($health.Overall) { Write-Host " HEALTHY" -ForegroundColor Green } else { Write-Host " UNHEALTHY" -ForegroundColor Red }
            
            Write-Host "`nPress any key to return..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
        }
        '6' {
            Clear-Host
            Write-Host "`n=== Force Auto-Restart Recovery ===`n" -ForegroundColor Cyan
            Write-Host "This will attempt to restart all services including Docker and Redis." -ForegroundColor Yellow
            Write-Host ""
            $confirm = Read-Host "Are you sure you want to force auto-restart recovery? (y/N)"
            if ($confirm -eq 'y') {
                # Determine current environment
                $currentEnv = "Development"
                if ($script:NginxProcess -and !$script:NginxProcess.HasExited) {
                    $currentEnv = "Production"
                }
                
                if (Start-AutoRestartServices -Environment $currentEnv) {
                    Write-Host "`n✅ Auto-restart recovery completed successfully!" -ForegroundColor Green
                } else {
                    Write-Host "`n❌ Auto-restart recovery failed!" -ForegroundColor Red
                }
                Write-Host "`nPress any key to return..." -NoNewline
                $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
            }
        }
        '0' { return }
        default { 
            Write-Host "Invalid selection!" -ForegroundColor Red
        }
    }
    
    Write-Host "`nPress any key to return to the menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Show-Menu {
    param (
        [string]$Title = 'CaseStrainer Launcher',
        [string]$Message = 'Select an option:'
    )
    Clear-Host
    Write-Host "`n"
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " $Title" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if ($Message) {
        Write-Host " $Message" -ForegroundColor Yellow
        Write-Host ""
    }
    
    Write-Host " 1. Development Mode" -ForegroundColor Green
    Write-Host "    - Vue dev server with hot reload"
    Write-Host "    - Flask backend with debug mode"
    Write-Host "    - CORS enabled for local development"
    Write-Host ""
    
    Write-Host " 2. Production Mode" -ForegroundColor Green
    Write-Host "    - Built Vue.js frontend"
    Write-Host "    - Waitress WSGI server"
    Write-Host "    - Nginx reverse proxy with SSL"
    Write-Host ""
    
    Write-Host " 3. Check Server Status" -ForegroundColor Yellow
    Write-Host " 4. Stop All Services" -ForegroundColor Red
    Write-Host " 5. Restart Development Backend" -ForegroundColor Yellow
    Write-Host " 6. Restart Production Backend" -ForegroundColor Yellow
    Write-Host " 7. View Logs" -ForegroundColor Yellow
    Write-Host " 8. View LangSearch Cache" -ForegroundColor Yellow
    Write-Host " 9. Redis/RQ Management (Background Tasks)" -ForegroundColor Yellow
    Write-Host "10. Help" -ForegroundColor Cyan
    Write-Host "11. View Citation Cache Info" -ForegroundColor Yellow
    Write-Host "12. Clear Unverified Citation Cache" -ForegroundColor Yellow
    Write-Host "13. Clear All Citation Cache" -ForegroundColor Red
    Write-Host "14. View Non-CourtListener Verified Citation Cache" -ForegroundColor Yellow
    Write-Host "15. Service Monitoring Status" -ForegroundColor Blue
    Write-Host " 0. Exit" -ForegroundColor Gray
    Write-Host ""
    
    $selection = Read-Host "Select an option (0-15)"
    return $selection
}

function Show-Help {
    Clear-Host
    Write-Host "`nCaseStrainer Launcher - Help`n" -ForegroundColor Cyan
    Write-Host "Usage:"
    Write-Host "  .\launcher.ps1 [Options]`n"
    Write-Host "Options:"
    Write-Host "  -Environment <Development|Production|Menu>"
    Write-Host "      Select environment directly (default: Menu)`n"
    Write-Host "  -NoMenu"
    Write-Host "      Run without showing the interactive menu`n"
    Write-Host "  -SkipBuild"
    Write-Host "      Skip frontend build in production mode`n"
    Write-Host "  -VerboseLogging"
    Write-Host "      Enable detailed logging output`n"
    Write-Host "  -Help"
    Write-Host "      Show this help message`n"
    Write-Host "Examples:"
    Write-Host "  .\launcher.ps1                           # Show interactive menu"
    Write-Host "  .\launcher.ps1 -Environment Development  # Start in Development mode"
    Write-Host "  .\launcher.ps1 -Environment Production   # Start in Production mode"
    Write-Host "  .\launcher.ps1 -NoMenu -Env Production -SkipBuild   # Quick production start`n"
    Write-Host "Press any key to return to the menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Initialize-LogDirectory {
    if (!(Test-Path $script:LogDirectory)) {
        New-Item -ItemType Directory -Path $script:LogDirectory -Force | Out-Null
        Write-Host "Created log directory: $script:LogDirectory" -ForegroundColor Green
    }
}

function Show-ServerStatus {
    Clear-Host
    Write-Host "`n=== Server Status ===`n" -ForegroundColor Cyan
    
    # Check backend (Waitress or Flask dev)
    $backendProcesses = Get-Process python -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*waitress-serve*' -or $_.CommandLine -like '*app_final_vue*' }
    
    Write-Host "Backend:" -NoNewline
    if ($backendProcesses) {
        Write-Host " RUNNING (PID: $($backendProcesses[0].Id))" -ForegroundColor Green
        
        # Test backend health
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:$($config.BackendPort)/casestrainer/api/health" -TimeoutSec 5
            Write-Host "  Status: $($response.status)" -ForegroundColor Green
            Write-Host "  Environment: $($response.environment)" -ForegroundColor Gray
        } catch {
            Write-Host "  API not responding" -ForegroundColor Yellow
        }
    } else {
        Write-Host " STOPPED" -ForegroundColor Red
    }
    
    # Check frontend (Vue dev server)
    $frontendProcesses = Get-Process node -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*vite*' -or $_.CommandLine -like '*vue-cli-service*' }
    
    Write-Host "Frontend Dev:" -NoNewline
    if ($frontendProcesses) {
        Write-Host " RUNNING (PID: $($frontendProcesses[0].Id))" -ForegroundColor Green
    } else {
        Write-Host " STOPPED" -ForegroundColor Red
    }
    
    # Check Nginx
    $nginxProcesses = Get-Process nginx -ErrorAction SilentlyContinue
    Write-Host "Nginx:" -NoNewline
    if ($nginxProcesses) {
        Write-Host "     RUNNING (PID: $($nginxProcesses[0].Id))" -ForegroundColor Green
    } else {
        Write-Host "     STOPPED" -ForegroundColor Red
    }
    
    # Check Redis
    Show-RedisDockerStatus
    
    # Check RQ Worker
    $rqWorkerProcesses = Get-Process python -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*rq worker*' }
    
    Write-Host "RQ Worker:" -NoNewline
    if ($rqWorkerProcesses) {
        Write-Host "   RUNNING (PID: $($rqWorkerProcesses[0].Id))" -ForegroundColor Green
    } else {
        Write-Host "   STOPPED" -ForegroundColor Red
    }
    
    Write-Host "`nAccess URLs:" -ForegroundColor Cyan
    if ($nginxProcesses) {
        Write-Host "  Production: https://localhost:443/casestrainer/" -ForegroundColor Green
        Write-Host "  External:   https://wolf.law.uw.edu/casestrainer/" -ForegroundColor Green
    }
    if ($frontendProcesses) {
        Write-Host "  Development: http://localhost:5173/" -ForegroundColor Green
    }
    if ($backendProcesses) {
        Write-Host "  API Direct: http://localhost:5000/casestrainer/api/health" -ForegroundColor Green
    }
    
    Write-Host "`nPress any key to return to the menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Stop-AllServices {
    Clear-Host
    Write-Host "`n=== Stopping All Services ===`n" -ForegroundColor Red
    
    # Stop nginx
    $nginxProcesses = Get-Process nginx -ErrorAction SilentlyContinue
    if ($nginxProcesses) {
        Write-Host "Stopping Nginx..." -NoNewline
        Stop-Process -Name nginx -Force -ErrorAction SilentlyContinue
        Write-Host " DONE" -ForegroundColor Green
    } else {
        Write-Host "Nginx is not running" -ForegroundColor Gray
    }
    
    # Stop frontend (Node.js/Vite)
    $frontendProcesses = Get-Process node -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*vite*' -or $_.CommandLine -like '*vue-cli-service*' }
    
    if ($frontendProcesses) {
        Write-Host "Stopping Frontend..." -NoNewline
        $frontendProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host " DONE" -ForegroundColor Green
    } else {
        Write-Host "Frontend is not running" -ForegroundColor Gray
    }
    
    # Stop backend (Python/Waitress)
    $backendProcesses = Get-Process python -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*waitress-serve*' -or $_.CommandLine -like '*app_final_vue*' }
    
    if ($backendProcesses) {
        Write-Host "Stopping Backend..." -NoNewline
        $backendProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host " DONE" -ForegroundColor Green
    } else {
        Write-Host "Backend is not running" -ForegroundColor Gray
    }
    
    # Stop RQ worker
    $rqWorkerProcesses = Get-Process python -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*rq worker*' }
    
    if ($rqWorkerProcesses) {
        Write-Host "Stopping RQ Worker..." -NoNewline
        $rqWorkerProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host " DONE" -ForegroundColor Green
    } else {
        Write-Host "RQ Worker is not running" -ForegroundColor Gray
    }
    
    Stop-RedisDocker
    
    Write-Host "`nAll services have been stopped."
    Write-Host "Press any key to return to the menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Show-Logs {
    Clear-Host
    Write-Host "`n=== View Logs ===`n" -ForegroundColor Cyan
    Write-Host "Available log files:`n"
    
    $logFiles = Get-ChildItem -Path $script:LogDirectory -Filter "*.log" -ErrorAction SilentlyContinue
    
    if ($logFiles) {
        for ($i = 0; $i -lt $logFiles.Count; $i++) {
            $file = $logFiles[$i]
            Write-Host " $($i + 1). $($file.Name) ($('{0:yyyy-MM-dd HH:mm:ss}' -f $file.LastWriteTime))"
        }
        Write-Host ""
        Write-Host " 0. Back to Menu"
        Write-Host ""
        
        $selection = Read-Host "Select log file (0-$($logFiles.Count))"
        
        if ($selection -gt 0 -and $selection -le $logFiles.Count) {
            $selectedFile = $logFiles[$selection - 1]
            Clear-Host
            Write-Host "`n=== $($selectedFile.Name) ===`n" -ForegroundColor Cyan
            Write-Host "Press Ctrl+C to stop viewing logs`n" -ForegroundColor Yellow
            Get-Content $selectedFile.FullName -Tail 50 -Wait
        }
    } else {
        Write-Host "No log files found in $script:LogDirectory" -ForegroundColor Yellow
        Write-Host "Press any key to return to the menu..." -NoNewline
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    }
}

function Show-LangSearchCache {
    Clear-Host
    Write-Host "`n=== LangSearch Cache Viewer ===`n" -ForegroundColor Cyan
    
    $cachePath = "langsearch_cache.db"
    if (-not (Test-Path $cachePath)) {
        Write-Host "LangSearch cache file not found at: $cachePath" -ForegroundColor Red
        Write-Host "`nPress any key to return to the menu..." -NoNewline
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
        return
    }
    
    try {
        # Create a temporary Python script to read the shelve database
        $tempScript = @"
import shelve
import json
from datetime import datetime
import csv
import sys
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def format_timestamp(ts):
    try:
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(ts)

def get_cache_entries():
    with shelve.open('langsearch_cache.db') as db:
        entries = []
        for key in db:
            value = db[key]
            if isinstance(value, dict):
                # Add timestamp if not present
                if 'timestamp' not in value:
                    value['timestamp'] = None
                entries.append({
                    'citation': key,
                    'timestamp': format_timestamp(value.get('timestamp')),
                    'verified': value.get('verified', False),
                    'summary': value.get('summary', ''),
                    'links': value.get('links', []),
                    'raw_timestamp': value.get('timestamp')
                })
        return entries

def export_to_excel(entries, output_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "LangSearch Cache"
    
    # Define styles
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell_alignment = Alignment(vertical="top", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Headers
    headers = ['Citation', 'Timestamp', 'Verified', 'Summary', 'Links']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # Data
    for row, entry in enumerate(entries, 2):
        ws.cell(row=row, column=1, value=entry['citation']).border = thin_border
        ws.cell(row=row, column=2, value=entry['timestamp']).border = thin_border
        ws.cell(row=row, column=3, value=entry['verified']).border = thin_border
        ws.cell(row=row, column=4, value=entry['summary']).border = thin_border
        ws.cell(row=row, column=5, value='; '.join(entry['links']) if entry['links'] else '').border = thin_border
        
        # Set alignment for all cells in the row
        for col in range(1, 6):
            ws.cell(row=row, column=col).alignment = cell_alignment
    
    # Auto-adjust column widths
    for col in range(1, 6):
        max_length = 0
        column = get_column_letter(col)
        for cell in ws[column]:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = min(adjusted_width, 100)  # Cap at 100
    
    # Add statistics sheet
    stats_sheet = wb.create_sheet("Statistics")
    stats_sheet['A1'] = "Cache Statistics"
    stats_sheet['A1'].font = Font(bold=True, size=14)
    
    total_entries = len(entries)
    verified_entries = sum(1 for e in entries if e['verified'])
    unverified_entries = total_entries - verified_entries
    
    stats = [
        ("Total Entries", total_entries),
        ("Verified Entries", verified_entries),
        ("Unverified Entries", unverified_entries),
        ("Verification Rate", f"{(verified_entries/total_entries*100):.1f}%" if total_entries > 0 else "N/A")
    ]
    
    # Add timestamp statistics if available
    timestamps = [e['raw_timestamp'] for e in entries if e['raw_timestamp']]
    if timestamps:
        oldest = min(timestamps)
        newest = max(timestamps)
        stats.extend([
            ("Oldest Entry", format_timestamp(oldest)),
            ("Newest Entry", format_timestamp(newest))
        ])
    
    for row, (label, value) in enumerate(stats, 3):
        stats_sheet[f'A{row}'] = label
        stats_sheet[f'B{row}'] = value
        stats_sheet[f'A{row}'].font = Font(bold=True)
    
    # Save the workbook
    wb.save(output_path)
    return True

if __name__ == '__main__':
    entries = get_cache_entries()
    if len(sys.argv) > 1 and sys.argv[1] == '--export':
        format = sys.argv[2] if len(sys.argv) > 2 else 'json'
        output_path = sys.argv[3] if len(sys.argv) > 3 else None
        
        if format == 'excel' and output_path:
            try:
                export_to_excel(entries, output_path)
                print(json.dumps({"status": "success", "path": output_path}))
            except Exception as e:
                print(json.dumps({"status": "error", "error": str(e)}))
        elif format == 'csv':
            # Write CSV
            writer = csv.writer(sys.stdout)
            writer.writerow(['Citation', 'Timestamp', 'Verified', 'Summary', 'Links'])
            for entry in entries:
                writer.writerow([
                    entry['citation'],
                    entry['timestamp'],
                    entry['verified'],
                    entry['summary'],
                    '; '.join(entry['links']) if entry['links'] else ''
                ])
        else:
            # Write JSON
            print(json.dumps(entries, indent=2))
    else:
        # Just print JSON for display
        print(json.dumps(entries, indent=2))
"@
        
        $tempScriptPath = "temp_cache_viewer.py"
        $tempScript | Out-File -FilePath $tempScriptPath -Encoding utf8
        
        Write-Host "Reading LangSearch cache...`n" -ForegroundColor Yellow
        
        # Run the Python script and capture output
        $cacheData = python $tempScriptPath | ConvertFrom-Json
        
        # Clean up temp script
        Remove-Item $tempScriptPath -Force
        
        if ($cacheData.Count -eq 0) {
            Write-Host "Cache is empty" -ForegroundColor Yellow
        } else {
            Write-Host "Found $($cacheData.Count) entries in cache:`n" -ForegroundColor Green
            
            # Display cache entries in a table format
            $cacheData | ForEach-Object {
                Write-Host "Citation: $($_.citation)" -ForegroundColor Cyan
                Write-Host "  Timestamp: $($_.timestamp)"
                Write-Host "  Verified: $($_.verified)"
                if ($_.summary) {
                    Write-Host "  Summary: $($_.summary.Substring(0, [Math]::Min(100, $_.summary.Length)))..."
                }
                if ($_.links) {
                    Write-Host "  Links: $($_.links[0..1] -join ', ')..."
                }
                Write-Host ""
            }
            
            Write-Host "Cache Statistics:" -ForegroundColor Yellow
            Write-Host "  Total Entries: $($cacheData.Count)"
            Write-Host "  Verified Entries: $($cacheData | Where-Object { $_.verified } | Measure-Object | Select-Object -ExpandProperty Count)"
            Write-Host "  Unverified Entries: $($cacheData | Where-Object { -not $_.verified } | Measure-Object | Select-Object -ExpandProperty Count)"
            
            # Add timestamp statistics
            $timestamps = $cacheData | Where-Object { $_.raw_timestamp } | ForEach-Object { 
                [datetime]::ParseExact($_.timestamp, "yyyy-MM-dd HH:mm:ss", $null)
            }
            if ($timestamps) {
                $oldest = ($timestamps | Measure-Object -Minimum).Minimum
                $newest = ($timestamps | Measure-Object -Maximum).Maximum
                Write-Host "  Oldest Entry: $($oldest.ToString('yyyy-MM-dd HH:mm:ss'))"
                Write-Host "  Newest Entry: $($newest.ToString('yyyy-MM-dd HH:mm:ss'))"
            }
        }
    } catch {
        Write-Host "Error reading LangSearch cache: $_" -ForegroundColor Red
    }
    
    Write-Host "`nOptions:" -ForegroundColor Yellow
    Write-Host "  R - Refresh cache view"
    Write-Host "  C - Clear cache"
    Write-Host "  E - Export cache"
    Write-Host "  M - Return to menu"
    Write-Host ""
    
    $choice = Read-Host "Select an option (R/C/E/M)"
    
    switch ($choice.ToUpper()) {
        'R' { Show-LangSearchCache }
        'C' {
            $confirm = Read-Host "Are you sure you want to clear the LangSearch cache? (Y/N)"
            if ($confirm -eq 'Y') {
                try {
                    Remove-Item $cachePath -Force
                    Write-Host "Cache cleared successfully" -ForegroundColor Green
                    Start-Sleep -Seconds 2
                    Show-LangSearchCache
                } catch {
                    Write-Host "Error clearing cache: $_" -ForegroundColor Red
                    Start-Sleep -Seconds 2
                }
            }
        }
        'E' {
            Write-Host "`nExport Format:" -ForegroundColor Yellow
            Write-Host "  1. JSON (full data)"
            Write-Host "  2. CSV (spreadsheet format)"
            Write-Host "  3. Excel (formatted spreadsheet)"
            Write-Host ""
            $format = Read-Host "Select format (1-3)"
            
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $exportDir = "cache_exports"
            if (-not (Test-Path $exportDir)) {
                New-Item -ItemType Directory -Path $exportDir | Out-Null
            }
            
            switch ($format) {
                '1' {
                    $exportPath = Join-Path $exportDir "langsearch_cache_$timestamp.json"
                    try {
                        python $tempScriptPath --export json | Out-File -FilePath $exportPath -Encoding utf8
                        Write-Host "`nExported to: $exportPath" -ForegroundColor Green
                    } catch {
                        Write-Host "Error exporting JSON: $_" -ForegroundColor Red
                    }
                }
                '2' {
                    $exportPath = Join-Path $exportDir "langsearch_cache_$timestamp.csv"
                    try {
                        python $tempScriptPath --export csv | Out-File -FilePath $exportPath -Encoding utf8
                        Write-Host "`nExported to: $exportPath" -ForegroundColor Green
                    } catch {
                        Write-Host "Error exporting CSV: $_" -ForegroundColor Red
                    }
                }
                '3' {
                    $exportPath = Join-Path $exportDir "langsearch_cache_$timestamp.xlsx"
                    try {
                        $result = python $tempScriptPath --export excel $exportPath | ConvertFrom-Json
                        if ($result.status -eq "success") {
                            Write-Host "`nExported to: $exportPath" -ForegroundColor Green
                            # Try to open the Excel file
                            try {
                                Start-Process $exportPath
                            } catch {
                                Write-Host "Note: Excel file was created but could not be opened automatically" -ForegroundColor Yellow
                            }
                        } else {
                            Write-Host "Error exporting Excel: $($result.error)" -ForegroundColor Red
                        }
                    } catch {
                        Write-Host "Error exporting Excel: $_" -ForegroundColor Red
                    }
                }
                default {
                    Write-Host "Invalid format selection" -ForegroundColor Red
                }
            }
            Start-Sleep -Seconds 2
            Show-LangSearchCache
        }
        'M' { return }
        default { Show-LangSearchCache }
    }
}

function Show-CitationCacheInfo {
    Clear-Host
    Write-Host "`n=== Citation Cache Info ===`n" -ForegroundColor Cyan
    & $venvPython clear_cache.py --type info
    Write-Host "`nPress any key to return to the menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Clear-UnverifiedCitationCache {
    Clear-Host
    Write-Host "`n=== Clear Unverified Citation Cache ===`n" -ForegroundColor Yellow
    $confirm = Read-Host "Are you sure you want to clear all UNVERIFIED citation cache? (y/N)"
    if ($confirm -eq 'y') {
        & $venvPython clear_cache.py --type unverified --force
        Write-Host "`nUnverified citation cache cleared."
    } else {
        Write-Host "`nOperation cancelled."
    }
    Write-Host "`nPress any key to return to the menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Clear-AllCitationCache {
    Clear-Host
    Write-Host "`n=== Clear ALL Citation Cache ===`n" -ForegroundColor Red
    $confirm = Read-Host "Are you sure you want to clear ALL citation cache? (y/N)"
    if ($confirm -eq 'y') {
        & $venvPython clear_cache.py --type all --force
        Write-Host "`nAll citation cache cleared."
    } else {
        Write-Host "`nOperation cancelled."
    }
    Write-Host "`nPress any key to return to the menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Show-UnverifiedCitationCache {
    Clear-Host
    Write-Host "`n=== Non-CourtListener Verified Citation Cache ===`n" -ForegroundColor Cyan
    Write-Host "This cache contains citations verified by LangSearch, Database, Fuzzy Matching, and other sources" -ForegroundColor Gray
    Write-Host "but NOT by CourtListener (the primary verification source)." -ForegroundColor Gray
    
    $cachePath = "data/citations/unverified_citations_with_sources.json"
    if (!(Test-Path $cachePath)) {
        Write-Host "No non-CourtListener verified citation cache file found at $cachePath" -ForegroundColor Red
        Write-Host "`nPress any key to return to the menu..." -NoNewline
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
        return
    }
    
    try {
        $cacheData = Get-Content $cachePath | ConvertFrom-Json
        
        if ($cacheData.Count -eq 0) {
            Write-Host "Non-CourtListener verified citation cache is empty" -ForegroundColor Yellow
        } else {
            Write-Host "=== Cache Statistics ===" -ForegroundColor Green
            Write-Host "Total citations: $($cacheData.Count)" -ForegroundColor White
            
            # Group by verification source
            $sourceGroups = $cacheData | Group-Object -Property source | Sort-Object Count -Descending
            Write-Host "`nVerification Sources:" -ForegroundColor Green
            foreach ($group in $sourceGroups) {
                Write-Host "  $($group.Name): $($group.Count) citations" -ForegroundColor White
            }
            
            # Group by status
            $statusGroups = $cacheData | Group-Object -Property status | Sort-Object Count -Descending
            Write-Host "`nStatus Breakdown:" -ForegroundColor Green
            foreach ($group in $statusGroups) {
                Write-Host "  $($group.Name): $($group.Count) citations" -ForegroundColor White
            }
            
            # Show timestamp statistics
            $timestamps = $cacheData | Where-Object { $_.timestamp } | ForEach-Object { [datetime]::Parse($_.timestamp) }
            if ($timestamps.Count -gt 0) {
                $oldest = ($timestamps | Sort-Object | Select-Object -First 1).ToString("yyyy-MM-dd HH:mm:ss")
                $newest = ($timestamps | Sort-Object | Select-Object -Last 1).ToString("yyyy-MM-dd HH:mm:ss")
                Write-Host "`nTime Range:" -ForegroundColor Green
                Write-Host "  Oldest: $oldest" -ForegroundColor White
                Write-Host "  Newest: $newest" -ForegroundColor White
            }
            
            Write-Host "`n=== Recent Entries (Last 10) ===" -ForegroundColor Green
            $recentEntries = $cacheData | Sort-Object timestamp -Descending | Select-Object -First 10
            
            foreach ($entry in $recentEntries) {
                $timestamp = if ($entry.timestamp) { [datetime]::Parse($entry.timestamp).ToString("yyyy-MM-dd HH:mm:ss") } else { "Unknown" }
                $summary = if ($entry.summary) { $entry.summary.Substring(0, [Math]::Min(100, $entry.summary.Length)) } else { "No summary" }
                if ($entry.summary.Length -gt 100) { $summary += "..." }
                
                Write-Host "`n[$timestamp] $($entry.citation)" -ForegroundColor Cyan
                Write-Host "  Source: $($entry.source)" -ForegroundColor Yellow
                Write-Host "  Status: $($entry.status)" -ForegroundColor Yellow
                Write-Host "  Summary: $summary" -ForegroundColor Gray
            }
        }
        
        Write-Host "`n=== Export Options ===" -ForegroundColor Green
        Write-Host "1. Export as JSON (full data)"
        Write-Host "2. Export as CSV (spreadsheet format)"
        Write-Host "3. Export as Excel (formatted spreadsheet)"
        Write-Host "4. Return to menu"
        
        $choice = Read-Host "`nSelect an option (1-4)"
        
        switch ($choice) {
            "1" {
                $exportPath = "data/citations/non_courtlistener_verified_export_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
                $cacheData | ConvertTo-Json -Depth 10 | Out-File -FilePath $exportPath -Encoding UTF8
                Write-Host "`n✅ Exported to: $exportPath" -ForegroundColor Green
            }
            "2" {
                $exportPath = "data/citations/non_courtlistener_verified_export_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"
                $csvData = $cacheData | ForEach-Object {
                    [PSCustomObject]@{
                        Citation = $_.citation
                        Source = $_.source
                        Status = $_.status
                        Timestamp = $_.timestamp
                        Summary = $_.summary
                        CaseName = $_.case_name
                        Confidence = $_.confidence
                        URL = $_.url
                    }
                }
                $csvData | Export-Csv -Path $exportPath -NoTypeInformation -Encoding UTF8
                Write-Host "`n✅ Exported to: $exportPath" -ForegroundColor Green
            }
            "3" {
                $exportPath = "data/citations/non_courtlistener_verified_export_$(Get-Date -Format 'yyyyMMdd_HHmmss').xlsx"
                
                # Create Excel file with formatting
                $excel = New-Object -ComObject Excel.Application
                $excel.Visible = $false
                $workbook = $excel.Workbooks.Add()
                $worksheet = $workbook.Worksheets.Item(1)
                
                # Set headers
                $headers = @("Citation", "Source", "Status", "Timestamp", "Summary", "Case Name", "Confidence", "URL")
                for ($i = 0; $i -lt $headers.Count; $i++) {
                    $worksheet.Cells.Item(1, $i + 1) = $headers[$i]
                    $worksheet.Cells.Item(1, $i + 1).Font.Bold = $true
                    $worksheet.Cells.Item(1, $i + 1).Interior.ColorIndex = 15
                }
                
                # Add data
                $row = 2
                foreach ($entry in $cacheData) {
                    $worksheet.Cells.Item($row, 1) = $entry.citation
                    $worksheet.Cells.Item($row, 2) = $entry.source
                    $worksheet.Cells.Item($row, 3) = $entry.status
                    $worksheet.Cells.Item($row, 4) = $entry.timestamp
                    $worksheet.Cells.Item($row, 5) = $entry.summary
                    $worksheet.Cells.Item($row, 6) = $entry.case_name
                    $worksheet.Cells.Item($row, 7) = $entry.confidence
                    $worksheet.Cells.Item($row, 8) = $entry.url
                    $row++
                }
                
                # Auto-fit columns
                $worksheet.Columns.AutoFit() | Out-Null
                
                # Save and close
                $workbook.SaveAs($exportPath)
                $workbook.Close($true)
                $excel.Quit()
                [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
                
                Write-Host "`n✅ Exported to: $exportPath" -ForegroundColor Green
            }
            "4" { return }
            default {
                Write-Host "`n❌ Invalid option. Press any key to continue..." -ForegroundColor Red
                $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
            }
        }
        
    } catch {
        Write-Host "`n❌ Error reading cache file: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host "`nPress any key to return to the menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Start-DevelopmentMode {
    Write-Host "`n=== Starting Development Mode ===`n" -ForegroundColor Green
    
    # Set environment variables
    $env:FLASK_ENV = "development"
    $env:FLASK_APP = $config.BackendPath
    $env:PYTHONPATH = $PSScriptRoot
    $env:NODE_ENV = ""  # Clear NODE_ENV for Vite
    
    # Create data directory
    $dataDir = Split-Path $config.DatabasePath -Parent
    if (!(Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    }
    
    Write-Host "Starting Flask backend in development mode..." -ForegroundColor Cyan
    
    # Start Flask in development mode with CORS
    $flaskScript = @"
import os
import sys
from flask_cors import CORS

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.app_final_vue import create_app

app = create_app()

# Enable CORS for development
CORS(app, resources={
    r"/casestrainer/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=$($config.BackendPort), debug=True)
"@
    
    $tempScript = [System.IO.Path]::GetTempFileName() + ".py"
    $flaskScript | Out-File -FilePath $tempScript -Encoding UTF8
    
    try {
        $script:BackendProcess = Start-Process -FilePath $venvPython -ArgumentList $tempScript -NoNewWindow -PassThru
        Write-Host "Backend started (PID: $($script:BackendProcess.Id))" -ForegroundColor Green
        
        # Wait for backend to start
        Start-Sleep -Seconds 5
        
        # Test backend
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:$($config.BackendPort)/casestrainer/api/health" -TimeoutSec 10
            Write-Host "Backend health check: $($response.status)" -ForegroundColor Green
        } catch {
            Write-Host "Backend health check failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
        # Start RQ worker for task processing
        Write-Host "`nStarting RQ worker..." -ForegroundColor Cyan
        if (-not (Start-RQWorker)) {
            Write-Host "Warning: RQ worker failed to start. Tasks may not be processed." -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "Failed to start backend: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    # Start frontend development server
    Write-Host "`nStarting Vue.js development server..." -ForegroundColor Cyan
    
    $frontendPath = Join-Path $PSScriptRoot $config.FrontendPath
    $packageJsonPath = Join-Path $frontendPath 'package.json'
    if (!(Test-Path $frontendPath)) {
        Write-Host "Frontend directory not found at: $frontendPath" -ForegroundColor Red
        return $false
    }
    if (!(Test-Path $packageJsonPath)) {
        Write-Host "package.json not found in: $frontendPath" -ForegroundColor Red
        return $false
    }

    # Get the full path to npm - use a more robust method
    $npmPath = $null
    try {
        # Try to get npm from PATH
        $npmCommand = Get-Command npm -ErrorAction Stop
        $npmPath = $npmCommand.Source
        Write-Host "Found npm at: $npmPath" -ForegroundColor Gray
    } catch {
        # Try alternative locations
        $possibleNpmPaths = @(
            "${env:ProgramFiles}\nodejs\npm.cmd",
            "${env:ProgramFiles}\nodejs\npm.exe",
            "${env:ProgramFiles(x86)}\nodejs\npm.cmd",
            "${env:ProgramFiles(x86)}\nodejs\npm.exe",
            "${env:APPDATA}\npm\npm.cmd",
            "${env:APPDATA}\npm\npm.exe"
        )
        
        foreach ($path in $possibleNpmPaths) {
            if (Test-Path $path) {
                $npmPath = $path
                Write-Host "Found npm at: $npmPath" -ForegroundColor Gray
                break
            }
        }
    }
    
    if (!$npmPath) {
        Write-Host "npm not found in PATH or common locations" -ForegroundColor Red
        Write-Host "Please ensure Node.js and npm are installed and in your PATH" -ForegroundColor Yellow
        return $false
    }

    Push-Location $frontendPath
    try {
        # Install dependencies if needed
        if (!(Test-Path "node_modules")) {
            Write-Host "Installing npm dependencies in $frontendPath..." -ForegroundColor Yellow
            & $npmPath install
            if ($LASTEXITCODE -ne 0) {
                throw "npm install failed with exit code $LASTEXITCODE"
            }
        }
        
        # Start dev server using cmd.exe to handle npm properly
        Write-Host "Starting dev server in $frontendPath..." -ForegroundColor Yellow
        $script:FrontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm", "run", "dev" -WorkingDirectory $frontendPath -NoNewWindow -PassThru
        if (!$script:FrontendProcess) {
            throw "Failed to start frontend process"
        }
        Write-Host "Frontend started (PID: $($script:FrontendProcess.Id))" -ForegroundColor Green
        
    } catch {
        Write-Host "Failed to start frontend: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    } finally {
        Pop-Location
    }
    
    # Wait for frontend to start
    Start-Sleep -Seconds 5
    
    Write-Host "`n=== Development Mode Ready ===`n" -ForegroundColor Green
    Write-Host "Frontend (Vue): http://localhost:$($config.FrontendDevPort)/" -ForegroundColor Green
    Write-Host "Backend API:    http://localhost:$($config.BackendPort)/casestrainer/api/" -ForegroundColor Green
    Write-Host "`nPress Ctrl+C to stop all services" -ForegroundColor Yellow
    
    # Open browser
    try {
        Start-Process "http://localhost:$($config.FrontendDevPort)/"
    } catch {
        Write-Host "Could not open browser automatically" -ForegroundColor Yellow
    }
    
    return $true
}

function Start-ProductionMode {
    Write-Host "`n=== Starting Production Mode ===`n" -ForegroundColor Green
    
    Initialize-LogDirectory
    
    # Set environment variables
    $env:FLASK_ENV = "production"
    $env:FLASK_APP = $config.BackendPath
    $env:CORS_ORIGINS = $config.CORS_ORIGINS
    $env:DATABASE_PATH = $config.DatabasePath
    $env:LOG_LEVEL = "INFO"
    $env:PYTHONPATH = $PSScriptRoot
    
    # Create data directory
    $dataDir = Split-Path $config.DatabasePath -Parent
    if (!(Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    }
    
    # Build frontend unless skipped
    if (!$SkipBuild) {
        Write-Host "Building frontend for production..." -ForegroundColor Cyan
        
        Push-Location (Join-Path $PSScriptRoot $config.FrontendPath)
        try {
            # Clear NODE_ENV to avoid Vite issues
            $originalNodeEnv = $env:NODE_ENV
            $env:NODE_ENV = $null
            
            # Skip npm ci to avoid file lock issues, just run build directly
            # npm ci 2>&1 | Tee-Object -FilePath "../$script:LogDirectory/npm_install.log"
            # if ($LASTEXITCODE -ne 0) {
            #     throw "npm ci failed"
            # }
            
            npm run build 2>&1 | Tee-Object -FilePath "../$script:LogDirectory/npm_build.log"
            if ($LASTEXITCODE -ne 0) {
                throw "npm build failed"
            }
            
            Write-Host "Frontend build completed" -ForegroundColor Green
            
        } catch {
            Write-Host "Frontend build failed: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        } finally {
            $env:NODE_ENV = $originalNodeEnv
            Pop-Location
        }
    }
    
    # Start backend with Waitress
    Write-Host "`nStarting Flask backend with Waitress..." -ForegroundColor Cyan
    
    $backendLogPath = Join-Path $script:LogDirectory "backend.log"
    $backendErrorPath = Join-Path $script:LogDirectory "backend_error.log"
    
    try {
        $waitressArgs = @(
            "--host=0.0.0.0"
            "--port=$($config.BackendPort)"
            "--threads=4"
            "--call"
            "src.app_final_vue:create_app"
        )
        
        # Set PYTHONPATH to ensure src module can be found
        $env:PYTHONPATH = $PSScriptRoot
        
        $script:BackendProcess = Start-Process -FilePath $waitressExe -ArgumentList $waitressArgs -NoNewWindow -PassThru -RedirectStandardOutput $backendLogPath -RedirectStandardError $backendErrorPath
        
        Write-Host "Backend started (PID: $($script:BackendProcess.Id))" -ForegroundColor Green
        
        # Wait and test backend
        Start-Sleep -Seconds 8
        
        if ($script:BackendProcess.HasExited) {
            throw "Backend process exited immediately"
        }
        
        # Test backend health
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:$($config.BackendPort)/casestrainer/api/health" -TimeoutSec 10
            Write-Host "Backend health check: $($response.status)" -ForegroundColor Green
        } catch {
            Write-Host "Backend health check failed" -ForegroundColor Yellow
        }
        
        # Start RQ worker for task processing
        Write-Host "`nStarting RQ worker..." -ForegroundColor Cyan
        if (-not (Start-RQWorker)) {
            Write-Host "Warning: RQ worker failed to start. Tasks may not be processed." -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "Failed to start backend: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    # Generate and start Nginx using the WORKING configuration
    Write-Host "`nStarting Nginx..." -ForegroundColor Cyan
    
    $nginxDir = Join-Path $PSScriptRoot $config.NginxPath
    # $nginxExe = Join-Path $nginxDir $config.NginxExe  # Commented out due to PSScriptAnalyzer warning (unused variable)
    $frontendPath = (Join-Path $PSScriptRoot "$($config.FrontendPath)/dist") -replace '\\', '/'
    $sslCertPath = $config.SSL_CERT -replace '\\', '/'
    $sslKeyPath = $config.SSL_KEY -replace '\\', '/'
    
    # Create the WORKING nginx configuration (no mime.types dependency)
    $configLines = @(
        "worker_processes  1;",
        "",
        "events {",
        "    worker_connections  1024;",
        "}",
        "",
        "http {",
        "    # Basic MIME types - inline instead of include",
        "    types {",
        "        text/html                             html htm shtml;",
        "        text/css                              css;",
        "        application/javascript                js;",
        "        application/json                      json;",
        "        image/png                             png;",
        "        image/jpeg                            jpeg jpg;",
        "        image/gif                             gif;",
        "        image/svg+xml                         svg;",
        "        font/woff                             woff;",
        "        font/woff2                            woff2;",
        "    }",
        "    ",
        "    default_type  application/octet-stream;",
        "    sendfile        on;",
        "    keepalive_timeout  65;",
        "",
        "    access_log  logs/access.log;",
        "    error_log   logs/error.log warn;",
        "",
        "    server {",
        "        listen       $($config.ProductionPort) ssl;",
        "        server_name  wolf.law.uw.edu localhost;",
        "        ",
        "        ssl_certificate     `"$sslCertPath`";",
        "        ssl_certificate_key `"$sslKeyPath`";",
        "        ssl_protocols       TLSv1.2 TLSv1.3;",
        "        ssl_ciphers         HIGH:!aNULL:!MD5;",
        "        ",
        "        client_max_body_size 100M;",
        "",
        "        # API routes - proxy to backend",
        "        location /casestrainer/api/ {",
        "            proxy_pass http://127.0.0.1:$($config.BackendPort);",
        "            proxy_set_header Host `$host;",
        "            proxy_set_header X-Real-IP `$remote_addr;",
        "            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;",
        "            proxy_set_header X-Forwarded-Proto `$scheme;",
        "            proxy_http_version 1.1;",
        "            proxy_connect_timeout 30s;",
        "            proxy_send_timeout 30s;",
        "            proxy_read_timeout 30s;",
        "        }",
        "",
        "        # Vue.js assets",
        "        location /casestrainer/assets/ {",
        "            alias `"$frontendPath/assets/`";",
        "            expires 1y;",
        "            add_header Cache-Control `"public, immutable`";",
        "        }",
        "",
        "        # Frontend - Vue.js SPA (FIXED: no redirect loop)",
        "        location /casestrainer/ {",
        "            alias `"$frontendPath/`";",
        "            index index.html;",
        "            try_files `$uri `$uri/ /casestrainer/index.html;",
        "        }",
        "",
        "        # Root redirect",
        "        location = / {",
        "            return 301 /casestrainer/;",
        "        }",
        "",
        "        # Simple error page",
        "        error_page 500 502 503 504 /50x.html;",
        "        location = /50x.html {",
        "            return 200 `"Service temporarily unavailable`";",
        "            add_header Content-Type text/plain;",
        "        }",
        "    }",
        "}"
    )
    
    # Create config in nginx directory
    $configContent = $configLines -join "`n"
    $configFile = Join-Path $nginxDir "production.conf"
    [System.IO.File]::WriteAllText($configFile, $configContent, [System.Text.UTF8Encoding]::new($false))
    
    # Create logs directory in nginx folder
    $nginxLogsDir = Join-Path $nginxDir "logs"
    if (!(Test-Path $nginxLogsDir)) {
        New-Item -ItemType Directory -Path $nginxLogsDir -Force | Out-Null
    }
    
    # Test and start nginx from its directory
    $originalLocation = Get-Location
    try {
        Set-Location $nginxDir
        
        # Test configuration
        & ".\nginx.exe" -t -c "production.conf" 2>&1 | Write-Host -ForegroundColor Gray
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Nginx configuration test: PASSED" -ForegroundColor Green
        } else {
            Write-Host "Nginx configuration test: FAILED (continuing anyway)" -ForegroundColor Yellow
        }
        
        # Start nginx
        $script:NginxProcess = Start-Process -FilePath ".\nginx.exe" -ArgumentList "-c", "production.conf" -NoNewWindow -PassThru
        Write-Host "Nginx started (PID: $($script:NginxProcess.Id))" -ForegroundColor Green
        
    } catch {
        Write-Host "Failed to start Nginx: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    } finally {
        Set-Location $originalLocation
    }
    
    Write-Host "`n=== Production Mode Ready ===`n" -ForegroundColor Green
    Write-Host "Application: https://localhost:$($config.ProductionPort)/casestrainer/" -ForegroundColor Green
    Write-Host "External:    https://wolf.law.uw.edu/casestrainer/" -ForegroundColor Green
    Write-Host "API Direct:  http://localhost:$($config.BackendPort)/casestrainer/api/" -ForegroundColor Green
    Write-Host "`nPress Ctrl+C to stop all services" -ForegroundColor Yellow
    
    # Open browser with external URL instead of localhost
    try {
        Start-Process "https://wolf.law.uw.edu/casestrainer/"
    } catch {
        Write-Host "Could not open browser automatically" -ForegroundColor Yellow
    }
    
    return $true
}

function Stop-Services {
    Write-CrashLog "Stopping all services forcefully" -Level "INFO"
    Write-Host "`nStopping all services..." -ForegroundColor Yellow
    
    # Stop monitoring first to prevent immediate restarts
    Stop-Monitoring
    
    # More robust process killing - find by name and command line
    $processesToKill = @(
        @{ Name = "nginx"; Reason = "Nginx" },
        @{ Name = "node"; CommandLine = "*vite*"; Reason = "Frontend Dev Server" },
        @{ Name = "python"; CommandLine = "*waitress-serve*"; Reason = "Backend (Waitress)" },
        @{ Name = "python"; CommandLine = "*app_final_vue*"; Reason = "Backend (Flask Dev)" },
        @{ Name = "python"; CommandLine = "*rq worker*"; Reason = "RQ Worker" }
    )

    foreach ($procInfo in $processesToKill) {
        $foundProcesses = Get-Process -Name $procInfo.Name -ErrorAction SilentlyContinue
        if ($procInfo.CommandLine) {
            $foundProcesses = $foundProcesses | Where-Object { $_.CommandLine -like $procInfo.CommandLine }
        }
        
        if ($foundProcesses) {
            Write-Host "Stopping $($procInfo.Reason)..." -NoNewline
            $foundProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
            Write-CrashLog "$($procInfo.Reason) stopped" -Level "INFO"
            Write-Host " DONE" -ForegroundColor Green
        }
    }
    
    # Stop Redis Docker container
    Stop-RedisDocker
    
    Write-CrashLog "All services stopped" -Level "INFO"
    Write-Host "All services stopped" -ForegroundColor Green
}

function Cleanup-ServicesForRestart {
    Write-CrashLog "Cleaning up services for restart" -Level "INFO"
    Write-Host "Cleaning up services for restart..." -ForegroundColor Yellow
    
    # Stop all processes but don't stop Redis (we want to keep it running)
    if ($script:NginxProcess -and !$script:NginxProcess.HasExited) {
        Stop-Process -Id $script:NginxProcess.Id -Force -ErrorAction SilentlyContinue
        $script:NginxProcess = $null
    }
    
    if ($script:BackendProcess -and !$script:BackendProcess.HasExited) {
        Stop-Process -Id $script:BackendProcess.Id -Force -ErrorAction SilentlyContinue
        $script:BackendProcess = $null
    }
    
    if ($script:FrontendProcess -and !$script:FrontendProcess.HasExited) {
        Stop-Process -Id $script:FrontendProcess.Id -Force -ErrorAction SilentlyContinue
        $script:FrontendProcess = $null
    }
    
    if ($script:RQWorkerProcess -and !$script:RQWorkerProcess.HasExited) {
        Stop-Process -Id $script:RQWorkerProcess.Id -Force -ErrorAction SilentlyContinue
        $script:RQWorkerProcess = $null
    }
    
    # Wait a moment for processes to fully stop
    Start-Sleep -Seconds 3
    
    Write-CrashLog "Service cleanup completed" -Level "INFO"
    Write-Host "Service cleanup completed" -ForegroundColor Green
}

function Restart-DevelopmentBackend {
    Clear-Host
    Write-Host "`n=== Restarting Development Backend ===`n" -ForegroundColor Cyan
    
    # Check if backend is currently running
    $backendProcesses = Get-Process python -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*waitress-serve*' -or $_.CommandLine -like '*app_final_vue*' }
    
    if ($backendProcesses) {
        Write-Host "Backend is currently running (PID: $($backendProcesses[0].Id))" -ForegroundColor Yellow
        Write-Host "Stopping backend..." -ForegroundColor Yellow
        
        # Stop the backend process
        $backendProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        
        Write-Host "Backend stopped successfully" -ForegroundColor Green
    } else {
        Write-Host "Backend is not currently running" -ForegroundColor Gray
    }
    
    Write-Host "`nStarting development backend (Flask)..." -ForegroundColor Yellow
    
    # Start development backend with Flask
    $backendStarted = $false
    try {
        $script:BackendProcess = Start-Process -FilePath $venvPython -ArgumentList @(
            "app_final_vue.py"
        ) -WorkingDirectory "src" -PassThru -WindowStyle Hidden
        
        if ($script:BackendProcess) {
            Write-Host "Development backend started (PID: $($script:BackendProcess.Id))" -ForegroundColor Green
            $backendStarted = $true
        }
    } catch {
        Write-Host "Failed to start development backend: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    if ($backendStarted) {
        Write-Host "`nWaiting for backend to initialize..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # Test backend health
        $healthCheckAttempts = 0
        $maxHealthCheckAttempts = 6
        
        while ($healthCheckAttempts -lt $maxHealthCheckAttempts) {
            try {
                $response = Invoke-RestMethod -Uri "http://127.0.0.1:$($config.BackendPort)/casestrainer/api/health" -TimeoutSec 5
                if ($response.status -eq "healthy") {
                    Write-Host "✅ Development backend is healthy and responding!" -ForegroundColor Green
                    Write-Host "  Status: $($response.status)" -ForegroundColor Green
                    Write-Host "  Environment: $($response.environment)" -ForegroundColor Gray
                    break
                }
            } catch {
                $healthCheckAttempts++
                if ($healthCheckAttempts -lt $maxHealthCheckAttempts) {
                    Write-Host "Backend not ready yet, waiting... (attempt $healthCheckAttempts/$maxHealthCheckAttempts)" -ForegroundColor Yellow
                    Start-Sleep -Seconds 5
                } else {
                    Write-Host "⚠️  Backend started but health check failed after $maxHealthCheckAttempts attempts" -ForegroundColor Yellow
                    Write-Host "The backend may still be starting up. Check the logs if issues persist." -ForegroundColor Yellow
                }
            }
        }
        
        Write-CrashLog "Development backend restarted successfully" -Level "INFO"
    } else {
        Write-Host "❌ Failed to restart development backend" -ForegroundColor Red
        Write-CrashLog "Failed to restart development backend" -Level "ERROR"
    }
    
    Write-Host "`nPress any key to return to the menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Restart-ProductionBackend {
    Clear-Host
    Write-Host "`n=== Restarting Production Backend ===`n" -ForegroundColor Cyan
    
    # Check if backend is currently running
    $backendProcesses = Get-Process python -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like '*waitress-serve*' -or $_.CommandLine -like '*app_final_vue*' }
    
    if ($backendProcesses) {
        Write-Host "Backend is currently running (PID: $($backendProcesses[0].Id))" -ForegroundColor Yellow
        Write-Host "Stopping backend..." -ForegroundColor Yellow
        
        # Stop the backend process
        $backendProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        
        Write-Host "Backend stopped successfully" -ForegroundColor Green
    } else {
        Write-Host "Backend is not currently running" -ForegroundColor Gray
    }
    
    Write-Host "`nStarting production backend (Waitress)..." -ForegroundColor Yellow
    
    # Start production backend with Waitress
    $backendStarted = $false
    try {
        $script:BackendProcess = Start-Process -FilePath $waitressExe -ArgumentList @(
            "--host=127.0.0.1",
            "--port=$($config.BackendPort)",
            "--call",
            "app_final_vue:app"
        ) -WorkingDirectory "src" -PassThru -WindowStyle Hidden
        
        if ($script:BackendProcess) {
            Write-Host "Production backend started (PID: $($script:BackendProcess.Id))" -ForegroundColor Green
            $backendStarted = $true
        }
    } catch {
        Write-Host "Failed to start production backend: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    if ($backendStarted) {
        Write-Host "`nWaiting for backend to initialize..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # Test backend health
        $healthCheckAttempts = 0
        $maxHealthCheckAttempts = 6
        
        while ($healthCheckAttempts -lt $maxHealthCheckAttempts) {
            try {
                $response = Invoke-RestMethod -Uri "http://127.0.0.1:$($config.BackendPort)/casestrainer/api/health" -TimeoutSec 5
                if ($response.status -eq "healthy") {
                    Write-Host "✅ Production backend is healthy and responding!" -ForegroundColor Green
                    Write-Host "  Status: $($response.status)" -ForegroundColor Green
                    Write-Host "  Environment: $($response.environment)" -ForegroundColor Gray
                    break
                }
            } catch {
                $healthCheckAttempts++
                if ($healthCheckAttempts -lt $maxHealthCheckAttempts) {
                    Write-Host "Backend not ready yet, waiting... (attempt $healthCheckAttempts/$maxHealthCheckAttempts)" -ForegroundColor Yellow
                    Start-Sleep -Seconds 5
                } else {
                    Write-Host "⚠️  Backend started but health check failed after $maxHealthCheckAttempts attempts" -ForegroundColor Yellow
                    Write-Host "The backend may still be starting up. Check the logs if issues persist." -ForegroundColor Yellow
                }
            }
        }
        
        Write-CrashLog "Production backend restarted successfully" -Level "INFO"
    } else {
        Write-Host "❌ Failed to restart production backend" -ForegroundColor Red
        Write-CrashLog "Failed to restart production backend" -Level "ERROR"
    }
    
    Write-Host "`nPress any key to return to the menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

# Main execution
try {
    # Initialize crash logging
    Initialize-CrashLogging
    
    # Initialize log directory
    Initialize-LogDirectory
    
    # If environment is set via parameter and NoMenu is specified, skip the menu
    if ($Environment -ne "Menu" -and $NoMenu) {
        # Continue with the specified environment
    } else {
        # Show interactive menu
        do {
            $selection = Show-Menu
            
            switch ($selection) {
                '1' { $Environment = "Development"; break }
                '2' { $Environment = "Production"; break }
                '3' { Show-ServerStatus; continue }
                '4' { Stop-AllServices; continue }
                '5' { Restart-DevelopmentBackend; continue }
                '6' { Restart-ProductionBackend; continue }
                '7' { Show-Logs; continue }
                '8' { Show-LangSearchCache; continue }
                '9' { Show-RedisDockerStatus; continue }
                '10' { Show-Help; continue }
                '11' { Show-CitationCacheInfo; continue }
                '12' { Clear-UnverifiedCitationCache; continue }
                '13' { Clear-AllCitationCache; continue }
                '14' { Show-UnverifiedCitationCache; continue }
                '15' { Show-MonitoringStatus; continue }
                '0' { exit 0 }
                default { 
                    Write-Host "`nInvalid selection. Please try again." -ForegroundColor Red
                    Start-Sleep -Seconds 1
                    continue 
                }
            }
            
            # If we got here, user selected a valid environment
            break
        } while ($true)
    }
    
    # Start the selected environment
    $success = $false
    
    switch ($Environment) {
        "Development" {
            Write-CrashLog "Starting Development mode" -Level "INFO"
            $redisStarted = Start-RedisDocker
            if (-not $redisStarted) {
                Write-CrashLog "Redis is not available - continuing with limited functionality" -Level "WARN"
                Write-Host "`nWarning: Redis is not available. Some features may be limited." -ForegroundColor Yellow
                Write-Host "Citation processing and background tasks will not work." -ForegroundColor Yellow
                Write-Host "You can still use the basic citation validation features." -ForegroundColor Green
                Write-Host ""
                $continue = Read-Host "Continue without Redis? (y/N)"
                if ($continue -ne 'y') {
                    Write-CrashLog "User chose to exit due to Redis unavailability" -Level "INFO"
                    Write-Host "Exiting..." -ForegroundColor Yellow
                    exit 1
                }
            }
            $success = Start-DevelopmentMode
        }
        "Production" {
            Write-CrashLog "Starting Production mode" -Level "INFO"
            $redisStarted = Start-RedisDocker
            if (-not $redisStarted) {
                Write-CrashLog "Redis is not available - continuing with limited functionality" -Level "WARN"
                Write-Host "`nWarning: Redis is not available. Some features may be limited." -ForegroundColor Yellow
                Write-Host "Citation processing and background tasks will not work." -ForegroundColor Yellow
                Write-Host "You can still use the basic citation validation features." -ForegroundColor Green
                Write-Host ""
                $continue = Read-Host "Continue without Redis? (y/N)"
                if ($continue -ne 'y') {
                    Write-CrashLog "User chose to exit due to Redis unavailability" -Level "INFO"
                    Write-Host "Exiting..." -ForegroundColor Yellow
                    exit 1
                }
            }
            $success = Start-ProductionMode
        }
    }
    
    if ($success) {
        Write-CrashLog "$Environment mode started successfully" -Level "INFO"
        
        # Start basic monitoring if auto-restart is enabled
        if ($script:AutoRestartEnabled) {
            Write-CrashLog "Auto-restart monitoring enabled" -Level "INFO"
            Write-Host "`nAuto-restart monitoring is enabled. Services will be automatically restarted if they crash." -ForegroundColor Green
            
            # Add a grace period before starting health checks
            $initialGracePeriod = 30 # seconds
            Write-Host "Waiting $initialGracePeriod seconds for services to stabilize before starting health checks..." -ForegroundColor Cyan
            Start-Sleep -Seconds $initialGracePeriod
        }
        
        # Keep script running until Ctrl+C
        try {
            while ($true) {
                # Basic health check every 30 seconds
                if ($script:AutoRestartEnabled) {
                    # Use the intended environment instead of trying to detect it
                    $currentEnv = $Environment
                    
                    # Perform comprehensive health check
                    $health = Test-ServiceHealth -Environment $currentEnv
                    
                    # Check if any critical services are unhealthy
                    if (-not $health.Overall) {
                        # Add more detailed logging to identify the failed service
                        $failedServices = @()
                        if (-not $health.Backend) { $failedServices += "Backend" }
                        if ($currentEnv -eq "Development" -and -not $health.Frontend) { $failedServices += "Frontend" }
                        if ($currentEnv -eq "Production" -and -not $health.Nginx) { $failedServices += "Nginx" }

                        $failMsg = "Service health check failed for critical services: $($failedServices -join ', ')"
                        Write-CrashLog $failMsg -Level "WARN"
                        Write-Host "`n⚠️  $failMsg. Attempting auto-restart..." -ForegroundColor Yellow
                        Write-Host "Auto-restarting in $currentEnv mode..." -ForegroundColor Cyan
                        
                        if ($script:RestartCount -lt $script:MaxRestartAttempts) {
                            Write-CrashLog "Attempting auto-restart recovery (attempt $($script:RestartCount + 1)/$($script:MaxRestartAttempts))" -Level "WARN"
                            
                            if (Start-AutoRestartServices -Environment $currentEnv) {
                                Write-CrashLog "Auto-restart recovery successful" -Level "INFO"
                                Write-Host "✅ Auto-restart recovery completed successfully!" -ForegroundColor Green
                                
                                # Wait a bit longer after successful restart
                                Start-Sleep -Seconds 60
                            } else {
                                Write-CrashLog "Auto-restart recovery failed" -Level "ERROR"
                                Write-Host "❌ Auto-restart recovery failed!" -ForegroundColor Red
                                
                                if ($script:RestartCount -ge $script:MaxRestartAttempts) {
                                    Write-CrashLog "Maximum restart attempts reached. Manual intervention required." -Level "ERROR"
                                    Write-Host "`n🚨 Maximum restart attempts reached. Manual intervention required." -ForegroundColor Red
                                    Write-Host "Please check the crash log for details: $($script:CrashLogFile)" -ForegroundColor Yellow
                                    break
                                }
                            }
                        } else {
                            Write-CrashLog "Maximum restart attempts reached. Manual intervention required." -Level "ERROR"
                            Write-Host "`n🚨 Maximum restart attempts reached. Manual intervention required." -ForegroundColor Red
                            Write-Host "Please check the crash log for details: $($script:CrashLogFile)" -ForegroundColor Yellow
                            break
                        }
                    } else {
                        # Services are healthy - log periodic status
                        if ((Get-Date).Minute % 5 -eq 0 -and (Get-Date).Second -lt 30) {
                            Write-CrashLog "Service health check passed - all services healthy" -Level "DEBUG"
                        }
                    }
                }
                
                Start-Sleep -Seconds 30
            }
        } catch [System.Management.Automation.PipelineStoppedException] {
            Write-CrashLog "Received stop signal" -Level "INFO"
            Write-Host "`nReceived stop signal..." -ForegroundColor Yellow
        }
    } else {
        Write-CrashLog "Failed to start $Environment mode" -Level "ERROR"
        Write-Host "`nFailed to start $Environment mode" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-CrashLog "Fatal error in main execution" -Level "ERROR" -Exception $_
    Write-Host "`nError: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    Write-CrashLog "Shutting down services" -Level "INFO"
    Stop-Services
}
