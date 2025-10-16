# Deployment.psm1 - Deployment strategy functions

# Import required modules
Import-Module (Join-Path $PSScriptRoot "VueBuild.psm1") -Force
Import-Module (Join-Path $PSScriptRoot "HealthCheck.psm1") -Force

function Start-QuickDeployment {
    <#
    .SYNOPSIS
    Quick deployment - no code changes detected
    
    .DESCRIPTION
    Minimal deployment:
    - Checks health
    - Restarts containers if needed
    - No rebuilds
    #>
    
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Quick Deployment ===" -ForegroundColor Green
    Write-Host "No code changes detected - performing minimal restart" -ForegroundColor Gray
    
    try {
        # Check if containers are running
        if (Test-DockerHealth) {
            $backendRunning = docker ps --format '{{.Names}}' | Where-Object { $_ -eq 'casestrainer-backend-prod' }
            
            if ($backendRunning) {
                Write-Host "Containers already running - no action needed" -ForegroundColor Green
                return $true
            }
        }
        
        # Start containers
        Write-Host "Starting containers..." -ForegroundColor Cyan
        docker compose -f docker-compose.prod.yml up -d
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to start containers"
        }
        
        Write-Host "Quick deployment completed!" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Error "Quick deployment failed: $($_.Exception.Message)"
        return $false
    }
}

function Start-FastDeployment {
    <#
    .SYNOPSIS
    Fast deployment - code changes detected
    
    .DESCRIPTION
    Restart containers with latest code:
    - Stop containers
    - Start containers (picks up bind mount changes)
    - No image rebuild
    #>
    
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Fast Deployment ===" -ForegroundColor Cyan
    Write-Host "Code changes detected - restarting containers" -ForegroundColor Gray
    
    try {
        # Stop containers
        Write-Host "Stopping containers..." -ForegroundColor Yellow
        docker compose -f docker-compose.prod.yml down
        
        # Start containers
        Write-Host "Starting containers with latest code..." -ForegroundColor Cyan
        docker compose -f docker-compose.prod.yml up -d
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to start containers"
        }
        
        Write-Host "Fast deployment completed!" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Error "Fast deployment failed: $($_.Exception.Message)"
        return $false
    }
}

function Start-FullDeployment {
    <#
    .SYNOPSIS
    Full deployment - rebuild everything
    
    .DESCRIPTION
    Complete rebuild:
    - Stop containers
    - Rebuild images
    - Start containers
    #>
    
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Full Deployment ===" -ForegroundColor Yellow
    Write-Host "Dependency changes detected - rebuilding everything" -ForegroundColor Gray
    
    try {
        # Stop containers and remove volumes
        Write-Host "Stopping containers..." -ForegroundColor Yellow
        docker compose -f docker-compose.prod.yml down --remove-orphans
        
        # Remove any lingering containers
        Write-Host "Cleaning up orphaned containers..." -ForegroundColor Yellow
        $orphans = docker ps -a --filter "name=casestrainer-" --format "{{.Names}}"
        if ($orphans) {
            $orphans | ForEach-Object { docker rm -f $_ 2>$null }
        }
        
        # Rebuild images
        Write-Host "Rebuilding images..." -ForegroundColor Yellow
        docker compose -f docker-compose.prod.yml build --no-cache
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to build images"
        }
        
        # Start containers
        Write-Host "Starting containers..." -ForegroundColor Cyan
        docker compose -f docker-compose.prod.yml up -d
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to start containers"
        }
        
        Write-Host "Full deployment completed!" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Error "Full deployment failed: $($_.Exception.Message)"
        return $false
    }
}

function Start-FrontendDeployment {
    <#
    .SYNOPSIS
    Frontend-only deployment
    
    .DESCRIPTION
    Deploy frontend changes:
    - Build Vue if needed
    - Copy to static
    - Restart frontend and backend containers
    
    .PARAMETER Force
    Force rebuild even if not needed
    #>
    
    [CmdletBinding()]
    param(
        [switch]$Force
    )
    
    Write-Host "`n=== Frontend Deployment ===" -ForegroundColor Magenta
    
    try {
        # Update Vue frontend
        $result = Update-VueFrontend -Force:$Force
        
        if (-not $result) {
            throw "Vue frontend update failed"
        }
        
        Write-Host "Frontend deployment completed!" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Error "Frontend deployment failed: $($_.Exception.Message)"
        return $false
    }
}

function Start-BackendDeployment {
    <#
    .SYNOPSIS
    Backend-only deployment
    
    .DESCRIPTION
    Deploy backend changes:
    - Clear Python cache
    - Restart backend containers
    
    .PARAMETER Force
    Force restart even if not needed
    #>
    
    [CmdletBinding()]
    param(
        [switch]$Force
    )
    
    Write-Host "`n=== Backend Deployment ===" -ForegroundColor Yellow
    
    try {
        # Clear Python cache
        Write-Host "Clearing Python cache..." -ForegroundColor Cyan
        $srcDir = Join-Path $PSScriptRoot "..\..\src"
        if (Test-Path $srcDir) {
            Get-ChildItem $srcDir -Recurse -Filter "*.pyc" | Remove-Item -Force
            Get-ChildItem $srcDir -Recurse -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force
            Write-Verbose "Python cache cleared"
        }
        
        # Check if backend container exists
        $backendExists = docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq 'casestrainer-backend-prod' }
        
        if ($backendExists) {
            # Container exists, just restart it
            Write-Host "Restarting backend container..." -ForegroundColor Cyan
            docker restart casestrainer-backend-prod
            
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to restart backend"
            }
            
            # Also restart workers
            docker restart casestrainer-rqworker1-prod casestrainer-rqworker2-prod casestrainer-rqworker3-prod 2>$null
        }
        else {
            # Container doesn't exist, start it (no rebuild needed due to bind mounts)
            Write-Host "Backend container doesn't exist - starting it..." -ForegroundColor Cyan
            docker compose -f docker-compose.prod.yml up -d backend rqworker1 rqworker2 rqworker3
            
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to start backend"
            }
        }
        
        Write-Host "Backend deployment completed!" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Error "Backend deployment failed: $($_.Exception.Message)"
        return $false
    }
}

function Start-SmartDeployment {
    <#
    .SYNOPSIS
    Smart deployment - auto-detect what needs updating
    
    .DESCRIPTION
    Analyzes changes and chooses optimal deployment strategy:
    - Frontend changes → Frontend deployment
    - Backend changes → Backend deployment  
    - Dependency changes → Full deployment
    - No changes → Quick deployment
    
    .OUTPUTS
    Boolean - $true if successful
    #>
    
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Smart Deployment ===" -ForegroundColor Cyan
    Write-Host "Analyzing changes to determine optimal strategy..." -ForegroundColor Gray
    
    try {
        # Import file monitoring module
        Import-Module (Join-Path $PSScriptRoot "FileMonitoring.psm1") -Force
        
        # Get changed files
        $changes = Get-ChangedFiles
        
        # Determine strategy
        if ($changes.Dependencies.Count -gt 0) {
            Write-Host "Dependency changes detected:" -ForegroundColor Yellow
            $changes.Dependencies | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
            return Start-FullDeployment
        }
        elseif ($changes.Frontend.Count -gt 0) {
            Write-Host "Frontend changes detected:" -ForegroundColor Magenta
            $changes.Frontend | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
            return Start-FrontendDeployment
        }
        elseif ($changes.Backend.Count -gt 0) {
            Write-Host "Backend changes detected:" -ForegroundColor Yellow
            $changes.Backend | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
            return Start-BackendDeployment
        }
        else {
            Write-Host "No code changes detected" -ForegroundColor Green
            
            # Only check if dist exists (don't do timestamp comparison)
            # Timestamp comparison is too aggressive and triggers on config file touches
            $distDir = Join-Path $PSScriptRoot "..\..\casestrainer-vue-new\dist"
            if (-not (Test-Path $distDir)) {
                Write-Host "Vue dist files missing - rebuilding..." -ForegroundColor Yellow
                return Start-FrontendDeployment
            }
            
            Write-Host "Using existing build - no rebuild needed" -ForegroundColor Green
            return Start-QuickDeployment
        }
        
    } catch {
        Write-Error "Smart deployment failed: $($_.Exception.Message)"
        return $false
    }
}

# Export functions
Export-ModuleMember -Function @(
    'Start-QuickDeployment',
    'Start-FastDeployment',
    'Start-FullDeployment',
    'Start-FrontendDeployment',
    'Start-BackendDeployment',
    'Start-SmartDeployment'
)
