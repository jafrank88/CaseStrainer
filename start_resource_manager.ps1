# Smart Resource Manager Launcher for CaseStrainer
# Automatically manages Dify containers to prioritize CaseStrainer

param(
    [switch]$DryRun,
    [switch]$Verbose,
    [switch]$Help,
    [int]$CheckInterval = 60,
    [int]$MemoryThreshold = 80,
    [int]$CPUThreshold = 70,
    [int]$DifyRestartDelay = 900
)

if ($Help) {
    Write-Host "Smart Resource Manager for CaseStrainer" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  .\start_resource_manager.ps1                    # Start with default settings" -ForegroundColor Green
    Write-Host "  .\start_resource_manager.ps1 -DryRun            # Test mode (no actual changes)" -ForegroundColor Yellow
    Write-Host "  .\start_resource_manager.ps1 -Verbose           # Show detailed output" -ForegroundColor Cyan
    Write-Host "  .\start_resource_manager.ps1 -CheckInterval 30  # Check every 30 seconds" -ForegroundColor Green
    Write-Host "  .\start_resource_manager.ps1 -MemoryThreshold 70 # Stop Dify at 70% memory" -ForegroundColor Green
    Write-Host "  .\start_resource_manager.ps1 -CPUThreshold 60   # Stop Dify at 60% CPU" -ForegroundColor Green
    Write-Host "  .\start_resource_manager.ps1 -DifyRestartDelay 600 # Restart Dify after 10 minutes" -ForegroundColor Green
    Write-Host ""
    Write-Host "Default Configuration:" -ForegroundColor White
    Write-Host "  Check Interval: 60 seconds" -ForegroundColor Gray
    Write-Host "  Memory Threshold: 80%" -ForegroundColor Gray
    Write-Host "  CPU Threshold: 70%" -ForegroundColor Gray
    Write-Host "  Dify Restart Delay: 15 minutes (900 seconds)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "What it does:" -ForegroundColor White
    Write-Host "  • Monitors system resources and CaseStrainer health" -ForegroundColor Gray
    Write-Host "  • Automatically stops Dify containers when resource pressure is detected" -ForegroundColor Gray
    Write-Host "  • Restarts Dify containers after 15 minutes if resources are available" -ForegroundColor Gray
    Write-Host "  • Prioritizes CaseStrainer performance while keeping Dify available" -ForegroundColor Gray
    exit 0
}

# Check if the main script exists
if (!(Test-Path "smart_resource_manager.ps1")) {
    Write-Host "Error: smart_resource_manager.ps1 not found!" -ForegroundColor Red
    Write-Host "Please ensure the resource manager script is in the current directory." -ForegroundColor Yellow
    exit 1
}

# Display configuration
Write-Host "Starting Smart Resource Manager with configuration:" -ForegroundColor Cyan
Write-Host "  Check Interval: $CheckInterval seconds" -ForegroundColor White
Write-Host "  Memory Threshold: $MemoryThreshold%" -ForegroundColor White
Write-Host "  CPU Threshold: $CPUThreshold%" -ForegroundColor White
Write-Host "  Dify Restart Delay: $DifyRestartDelay seconds ($([math]::Round($DifyRestartDelay/60, 1)) minutes)" -ForegroundColor White
Write-Host "  Dry Run Mode: $DryRun" -ForegroundColor $(if($DryRun){"Yellow"}else{"Green"})
Write-Host "  Verbose Mode: $Verbose" -ForegroundColor $(if($Verbose){"Cyan"}else{"Gray"})
Write-Host ""

# Build the command
$params = @(
    "-CheckInterval", $CheckInterval,
    "-MemoryThreshold", $MemoryThreshold,
    "-CPUThreshold", $CPUThreshold,
    "-DifyRestartDelay", $DifyRestartDelay
)

if ($DryRun) { $params += "-DryRun" }
if ($Verbose) { $params += "-Verbose" }

# Start the resource manager
Write-Host "Launching Smart Resource Manager..." -ForegroundColor Green
& ".\smart_resource_manager.ps1" @params

