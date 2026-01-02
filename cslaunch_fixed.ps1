# cslaunch_fixed.ps1 - Clean version without Unicode character issues
# This is a clean version of the script with all Unicode characters removed

param(
    [switch]$Build,
    [switch]$Force,
    [switch]$NoCache,
    [switch]$Monitor,
    [switch]$NoMonitor,
    [switch]$ConfigureAutostart,
    [switch]$NoAutostart,
    [switch]$ConfigurePeriodicHealthCheck,
    [switch]$RemovePeriodicHealthCheck,
    [int]$MonitorInterval = 30,
    [switch]$EnableDockerDaemonMonitor,
    [int]$DockerDaemonTimeout = 15,
    [int]$MaxDockerRestartsPerHour = 8,
    [int]$ExtendedDowntimeMinutes = 15,
    [bool]$EnableNotifications = $false,
    [switch]$EnableEnhancedMonitoring,
    [switch]$EnableSelfHealthMonitoring,
    [switch]$EnableSystemRecoveryLogging,
    [switch]$EnableEscalationManager,
    [switch]$EnableAutoRecovery,
    [switch]$EnableResourceMonitoring,
    [int]$MemoryThreshold = 80,
    [int]$CpuThreshold = 80,
    [int]$EnhancedCheckInterval = 60,
    [switch]$DeepCleanRestart,
    [switch]$MemoryOptimizeRestart,
    [switch]$WhatIf
)

# Set error action preference
$ErrorActionPreference = 'Stop'

# Import enhanced monitoring functions
$scriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$enhancedFunctionsPath = Join-Path $scriptsDir "scripts\enhanced_monitoring_functions.ps1"

if (Test-Path $enhancedFunctionsPath) {
    try {
        . $enhancedFunctionsPath
        Write-Host "[INFO] Loaded enhanced monitoring functions" -ForegroundColor Green
    } catch {
        Write-Host "[WARNING] Failed to load enhanced monitoring functions: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARNING] Enhanced monitoring functions not found at: $enhancedFunctionsPath" -ForegroundColor Yellow
}

# Main script execution
try {
    # Start enhanced monitoring if enabled
    if ($EnableEnhancedMonitoring) {
        Start-EnhancedMonitoringSuite
    }
    
    # Rest of your existing script logic would go here
    # ...
    
    Write-Host "[INFO] Script execution completed successfully" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Script failed: $_" -ForegroundColor Red
    exit 1
}
