<#
.SYNOPSIS
CaseStrainer Interactive Launcher

.DESCRIPTION
Interactive PowerShell launcher for CaseStrainer application with Docker support.
Uses Write-Host for colored console output which is appropriate for user interaction.

.NOTES
PSScriptAnalyzer suppressions:
- PSAvoidUsingWriteHost: Acceptable for interactive scripts requiring colored output
- PSUseSingularNouns: Service management functions use plural nouns by design
#>
# Batch section - commented out to prevent PowerShell linter errors
# @echo off
# title CaseStrainer Launcher
#
# :: Check if running from CMD or PowerShell
# set "POWERSHELL_BITS=%PROCESSOR_ARCHITEW6432%"
# if not defined POWERSHELL_BITS set "POWERSHELL_BITS=%PROCESSOR_ARCHITECTURE%"
#
# :: If running from CMD, restart with PowerShell
# if "%POWERSHELL_BITS%" neq "" (
#     powershell -NoProfile -ExecutionPolicy Bypass -Command "& '%~dpn0.ps1' %*"
#     exit /b %ERRORLEVEL%
# )
#
# echo This should not be reached if PowerShell is available
# exit /b 1

#>
# Final Working CaseStrainer Launcher - All fixes integrated

param(
    [ValidateSet("Development", "Production", "DockerDevelopment", "DockerProduction", "Menu")]
    [string]$Environment = "Menu",
    [switch]$NoMenu,
    [switch]$Help,
    [switch]$SkipBuild,
    [switch]$ForceBuild,
    [switch]$VerboseLogging,
    [switch]$AutoRestart,
    [switch]$DebugCaseNameExtraction
)

# Global variables for auto-restart and monitoring
$script:AutoRestartEnabled = $AutoRestart.IsPresent
$script:RestartCount = 0
$script:MaxRestartAttempts = 3
$script:CrashLogFile = Join-Path $PSScriptRoot "logs\crash.log"
$script:MonitoringJob = $null
$script:LastCrashTime = $null

# Show help
if ($Help) {
    Write-Host @"
Enhanced CaseStrainer Interactive Launcher v2.0 - Help

Usage:
  .\launcher.ps1 [Options]

Environment Options:
  -Environment Development        Start in Development mode
  -Environment Production         Start in Production mode  
  -Environment DockerDevelopment  Start in Docker Development mode
  -Environment DockerProduction   Start in Docker Production mode
  -Environment Menu              Show interactive menu (default)

Additional Options:
  -NoMenu                        Skip interactive menu
  -SkipBuild                     Skip Vue frontend build
  -ForceBuild                    Force Vue frontend rebuild
  -VerboseLogging                Enable verbose logging
  -AutoRestart                   Enable auto-restart monitoring
  -DebugCaseNameExtraction       Enable DEBUG logging for case name extraction
  -Help                          Show this help

Examples:
  .\launcher.ps1                           # Show interactive menu
  .\launcher.ps1 -Environment Development  # Start in Development mode
  .\launcher.ps1 -Environment Production   # Start in Production mode
  .\launcher.ps1 -Environment DockerDevelopment   # Start in Docker Development mode
  .\launcher.ps1 -Environment DockerProduction    # Start in Docker Production mode
  .\launcher.ps1 -NoMenu -Environment Production -SkipBuild   # Quick production start
  .\launcher.ps1 -NoMenu -Environment Production -ForceBuild  # Force rebuild frontend
  .\launcher.ps1 -Environment DockerProduction -AutoRestart   # Start with auto-restart
"@ -ForegroundColor Cyan
    exit 0
}

# Enhanced crash logging function
function Write-CrashLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        [ValidateSet("INFO", "WARN", "ERROR", "DEBUG")]
        [string]$Level = "INFO",
        [System.Management.Automation.ErrorRecord]$Exception = $null
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    if ($Exception) {
        $logEntry += " - Exception: $($Exception.Exception.Message)"
        $logEntry += " - StackTrace: $($Exception.ScriptStackTrace)"
    }
    
    try {
        $logDir = Split-Path $script:CrashLogFile -Parent
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        }
        Add-Content -Path $script:CrashLogFile -Value $logEntry -ErrorAction Stop
    }
    catch {
        Write-Warning "Could not write to crash log: $($_.Exception.Message)"
    }
}

# Enhanced environment validation
function Test-ScriptEnvironment {
    [CmdletBinding()]
    param()
    
    $requiredFiles = @(
        "docker-compose.prod.yml",
        "casestrainer-vue-new"
    )
    
    foreach ($file in $requiredFiles) {
        $path = Join-Path $PSScriptRoot $file
        if (-not (Test-Path $path)) {
            Write-CrashLog "Required file/directory not found: $file" -Level "ERROR"
            throw "Required file/directory not found: $file"
        }
    }
}

# Enhanced Docker availability check
function Test-DockerAvailability {
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    
    try {
        $null = docker info --format "{{.ServerVersion}}" 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch {
        Write-CrashLog "Docker availability check failed" -Level "ERROR" -Exception $_
        return $false
    }
}

# Enhanced auto-restart monitoring
function Start-AutoRestartMonitoring {
    [CmdletBinding()]
    param()
    
    if (-not $script:AutoRestartEnabled) {
        return
    }
    
    Write-Host "`n=== Starting Auto-Restart Monitoring ===" -ForegroundColor Magenta
    Write-Host "Monitoring Docker containers for crashes..." -ForegroundColor Yellow
    
    $script:MonitoringJob = Start-Job -ScriptBlock {
        param($ProjectRoot)
        
        while ($true) {
            try {
                # Check if containers are running
                $containers = docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}" 2>$null
                
                if ($LASTEXITCODE -ne 0) {
                    Write-Output "DOCKER_ERROR: $($containers)"
                    Start-Sleep -Seconds 30
                    continue
                }
                
                # Check for crashed containers
                $crashed = $containers | Where-Object { $_ -match "Exited" }
                if ($crashed) {
                    Write-Output "CRASH_DETECTED: $crashed"
                }
                
                Start-Sleep -Seconds 10
            }
            catch {
                Write-Output "MONITORING_ERROR: $($_.Exception.Message)"
                Start-Sleep -Seconds 30
            }
        }
    } -ArgumentList $PSScriptRoot
    
    Write-Host "Auto-restart monitoring started (Job ID: $($script:MonitoringJob.Id))" -ForegroundColor Green
}

# Enhanced Docker production mode with better error handling
function Start-DockerProduction {
    [CmdletBinding(SupportsShouldProcess)]
    [OutputType([bool])]
    param()
    
    Write-Host "`n=== Starting Enhanced Docker Production Mode ===`n" -ForegroundColor Green
    
    try {
        # Validate environment first
        Test-ScriptEnvironment
        
        if (-not (Test-DockerAvailability)) {
            Write-Host "ERROR: Docker is not running or not available" -ForegroundColor Red
            Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
            Write-CrashLog "Docker not available for production mode" -Level "ERROR"
            return $false
        }
        Write-Host "OK: Docker is running" -ForegroundColor Green
        
        # Set debug logging if requested
        if ($DebugCaseNameExtraction) {
            Write-Host "[DEBUG] Enabling DEBUG logging for case_name_extraction in backend..." -ForegroundColor Yellow
            $env:LOG_LEVEL_CASE_NAME_EXTRACTION = "DEBUG"
        }
        
        # Build Vue frontend if needed
        if (-not $SkipBuild) {
            Write-Host "Building Vue frontend for production..." -ForegroundColor Cyan
            $buildSuccess = Build-VueFrontend
            if (-not $buildSuccess) {
                Write-Host "Warning: Vue build failed, continuing with existing files" -ForegroundColor Yellow
            }
        }
        
        # Start auto-restart monitoring if enabled
        if ($script:AutoRestartEnabled) {
            Start-AutoRestartMonitoring
        }
        
        # Start Docker Compose
        Write-Host "Starting Docker Compose production services..." -ForegroundColor Cyan
        $dockerComposeArgs = @(
            "-f", "docker-compose.prod.yml",
            "up", "-d"
        )
        
        if ($VerboseLogging) {
            $dockerComposeArgs += "--verbose"
        }
        
        $process = Start-Process -FilePath "docker-compose" -ArgumentList $dockerComposeArgs -NoNewWindow -PassThru -Wait
        
        if ($process.ExitCode -eq 0) {
            Write-Host "SUCCESS: Docker production services started" -ForegroundColor Green
            Write-CrashLog "Docker production services started successfully" -Level "INFO"
            
            # Show service status
            Start-Sleep -Seconds 5
            Show-DockerStatus
            
            return $true
        } else {
            Write-Host "ERROR: Docker Compose failed with exit code: $($process.ExitCode)" -ForegroundColor Red
            Write-CrashLog "Docker Compose failed with exit code: $($process.ExitCode)" -Level "ERROR"
            return $false
        }
    }
    catch {
        Write-Host "ERROR: Failed to start Docker production mode: $($_.Exception.Message)" -ForegroundColor Red
        Write-CrashLog "Docker production mode startup failed" -Level "ERROR" -Exception $_
        return $false
    }
}

# Enhanced Docker status display
function Show-DockerStatus {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Docker Container Status ===" -ForegroundColor Cyan
    
    try {
        $containers = docker ps --filter "name=casestrainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
        
        if ($LASTEXITCODE -eq 0 -and $containers) {
            Write-Host $containers -ForegroundColor White
        } else {
            Write-Host "No casestrainer containers found or Docker error" -ForegroundColor Yellow
        }
        
        # Show logs for each container
        Write-Host "`n=== Recent Logs ===" -ForegroundColor Cyan
        $containerNames = @("casestrainer-backend", "casestrainer-frontend", "casestrainer-nginx", "casestrainer-redis", "casestrainer-worker")
        
        foreach ($container in $containerNames) {
            try {
                $logs = docker logs --tail 3 $container 2>$null
                if ($logs) {
                    Write-Host "`n$container:" -ForegroundColor Yellow
                    Write-Host $logs -ForegroundColor Gray
                }
            }
            catch {
                # Container might not exist yet
            }
        }
    }
    catch {
        Write-Host "Error getting Docker status: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Enhanced production diagnostics
function Show-ProductionDiagnostics {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Enhanced Production Diagnostics ===" -ForegroundColor Cyan
    
    # System checks
    Write-Host "`n1. System Resources:" -ForegroundColor Yellow
    $cpu = Get-WmiObject -Class Win32_Processor | Select-Object -First 1
    $memory = Get-WmiObject -Class Win32_ComputerSystem
    $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
    
    Write-Host "   CPU: $($cpu.Name)" -ForegroundColor White
    Write-Host "   Memory: $([math]::Round($memory.TotalPhysicalMemory/1GB, 2)) GB" -ForegroundColor White
    Write-Host "   Disk C: $([math]::Round($disk.FreeSpace/1GB, 2)) GB free of $([math]::Round($disk.Size/1GB, 2)) GB" -ForegroundColor White
    
    # Docker checks
    Write-Host "`n2. Docker Status:" -ForegroundColor Yellow
    if (Test-DockerAvailability) {
        Write-Host "   Docker: Running" -ForegroundColor Green
        $dockerVersion = docker version --format "{{.Server.Version}}" 2>$null
        Write-Host "   Version: $dockerVersion" -ForegroundColor White
    } else {
        Write-Host "   Docker: Not available" -ForegroundColor Red
    }
    
    # Container health checks
    Write-Host "`n3. Container Health:" -ForegroundColor Yellow
    try {
        $containers = docker ps --filter "name=casestrainer" --format "{{.Names}}: {{.Status}}" 2>$null
        if ($containers) {
            foreach ($container in $containers) {
                Write-Host "   $container" -ForegroundColor White
            }
        } else {
            Write-Host "   No casestrainer containers running" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "   Error checking containers: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Network connectivity
    Write-Host "`n4. Network Connectivity:" -ForegroundColor Yellow
    $testUrls = @("https://www.google.com", "https://www.courtlistener.com")
    foreach ($url in $testUrls) {
        try {
            $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 -UseBasicParsing
            Write-Host "   $url : OK ($($response.StatusCode))" -ForegroundColor Green
        }
        catch {
            Write-Host "   $url : FAILED" -ForegroundColor Red
        }
    }
    
    # Cache status
    Write-Host "`n5. Cache Status:" -ForegroundColor Yellow
    $cacheDirs = @("citation_cache", "correction_cache", "cache")
    foreach ($dir in $cacheDirs) {
        $path = Join-Path $PSScriptRoot $dir
        if (Test-Path $path) {
            $size = (Get-ChildItem -Path $path -Recurse -File | Measure-Object -Property Length -Sum).Sum
            $sizeMB = [math]::Round($size / 1MB, 2)
            Write-Host "   $dir : $sizeMB MB" -ForegroundColor White
        } else {
            Write-Host "   $dir : Not found" -ForegroundColor Yellow
        }
    }
    
    # Recent crash logs
    Write-Host "`n6. Recent Crash Logs:" -ForegroundColor Yellow
    if (Test-Path $script:CrashLogFile) {
        $recentLogs = Get-Content $script:CrashLogFile -Tail 5
        foreach ($log in $recentLogs) {
            Write-Host "   $log" -ForegroundColor Gray
        }
    } else {
        Write-Host "   No crash logs found" -ForegroundColor Green
    }
}

# Enhanced cache management
function Manage-CitationCache {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Citation Cache Management ===" -ForegroundColor Yellow
    
    do {
        Write-Host "`n1. View cache information" -ForegroundColor Cyan
        Write-Host "2. Clear unverified citations" -ForegroundColor Yellow
        Write-Host "3. Clear all citation cache" -ForegroundColor Red
        Write-Host "4. Show cache statistics" -ForegroundColor Green
        Write-Host "0. Back to main menu" -ForegroundColor Gray
        
        $selection = Read-Host "`nSelect an option (0-4)"
        
        switch ($selection) {
            "1" {
                Show-CacheInformation
            }
            "2" {
                Clear-UnverifiedCitations
            }
            "3" {
                Clear-AllCitationCache
            }
            "4" {
                Show-CacheStatistics
            }
            "0" {
                return
            }
            default {
                Write-Host "Invalid selection. Please try again." -ForegroundColor Red
            }
        }
    } while ($true)
}

function Show-CacheInformation {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Cache Information ===" -ForegroundColor Cyan
    
    $cacheDirs = @{
        "Citation Cache" = "citation_cache"
        "Correction Cache" = "correction_cache"
        "General Cache" = "cache"
    }
    
    foreach ($name in $cacheDirs.Keys) {
        $path = Join-Path $PSScriptRoot $cacheDirs[$name]
        Write-Host "`n$name:" -ForegroundColor Yellow
        
        if (Test-Path $path) {
            $files = Get-ChildItem -Path $path -Recurse -File
            $size = ($files | Measure-Object -Property Length -Sum).Sum
            $sizeMB = [math]::Round($size / 1MB, 2)
            
            Write-Host "   Path: $path" -ForegroundColor White
            Write-Host "   Files: $($files.Count)" -ForegroundColor White
            Write-Host "   Size: $sizeMB MB" -ForegroundColor White
            
            # Show file types
            $extensions = $files | Group-Object Extension | Sort-Object Count -Descending | Select-Object -First 5
            Write-Host "   Top file types:" -ForegroundColor Gray
            foreach ($ext in $extensions) {
                Write-Host "     $($ext.Name): $($ext.Count) files" -ForegroundColor Gray
            }
        } else {
            Write-Host "   Not found" -ForegroundColor Yellow
        }
    }
}

function Clear-UnverifiedCitations {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Host "`n=== Clear Unverified Citations ===" -ForegroundColor Yellow
    
    $cachePath = Join-Path $PSScriptRoot "citation_cache"
    if (-not (Test-Path $cachePath)) {
        Write-Host "Citation cache directory not found." -ForegroundColor Yellow
        return
    }
    
    $unverifiedFiles = Get-ChildItem -Path $cachePath -Filter "*_unverified*" -Recurse
    if (-not $unverifiedFiles) {
        Write-Host "No unverified citation files found." -ForegroundColor Green
        return
    }
    
    Write-Host "Found $($unverifiedFiles.Count) unverified citation files." -ForegroundColor Yellow
    
    if ($PSCmdlet.ShouldProcess("$($unverifiedFiles.Count) unverified citation files", "Remove")) {
        try {
            $unverifiedFiles | Remove-Item -Force
            Write-Host "Successfully removed $($unverifiedFiles.Count) unverified citation files." -ForegroundColor Green
            Write-CrashLog "Cleared $($unverifiedFiles.Count) unverified citation files" -Level "INFO"
        }
        catch {
            Write-Host "Error removing unverified citation files: $($_.Exception.Message)" -ForegroundColor Red
            Write-CrashLog "Failed to clear unverified citations" -Level "ERROR" -Exception $_
        }
    }
}

function Clear-AllCitationCache {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    
    Write-Host "`n=== Clear All Citation Cache ===" -ForegroundColor Red
    Write-Host "WARNING: This will remove ALL citation cache files!" -ForegroundColor Red
    
    $cachePath = Join-Path $PSScriptRoot "citation_cache"
    if (-not (Test-Path $cachePath)) {
        Write-Host "Citation cache directory not found." -ForegroundColor Yellow
        return
    }
    
    $allFiles = Get-ChildItem -Path $cachePath -Recurse -File
    if (-not $allFiles) {
        Write-Host "No citation cache files found." -ForegroundColor Green
        return
    }
    
    Write-Host "Found $($allFiles.Count) citation cache files." -ForegroundColor Yellow
    
    $confirm = Read-Host "Are you sure you want to remove ALL citation cache files? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        return
    }
    
    if ($PSCmdlet.ShouldProcess("$($allFiles.Count) citation cache files", "Remove")) {
        try {
            $allFiles | Remove-Item -Force
            Write-Host "Successfully removed $($allFiles.Count) citation cache files." -ForegroundColor Green
            Write-CrashLog "Cleared all citation cache files ($($allFiles.Count) files)" -Level "INFO"
        }
        catch {
            Write-Host "Error removing citation cache files: $($_.Exception.Message)" -ForegroundColor Red
            Write-CrashLog "Failed to clear all citation cache" -Level "ERROR" -Exception $_
        }
    }
}

function Show-CacheStatistics {
    [CmdletBinding()]
    param()
    
    Write-Host "`n=== Cache Statistics ===" -ForegroundColor Cyan
    
    $cachePath = Join-Path $PSScriptRoot "citation_cache"
    if (-not (Test-Path $cachePath)) {
        Write-Host "Citation cache directory not found." -ForegroundColor Yellow
        return
    }
    
    $files = Get-ChildItem -Path $cachePath -Recurse -File
    $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
    $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
    
    Write-Host "Total files: $($files.Count)" -ForegroundColor White
    Write-Host "Total size: $totalSizeMB MB" -ForegroundColor White
    
    # File type breakdown
    $extensions = $files | Group-Object Extension | Sort-Object Count -Descending
    Write-Host "`nFile type breakdown:" -ForegroundColor Yellow
    foreach ($ext in $extensions) {
        $extSize = ($ext.Group | Measure-Object -Property Length -Sum).Sum
        $extSizeMB = [math]::Round($extSize / 1MB, 2)
        Write-Host "  $($ext.Name): $($ext.Count) files ($extSizeMB MB)" -ForegroundColor White
    }
    
    # Age analysis
    $now = Get-Date
    $recentFiles = $files | Where-Object { $_.LastWriteTime -gt $now.AddDays(-1) }
    $oldFiles = $files | Where-Object { $_.LastWriteTime -lt $now.AddDays(-7) }
    
    Write-Host "`nAge analysis:" -ForegroundColor Yellow
    Write-Host "  Files modified in last 24 hours: $($recentFiles.Count)" -ForegroundColor White
    Write-Host "  Files older than 7 days: $($oldFiles.Count)" -ForegroundColor White
}

# ... existing code ...
