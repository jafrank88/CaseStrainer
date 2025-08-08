# CaseStrainer Monitoring System Launcher
# Starts both Docker Auto-Recovery and Smart Resource Manager

param(
    [switch]$Background,
    [switch]$Verbose,
    [switch]$DryRun,
    [switch]$Help
)

if ($Help) {
    Write-Host "CaseStrainer Monitoring System" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  .\start_monitoring.ps1                    # Start monitoring in foreground" -ForegroundColor Green
    Write-Host "  .\start_monitoring.ps1 -Background        # Start monitoring in background" -ForegroundColor Yellow
    Write-Host "  .\start_monitoring.ps1 -Verbose           # Show detailed output" -ForegroundColor Cyan
    Write-Host "  .\start_monitoring.ps1 -DryRun            # Test mode (no actual changes)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "What it starts:" -ForegroundColor White
    Write-Host "  • Docker Auto-Recovery System" -ForegroundColor Gray
    Write-Host "  • Smart Resource Manager" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Monitoring Features:" -ForegroundColor White
    Write-Host "  • Auto-restart Docker Desktop when it stops" -ForegroundColor Gray
    Write-Host "  • Manage Dify containers based on resource usage" -ForegroundColor Gray
    Write-Host "  • Prioritize CaseStrainer performance" -ForegroundColor Gray
    Write-Host "  • Comprehensive logging and alerting" -ForegroundColor Gray
    exit 0
}

# Check if required scripts exist
$requiredScripts = @("docker_auto_recovery.ps1", "start_resource_manager.ps1")
foreach ($script in $requiredScripts) {
    if (!(Test-Path $script)) {
        Write-Host "Error: $script not found!" -ForegroundColor Red
        Write-Host "Please ensure all monitoring scripts are in the current directory." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Starting CaseStrainer Monitoring System..." -ForegroundColor Cyan
Write-Host ""

# Build parameters for both scripts
$autoRecoveryParams = @("-CheckInterval", "30")
$resourceManagerParams = @("-CheckInterval", "60")

if ($Verbose) { 
    $autoRecoveryParams += "-Verbose"
    $resourceManagerParams += "-Verbose"
}
if ($DryRun) { 
    $autoRecoveryParams += "-DryRun"
    $resourceManagerParams += "-DryRun"
}

if ($Background) {
    Write-Host "Starting monitoring systems in background..." -ForegroundColor Yellow
    
    # Start Docker Auto-Recovery in background
    $autoRecoveryJob = Start-Job -ScriptBlock {
        param($scriptPath, $verbose, $dryRun)
        Set-Location $scriptPath
        if ($verbose) {
            & ".\docker_auto_recovery.ps1" -CheckInterval 30 -Verbose
        } elseif ($dryRun) {
            & ".\docker_auto_recovery.ps1" -CheckInterval 30 -DryRun
        } else {
            & ".\docker_auto_recovery.ps1" -CheckInterval 30
        }
    } -ArgumentList (Get-Location).Path, $Verbose, $DryRun
    
    # Start Resource Manager in background
    $resourceManagerJob = Start-Job -ScriptBlock {
        param($scriptPath, $verbose, $dryRun)
        Set-Location $scriptPath
        if ($verbose) {
            & ".\start_resource_manager.ps1" -CheckInterval 60 -Verbose
        } elseif ($dryRun) {
            & ".\start_resource_manager.ps1" -CheckInterval 60 -DryRun
        } else {
            & ".\start_resource_manager.ps1" -CheckInterval 60
        }
    } -ArgumentList (Get-Location).Path, $Verbose, $DryRun
    
    Write-Host "✅ Docker Auto-Recovery System started (Job ID: $($autoRecoveryJob.Id))" -ForegroundColor Green
    Write-Host "✅ Smart Resource Manager started (Job ID: $($resourceManagerJob.Id))" -ForegroundColor Green
    Write-Host ""
    Write-Host "Monitoring systems are running in background." -ForegroundColor Cyan
    Write-Host "To check status:" -ForegroundColor White
    Write-Host "  Get-Job" -ForegroundColor Gray
    Write-Host "  Receive-Job -Id $($autoRecoveryJob.Id)" -ForegroundColor Gray
    Write-Host "  Receive-Job -Id $($resourceManagerJob.Id)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To stop monitoring:" -ForegroundColor White
    Write-Host "  Stop-Job -Id $($autoRecoveryJob.Id), $($resourceManagerJob.Id)" -ForegroundColor Gray
    Write-Host "  Remove-Job -Id $($autoRecoveryJob.Id), $($resourceManagerJob.Id)" -ForegroundColor Gray
} else {
    Write-Host "Starting monitoring systems in foreground..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop both systems." -ForegroundColor Gray
    Write-Host ""
    
    # Start both systems in parallel using jobs but monitor them
    $autoRecoveryJob = Start-Job -ScriptBlock {
        param($scriptPath, $verbose, $dryRun)
        Set-Location $scriptPath
        if ($verbose) {
            & ".\docker_auto_recovery.ps1" -CheckInterval 30 -Verbose
        } elseif ($dryRun) {
            & ".\docker_auto_recovery.ps1" -CheckInterval 30 -DryRun
        } else {
            & ".\docker_auto_recovery.ps1" -CheckInterval 30
        }
    } -ArgumentList (Get-Location).Path, $Verbose, $DryRun
    
    $resourceManagerJob = Start-Job -ScriptBlock {
        param($scriptPath, $verbose, $dryRun)
        Set-Location $scriptPath
        if ($verbose) {
            & ".\start_resource_manager.ps1" -CheckInterval 60 -Verbose
        } elseif ($dryRun) {
            & ".\start_resource_manager.ps1" -CheckInterval 60 -DryRun
        } else {
            & ".\start_resource_manager.ps1" -CheckInterval 60
        }
    } -ArgumentList (Get-Location).Path, $Verbose, $DryRun
    
    try {
        # Monitor both jobs and display output
        while ($true) {
            $autoRecoveryOutput = Receive-Job -Job $autoRecoveryJob -Keep
            $resourceManagerOutput = Receive-Job -Job $resourceManagerJob -Keep
            
            if ($autoRecoveryOutput) {
                foreach ($line in $autoRecoveryOutput) {
                    Write-Host "[Auto-Recovery] $line" -ForegroundColor Blue
                }
            }
            
            if ($resourceManagerOutput) {
                foreach ($line in $resourceManagerOutput) {
                    Write-Host "[Resource Manager] $line" -ForegroundColor Green
                }
            }
            
            # Check if jobs are still running
            if ($autoRecoveryJob.State -eq "Failed" -or $resourceManagerJob.State -eq "Failed") {
                Write-Host "One or more monitoring systems failed!" -ForegroundColor Red
                break
            }
            
            Start-Sleep -Seconds 1
        }
    }
    catch {
        Write-Host "Stopping monitoring systems..." -ForegroundColor Yellow
    }
    finally {
        # Clean up jobs
        Stop-Job -Job $autoRecoveryJob, $resourceManagerJob -ErrorAction SilentlyContinue
        Remove-Job -Job $autoRecoveryJob, $resourceManagerJob -ErrorAction SilentlyContinue
        Write-Host "Monitoring systems stopped." -ForegroundColor Cyan
    }
}
