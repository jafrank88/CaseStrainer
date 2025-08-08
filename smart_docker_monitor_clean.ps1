# Smart Docker Monitor for CaseStrainer
# Monitors Docker processes and performs intelligent cleanup

param(
    [int]$CheckInterval = 300,  # Check every 5 minutes
    [int]$MaxDockerProcesses = 15,  # Maximum reasonable Docker processes
    [switch]$Verbose,
    [switch]$DryRun
)

$LogFile = "logs/smart_docker_monitor.log"

function Write-Log {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"

    Write-Host $logMessage -ForegroundColor $(switch($Level) {
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "INFO" { "Green" }
        "CLEANUP" { "Magenta" }
        default { "White" }
    })

    Add-Content -Path $LogFile -Value $logMessage -Force
}

function Get-SmartDockerAnalysis {
    $allProcesses = Get-Process | Where-Object { $_.ProcessName -like "*docker*" }

    # Categorize processes
    $legitimate = @()
    $suspicious = @()
    $zombie = @()

    foreach ($proc in $allProcesses) {
        $isLegitimate = $false

        # Check if it's a critical Docker service
        if ($proc.ProcessName -match "com\.docker\.service|com\.docker\.backend|Docker Desktop") {
            $isLegitimate = $true
        }

        # Check if it's an active CLI process (recent CPU usage)
        if ($proc.CPU -gt 0.1 -and $proc.ProcessName -eq "docker") {
            $isLegitimate = $true
        }

        # Check age (processes older than 1 hour with no CPU might be zombies)
        $age = (Get-Date) - $proc.StartTime
        if ($age.TotalHours -gt 1 -and $proc.CPU -lt 0.01) {
            $zombie += $proc
        } elseif (!$isLegitimate) {
            $suspicious += $proc
        } else {
            $legitimate += $proc
        }
    }

    return @{
        Legitimate = $legitimate
        Suspicious = $suspicious
        Zombie = $zombie
        Total = $allProcesses.Count
    }
}

function Invoke-SmartCleanup {
    $analysis = Get-SmartDockerAnalysis

    Write-Log "=== SMART DOCKER CLEANUP ===" -Level "INFO"
    Write-Log "Total processes: $($analysis.Total)" -Level "INFO"
    Write-Log "Legitimate: $($analysis.Legitimate.Count)" -Level "INFO"
    Write-Log "Suspicious: $($analysis.Suspicious.Count)" -Level "WARN"
    Write-Log "Zombie: $($analysis.Zombie.Count)" -Level "CLEANUP"

    if ($analysis.Total -gt $MaxDockerProcesses) {
        Write-Log "Process count exceeds threshold ($MaxDockerProcesses)" -Level "WARN"
    }

    # Kill only zombie processes (old, inactive)
    $killed = 0
    foreach ($proc in $analysis.Zombie) {
        Write-Log "Killing zombie process: $($proc.ProcessName) (PID: $($proc.Id), Age: $([math]::Round(((Get-Date) - $proc.StartTime).TotalHours, 1))h)" -Level "CLEANUP"

        if (!$DryRun) {
            try {
                Stop-Process -Id $proc.Id -Force
                $killed++
            } catch {
                Write-Log "Failed to kill process $($proc.Id): $($_.Exception.Message)" -Level "ERROR"
            }
        }
    }

    # Log suspicious but don't auto-kill (could be test scripts)
    foreach ($proc in $analysis.Suspicious) {
        Write-Log "Suspicious process detected: $($proc.ProcessName) (PID: $($proc.Id))" -Level "WARN"
    }
    
    return $killed
}

function Start-ContinuousMonitoring {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param()
    
    Write-Log "Starting Smart Docker Monitor (interval: ${CheckInterval}s)"
    
    while ($true) {
        Invoke-SmartCleanup
        Start-Sleep -Seconds $CheckInterval
    }
}

# Create startup script
function Start-MonitorService {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param()
    
    Write-Log "Starting Docker process monitoring service..."
    
    # Ensure log directory exists
    if (!(Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    }
    
    # Initial cleanup
    $initialKilled = Invoke-SmartCleanup
    if ($initialKilled -gt 0) {
        Write-Log "Initial cleanup: killed $initialKilled zombie processes" -Level "CLEANUP"
    }
    
    # Start continuous monitoring
    Start-ContinuousMonitoring
}

# Integration with cslaunch
Write-Log "Smart Docker Monitor ready"
Write-Log "Usage:"
Write-Log "  .\smart_docker_monitor_clean.ps1                    # Run once"
Write-Log "  .\smart_docker_monitor_clean.ps1 -CheckInterval 60  # Run every minute"
Write-Log "  .\smart_docker_monitor_clean.ps1 -DryRun            # Preview actions"

# Run based on parameters
if ($MyInvocation.BoundParameters.Count -eq 0) {
    Invoke-SmartCleanup
} else {
    Start-MonitorService
}
