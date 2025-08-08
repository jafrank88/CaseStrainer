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

# Start production environment
function Start-Production {
    [CmdletBinding()]
    param(
        [switch]$Build,
        [switch]$NoCache,
        [switch]$Force
    )
    
    Write-Host "`n=== Starting Production Environment ===" -ForegroundColor Cyan
    
    # Check for existing containers
    $containers = docker ps -a --format '{{.Names}}' | Where-Object { $_ -match 'casestrainer_' }
    
    if ($containers -and -not $Force) {
        Write-Host "[WARNING] Existing containers found. Use -Force to recreate them." -ForegroundColor Yellow
        return
    }
    
    # Build containers if requested
    if ($Build) {
        Write-Host "Building production containers..." -ForegroundColor Yellow
        if (-not (Start-DockerBuild -DockerComposeFile $config.DockerComposeFile -DockerComposeFile $config.DockerComposeProdFile -NoCache:$NoCache)) {
            throw "Failed to build production containers"
        }
    }
    
    # Start services
    Write-Host "Starting production services..." -ForegroundColor Yellow
    $composeArgs = @(
        "-f", $config.DockerComposeFile,
        "-f", $config.DockerComposeProdFile,
        "up", "-d"
    )
    
    if ($Force) {
        $composeArgs += "--force-recreate"
    }
    
    docker-compose @composeArgs
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start production services"
    }
    
    Write-Host "`nProduction environment is now running!" -ForegroundColor Green
    Write-Host "- Application: http://localhost" -ForegroundColor Cyan
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
    $containers = docker ps -a --format '{{.Names}}' | Where-Object { $_ -match 'casestrainer_' }
    
    if (-not $containers) {
        Write-Host "No CaseStrainer containers are running" -ForegroundColor Yellow
    }
    else {
        # Get detailed container info
        $containerInfo = docker ps -a --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' | 
            Where-Object { $_ -match 'casestrainer_' }
    
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
        $containerName = "casestrainer_${service}_1"
        
        # Check if container exists
        $exists = docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $containerName }
        
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
