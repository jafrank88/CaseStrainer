# Smart CaseStrainer Launcher - Automated & Efficient
# Automatically selects the best startup option based on current state

param(
    [switch]$ForceRebuild,
    [switch]$QuickStart,
    [switch]$SkipValidation,
    [switch]$AutoMode,
    [string]$Mode = "Auto"
)

# Import the original cslaunch functions
. .\cslaunch.ps1

function Test-ApplicationState {
    """Analyze current application state to determine best startup strategy."""
    
    $state = @{
        DockerRunning = $false
        ContainersRunning = $false
        CodeChanged = $false
        FrontendChanged = $false
        CacheDirty = $false
        RecommendedAction = "unknown"
    }
    
    Write-Host "🔍 Analyzing current application state..." -ForegroundColor Cyan
    
    # Check if Docker is running
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            $state.DockerRunning = $true
            Write-Host "✅ Docker is running" -ForegroundColor Green
        } else {
            Write-Host "❌ Docker is not running" -ForegroundColor Red
            $state.RecommendedAction = "start_docker"
            return $state
        }
    } catch {
        Write-Host "❌ Docker is not accessible" -ForegroundColor Red
        $state.RecommendedAction = "start_docker"
        return $state
    }
    
    # Check if containers are running
    try {
        $containers = docker ps --filter "name=casestrainer" --format "{{.Names}}" 2>$null
        if ($containers) {
            $state.ContainersRunning = $true
            Write-Host "✅ Containers are running" -ForegroundColor Green
        } else {
            Write-Host "ℹ️  No containers running" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "ℹ️  Could not check container status" -ForegroundColor Yellow
    }
    
    # Check for code changes (simplified)
    try {
        $lastGitCommit = git log -1 --format="%H" 2>$null
        $lastBuildTime = Get-ChildItem "docker-compose.prod.yml" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty LastWriteTime
        $timeSinceBuild = (Get-Date) - $lastBuildTime
        
        if ($timeSinceBuild.TotalMinutes -gt 30) {
            $state.CodeChanged = $true
            Write-Host "ℹ️  Code may have changed (build was $([math]::Round($timeSinceBuild.TotalMinutes)) minutes ago)" -ForegroundColor Yellow
        } else {
            Write-Host "✅ Code is recent" -ForegroundColor Green
        }
    } catch {
        Write-Host "ℹ️  Could not check code changes" -ForegroundColor Yellow
    }
    
    # Check frontend changes
    try {
        $vueFiles = Get-ChildItem -Path "casestrainer-vue-new" -Recurse -Include "*.vue", "*.js", "*.css" -ErrorAction SilentlyContinue | 
                   Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-30) }
        if ($vueFiles) {
            $state.FrontendChanged = $true
            Write-Host "ℹ️  Frontend files have changed recently" -ForegroundColor Yellow
        } else {
            Write-Host "✅ Frontend is up to date" -ForegroundColor Green
        }
    } catch {
        Write-Host "ℹ️  Could not check frontend changes" -ForegroundColor Yellow
    }
    
    # Determine recommended action
    if (-not $state.DockerRunning) {
        $state.RecommendedAction = "start_docker"
    } elseif (-not $state.ContainersRunning) {
        if ($state.CodeChanged -or $state.FrontendChanged) {
            $state.RecommendedAction = "fast_start"  # Option 2
        } else {
            $state.RecommendedAction = "quick_start"  # Option 1
        }
    } elseif ($state.CodeChanged -or $state.FrontendChanged) {
        $state.RecommendedAction = "fast_start"  # Option 2
    } else {
        $state.RecommendedAction = "quick_start"  # Option 1
    }
    
    return $state
}

function Start-SmartLaunch {
    """Smart launcher that automatically selects the best startup option."""
    
    Write-Host "🚀 Smart CaseStrainer Launcher" -ForegroundColor Cyan
    Write-Host "Automatically selecting the best startup option..." -ForegroundColor Gray
    Write-Host ""
    
    # Analyze current state
    $state = Test-ApplicationState
    
    Write-Host ""
    Write-Host "📊 Analysis Results:" -ForegroundColor Cyan
    Write-Host "  Docker Running: $($state.DockerRunning)" -ForegroundColor $(if($state.DockerRunning){"Green"}else{"Red"})
    Write-Host "  Containers Running: $($state.ContainersRunning)" -ForegroundColor $(if($state.ContainersRunning){"Green"}else{"Yellow"})
    Write-Host "  Code Changed: $($state.CodeChanged)" -ForegroundColor $(if($state.CodeChanged){"Yellow"}else{"Green"})
    Write-Host "  Frontend Changed: $($state.FrontendChanged)" -ForegroundColor $(if($state.FrontendChanged){"Yellow"}else{"Green"})
    Write-Host ""
    
    # Determine action based on state
    switch ($state.RecommendedAction) {
        "start_docker" {
            Write-Host "🎯 Recommended Action: Start Docker Desktop" -ForegroundColor Red
            Write-Host "Please start Docker Desktop manually and run this script again." -ForegroundColor Yellow
            Write-Host "Or use: .\cslaunch.ps1 -Mode Production" -ForegroundColor Gray
            exit 1
        }
        "quick_start" {
            Write-Host "🎯 Recommended Action: Quick Start (Option 1)" -ForegroundColor Green
            Write-Host "  - Fastest startup, minimal checks" -ForegroundColor Gray
            Write-Host "  - Use when everything is already set up" -ForegroundColor Gray
            Write-Host ""
            
            if ($AutoMode) {
                Write-Host "🔄 Auto-executing Quick Start..." -ForegroundColor Green
                Start-QuickProduction
            } else {
                $response = Read-Host "Execute Quick Start? (Y/n)"
                if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
                    Start-QuickProduction
                } else {
                    Write-Host "Cancelled." -ForegroundColor Yellow
                    exit 0
                }
            }
        }
        "fast_start" {
            Write-Host "🎯 Recommended Action: Fast Start (Option 2)" -ForegroundColor Cyan
            Write-Host "  - Restart with latest code" -ForegroundColor Gray
            Write-Host "  - Rebuild frontend if needed" -ForegroundColor Gray
            Write-Host ""
            
            if ($AutoMode) {
                Write-Host "🔄 Auto-executing Fast Start..." -ForegroundColor Green
                Start-FastProduction
            } else {
                $response = Read-Host "Execute Fast Start? (Y/n)"
                if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
                    Start-FastProduction
                } else {
                    Write-Host "Cancelled." -ForegroundColor Yellow
                    exit 0
                }
            }
        }
        "full_rebuild" {
            Write-Host "🎯 Recommended Action: Full Rebuild (Option 3)" -ForegroundColor Yellow
            Write-Host "  - Complete rebuild, use when needed" -ForegroundColor Gray
            Write-Host "  - Takes longer but ensures clean state" -ForegroundColor Gray
            Write-Host ""
            
            if ($AutoMode) {
                Write-Host "🔄 Auto-executing Full Rebuild..." -ForegroundColor Green
                Start-FullRebuild
            } else {
                $response = Read-Host "Execute Full Rebuild? (Y/n)"
                if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
                    Start-FullRebuild
                } else {
                    Write-Host "Cancelled." -ForegroundColor Yellow
                    exit 0
                }
            }
        }
    }
}

function Start-QuickProduction {
    """Execute Quick Production Start (Option 1)."""
    Write-Host "🚀 Starting Quick Production Start..." -ForegroundColor Green
    
    # Set quick start flags
    $script:QuickStart = $true
    $script:SkipVueBuild = $true
    
    try {
        # Call the original Start-DockerProduction function
        Start-DockerProduction -NoValidation:$true
        
        Write-Host "✅ Quick Production Start completed successfully!" -ForegroundColor Green
        Write-Host "🌐 Application should be available at: https://localhost:443" -ForegroundColor Cyan
    } catch {
        Write-Host "❌ Quick Production Start failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

function Start-FastProduction {
    """Execute Fast Production Start (Option 2)."""
    Write-Host "🚀 Starting Fast Production Start..." -ForegroundColor Cyan
    
    # Clean Python cache
    Write-Host "🧹 Cleaning Python cache..." -ForegroundColor Yellow
    Get-ChildItem -Path . -Recurse -Include *.pyc | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Directory -Include __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    
    try {
        # Call the original Start-DockerProduction function with restart
        Start-DockerProduction -ForceRebuild:$false -NoValidation:$false
        
        Write-Host "✅ Fast Production Start completed successfully!" -ForegroundColor Green
        Write-Host "🌐 Application should be available at: https://localhost:443" -ForegroundColor Cyan
    } catch {
        Write-Host "❌ Fast Production Start failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

function Start-FullRebuild {
    """Execute Full Rebuild (Option 3)."""
    Write-Host "🚀 Starting Full Rebuild..." -ForegroundColor Yellow
    
    try {
        # Call the original Start-DockerProduction function with full rebuild
        Start-DockerProduction -ForceRebuild:$true -NoValidation:$false
        
        Write-Host "✅ Full Rebuild completed successfully!" -ForegroundColor Green
        Write-Host "🌐 Application should be available at: https://localhost:443" -ForegroundColor Cyan
    } catch {
        Write-Host "❌ Full Rebuild failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Main execution
if ($Mode -eq "Auto" -or $AutoMode) {
    Start-SmartLaunch
} else {
    # Fall back to original cslaunch behavior
    & .\cslaunch.ps1 @PSBoundParameters
} 