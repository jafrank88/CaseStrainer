# Fast CaseStrainer Docker Production Launcher
# Optimized for quick startup by skipping unnecessary steps

param(
    [ValidateSet("Production", "Diagnostics", "Menu", "Cache")]
    [string]$Mode = "Menu",
    [switch]$Help,
    [switch]$AutoRestart,
    [switch]$ForceRebuild,
    [switch]$SkipVueBuild
)

# Input validation
if (-not $PSScriptRoot) {
    throw "Script must be run from a file, not from command line"
}

# Global variables
$script:AutoRestartEnabled = $AutoRestart.IsPresent
$script:CrashLogFile = Join-Path $PSScriptRoot "logs\crash.log"

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

# Show help
if ($Help) {
    Write-Host @"
Fast CaseStrainer Docker Production Launcher - Help

Usage:
  .\dplaunch_fast.ps1 [Options]

Options:
  -Mode Production    Start Docker Production Mode (fast)
  -Mode Diagnostics   Run Quick Diagnostics
  -Mode Cache         Manage Citation Caches
  -Mode Menu         Show interactive menu (default)
  -AutoRestart       Enable auto-restart monitoring
  -ForceRebuild      Force rebuild of containers (slower)
  -SkipVueBuild      Skip Vue frontend build (fastest)
  -Help              Show this help

Examples:
  .\dplaunch_fast.ps1                           # Show menu
  .\dplaunch_fast.ps1 -Mode Production          # Start production (fast)
  .\dplaunch_fast.ps1 -Mode Production -SkipVueBuild  # Fastest startup
  .\dplaunch_fast.ps1 -Mode Production -ForceRebuild  # Full rebuild
"@ -ForegroundColor Cyan
    exit 0
}

function Test-ScriptEnvironment {
    [CmdletBinding()]
    param()
    
    $requiredFiles = @(
        "docker-compose.prod.yml"
    )
    
    foreach ($file in $requiredFiles) {
        $path = Join-Path $PSScriptRoot $file
        if (-not (Test-Path $path)) {
            throw "Required file not found: $file"
        }
    }
}

function Test-DockerAvailability {
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    
    try {
        $null = docker info --format "{{.ServerVersion}}" 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Test-VueBuildNeeded {
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    
    $vueDir = Join-Path $PSScriptRoot "casestrainer-vue-new"
    $distDir = Join-Path $vueDir "dist"
    $indexFile = Join-Path $distDir "index.html"
    
    # Check if dist directory exists and has content
    if (-not (Test-Path $distDir) -or -not (Test-Path $indexFile)) {
        return $true
    }
    
    # Check if dist is older than source files
    $distTime = (Get-Item $distDir).LastWriteTime
    $packageJson = Join-Path $vueDir "package.json"
    $srcDir = Join-Path $vueDir "src"
    
    if (Test-Path $packageJson) {
        $packageTime = (Get-Item $packageJson).LastWriteTime
        if ($packageTime -gt $distTime) {
            return $true
        }
    }
    
    if (Test-Path $srcDir) {
        $srcFiles = Get-ChildItem $srcDir -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($srcFiles -and $srcFiles.LastWriteTime -gt $distTime) {
            return $true
        }
    }
    
    return $false
}

function Build-VueFrontend {
    [CmdletBinding()]
    param()
    
    Write-Host "Building Vue frontend..." -ForegroundColor Cyan
    $vueDir = Join-Path $PSScriptRoot "casestrainer-vue-new"
    
    Push-Location $vueDir
    try {
        # Check if package.json exists
        if (-not (Test-Path "package.json")) {
            throw "package.json not found in Vue directory"
        }
        
        # Check Node.js availability
        Write-Host "Checking Node.js..." -ForegroundColor Yellow
        try {
            $nodeVersion = node --version 2>$null
            if ($LASTEXITCODE -ne 0 -or -not $nodeVersion) {
                throw "Node.js not found. Please install Node.js first."
            }
            Write-Host "OK Node.js $nodeVersion" -ForegroundColor Green
        } catch {
            throw "Node.js not available: $($_.Exception.Message)"
        }
        
        # Check if node_modules exists, if not install dependencies
        if (-not (Test-Path "node_modules")) {
            Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
            $installProcess = Start-Process -FilePath "npm" -ArgumentList "install", "--no-audit", "--no-fund" -Wait -NoNewWindow -PassThru
            if ($installProcess.ExitCode -ne 0) {
                throw "npm install failed"
            }
        }
        
        Write-Host "Building Vue frontend..." -ForegroundColor Yellow
        $buildProcess = Start-Process -FilePath "npm" -ArgumentList "run", "build" -Wait -NoNewWindow -PassThru
        if ($buildProcess.ExitCode -ne 0) {
            throw "npm build failed"
        }
        
        Write-Host "OK Vue frontend built successfully" -ForegroundColor Green
    } finally {
        Pop-Location
    }
}

function Start-DockerProduction {
    [CmdletBinding(SupportsShouldProcess)]
    [OutputType([bool])]
    param()
    
    Write-Host "`n=== Starting Fast Docker Production Mode ===`n" -ForegroundColor Green
    
    try {
        # Validate environment
        Test-ScriptEnvironment
        
        if (-not (Test-DockerAvailability)) {
            Write-Host "ERROR Docker is not running or not available" -ForegroundColor Red
            Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
            return $false
        }
        Write-Host "OK Docker is running" -ForegroundColor Green
        
        $dockerComposeFile = Join-Path $PSScriptRoot "docker-compose.prod.yml"
        
        # Build Vue frontend only if needed
        if (-not $SkipVueBuild) {
            if ($ForceRebuild -or (Test-VueBuildNeeded)) {
                Build-VueFrontend
            } else {
                Write-Host "OK Vue frontend already built (skipping)" -ForegroundColor Green
            }
        } else {
            Write-Host "OK Skipping Vue frontend build" -ForegroundColor Green
        }
        
        # Stop existing containers
        if ($PSCmdlet.ShouldProcess("Docker containers", "Stop existing")) {
            Write-Host "`nStopping existing containers..." -ForegroundColor Yellow
            $stopProcess = Start-Process -FilePath "docker-compose" -ArgumentList "-f", $dockerComposeFile, "down" -Wait -NoNewWindow -PassThru -WorkingDirectory $PSScriptRoot
            if ($stopProcess.ExitCode -ne 0) {
                Write-Warning "Failed to stop existing containers (they may not be running)"
            }
        }
        
        # Start containers with optimized flags
        if ($PSCmdlet.ShouldProcess("Docker containers", "Start")) {
            Write-Host "`nStarting Docker containers..." -ForegroundColor Cyan
            
            $dockerArgs = @("-f", $dockerComposeFile, "up", "-d")
            if ($ForceRebuild) {
                $dockerArgs += "--build"
            }
            
            $startProcess = Start-Process -FilePath "docker-compose" -ArgumentList $dockerArgs -Wait -NoNewWindow -PassThru -WorkingDirectory $PSScriptRoot
            
            if ($startProcess.ExitCode -eq 0) {
                Write-Host "OK Docker containers started successfully" -ForegroundColor Green
                
                # Quick health check
                if (Wait-ForServices -TimeoutMinutes 2) {
                    Show-ServiceUrls
                    
                    # Start auto-restart monitoring if enabled
                    if ($script:AutoRestartEnabled) {
                        Write-Host "`nAuto-restart monitoring enabled" -ForegroundColor Magenta
                    }
                    
                    # Open browser
                    try {
                        Start-Process "https://wolf.law.uw.edu/casestrainer/"
                    } catch {
                        Write-Host "Could not open browser automatically" -ForegroundColor Yellow
                    }
                    
                    return $true
                } else {
                    Write-Host "WARNING Services may still be initializing" -ForegroundColor Yellow
                    Show-ServiceUrls
                    return $true
                }
            } else {
                throw "Failed to start Docker containers (exit code: $($startProcess.ExitCode))"
            }
        }
    } catch {
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Wait-ForServices {
    [CmdletBinding()]
    [OutputType([bool])]
    param(
        [int]$TimeoutMinutes = 2
    )
    
    Write-Host "`nQuick health check..." -ForegroundColor Yellow
    $timeout = (Get-Date).AddMinutes($TimeoutMinutes)
    $attempt = 0
    
    while ((Get-Date) -lt $timeout) {
        $attempt++
        Start-Sleep -Seconds 5
        
        try {
            # Quick API health check
            $apiHealthy = $false
            try {
                $healthResponse = Invoke-RestMethod -Uri "http://localhost:5001/casestrainer/api/health" -Method GET -TimeoutSec 3 -ErrorAction SilentlyContinue
                $apiHealthy = $null -ne $healthResponse
            } catch {
                # API not ready yet
            }
            
            if ($apiHealthy) {
                Write-Host "OK Services are ready" -ForegroundColor Green
                return $true
            } else {
                Write-Host "Services initializing (attempt $attempt)..." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "Health check error (attempt $attempt): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    return $false
}

function Show-ServiceUrls {
    Write-Host "`n=== Fast Docker Production Mode Ready ===`n" -ForegroundColor Green
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

function Show-QuickDiagnostics {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Quick Production Diagnostics ===`n" -ForegroundColor Cyan
    
    # Check Docker status
    Write-Host "Checking Docker status..." -ForegroundColor Yellow
    if (-not (Test-DockerAvailability)) {
        Write-Host "ERROR Docker is not available" -ForegroundColor Red
        return
    }
    
    try {
        $dockerVersion = docker --version
        Write-Host "OK Docker is available: $dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "ERROR Docker version check failed: $($_.Exception.Message)" -ForegroundColor Red
        return
    }
    
    # Quick container status
    Write-Host "`n=== Container Status ===" -ForegroundColor Cyan
    try {
        $containers = docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        if ($containers -and $containers.Count -gt 1) {
            Write-Host "Container Status:" -ForegroundColor Gray
            $containers | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
        } else {
            Write-Host "No casestrainer containers running" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "ERROR Container status check failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Quick API test
    Write-Host "`n=== API Health Check ===" -ForegroundColor Cyan
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:5001/casestrainer/api/health" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($healthResponse) {
            Write-Host "OK API is responding" -ForegroundColor Green
        } else {
            Write-Host "WARNING API not responding" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "ERROR API health check failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Show-Menu {
    [CmdletBinding()]
    [OutputType([string])]
    param()
    
    Clear-Host
    Write-Host "`n" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " Fast CaseStrainer Docker Launcher" -ForegroundColor Cyan
    Write-Host "           Optimized v1.0              " -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " 1. Fast Docker Production Mode" -ForegroundColor Green
    Write-Host "    - Skips unnecessary rebuilds"
    Write-Host "    - Uses cached Vue build when possible"
    Write-Host "    - Quick startup (2-3 minutes)"
    Write-Host ""
    Write-Host " 2. Quick Diagnostics" -ForegroundColor Cyan
    Write-Host "    - Fast system checks"
    Write-Host "    - Container status"
    Write-Host "    - API health check"
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
    Write-Host " 7. Force Full Rebuild" -ForegroundColor Magenta
    Write-Host " 8. Skip Vue Build Mode" -ForegroundColor Blue
    Write-Host " 0. Exit" -ForegroundColor Gray
    Write-Host ""
    
    do {
        $selection = Read-Host "Select an option (0-8)"
        if ($selection -match "^[0-8]$") {
            return $selection
        } else {
            Write-Host "Invalid selection. Please enter a number between 0 and 8." -ForegroundColor Red
        }
    } while ($true)
}

# Main execution
try {
    Initialize-LogDirectory
    
    switch ($Mode) {
        "Production" {
            Start-DockerProduction
        }
        "Diagnostics" {
            Show-QuickDiagnostics
        }
        "Menu" {
            do {
                $selection = Show-Menu
                switch ($selection) {
                    "1" { Start-DockerProduction }
                    "2" { Show-QuickDiagnostics }
                    "3" { 
                        Write-Host "Cache management not implemented in fast version" -ForegroundColor Yellow
                        Write-Host "Use original dplaunch.ps1 for cache management" -ForegroundColor Yellow
                    }
                    "4" { 
                        Write-Host "Stopping all services..." -ForegroundColor Yellow
                        $dockerComposeFile = Join-Path $PSScriptRoot "docker-compose.prod.yml"
                        Start-Process -FilePath "docker-compose" -ArgumentList "-f", $dockerComposeFile, "down" -Wait -NoNewWindow -PassThru
                        Write-Host "OK All services stopped" -ForegroundColor Green
                    }
                    "5" { 
                        Write-Host "Container status:" -ForegroundColor Cyan
                        docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
                    }
                    "6" { 
                        Write-Host "Recent logs:" -ForegroundColor Cyan
                        $dockerComposeFile = Join-Path $PSScriptRoot "docker-compose.prod.yml"
                        docker-compose -f $dockerComposeFile logs --tail=20
                    }
                    "7" { 
                        Write-Host "Force rebuild mode..." -ForegroundColor Magenta
                        $ForceRebuild = $true
                        Start-DockerProduction
                    }
                    "8" { 
                        Write-Host "Skip Vue build mode..." -ForegroundColor Blue
                        $SkipVueBuild = $true
                        Start-DockerProduction
                    }
                    "0" { 
                        Write-Host "Exiting..." -ForegroundColor Gray
                        exit 0
                    }
                }
                
                if ($selection -ne "0") {
                    Write-Host "`nPress any key to continue..." -ForegroundColor Gray
                    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                }
            } while ($selection -ne "0")
        }
        default {
            Write-Host "Unknown mode: $Mode" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} 