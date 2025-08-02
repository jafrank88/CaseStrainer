# Enhanced CaseStrainer Docker Production Launcher v1.1 - Optimized for Speed
# Major performance improvements: parallel checks, faster Vue builds, smarter caching

[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateSet("Production", "Diagnostics", "Menu", "Cache", "Test", "Debug")]
    [string]$Mode = "Menu",
    [switch]$Help,
    [switch]$AutoRestart,
    [switch]$SkipVueBuild,
    [switch]$QuickStart,
    [switch]$ForceRebuild,
    [switch]$TestAPI,
    [switch]$TestFrontend,
    [switch]$ShowLogs,
    [switch]$ClearCache,
    [switch]$NoValidation,
    [switch]$VerboseLogging,
    [string]$TestCitation = "534 F.3d 1290",
    [int]$TimeoutMinutes = 10,
    [int]$MenuOption = $null
)

# Input validation
if (-not $PSScriptRoot) {
    throw "Script must be run from a file, not from command line"
}

# Global variables
$script:AutoRestartEnabled = $AutoRestart.IsPresent
$script:RestartCount = 0
$script:MaxRestartAttempts = 3
$script:CrashLogFile = Join-Path $PSScriptRoot "logs\crash.log"
$script:MonitoringJob = $null

# ForceRebuild is now a parameter of Start-DockerProduction function

# Performance optimization: Cache expensive checks
$script:CachedChecks = @{
    DockerAvailable = $null
    VueBuildNeeded = $null
    NpmInstallNeeded = $null
    NpmPath = $null
    LastCheckTime = $null
}

# Show help
if ($Help) {
    Write-Host @"
Enhanced CaseStrainer Docker Production Launcher v1.2 - Help

Usage:
  .\dplaunch.ps1 [Options]

Modes:
  -Mode Production    Start Docker Production Mode
  -Mode Diagnostics   Run Advanced Production Diagnostics
  -Mode Cache         Manage Citation Caches
  -Mode Test          Run API and Frontend Tests
  -Mode Debug         Enable Debug Mode with extra logging
  -Mode Menu          Show interactive menu (default)

Deployment Options:
  -ForceRebuild       Force full Docker and Vue rebuild
  -SkipVueBuild       Skip Vue frontend build (fastest)
  -QuickStart         Skip most checks for maximum speed
  -NoValidation       Skip post-startup validation
  -TimeoutMinutes     Set timeout for operations (default: 10)

Testing & Debugging:
  -TestAPI            Test API endpoints after deployment
  -TestFrontend       Test frontend functionality
  -TestCitation       Citation to test (default: "534 F.3d 1290")
  -VerboseLogging     Enable detailed logging
  -ShowLogs           Show container logs after deployment

Cache & Maintenance:
  -ClearCache         Clear all caches before deployment
  -AutoRestart        Enable auto-restart monitoring

Examples:
  .\dplaunch.ps1                                    # Show menu
  .\dplaunch.ps1 -Mode Production -QuickStart       # Fastest possible startup
  .\dplaunch.ps1 -Mode Production -ForceRebuild     # Full rebuild
  .\dplaunch.ps1 -Mode Test -TestAPI                # Test API only
  .\dplaunch.ps1 -Mode Debug -VerboseLogging        # Debug with verbose logging
  .\dplaunch.ps1 -Mode Production -TestCitation "200 Wn.2d 72"  # Test specific citation
"@ -ForegroundColor Cyan
    exit 0
}

function Initialize-LogDirectory {
    [CmdletBinding()]
    param()

    $logDir = Join-Path $PSScriptRoot "logs"
    if (-not (Test-Path $logDir)) {
        try {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        }
        catch {
            Write-Warning "Could not create log directory: $($_.Exception.Message)"
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
    }
    catch {
        Write-Warning "Could not write to crash log: $($_.Exception.Message)"
    }
}

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

function Test-VueBuildNeeded {
    [CmdletBinding()]
    [OutputType([bool])]
    param([switch]$Force)

    # Use cached result if recent (within 30 seconds) and not forcing
    if (-not $Force -and $script:CachedChecks.LastCheckTime -and
        ((Get-Date) - $script:CachedChecks.LastCheckTime).TotalSeconds -lt 30 -and
        $null -ne $script:CachedChecks.VueBuildNeeded) {
        return $script:CachedChecks.VueBuildNeeded
    }

    $vueDir = Join-Path $PSScriptRoot "casestrainer-vue-new"
    $distDir = Join-Path $vueDir "dist"
    $indexFile = Join-Path $distDir "index.html"

    if (-not (Test-Path $distDir) -or -not (Test-Path $indexFile)) {
        $script:CachedChecks.VueBuildNeeded = $true
        return $true
    }

    $distTime = (Get-Item $distDir).LastWriteTime

    # Quick check: only check package.json and skip deep src scan for speed
    $packageJson = Join-Path $vueDir "package.json"
    if (Test-Path $packageJson) {
        $packageTime = (Get-Item $packageJson).LastWriteTime
        if ($packageTime -gt $distTime) {
            $script:CachedChecks.VueBuildNeeded = $true
            return $true
        }
    }

    # Only do expensive src scan if dist is very old (>1 hour)
    if (((Get-Date) - $distTime).TotalHours -gt 1) {
        $srcDir = Join-Path $vueDir "src"
        if (Test-Path $srcDir) {
            # Faster check: only look at most recently modified file
            $newestSrcFile = Get-ChildItem $srcDir -Recurse -File |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1
            if ($newestSrcFile -and $newestSrcFile.LastWriteTime -gt $distTime) {
                $script:CachedChecks.VueBuildNeeded = $true
                return $true
            }
        }
    }

    $script:CachedChecks.VueBuildNeeded = $false
    $script:CachedChecks.LastCheckTime = Get-Date
    return $false
}

function Test-NpmInstallNeeded {
    [CmdletBinding()]
    [OutputType([bool])]
    param()

    # Use cached result if recent
    if ($script:CachedChecks.LastCheckTime -and
        ((Get-Date) - $script:CachedChecks.LastCheckTime).TotalSeconds -lt 30 -and
        $null -ne $script:CachedChecks.NpmInstallNeeded) {
        return $script:CachedChecks.NpmInstallNeeded
    }

    $vueDir = Join-Path $PSScriptRoot "casestrainer-vue-new"
    $nodeModules = Join-Path $vueDir "node_modules"
    $packageJson = Join-Path $vueDir "package.json"

    if (-not (Test-Path $nodeModules)) {
        $script:CachedChecks.NpmInstallNeeded = $true
        return $true
    }

    if (Test-Path $packageJson) {
        $packageTime = (Get-Item $packageJson).LastWriteTime
        $modulesTime = (Get-Item $nodeModules).LastWriteTime
        if ($packageTime -gt $modulesTime) {
            $script:CachedChecks.NpmInstallNeeded = $true
            return $true
        }
    }

    $script:CachedChecks.NpmInstallNeeded = $false
    return $false
}

function Find-NpmExecutable {
    [CmdletBinding()]
    [OutputType([string])]
    param()

    # Cache npm path for performance
    if ($script:CachedChecks.NpmPath) {
        return $script:CachedChecks.NpmPath
    }

    # Try to find npm in PATH first (fastest)
    $npmCommand = Get-Command npm -ErrorAction SilentlyContinue
    if ($npmCommand) {
        $npmSource = $npmCommand.Source
        # If it's a .ps1 file, look for .cmd or .exe in the same directory
        if ($npmSource -like "*.ps1") {
            $npmDir = Split-Path $npmSource -Parent
            $npmCmd = Join-Path $npmDir "npm.cmd"
            if (Test-Path $npmCmd) {
                $script:CachedChecks.NpmPath = $npmCmd
                return $npmCmd
            }
        }
        $script:CachedChecks.NpmPath = $npmSource
        return $npmSource
    }

    # Quick check of common paths
    $commonPaths = @(
        "$env:APPDATA\npm\npm.cmd",
        "$env:ProgramFiles\nodejs\npm.cmd",
        "C:\Program Files\nodejs\npm.cmd"
    )

    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            $script:CachedChecks.NpmPath = $path
            return $path
        }
    }

    return $null
}

function Invoke-VueFrontendBuild {
    [CmdletBinding()]
    param([switch]$Quick)

    $vueDir = Join-Path $PSScriptRoot "casestrainer-vue-new"
    Push-Location $vueDir
    try {
        if (-not (Test-Path "package.json")) {
            throw "package.json not found in Vue directory"
        }

        # Skip Node/npm version check in quick mode
        if (-not $Quick) {
            Write-Host "Checking Node.js and npm..." -ForegroundColor Yellow
            $nodeVersion = node --version 2>$null
            $npmVersion = npm --version 2>$null
            if ($LASTEXITCODE -ne 0 -or -not $nodeVersion -or -not $npmVersion) {
                throw "Node.js or npm not found. Please install Node.js first."
            }
            Write-Host "OK Node.js $nodeVersion, npm $npmVersion" -ForegroundColor Green
        }

        $npmPath = Find-NpmExecutable
        if (-not $npmPath) {
            throw "Could not find npm executable"
        }

        if (Test-NpmInstallNeeded) {
            Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
            # Faster npm install with optimizations
            $installArgs = @("install", "--no-audit", "--no-fund", "--prefer-offline", "--no-optional")
            $installProcess = Start-Process -FilePath $npmPath -ArgumentList $installArgs -Wait -NoNewWindow -PassThru
            if ($installProcess.ExitCode -ne 0) {
                throw "npm install failed"
            }
        } else {
            Write-Host "OK node_modules up to date (skipping npm install)" -ForegroundColor Green
        }

        # Use the ForceRebuild parameter here
        if (Test-VueBuildNeeded -Force:$ForceRebuild) {
            Write-Host "Building Vue frontend..." -ForegroundColor Yellow
            # Use production build with optimizations
            $buildArgs = @("run", "build")
            if (-not $Quick) {
                $buildArgs += "--verbose"
            }
            $buildProcess = Start-Process -FilePath $npmPath -ArgumentList $buildArgs -Wait -NoNewWindow -PassThru
            if ($buildProcess.ExitCode -ne 0) {
                throw "npm build failed"
            }
        } else {
            Write-Host "OK Vue build up to date (skipping build)" -ForegroundColor Green
        }
    } finally {
        Pop-Location
    }
}

function Test-DockerAvailability {
    [CmdletBinding()]
    [OutputType([bool])]
    param([switch]$Force)

    # Use cached result if recent and not forcing
    if (-not $Force -and $script:CachedChecks.LastCheckTime -and
        ((Get-Date) - $script:CachedChecks.LastCheckTime).TotalSeconds -lt 60 -and
        $null -ne $script:CachedChecks.DockerAvailable) {
        return $script:CachedChecks.DockerAvailable
    }

    try {
        # Faster Docker check - just ping daemon
        $null = docker version --format "{{.Server.Version}}" 2>$null
        $result = $LASTEXITCODE -eq 0
        $script:CachedChecks.DockerAvailable = $result
        return $result
    }
    catch {
        Write-CrashLog "Docker availability check failed" -Level "ERROR" -Exception $_
        $script:CachedChecks.DockerAvailable = $false
        return $false
    }
}

function Test-CodeChanges {
    [CmdletBinding()]
    [OutputType([bool])]
    param()

    # Only check critical files for faster startup
    $keyFiles = @(
        "src\unified_citation_processor.py",
        "src\case_name_extraction_core.py",
        "docker-compose.prod.yml",
        "Dockerfile"
    )

    $cutoffTime = (Get-Date).AddHours(-1)  # Increased to 1 hour for fewer false positives

    foreach ($file in $keyFiles) {
        $filePath = Join-Path $PSScriptRoot $file
        if (Test-Path $filePath) {
            $fileInfo = Get-Item $filePath
            if ($fileInfo.LastWriteTime -gt $cutoffTime) {
                return $true
            }
        }
    }
    return $false
}

function Wait-ForServices {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [int]$TimeoutMinutes = 5
    )

    Write-Host "`nWaiting for services to initialize..." -ForegroundColor Yellow
    $timeout = (Get-Date).AddMinutes($TimeoutMinutes)
    $attempt = 0

    while ((Get-Date) -lt $timeout) {
        $attempt++
        Start-Sleep -Seconds 10

        try {
            # Enhanced health checks
            $allHealthy = $true
            
            # Backend API health check
            $backendHealthy = Test-NetConnection -ComputerName localhost -Port 5001 -InformationLevel Quiet -WarningAction SilentlyContinue
            if (-not $backendHealthy) {
                Write-Host "Backend not ready (attempt $attempt)..." -ForegroundColor Yellow
                $allHealthy = $false
            }
            
            # Redis health check
            $redisHealthy = Test-NetConnection -ComputerName localhost -Port 6380 -InformationLevel Quiet -WarningAction SilentlyContinue
            if (-not $redisHealthy) {
                Write-Host "Redis not ready (attempt $attempt)..." -ForegroundColor Yellow
                $allHealthy = $false
            }
            
            # RQ Worker health check via Docker
            try {
                $workerStatus = docker ps --filter "name=casestrainer-rqworker" --format "{{.Status}}" 2>$null
                if (-not $workerStatus -or $workerStatus -like "*unhealthy*") {
                    Write-Host "RQ Worker not healthy (attempt $attempt)..." -ForegroundColor Yellow
                    $allHealthy = $false
                }
            } catch {
                Write-Host "Could not check RQ Worker status (attempt $attempt)..." -ForegroundColor Yellow
                $allHealthy = $false
            }

            if ($allHealthy) {
                Write-Host "OK All services are ready" -ForegroundColor Green
                return $true
            }
        }
        catch {
            Write-Host "Health check attempt $attempt failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    Write-Host "WARNING: Timeout waiting for services, but continuing..." -ForegroundColor Yellow
    return $false
}

function Show-ServiceUrls {
    Write-Host "`n=== Docker Production Mode Ready ===`n" -ForegroundColor Green
    Write-Host "INFO Production Site:  https://wolf.law.uw.edu/casestrainer" -ForegroundColor Green
    Write-Host ""
    Write-Host "Local Development URLs:" -ForegroundColor Cyan
    Write-Host "Backend API:    http://localhost:5001/casestrainer/api/" -ForegroundColor Gray
    Write-Host "Frontend Prod:  http://localhost:8080/" -ForegroundColor Gray
    Write-Host "Nginx (HTTP):   http://localhost:80/" -ForegroundColor Gray
    Write-Host "Nginx (HTTPS):  https://localhost:443/" -ForegroundColor Gray
    Write-Host "Local Frontend: https://localhost/casestrainer/" -ForegroundColor Gray
    Write-Host "API Health:     https://localhost/casestrainer/api/health" -ForegroundColor Gray

    Write-Host "`nDocker Commands:" -ForegroundColor Cyan
    Write-Host "  View logs:    docker-compose -f docker-compose.prod.yml logs [service]" -ForegroundColor Gray
    Write-Host "  Stop all:     docker-compose -f docker-compose.prod.yml down" -ForegroundColor Gray
    Write-Host "  Restart:      docker-compose -f docker-compose.prod.yml restart [service]" -ForegroundColor Gray
}

function Start-ServiceMonitoring {
    [CmdletBinding(SupportsShouldProcess)]
    param()

    if ($PSCmdlet.ShouldProcess("Service monitoring")) {
        Write-Host "Starting service monitoring..." -ForegroundColor Cyan
        
        # Monitor container logs for errors
        $script:MonitoringJob = Start-Job -ScriptBlock {
            param($ComposeFile)
            
            while ($true) {
                try {
                    # Check for worker crashes
                    $workerLogs = docker logs casestrainer-rqworker-prod --tail 10 2>$null
                    if ($workerLogs -match "Work-horse terminated unexpectedly|OOMKilled|Segmentation fault") {
                        Write-Host "[MONITOR] WARNING: Worker crash detected!" -ForegroundColor Red
                        Write-Host "[MONITOR] Consider restarting containers" -ForegroundColor Yellow
                    }
                    
                    # Check for backend errors
                    $backendLogs = docker logs casestrainer-backend-prod --tail 10 2>$null
                    if ($backendLogs -match "ERROR|Exception|Traceback") {
                        Write-Host "[MONITOR] WARNING: Backend errors detected!" -ForegroundColor Red
                    }
                    
                    Start-Sleep -Seconds 30
                } catch {
                    Write-Host "[MONITOR] Monitoring error: $($_.Exception.Message)" -ForegroundColor Yellow
                    Start-Sleep -Seconds 60
                }
            }
        } -ArgumentList (Join-Path $using:PSScriptRoot "docker-compose.prod.yml")
        
        Write-Host "Service monitoring started" -ForegroundColor Green
    }
}

function Stop-ServiceMonitoring {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param()

    if ($script:MonitoringJob) {
        try {
            Stop-Job $script:MonitoringJob -ErrorAction SilentlyContinue
            Remove-Job $script:MonitoringJob -ErrorAction SilentlyContinue
            $script:MonitoringJob = $null
            Write-CrashLog "Service monitoring stopped" -Level "INFO"
        }
        catch {
            Write-CrashLog "Error stopping service monitoring" -Level "WARN" -Exception $_
        }
    }
}

function Stop-AllMonitoring {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param()

    if ($PSCmdlet.ShouldProcess("All monitoring services")) {
        Stop-ServiceMonitoring
        $script:AutoRestartEnabled = $false
    }
}

function Start-DockerProduction {
    [CmdletBinding(SupportsShouldProcess)]
    [OutputType([bool])]
    param(
        [switch]$ForceRebuild,
        [switch]$NoValidation
    )

    Write-Host "`n=== Starting Docker Production Mode ===`n" -ForegroundColor Green

    try {
        # Quick start mode: minimal checks
        if ($QuickStart) {
            Write-Host "QUICK START MODE: Skipping most validation checks" -ForegroundColor Cyan
        } else {
            # Validate environment first
            Test-ScriptEnvironment
        }

        # Parallel Docker and build checks for speed
        $dockerJob = Start-Job -ScriptBlock {
            try {
                $null = docker version --format "{{.Server.Version}}" 2>$null
                return $LASTEXITCODE -eq 0
            } catch {
                return $false
            }
        }

        # Check if we need Vue build in parallel - using proper parameter passing
        $vueJob = $null
        if (-not $SkipVueBuild -and -not $QuickStart) {
            $vueJob = Start-Job -ScriptBlock {
                param($ForceRebuildFlag)
                $vueDir = Join-Path $using:PSScriptRoot "casestrainer-vue-new"
                $distDir = Join-Path $vueDir "dist"
                return (-not (Test-Path $distDir) -or $using:ForceRebuildFlag)
            } -ArgumentList $ForceRebuild
        }

        # Wait for Docker check
        $dockerAvailable = Receive-Job $dockerJob -Wait
        Remove-Job $dockerJob

        if (-not $dockerAvailable) {
            Write-Host "ERROR Docker is not running or not available" -ForegroundColor Red
            Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
            return $false
        }
        Write-Host "OK Docker is running" -ForegroundColor Green

        # Skip resource checks in quick mode
        if (-not $QuickStart) {
            # Quick disk space check only
            try {
                $diskSpace = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='C:'" -ErrorAction Stop
                $freeGB = [math]::Round($diskSpace.FreeSpace / 1GB, 2)
                if ($freeGB -lt 2) {
                    Write-Host "ERROR: Critically low disk space ($freeGB GB free)" -ForegroundColor Red
                    return $false
                }
                Write-Host "OK Sufficient disk space ($freeGB GB free)" -ForegroundColor Green
            }
            catch {
                Write-Host "WARNING: Could not check disk space" -ForegroundColor Yellow
            }
        }

        # Handle Vue build - using ForceRebuild parameter
        if (-not $SkipVueBuild) {
            if ($vueJob) {
                $needsBuild = Receive-Job $vueJob -Wait
                Remove-Job $vueJob
            } else {
                            $needsBuild = Test-VueBuildNeeded -Force:$ForceRebuild
        }

        if ($needsBuild -or $ForceRebuild) {
                Invoke-VueFrontendBuild -Quick:$QuickStart
            } else {
                Write-Host "OK Vue build up to date (skipping build)" -ForegroundColor Green
            }
        } else {
            Write-Host "Skipping Vue frontend build as requested" -ForegroundColor Green
        }

        $dockerComposeFile = Join-Path $PSScriptRoot "docker-compose.prod.yml"

        # Fast container management - Stop ALL containers first to avoid port conflicts
        if ($PSCmdlet.ShouldProcess("Docker containers", "Stop existing")) {
            Write-Host "Stopping ALL Docker containers to avoid port conflicts..." -ForegroundColor Yellow
            
            # Stop ALL containers first (not just from this compose file)
            try {
                $runningContainers = docker ps -q 2>$null
                if ($runningContainers) {
                    Write-Host "Found $($runningContainers.Count) running containers, stopping them..." -ForegroundColor Yellow
                    docker stop $runningContainers 2>$null
                    Start-Sleep -Seconds 2
                }
            } catch {
                Write-Host "Warning: Could not stop all containers: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
            # Also stop containers from this specific compose file
            $stopArgs = @("-f", $dockerComposeFile, "down")
            if ($QuickStart) {
                $stopArgs += @("--timeout", "5")
            }

            $null = Start-Process -FilePath "docker-compose" -ArgumentList $stopArgs -Wait -NoNewWindow -PassThru -WorkingDirectory $PSScriptRoot
        }

        # Optimized container startup - using ForceRebuild parameter
        if ($PSCmdlet.ShouldProcess("Docker containers", "Start")) {
            Write-Host "`nStarting Docker containers..." -ForegroundColor Cyan

            # Smart rebuild logic
            $composeArgs = @("-f", $dockerComposeFile, "up", "-d")

            if ($ForceRebuild -or (Test-CodeChanges)) {
                Write-Host "Forcing rebuild due to code changes..." -ForegroundColor Yellow
                $composeArgs += @("--build", "--force-recreate")
            } else {
                Write-Host "Using existing images (no rebuild needed)..." -ForegroundColor Green
            }

            $startProcess = Start-Process -FilePath "docker-compose" -ArgumentList $composeArgs -Wait -NoNewWindow -PassThru -WorkingDirectory $PSScriptRoot

            if ($startProcess.ExitCode -eq 0) {
                Write-Host "OK Docker containers started successfully" -ForegroundColor Green

                # Quick health check or full check based on mode
                if ($QuickStart) {
                    Write-Host "Quick mode: Skipping detailed health checks" -ForegroundColor Cyan
                    Start-Sleep -Seconds 5
                    $healthOK = $true
                } else {
                    $healthOK = Wait-ForServices -TimeoutMinutes 5
                    
                    # If health check fails, try to restart problematic containers
                    if (-not $healthOK) {
                        Write-Host "Health check failed, attempting container restart..." -ForegroundColor Yellow
                        try {
                            docker-compose -f $dockerComposeFile restart rqworker-prod backend-prod 2>$null
                            Start-Sleep -Seconds 10
                            $healthOK = Wait-ForServices -TimeoutMinutes 3
                        } catch {
                            Write-Host "Container restart failed: $($_.Exception.Message)" -ForegroundColor Red
                        }
                    }
                }

                if ($healthOK) {
                    Show-ServiceUrls
                    
                    # Post-startup validation (skip if NoValidation flag is set)
                    if (-not $NoValidation) {
                        Write-Host "`nRunning post-startup validation..." -ForegroundColor Cyan
                        $validationOK = Test-PostStartupValidation
                        
                        if ($validationOK) {
                            Write-Host "OK Post-startup validation passed" -ForegroundColor Green
                        } else {
                            Write-Host "WARNING: Post-startup validation failed - system may have issues" -ForegroundColor Yellow
                        }
                    } else {
                        Write-Host "Skipping post-startup validation as requested" -ForegroundColor Cyan
                    }

                    # Start auto-restart monitoring if enabled
                    if ($script:AutoRestartEnabled) {
                        Start-ServiceMonitoring
                        Write-Host "`nAuto-restart monitoring enabled" -ForegroundColor Magenta
                    }

                    # Try to open browser (non-blocking)
                    if (-not $QuickStart) {
                        Start-Job -ScriptBlock {
                            Start-Sleep -Seconds 2
                            try {
                                Start-Process "https://wolf.law.uw.edu/casestrainer/"
                            } catch {
                                Write-Warning "Could not open browser"
                            }
                        } | Out-Null
                    }

                    return $true
                }
                else {
                    Write-Host "ERROR Services failed to become healthy" -ForegroundColor Red
                    return $false
                }
            }
            else {
                throw "Failed to start Docker containers (exit code: $($startProcess.ExitCode))"
            }
        }
    }
    catch {
        Write-CrashLog "Error in Start-DockerProduction" -Level "ERROR" -Exception $_
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Show-AdvancedDiagnostics {
    [CmdletBinding()]
    param()

    Write-Host "`n=== Advanced Production Diagnostics ===`n" -ForegroundColor Cyan
    Write-Host "Placeholder for advanced diagnostics - implement as needed"
}

function Test-PostStartupValidation {
    [CmdletBinding()]
    [OutputType([bool])]
    param()

    Write-Host "  Testing API endpoints..." -ForegroundColor Gray
    
    try {
        # Test basic API health
        $healthResponse = Invoke-WebRequest -Uri "http://localhost:5001/casestrainer/api/health" -Method GET -TimeoutSec 10 -ErrorAction Stop
        if ($healthResponse.StatusCode -ne 200) {
            Write-Host "  ❌ API health check failed" -ForegroundColor Red
            return $false
        }
        
        # Test simple text processing
        $testPayload = @{
            type = "text"
            text = "The court in Smith v. Jones, 123 U.S. 456 (2020) held that..."
        } | ConvertTo-Json
        
        $testResponse = Invoke-WebRequest -Uri "http://localhost:5000/casestrainer/api/analyze" -Method POST -Body $testPayload -ContentType "application/json" -TimeoutSec 30 -ErrorAction Stop
        
        if ($testResponse.StatusCode -eq 200) {
            $result = $testResponse.Content | ConvertFrom-Json
            if ($result.status -eq "processing" -and $result.task_id) {
                Write-Host "  ✅ Text processing test passed" -ForegroundColor Green
                return $true
            } else {
                Write-Host "  ❌ Text processing test failed - unexpected response" -ForegroundColor Red
                return $false
            }
        } else {
            Write-Host "  ❌ Text processing test failed - HTTP $($testResponse.StatusCode)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "  ❌ Post-startup validation failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Show-CacheManagement {
    [CmdletBinding()]
    param()

    Write-Host "`n=== Cache Management ===`n" -ForegroundColor Cyan
    Write-Host "Placeholder for cache management - implement as needed"
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
                Write-Host "OK All Docker services stopped successfully" -ForegroundColor Green
            }
            else {
                Write-Host "WARNING: Docker services may not have stopped cleanly (exit code: $($stopProcess.ExitCode))" -ForegroundColor Yellow
            }
        }
        catch {
            Write-CrashLog "Error stopping services" -Level "ERROR" -Exception $_
            Write-Host "ERROR Error stopping services: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    else {
        Write-Host "Operation cancelled by user" -ForegroundColor Yellow
    }
}

function Show-QuickStatus {
    [CmdletBinding()]
    param()

    Write-Host "`n=== Quick Status Check ===`n" -ForegroundColor Magenta

    # Parallel status checks for speed
    $jobs = @()

    # Docker check
    $jobs += Start-Job -Name "Docker" -ScriptBlock {
        try {
            $null = docker version --format "{{.Server.Version}}" 2>$null
            return @{ Service = "Docker"; Status = if ($LASTEXITCODE -eq 0) { "OK" } else { "ERROR" } }
        } catch {
            return @{ Service = "Docker"; Status = "ERROR" }
        }
    }

    # Container check
    $jobs += Start-Job -Name "Containers" -ScriptBlock {
        try {
            $containers = docker ps --filter "name=casestrainer" --format "{{.Names}}" 2>$null
            $count = if ($containers) { ($containers | Measure-Object).Count } else { 0 }
            return @{ Service = "Containers"; Status = "$count running" }
        } catch {
            return @{ Service = "Containers"; Status = "ERROR" }
        }
    }

    # Backend check
    $jobs += Start-Job -Name "Backend" -ScriptBlock {
        try {
            $reachable = Test-NetConnection -ComputerName localhost -Port 5001 -InformationLevel Quiet -WarningAction SilentlyContinue
            return @{ Service = "Backend"; Status = if ($reachable) { "HEALTHY" } else { "DOWN" } }
        } catch {
            return @{ Service = "Backend"; Status = "ERROR" }
        }
    }

    # Wait for all jobs and display results
    foreach ($job in $jobs) {
        $result = Receive-Job $job -Wait
        Remove-Job $job

        $color = switch ($result.Status) {
            { $_ -like "*OK*" -or $_ -like "*HEALTHY*" -or $_ -match "^\d+ running$" } { "Green" }
            { $_ -like "*ERROR*" -or $_ -like "*DOWN*" } { "Red" }
            default { "Yellow" }
        }

        Write-Host "$($result.Service): $($result.Status)" -ForegroundColor $color
    }

    Write-Host "`nProduction URL: https://wolf.law.uw.edu/casestrainer" -ForegroundColor Cyan
}
function Show-Menu {
    [CmdletBinding()]
    [OutputType([string])]
    param()

    Clear-Host
    Write-Host "`n" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " Enhanced CaseStrainer Docker Launcher" -ForegroundColor Cyan
    Write-Host "                v1.1 (OPTIMIZED)      " -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " 1.  Quick Production Start (FASTEST)" -ForegroundColor Green
    Write-Host "    - Minimal checks, maximum speed"
    Write-Host ""
    Write-Host " 2.  Smart Production Start (RECOMMENDED)" -ForegroundColor Cyan
    Write-Host "    - Intelligent build detection, balanced speed"
    Write-Host ""
    Write-Host " 3.  Force Full Rebuild" -ForegroundColor Yellow
    Write-Host "    - Complete rebuild, use when needed"
    Write-Host ""
    Write-Host " 4.   Advanced Diagnostics" -ForegroundColor Blue
    Write-Host " 5.   Cache Management" -ForegroundColor Yellow
    Write-Host " 6.   Stop All Services" -ForegroundColor Red
    Write-Host " 7.  Quick Status Check" -ForegroundColor Magenta
    Write-Host " 0.  Exit" -ForegroundColor Gray
    Write-Host ""
    Write-Host "TIP: Use option 1 for fastest startup!" -ForegroundColor Green
    Write-Host ""

    do {
        $selection = Read-Host "Select an option (0-7)"
        if ($selection -match "^[0-7]$") {
            break
        } else {
            Write-Host "Invalid selection. Please enter a number between 0 and 7." -ForegroundColor Red
        }
    } while ($true)

    switch ($selection) {
        "1" {
            # Quick start mode
            $script:QuickStart = $true
            $script:SkipVueBuild = $true
            Start-DockerProduction
            $script:QuickStart = $false
            $script:SkipVueBuild = $false
        }
        "2" { Start-DockerProduction }
        "3" {
            Start-DockerProduction -ForceRebuild
        }
        "4" { Show-AdvancedDiagnostics }
        "5" { Show-CacheManagement }
        "6" { Stop-AllServices }
        "7" { Show-QuickStatus }
        "0" {
            Write-Host "Exiting..." -ForegroundColor Gray
            Stop-AllMonitoring
            exit 0
        }
    }

    return $selection
}

# Register cleanup on script exit
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Stop-AllMonitoring
} | Out-Null

# Main execution
try {
    Initialize-LogDirectory
    Write-CrashLog "Script started with Mode: $Mode, QuickStart: $QuickStart, SkipVue: $SkipVueBuild, MenuOption: $MenuOption" -Level "INFO"

    # Initialize cache
    $script:CachedChecks.LastCheckTime = Get-Date

    # Handle cache clearing
    if ($ClearCache) {
        Clear-AllCaches
    }

    # If MenuOption is provided, run the corresponding menu action and exit
    if ($null -ne $MenuOption) {
        switch ($MenuOption) {
            1 {
                $script:QuickStart = $true
                $script:SkipVueBuild = $true
                Start-DockerProduction
                $script:QuickStart = $false
                $script:SkipVueBuild = $false
                exit 0
            }
            2 {
                Start-DockerProduction
                exit 0
            }
            3 {
                Start-DockerProduction -ForceRebuild
                exit 0
            }
            4 { Show-AdvancedDiagnostics; exit 0 }
            5 { Show-CacheManagement; exit 0 }
            6 { Stop-AllServices; exit 0 }
            7 { Show-QuickStatus; exit 0 }
            0 {
                Write-Host "Exiting..." -ForegroundColor Gray
                Stop-AllMonitoring
                exit 0
            }
            default {
                Write-Host "Unknown menu option: $MenuOption" -ForegroundColor Red
                exit 1
            }
        }
    }

    # If a valid mode is provided (not Menu), run it directly and skip the menu
    if ($Mode -ne "Menu") {
        switch ($Mode) {
            "Production" {
                Write-Host "[dplaunch] Starting in Production mode..." -ForegroundColor Green
                Start-DockerProduction
                exit 0
            }
            "Diagnostics" {
                Write-Host "[dplaunch] Starting in Diagnostics mode..." -ForegroundColor Green
                Show-AdvancedDiagnostics
                exit 0
            }
            "Cache" {
                Write-Host "[dplaunch] Starting in Cache management mode..." -ForegroundColor Green
                Show-CacheManagement
                exit 0
            }
            "Test" {
                Write-Host "[dplaunch] Starting in Test mode..." -ForegroundColor Green
                
                # Start services if needed
                if (-not (Test-NetConnection -ComputerName localhost -Port 5001 -InformationLevel Quiet -WarningAction SilentlyContinue)) {
                    Write-Host "Starting services for testing..." -ForegroundColor Yellow
                    Start-DockerProduction -NoValidation
                }
                
                $apiSuccess = $true
                $frontendSuccess = $true
                
                if ($TestAPI) {
                    $apiSuccess = Test-APIFunctionality -TestCitation $TestCitation
                }
                
                if ($TestFrontend) {
                    $frontendSuccess = Test-FrontendFunctionality
                }
                
                if ($ShowLogs) {
                    Show-ContainerLogs
                }
                
                if ($apiSuccess -and $frontendSuccess) {
                    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
                } else {
                    Write-Host "`n❌ Some tests failed!" -ForegroundColor Red
                }
                
                exit 0
            }
            "Debug" {
                Write-Host "[dplaunch] Starting in Debug mode..." -ForegroundColor Green
                
                if ($VerboseLogging) {
                    $VerbosePreference = "Continue"
                }
                
                Write-Host "Debug Mode Enabled" -ForegroundColor Cyan
                Write-Host "Test Citation: $TestCitation" -ForegroundColor Yellow
                Write-Host "Timeout: $TimeoutMinutes minutes" -ForegroundColor Yellow
                
                # Start with debug info
                Start-DockerProduction -NoValidation
                
                # Run tests with debug output
                Test-APIFunctionality -TestCitation $TestCitation
                Test-FrontendFunctionality
                
                if ($ShowLogs) {
                    Show-ContainerLogs
                }
                
                exit 0
            }
            default {
                Write-Host "[dplaunch] Unknown mode: $Mode" -ForegroundColor Red
                exit 1
            }
        }
    }

    # If no valid mode is provided, show the interactive menu as before
    do {
        $selection = Show-Menu

        if ($selection -ne "0") {
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
    } while ($selection -ne "0")
}
catch {
    Write-CrashLog "Fatal error in main execution" -Level "ERROR" -Exception $_
    Write-Host "`nFatal Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check log file: $($script:CrashLogFile)" -ForegroundColor Yellow
    Stop-AllMonitoring
    exit 1
}
finally {
    # Ensure cleanup happens
    Stop-AllMonitoring
}
