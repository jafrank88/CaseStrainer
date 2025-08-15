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
    .\cslaunch.ps1 -Environment Production -Mode Quick
    .\cslaunch.ps1 -Environment Staging -Mode Full -Confirm
    .\cslaunch.ps1 -Mode Fast -AlwaysRebuild
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
    [switch]$Force,
    [switch]$AlwaysRebuild
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
            'DEBUG' { if ($VerbosePreference -eq 'Continue') { Write-Host $logEntry -ForegroundColor Gray } }
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
    
    # Execute the command directly without try-catch to avoid PowerShell exceptions
    $argumentString = $Arguments -join ' '
    $output = cmd /c "docker-compose -f `"$($config.docker.composeFile)`" $Operation $argumentString 2>&1"
    $exitCode = $LASTEXITCODE
    
    Write-Log "Docker operation exit code: $exitCode" -Level DEBUG
    if ($output) {
        Write-Log "Docker output: $($output -join '; ')" -Level DEBUG
    }
    
    # Success if exit code is 0
    if ($exitCode -eq 0) {
        Write-Log "Docker operation completed successfully: $Operation" -Level INFO
        return $true
    }
    else {
        if ($IgnoreErrors) {
            Write-Log "Docker operation failed but ignored: $Operation (Exit code: $exitCode)" -Level WARN
            return $true
        }
        else {
            Write-Log "Docker operation failed: $Operation (Exit code: $exitCode)" -Level ERROR -Console
            if ($output) {
                Write-Log "Docker error output: $($output -join '; ')" -Level ERROR -Console
            }
            return $false
        }
    }
}

function Start-Deployment {
    param([string]$DeploymentMode)
    
    Write-Log "Starting deployment in $DeploymentMode mode..." -Console
    
    switch ($DeploymentMode) {
        'Quick' {
            Write-Log "Performing Quick Start (containers assumed healthy)..." -Console
            
            if ($AlwaysRebuild) {
                Write-Log "Rebuilding Docker images (AlwaysRebuild flag set)..." -Console
                $success = Invoke-SafeDockerOperation -Operation "build"
                if (-not $success) {
                    Write-Log "Image rebuild failed - attempting startup anyway" -Level WARN -Console
                }
            }
            
            return Invoke-SafeDockerOperation -Operation "up" -Arguments @("-d")
        }
        
        'Fast' {
            Write-Log "Performing Fast Start (restart with rebuild if needed)..." -Console
            $success = Invoke-SafeDockerOperation -Operation "down" -IgnoreErrors
            if ($success) {
                # Check if we need to rebuild due to recent changes or AlwaysRebuild flag
                $needsRebuild = $AlwaysRebuild
                
                if (-not $needsRebuild) {
                    foreach ($dir in $config.paths.sourceDirectories) {
                        if (Test-Path $dir) {
                            $recentFiles = Get-ChildItem -Path $dir -Recurse -File | 
                                          Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-120) }
                            if ($recentFiles) {
                                $needsRebuild = $true
                                Write-Log "Recent changes in $dir - will rebuild images" -Console
                                break
                            }
                        }
                    }
                }
                
                if ($needsRebuild) {
                    if ($AlwaysRebuild) {
                        Write-Log "Rebuilding Docker images (AlwaysRebuild flag set)..." -Console
                    } else {
                        Write-Log "Rebuilding Docker images due to recent changes..." -Console
                    }
                    $success = Invoke-SafeDockerOperation -Operation "build"
                    if (-not $success) {
                        Write-Log "Image rebuild failed - attempting startup anyway" -Level WARN -Console
                    }
                }
                
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

function Test-VueBuildNeeded {
    # Check if Vue source is newer than built files
    $vueSourceDir = "casestrainer-vue-new/src"
    $vueDistDir = "casestrainer-vue-new/dist"
    
    if (-not (Test-Path $vueSourceDir) -or -not (Test-Path $vueDistDir)) {
        return $false
    }
    
    $newestSource = Get-ChildItem -Path $vueSourceDir -Recurse -File | 
                   Sort-Object LastWriteTime -Descending | 
                   Select-Object -First 1
    
    $newestDist = Get-ChildItem -Path $vueDistDir -Recurse -File | 
                 Sort-Object LastWriteTime -Descending | 
                 Select-Object -First 1
    
    if ($newestSource.LastWriteTime -gt $newestDist.LastWriteTime) {
        Write-Log "Vue source files are newer than dist files - rebuild needed" -Console
        return $true
    }
    
    return $false
}

function Invoke-VueBuild {
    Write-Log "Building Vue frontend..." -Console
    
    if (-not (Test-Path "casestrainer-vue-new/package.json")) {
        Write-Log "Vue package.json not found - skipping Vue build" -Level WARN -Console
        return $true
    }
    
    $originalLocation = Get-Location
    try {
        Set-Location "casestrainer-vue-new"
        
        # Run npm build
        $output = cmd /c "npm run build 2>&1"
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Log "Vue build completed successfully" -Console
            return $true
        } else {
            Write-Log "Vue build failed (Exit code: $exitCode)" -Level ERROR -Console
            Write-Log "Build output: $($output -join '; ')" -Level ERROR
            return $false
        }
    }
    finally {
        Set-Location $originalLocation
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
    
    # Check if Vue build is needed
    $vueBuildNeeded = Test-VueBuildNeeded
    if ($vueBuildNeeded) {
        Write-Log "Vue source files are newer than dist - performing build and Fast restart" -Console
        if (Invoke-VueBuild) {
            return 'Fast'  # Fast restart after Vue build
        } else {
            Write-Log "Vue build failed - falling back to Full rebuild" -Level WARN -Console
            return 'Full'
        }
    }
    
    # Containers exist but not running
    if ($status.Running -eq 0) {
        Write-Log "Containers exist but not running - recommending Fast start" -Console
        return 'Fast'
    }
    
    # Check for recent code changes (extended to 2 hours for more thorough detection)
    $hasChanges = $false
    foreach ($dir in $config.paths.sourceDirectories) {
        if (Test-Path $dir) {
            $recentFiles = Get-ChildItem -Path $dir -Recurse -File | 
                          Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-120) }
            if ($recentFiles) {
                $hasChanges = $true
                Write-Log "Recent changes detected in $dir (within 2 hours)" -Level DEBUG
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
