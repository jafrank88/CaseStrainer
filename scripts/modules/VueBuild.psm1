# VueBuild.psm1 - Vue.js build and deployment functions

function Test-VueBuildNeeded {
    <#
    .SYNOPSIS
    Check if Vue build is needed by comparing source files with dist files
    
    .DESCRIPTION
    Compares timestamps of Vue source files (.vue, .js, .ts, .css) with dist files
    Returns true if source files are newer than dist files or if dist doesn't exist
    
    .OUTPUTS
    Boolean - $true if build needed, $false otherwise
    #>
    
    [CmdletBinding()]
    param()
    
    try {
        $vueDir = Join-Path $PSScriptRoot "..\..\casestrainer-vue-new"
        $sourceDir = Join-Path $vueDir "src"
        $distDir = Join-Path $vueDir "dist\assets"
        
        # Check if dist directory exists
        if (-not (Test-Path $distDir)) {
            Write-Verbose "Dist directory not found - build needed"
            return $true
        }
        
        # Check if dist has files
        $distFiles = Get-ChildItem $distDir -File -ErrorAction SilentlyContinue
        if ($distFiles.Count -eq 0) {
            Write-Verbose "Dist directory empty - build needed"
            return $true
        }
        
        # Check if source directory exists
        if (-not (Test-Path $sourceDir)) {
            Write-Warning "Source directory not found at: $sourceDir"
            return $false
        }
        
        # Get latest source file time
        $sourceFiles = Get-ChildItem $sourceDir -Recurse -File | Where-Object {
            $_.Extension -in @('.vue', '.js', '.ts', '.css', '.html', '.json')
        }
        
        if ($sourceFiles.Count -eq 0) {
            Write-Warning "No source files found"
            return $false
        }
        
        $latestSourceTime = ($sourceFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
        $latestDistTime = ($distFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
        
        # Compare timestamps
        if ($latestSourceTime -gt $latestDistTime) {
            Write-Verbose "Source files newer than dist - build needed"
            Write-Verbose "  Source: $latestSourceTime"
            Write-Verbose "  Dist: $latestDistTime"
            return $true
        }
        
        Write-Verbose "Dist files up to date - no build needed"
        return $false
        
    } catch {
        Write-Warning "Error checking Vue build status: $($_.Exception.Message)"
        return $true  # Build on error to be safe
    }
}

function Start-VueBuild {
    <#
    .SYNOPSIS
    Build the Vue.js application
    
    .DESCRIPTION
    Runs npm run build in the Vue directory
    Handles errors and provides clear output
    
    .OUTPUTS
    Boolean - $true if build successful, $false otherwise
    #>
    
    [CmdletBinding()]
    param()
    
    try {
        $vueDir = Join-Path $PSScriptRoot "..\..\casestrainer-vue-new"
        
        if (-not (Test-Path $vueDir)) {
            Write-Error "Vue directory not found at: $vueDir"
            return $false
        }
        
        Write-Host "Building Vue application..." -ForegroundColor Cyan
        
        Push-Location $vueDir
        try {
            # Check if node_modules exists
            if (-not (Test-Path "node_modules")) {
                Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
                npm install
                if ($LASTEXITCODE -ne 0) {
                    throw "npm install failed with exit code: $LASTEXITCODE"
                }
            }
            
            # Run build
            npm run build
            if ($LASTEXITCODE -ne 0) {
                throw "npm build failed with exit code: $LASTEXITCODE"
            }
            
            Write-Host "Vue build completed successfully!" -ForegroundColor Green
            return $true
            
        } finally {
            Pop-Location
        }
        
    } catch {
        Write-Error "Vue build failed: $($_.Exception.Message)"
        return $false
    }
}

function Copy-VueDistToStatic {
    <#
    .SYNOPSIS
    Copy Vue dist files to static directory
    
    .DESCRIPTION
    Copies built Vue files from dist/ to static/ directory
    Used by both frontend and backend containers
    
    .OUTPUTS
    Boolean - $true if copy successful, $false otherwise
    #>
    
    [CmdletBinding()]
    param()
    
    try {
        $vueDir = Join-Path $PSScriptRoot "..\..\casestrainer-vue-new"
        $staticDir = Join-Path $PSScriptRoot "..\..\static"
        
        $distIndexPath = Join-Path $vueDir "dist\index.html"
        $distAssetsPath = Join-Path $vueDir "dist\assets"
        $staticIndexPath = Join-Path $staticDir "index.html"
        $staticAssetsPath = Join-Path $staticDir "assets"
        
        # Check if dist files exist
        if (-not (Test-Path $distIndexPath)) {
            Write-Error "Dist index.html not found at: $distIndexPath"
            return $false
        }
        
        if (-not (Test-Path $distAssetsPath)) {
            Write-Error "Dist assets not found at: $distAssetsPath"
            return $false
        }
        
        Write-Host "Copying Vue files to static directory..." -ForegroundColor Cyan
        
        # Create static directory if it doesn't exist
        if (-not (Test-Path $staticDir)) {
            New-Item -ItemType Directory -Path $staticDir -Force | Out-Null
        }
        
        # Copy index.html
        Copy-Item $distIndexPath $staticIndexPath -Force
        Write-Verbose "Copied index.html"
        
        # Create assets directory if it doesn't exist
        if (-not (Test-Path $staticAssetsPath)) {
            New-Item -ItemType Directory -Path $staticAssetsPath -Force | Out-Null
        }
        
        # Copy assets
        Copy-Item "$distAssetsPath\*" $staticAssetsPath -Force -Recurse
        Write-Verbose "Copied assets"
        
        Write-Host "Static files updated successfully!" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Error "Failed to copy dist files: $($_.Exception.Message)"
        return $false
    }
}

function Update-VueFrontend {
    <#
    .SYNOPSIS
    Complete Vue frontend update workflow
    
    .DESCRIPTION
    Performs complete frontend update:
    1. Checks if build is needed
    2. Builds Vue if needed
    3. Copies to static directory
    4. Restarts containers
    
    .PARAMETER Force
    Force rebuild even if not needed
    
    .PARAMETER SkipContainerRestart
    Skip restarting containers (useful for testing)
    
    .OUTPUTS
    Boolean - $true if update successful, $false otherwise
    #>
    
    [CmdletBinding()]
    param(
        [switch]$Force,
        [switch]$SkipContainerRestart
    )
    
    try {
        Write-Host "`n=== Vue Frontend Update ===" -ForegroundColor Cyan
        
        # Check if build is needed
        $buildNeeded = $Force -or (Test-VueBuildNeeded)
        
        if (-not $buildNeeded) {
            Write-Host "Vue build is up to date - no rebuild needed" -ForegroundColor Green
            return $true
        }
        
        # Build Vue
        Write-Host "Step 1/3: Building Vue application..." -ForegroundColor Yellow
        if (-not (Start-VueBuild)) {
            Write-Error "Vue build failed"
            return $false
        }
        
        # Copy to static
        Write-Host "Step 2/3: Copying files to static directory..." -ForegroundColor Yellow
        if (-not (Copy-VueDistToStatic)) {
            Write-Error "Failed to copy files to static"
            return $false
        }
        
        # Restart containers
        if (-not $SkipContainerRestart) {
            Write-Host "Step 3/3: Recreating containers to refresh bind mounts..." -ForegroundColor Yellow
            
            # Check if Docker is available
            $dockerVersion = docker --version 2>$null
            if (-not $dockerVersion) {
                Write-Warning "Docker not available - skipping container restart"
                return $true
            }
            
            # Use docker compose up --force-recreate to refresh bind mounts (Windows issue)
            # docker restart doesn't refresh bind mounts on Windows
            docker compose -f docker-compose.prod.yml up -d --force-recreate backend frontend-prod 2>$null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Containers recreated successfully!" -ForegroundColor Green
            } else {
                Write-Warning "Container recreation had issues, but continuing..."
            }
        } else {
            Write-Host "Skipping container restart (as requested)" -ForegroundColor Gray
        }
        
        Write-Host "`nVue frontend update completed successfully!" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Error "Vue frontend update failed: $($_.Exception.Message)"
        return $false
    }
}

# Export functions
Export-ModuleMember -Function @(
    'Test-VueBuildNeeded',
    'Start-VueBuild',
    'Copy-VueDistToStatic',
    'Update-VueFrontend'
)
