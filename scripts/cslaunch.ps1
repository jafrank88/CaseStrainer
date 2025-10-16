# cslaunch.ps1 - Main entry point for CaseStrainer deployment
# This script orchestrates the deployment and management of CaseStrainer services

# Set strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Import required modules
$modulePath = Join-Path $PSScriptRoot "modules"
Import-Module (Join-Path $modulePath "Docker.psm1") -Force -ErrorAction Stop
Import-Module (Join-Path $modulePath "DockerDiagnostics.ps1") -Force -ErrorAction SilentlyContinue
Import-Module (Join-Path $modulePath "Nginx.psm1") -Force -ErrorAction Stop

# Configuration
$config = @{
    ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
    DockerComposeFile = "docker-compose.yml"
    DockerComposeProdFile = "docker-compose.prod.yml"
    RequiredPorts = @(80, 443, 5000)
    NginxConfig = @{
        NginxPath = "C:\nginx\nginx.exe"
        ConfigPath = Join-Path $PSScriptRoot "..\nginx\nginx.conf"
        LogsPath = Join-Path $PSScriptRoot "..\logs\nginx"
    }
}

# Initialize Nginx configuration
$nginxConfig = @{
    NginxPath = $config.NginxConfig.NginxPath
    ConfigPath = $config.NginxConfig.ConfigPath
    LogsPath = $config.NginxConfig.LogsPath
}
Set-NginxConfig @nginxConfig

# Function to check and ensure Docker is running
function Test-EnsureDockerRunning {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Docker Pre‑Flight Check ===" -ForegroundColor Cyan
    
    # Ensure Docker CLI is available
    if (-not (Test-CommandExists 'docker')) {
        Write-Host "[ERROR] Docker CLI is not installed or not in PATH" -ForegroundColor Red
        Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
        return $false
    }
    
    $maxAttempts = 30
    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        try {
            docker info >$null 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK] Docker daemon is running and accessible (attempt $attempt)" -ForegroundColor Green
                return $true
            }
        } catch {
            # ignore errors, will retry
        }
        Start-Sleep -Seconds 2
    }
    
    Write-Host "[ERROR] Docker daemon is not reachable after $maxAttempts attempts." -ForegroundColor Red
    Write-Host "Please ensure Docker Desktop is running and the Docker service is started." -ForegroundColor Yellow
    Write-Host "You may need to start Docker Desktop manually or restart your computer." -ForegroundColor Yellow
    return $false
    # Service restart logic removed - Docker must be started manually

}

# Helper function to check if a command exists
function Test-CommandExists {
    param($command)
    return (Get-Command $command -ErrorAction SilentlyContinue) -ne $null
}

# Main function to handle the script's entry point
function Start-CaseStrainer {
    [CmdletBinding()]
    param(
        [ValidateSet('dev', 'prod', 'stop', 'status', 'logs')]
        [string]$Command = 'status',
        
        [switch]$Build,
        [switch]$NoCache,
        [switch]$Force,
        [string[]]$Services = @()
    )
    
    try {
        Write-Host "`n=== CaseStrainer Deployment Manager ===" -ForegroundColor Cyan
        
        # Check and ensure Docker is running before proceeding
        if (-not (Test-EnsureDockerRunning)) {
            Write-Host "[ERROR] Docker requirements not met. Please resolve Docker issues and try again." -ForegroundColor Red
            exit 1
        }
        
        # Additional Docker availability check using the module
        if (-not (Test-DockerAvailability)) {
            Write-Host "[WARNING] Docker is available but may have some issues. Continuing anyway..." -ForegroundColor Yellow
        }
        
        # Execute the requested command
        switch ($Command.ToLower()) {
            'dev' {
                Start-Development -Build:$Build -NoCache:$NoCache -Services $Services
            }
            'prod' {
                # Ensure Nginx is stopped before starting production
                try { Stop-NginxServer -ErrorAction SilentlyContinue | Out-Null } catch {}
                Start-Production -Build:$Build -NoCache:$NoCache -Force:$Force
            }
            'stop' {
                Stop-Services -RemoveVolumes:$Force
                # Also stop Nginx if running
                try { Stop-NginxServer -ErrorAction SilentlyContinue | Out-Null } catch {}
            }
            'status' {
                Get-ServiceStatus
            }
            'logs' {
                Show-Logs -Services $Services
            }
        }
    }
    catch {
        Write-Host "[ERROR] An error occurred: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host $_.ScriptStackTrace -ForegroundColor Gray
        exit 1
    }
}

# Start development environment
function Start-Development {
    [CmdletBinding()]
    param(
        [switch]$Build,
        [switch]$NoCache,
        [string[]]$Services = @()
    )
    
    Write-Host "`n=== Starting Development Environment ===" -ForegroundColor Cyan
    
    # Build containers if requested
    if ($Build) {
        Write-Host "Building development containers..." -ForegroundColor Yellow
        if (-not (Start-DockerBuild -DockerComposeFile $config.DockerComposeFile -NoCache:$NoCache)) {
            throw "Failed to build development containers"
        }
    }
    
    # Start services
    Write-Host "Starting development services..." -ForegroundColor Yellow
    $composeArgs = @(
        "-f", $config.DockerComposeFile
    )
    
    if ($Services) {
        # Filter out services that don't exist in the current setup
        $existingServices = docker-compose -f $config.DockerComposeFile config --services 2>$null
        if ($existingServices) {
            $validServices = $Services | Where-Object { $_ -in $existingServices }
            if ($validServices) {
                $composeArgs += $validServices
            }
        }
    }
    
    docker-compose @composeArgs up -d
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start development services"
    }
    
    Write-Host "`nDevelopment environment is now running!" -ForegroundColor Green
    Write-Host "- Frontend: http://localhost:8080" -ForegroundColor Cyan
    Write-Host "- Backend API: http://localhost:5000" -ForegroundColor Cyan
    Write-Host "- View logs with: .\cslaunch.ps1 logs" -ForegroundColor Cyan
}

# Build Vue frontend
function Build-VueFrontend {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Building Vue Frontend ===" -ForegroundColor Cyan
    
    $vueDir = Join-Path $config.ProjectRoot "casestrainer-vue-new"
    
    if (-not (Test-Path $vueDir)) {
        Write-Host "[WARNING] Vue directory not found at: $vueDir" -ForegroundColor Yellow
        return $false
    }
    
    Push-Location $vueDir
    try {
        Write-Host "Running npm run build..." -ForegroundColor Yellow
        
        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
            npm install
            if ($LASTEXITCODE -ne 0) {
                throw "npm install failed"
            }
        }
        
        # Build Vue
        npm run build
        if ($LASTEXITCODE -ne 0) {
            throw "npm build failed"
        }
        
        Write-Host "Vue frontend build completed successfully!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[ERROR] Vue build failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    finally {
        Pop-Location
    }
}

# Helper function to wait for services to be ready
function Wait-ForServices {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Waiting for services to be ready ===" -ForegroundColor Cyan
    
    try {
        # Check if backend container is running
        $backendRunning = docker ps --filter "name=casestrainer-backend-prod" --format "{{.Names}}" 2>$null
        
        if (-not $backendRunning) {
            Write-Host "[INFO] Backend container not running yet - skipping service checks" -ForegroundColor Yellow
            return
        }
        
        # Copy wait script to container
        $waitScript = Join-Path $config.ProjectRoot "scripts\wait-for-services.py"
        if (Test-Path $waitScript) {
            docker cp $waitScript casestrainer-backend-prod:/app/wait-for-services.py 2>$null
            
            # Run wait script
            $output = docker exec casestrainer-backend-prod python /app/wait-for-services.py 2>&1
            
            # Display output
            $output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        } else {
            Write-Host "[WARNING] Wait script not found at: $waitScript" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "[WARNING] Service readiness check failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "  (This is non-critical and won't affect deployment)" -ForegroundColor DarkGray
    }
}

# Helper function to cleanup stuck RQ jobs
function Clear-StuckJobs {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Cleaning up stuck RQ jobs ===" -ForegroundColor Cyan
    
    try {
        # Check if backend container is running
        $backendRunning = docker ps --filter "name=casestrainer-backend-prod" --format "{{.Names}}" 2>$null
        
        if (-not $backendRunning) {
            Write-Host "[INFO] Backend container not running yet - skipping cleanup" -ForegroundColor Yellow
            return
        }
        
        # Copy cleanup script to container
        $cleanupScript = Join-Path $config.ProjectRoot "scripts\cleanup-stuck-jobs.py"
        if (Test-Path $cleanupScript) {
            docker cp $cleanupScript casestrainer-backend-prod:/app/cleanup-stuck-jobs.py 2>$null
            
            # Run cleanup script
            $output = docker exec casestrainer-backend-prod python /app/cleanup-stuck-jobs.py 2>&1
            
            # Display output
            $output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            
            Write-Host "[OK] Job cleanup complete" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] Cleanup script not found at: $cleanupScript" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "[WARNING] Could not cleanup stuck jobs: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "  (This is non-critical and won't affect deployment)" -ForegroundColor DarkGray
    }
}

# Start production environment
function Start-Production {
    [CmdletBinding()]
    param(
        [switch]$Build,
        [switch]$NoCache,
        [switch]$Force
    )
    
    Write-Host "`n`n===============================================" -ForegroundColor Yellow
    Write-Host "=== UPDATED FAST-RESTART VERSION (v2.0) ===" -ForegroundColor Yellow
    Write-Host "==============================================`n" -ForegroundColor Yellow
    Write-Host "`n=== Starting Production Environment ===" -ForegroundColor Cyan
    
    # Always build Vue frontend to ensure latest source changes are deployed
    # This ensures frontend fixes (polling, error handling, etc.) are always included
    Write-Host "Building Vue frontend from source..." -ForegroundColor Yellow
    if (-not (Build-VueFrontend)) {
        Write-Host "[WARNING] Vue build failed or skipped. Continuing with existing build..." -ForegroundColor Yellow
    }
    
    # Check for existing containers (production uses hyphen, not underscore)
    $containers = @(docker ps -a --format '{{.Names}}' | Where-Object { $_ -match 'casestrainer-' })
    $containerCount = $containers.Count
    
    Write-Host "`n[DEBUG] Found $containerCount existing CaseStrainer containers" -ForegroundColor DarkGray
    
    # Skip build by default since we use volume mounts (much faster!)
    # Only rebuild Docker images when explicitly requested with -Build
    if ($Build) {
        Write-Host "Building production containers (this will take 5-8 minutes)..." -ForegroundColor Yellow
        if (-not (Start-DockerBuild -DockerComposeFile $config.DockerComposeFile -DockerComposeFile $config.DockerComposeProdFile -NoCache:$NoCache)) {
            throw "Failed to build production containers"
        }
        # After build, force recreate to use new images
        $Force = $true
    } else {
        Write-Host "Skipping Docker image rebuild (using volume mounts for fast Python updates)" -ForegroundColor Green
        Write-Host "  - To rebuild Docker images: ./cslaunch -Build" -ForegroundColor DarkGray
        Write-Host "  - Your Python code changes take effect immediately via volume mounts" -ForegroundColor DarkGray
    }
    
    # CRITICAL FIX: Check Count property, not array itself (empty arrays are truthy in PowerShell!)
    if ($containerCount -gt 0 -and -not $Force) {
        Write-Host "[INFO] Found $($containers.Count) existing containers. Performing quick restart..." -ForegroundColor Cyan
        Write-Host "  This should take ~10-20 seconds..." -ForegroundColor DarkGray
        docker-compose -f $config.DockerComposeFile -f $config.DockerComposeProdFile restart
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to restart containers"
        }
        Write-Host "`n✅ Production environment restarted in seconds!" -ForegroundColor Green
        
        # Wait for services to be ready
        Wait-ForServices
        
        # Cleanup stuck jobs after services are ready
        Clear-StuckJobs
        
        Write-Host "`n- Application: http://localhost" -ForegroundColor Cyan
        Write-Host "- Your Python changes from volume mounts are now active" -ForegroundColor DarkGray
        return
    }
    
    # Start services
    Write-Host "Starting production services..." -ForegroundColor Yellow
    $composeArgs = @(
        "-f", $config.DockerComposeFile,
        "-f", $config.DockerComposeProdFile,
        "up", "-d"
    )
    
    # CRITICAL: Add --no-build to prevent automatic rebuilding during 'up'
    # This ensures we only build when explicitly requested with -Build flag
    if (-not $Build) {
        $composeArgs += "--no-build"
        Write-Host "  Using --no-build flag (skipping image rebuild)" -ForegroundColor DarkGray
    }
    
    if ($Force) {
        $composeArgs += "--force-recreate"
    }
    
    docker-compose @composeArgs
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start production services"
    }
    
    Write-Host "`nProduction environment is now running!" -ForegroundColor Green
    
    # Wait for services to be ready
    Wait-ForServices
    
    # Cleanup stuck jobs after services are ready
    Clear-StuckJobs
    
    Write-Host "`n- Application: http://localhost" -ForegroundColor Cyan
    Write-Host "- View logs with: .\cslaunch.ps1 logs" -ForegroundColor Cyan
}

# Stop all services
function Stop-Services {
    [CmdletBinding()]
    param(
        [switch]$RemoveVolumes
    )
    
    Write-Host "`n=== Stopping Services ===" -ForegroundColor Cyan
    
    $composeArgs = @(
        "-f", $config.DockerComposeFile
    )
    
    if (Test-Path $config.DockerComposeProdFile) {
        $composeArgs += "-f", $config.DockerComposeProdFile
    }
    
    $composeArgs += "down"
    
    if ($RemoveVolumes) {
        $composeArgs += "-v"
    }
    
    docker-compose @composeArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARNING] Some services might not have stopped cleanly" -ForegroundColor Yellow
    } else {
        Write-Host "All services have been stopped" -ForegroundColor Green
    }
}

# Show service status
function Get-ServiceStatus {
    Write-Host "`n=== Service Status ===" -ForegroundColor Cyan
    
    # Get all CaseStrainer containers
    $containers = docker ps -a --format '{{.Names}}' | Where-Object { $_ -match 'casestrainer-' }
    
    if (-not $containers) {
        Write-Host "No CaseStrainer containers are running" -ForegroundColor Yellow
    }
    else {
        # Get detailed container info
        $containerInfo = docker ps -a --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' | 
            Where-Object { $_ -match 'casestrainer-' }
    
        if ($containerInfo) {
            Write-Host "`nContainers:" -ForegroundColor Yellow
            $containerInfo | ForEach-Object {
                $name, $status, $ports = $_ -split '\t', 3
                $color = if ($status -match '^Up') { 'Green' } else { 'Red' }
                Write-Host "- $name" -ForegroundColor $color -NoNewline
                Write-Host " ($status)" -ForegroundColor Gray
                if ($ports) {
                    Write-Host "  Ports: $ports" -ForegroundColor DarkGray
                }
            }
        }
    }
    
    # Check required ports
    Write-Host "`nPort Check:" -ForegroundColor Yellow
    $listening = netstat -ano | Select-String "LISTENING"
    
    foreach ($port in $config.RequiredPorts) {
        $isListening = $listening -match ":$port\s"
        $status = if ($isListening) { "In use" } else { "Available" }
        $color = if ($isListening) { 'Yellow' } else { 'Green' }
        Write-Host "- Port $port`t$status" -ForegroundColor $color
    }
    
    # Show Nginx status if installed
    $nginxStatus = Get-NginxStatus
    if ($nginxStatus.IsInstalled) {
        Write-Host "`nNginx Status:" -ForegroundColor Yellow
        Write-Host "- Installed: $($nginxStatus.Version)" -ForegroundColor Cyan
        Write-Host "- Running: $($nginxStatus.IsRunning)" -ForegroundColor $(if ($nginxStatus.IsRunning) { 'Green' } else { 'Red' })
        Write-Host "- Config: $($nginxStatus.ConfigFile)" -ForegroundColor Cyan
    }
}

# Show container logs
function Show-Logs {
    [CmdletBinding()]
    param(
        [string[]]$Services = @()
    )
    
    if (-not $Services) {
        # Show all services if none specified
        # Default services to show logs for
    $Services = @('backend', 'frontend', 'nginx', 'redis', 'db')
    }
    
    Write-Host "`n=== Container Logs ===" -ForegroundColor Cyan
    
    foreach ($service in $Services) {
        # Try production naming first (casestrainer-service-prod)
        $containerName = "casestrainer-${service}-prod"
        
        # Check if container exists
        $exists = docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $containerName }
        
        # Fallback to dev naming if not found
        if (-not $exists) {
            $containerName = "casestrainer_${service}_1"
            $exists = docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $containerName }
        }
        
        if (-not $exists) {
            Write-Host "[WARNING] Container $containerName not found" -ForegroundColor Yellow
            continue
        }
        
        Write-Host "`n--- $service ---" -ForegroundColor Yellow
        docker logs --tail=50 $containerName 2>&1
    }
}

# Execute the main function with provided parameters
Start-CaseStrainer @PSBoundParameters
