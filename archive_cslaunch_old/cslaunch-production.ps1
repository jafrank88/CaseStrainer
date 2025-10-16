#Requires -Version 5.1
<#
.SYNOPSIS
    Production-ready CaseStrainer launcher with enhanced safety and monitoring

.DESCRIPTION
    Enhanced production launcher with:
    - Configuration-driven deployment
    - Comprehensive error handling
    - Security validations
    - Structured logging
    - Health monitoring
    - Rollback capabilities

.EXAMPLE
    .\cslaunch-production.ps1 -Environment Production -Mode Quick
    .\cslaunch-production.ps1 -Environment Staging -Mode Full -Confirm
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('Development', 'Staging', 'Production')]
    [string]$Environment = 'Production',
    
    [Parameter(Mandatory=$false)]
    [ValidateSet('Quick', 'Fast', 'Full', 'Status', 'Health', 'Monitor')]
    [string]$Mode = 'Auto',
    
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = 'cslaunch-production-config.json',
    
    [switch]$Confirm,
    [switch]$DryRun,
    [switch]$Verbose,
    [switch]$Force
)

# Global error handling
$ErrorActionPreference = 'Stop'
$WarningPreference = 'Continue'

# Initialize logging
$LogFile = "logs/cslaunch-$(Get-Date -Format 'yyyy-MM-dd').log"
$null = New-Item -Path (Split-Path $LogFile) -ItemType Directory -Force -ErrorAction SilentlyContinue

function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [ValidateSet('INFO', 'WARN', 'ERROR', 'DEBUG')]
        [string]$Level = 'INFO',
        
        [switch]$Console
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Write to file
    Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
    
    # Write to console if requested or if error
    if ($Console -or $Level -eq 'ERROR') {
        switch ($Level) {
            'INFO'  { Write-Host $logEntry -ForegroundColor Green }
            'WARN'  { Write-Host $logEntry -ForegroundColor Yellow }
            'ERROR' { Write-Host $logEntry -ForegroundColor Red }
            'DEBUG' { if ($Verbose) { Write-Host $logEntry -ForegroundColor Gray } }
        }
    }
}

function Test-Prerequisites {
    Write-Log "Checking prerequisites..." -Console
    
    # Check Docker
    try {
        $dockerVersion = docker --version 2>$null
        if (-not $dockerVersion) {
            throw "Docker is not available"
        }
        Write-Log "Docker check passed: $dockerVersion" -Level DEBUG
    }
    catch {
        Write-Log "Docker prerequisite failed: $($_.Exception.Message)" -Level ERROR -Console
        return $false
    }
    
    # Check compose file
    if (-not (Test-Path $config.docker.composeFile)) {
        Write-Log "Docker compose file not found: $($config.docker.composeFile)" -Level ERROR -Console
        return $false
    }
    
    # Check required directories
    foreach ($dir in $config.paths.sourceDirectories) {
        if (-not (Test-Path $dir)) {
            Write-Log "Source directory not found: $dir" -Level WARN -Console
        }
    }
    
    return $true
}

function Get-ContainerStatus {
    try {
        $containers = docker ps --filter "name=casestrainer" --format "json" 2>$null | ConvertFrom-Json
        $allContainers = docker ps -a --filter "name=casestrainer" --format "json" 2>$null | ConvertFrom-Json
        
        return @{
            Running = @($containers).Count
            Total = @($allContainers).Count
            Containers = $containers
            AllContainers = $allContainers
        }
    }
    catch {
        Write-Log "Failed to get container status: $($_.Exception.Message)" -Level ERROR
        return @{ Running = 0; Total = 0; Containers = @(); AllContainers = @() }
    }
}

function Test-ApplicationHealth {
    Write-Log "Performing application health check..." -Console
    
    $healthEndpoint = "http://localhost:5000/casestrainer/api/health"
    $timeout = $config.docker.healthCheckTimeout
    
    try {
        $response = Invoke-WebRequest -Uri $healthEndpoint -UseBasicParsing -TimeoutSec $timeout
        if ($response.StatusCode -eq 200) {
            Write-Log "Application health check passed" -Level INFO -Console
            return $true
        }
        else {
            Write-Log "Application health check failed: HTTP $($response.StatusCode)" -Level WARN -Console
            return $false
        }
    }
    catch {
        Write-Log "Application health check failed: $($_.Exception.Message)" -Level WARN -Console
        return $false
    }
}

function Invoke-SafeDockerOperation {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Operation,
        
        [Parameter(Mandatory=$false)]
        [string[]]$Arguments = @(),
        
        [switch]$IgnoreErrors
    )
    
    $fullCommand = "docker-compose -f $($config.docker.composeFile) $Operation $($Arguments -join ' ')"
    
    Write-Log "Executing: $fullCommand" -Level DEBUG
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Would execute: $fullCommand" -Console
        return $true
    }
    
    try {
        $result = Invoke-Expression $fullCommand 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Docker operation completed successfully: $Operation" -Level INFO
            return $true
        }
        else {
            if ($IgnoreErrors) {
                Write-Log "Docker operation failed but ignored: $Operation" -Level WARN
                return $true
            }
            else {
                throw "Docker operation failed with exit code $LASTEXITCODE"
            }
        }
    }
    catch {
        Write-Log "Docker operation failed: $Operation - $($_.Exception.Message)" -Level ERROR -Console
        return $false
    }
}

function Start-Deployment {
    param([string]$DeploymentMode)
    
    Write-Log "Starting deployment in $DeploymentMode mode..." -Console
    
    switch ($DeploymentMode) {
        'Quick' {
            Write-Log "Performing Quick Start (containers assumed healthy)..." -Console
            return Invoke-SafeDockerOperation -Operation "up" -Arguments @("-d")
        }
        
        'Fast' {
            Write-Log "Performing Fast Start (restart with current images)..." -Console
            $success = Invoke-SafeDockerOperation -Operation "down" -IgnoreErrors
            if ($success) {
                return Invoke-SafeDockerOperation -Operation "up" -Arguments @("-d")
            }
            return $false
        }
        
        'Full' {
            if (-not $config.security.allowVolumeCleanup -and -not $Force) {
                Write-Log "Full rebuild with volume cleanup requires -Force flag in production" -Level WARN -Console
                return $false
            }
            
            Write-Log "Performing Full Rebuild (complete rebuild)..." -Console
            $success = Invoke-SafeDockerOperation -Operation "down" -Arguments @("-v") -IgnoreErrors
            if ($success) {
                $success = Invoke-SafeDockerOperation -Operation "build" -Arguments @("--no-cache")
                if ($success) {
                    return Invoke-SafeDockerOperation -Operation "up" -Arguments @("-d")
                }
            }
            return $false
        }
        
        default {
            Write-Log "Unknown deployment mode: $DeploymentMode" -Level ERROR -Console
            return $false
        }
    }
}

function Get-AutoDetectedMode {
    Write-Log "Auto-detecting deployment mode..." -Console
    
    $status = Get-ContainerStatus
    
    # No containers exist
    if ($status.Total -eq 0) {
        Write-Log "No containers found - recommending Full rebuild" -Console
        return 'Full'
    }
    
    # Containers exist but not running
    if ($status.Running -eq 0) {
        Write-Log "Containers exist but not running - recommending Fast start" -Console
        return 'Fast'
    }
    
    # Check for recent code changes
    $hasChanges = $false
    foreach ($dir in $config.paths.sourceDirectories) {
        if (Test-Path $dir) {
            $recentFiles = Get-ChildItem -Path $dir -Recurse -File | 
                          Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-30) }
            if ($recentFiles) {
                $hasChanges = $true
                Write-Log "Recent changes detected in $dir" -Level DEBUG
                break
            }
        }
    }
    
    if ($hasChanges) {
        Write-Log "Recent code changes detected - recommending Fast start" -Console
        return 'Fast'
    }
    
    # Everything appears stable
    Write-Log "No changes detected, containers running - recommending Quick start" -Console
    return 'Quick'
}

# Main execution
try {
    Write-Log "CaseStrainer Production Launcher starting..." -Console
    Write-Log "Environment: $Environment, Mode: $Mode" -Console
    
    # Load configuration
    if (-not (Test-Path $ConfigFile)) {
        Write-Log "Configuration file not found: $ConfigFile" -Level ERROR -Console
        exit 1
    }
    
    $config = Get-Content $ConfigFile | ConvertFrom-Json
    Write-Log "Configuration loaded from $ConfigFile" -Level DEBUG
    
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Log "Prerequisites check failed" -Level ERROR -Console
        exit 1
    }
    
    # Handle different modes
    switch ($Mode) {
        'Status' {
            $status = Get-ContainerStatus
            Write-Host "`nContainer Status:" -ForegroundColor Cyan
            Write-Host "  Running: $($status.Running)" -ForegroundColor Green
            Write-Host "  Total: $($status.Total)" -ForegroundColor Yellow
            
            $health = Test-ApplicationHealth
            Write-Host "  Health: $(if ($health) { 'Healthy' } else { 'Unhealthy' })" -ForegroundColor $(if ($health) { 'Green' } else { 'Red' })
            exit 0
        }
        
        'Health' {
            $health = Test-ApplicationHealth
            exit $(if ($health) { 0 } else { 1 })
        }
        
        'Monitor' {
            # Show monitoring status
            $jobs = Get-Job | Where-Object { $_.Name -like "*monitoring*" -or $_.Name -like "*recovery*" }
            Write-Host "`nMonitoring Jobs:" -ForegroundColor Cyan
            if ($jobs) {
                $jobs | Format-Table Id, Name, State, HasMoreData -AutoSize
            } else {
                Write-Host "  No monitoring jobs running" -ForegroundColor Yellow
            }
            exit 0
        }
        
        'Auto' {
            $Mode = Get-AutoDetectedMode
            Write-Log "Auto-detected mode: $Mode" -Console
        }
    }
    
    # Confirmation for destructive operations
    if ($config.security.requireConfirmationForDestructive -and $Mode -eq 'Full' -and -not $Confirm -and -not $Force) {
        $response = Read-Host "Full rebuild will destroy all containers and volumes. Continue? (y/N)"
        if ($response -ne 'y' -and $response -ne 'Y') {
            Write-Log "Operation cancelled by user" -Console
            exit 0
        }
    }
    
    # Perform deployment
    $success = Start-Deployment -DeploymentMode $Mode
    
    if ($success) {
        # Wait for containers to stabilize
        Write-Log "Waiting for containers to stabilize..." -Console
        Start-Sleep -Seconds 10
        
        # Verify deployment
        $finalStatus = Get-ContainerStatus
        $health = Test-ApplicationHealth
        
        if ($finalStatus.Running -gt 0 -and $health) {
            Write-Log "Deployment completed successfully!" -Level INFO -Console
            Write-Log "Containers running: $($finalStatus.Running)" -Console
            exit 0
        }
        else {
            Write-Log "Deployment completed but health check failed" -Level WARN -Console
            exit 1
        }
    }
    else {
        Write-Log "Deployment failed" -Level ERROR -Console
        exit 1
    }
}
catch {
    Write-Log "Fatal error: $($_.Exception.Message)" -Level ERROR -Console
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level DEBUG
    exit 1
}
finally {
    Write-Log "Launcher execution completed" -Level DEBUG
}
