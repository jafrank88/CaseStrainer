# External Monitoring Script for CaseStrainer
# This script runs independently to monitor system health and send alerts

param(
    [string]$Environment = "Production",
    [int]$CheckInterval = 300,  # 5 minutes
    [string]$AlertEmail = "",
    [string]$SlackWebhook = "",
    [switch]$Verbose,
    [switch]$TestMode
)

# Configuration
$LogDirectory = "logs"
$LogFile = Join-Path $LogDirectory "external_monitor_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$HealthCheckUrl = "http://localhost:5001/casestrainer/api/health"
$BackupHealthUrl = "http://localhost:5000/casestrainer/api/health"

# Statistics
$script:CheckCount = 0
$script:FailureCount = 0
$script:LastFailureTime = $null
$script:StartTime = Get-Date
$script:MonitoringActive = $true

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    Write-Host $logEntry -ForegroundColor $(if ($Level -eq "ERROR") { "Red" } elseif ($Level -eq "WARN") { "Yellow" } else { "Green" })
    Add-Content -Path $LogFile -Value $logEntry
}

function Test-ServiceHealth {
    param([string]$Url)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            return @{
                Healthy = $true
                ResponseTime = $response.BaseResponse.ResponseTime
                StatusCode = $response.StatusCode
                Error = $null
            }
        } else {
            return @{
                Healthy = $false
                Error = "HTTP $($response.StatusCode)"
            }
        }
    } catch {
        return @{
            Healthy = $false
            Error = $_.Exception.Message
        }
    }
}

function Test-DockerServices {
    try {
        $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1
        if ($LASTEXITCODE -eq 0) {
            return @{
                Healthy = $true
                Containers = $containers
                Error = $null
            }
        } else {
            return @{
                Healthy = $false
                Error = "Docker command failed"
            }
        }
    } catch {
        return @{
            Healthy = $false
            Error = $_.Exception.Message
        }
    }
}

function Test-RedisConnection {
    try {
        $redisTest = python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping(); print('OK')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            return @{
                Healthy = $true
                Error = $null
            }
        } else {
            return @{
                Healthy = $false
                Error = "Redis connection failed"
            }
        }
    } catch {
        return @{
            Healthy = $false
            Error = $_.Exception.Message
        }
    }
}

function Send-Alert {
    param(
        [string]$Message,
        [string]$Level = "WARN"
    )
    
    $alertMessage = "[CaseStrainer Monitor] $Message"
    Write-Log "Sending alert: $alertMessage" -Level $Level
    
    # Email alert
    if ($AlertEmail -and $Level -eq "ERROR") {
        try {
            Send-MailMessage -To $AlertEmail -Subject "CaseStrainer Alert" -Body $alertMessage -From "monitor@casestrainer.local"
            Write-Log "Email alert sent to $AlertEmail"
        } catch {
            Write-Log "Failed to send email alert: $($_.Exception.Message)" -Level "ERROR"
        }
    }
    
    # Slack alert
    if ($SlackWebhook -and $Level -eq "ERROR") {
        try {
            $slackPayload = @{
                text = $alertMessage
                color = if ($Level -eq "ERROR") { "danger" } else { "warning" }
            } | ConvertTo-Json
            
            Invoke-RestMethod -Uri $SlackWebhook -Method Post -Body $slackPayload -ContentType "application/json"
            Write-Log "Slack alert sent"
        } catch {
            Write-Log "Failed to send Slack alert: $($_.Exception.Message)" -Level "ERROR"
        }
    }
}

function Show-Statistics {
    $uptime = (Get-Date) - $script:StartTime
    $uptimeString = "{0:dd}:{1:hh}:{2:mm}:{3:ss}" -f $uptime.Days, $uptime.Hours, $uptime.Minutes, $uptime.Seconds
    
    Write-Log "=== External Monitoring Statistics ===" -Level "INFO"
    Write-Log "Uptime: $uptimeString" -Level "INFO"
    Write-Log "Total Checks: $($script:CheckCount)" -Level "INFO"
    Write-Log "Failures: $($script:FailureCount)" -Level "INFO"
    Write-Log "Success Rate: $([Math]::Round((($script:CheckCount - $script:FailureCount) / $script:CheckCount) * 100, 2))%" -Level "INFO"
    if ($script:LastFailureTime) {
        Write-Log "Last Failure: $($script:LastFailureTime.ToString('yyyy-MM-dd HH:mm:ss'))" -Level "INFO"
    }
    Write-Log "Log File: $LogFile" -Level "INFO"
}

function Start-ExternalMonitoring {
    Write-Log "Starting external monitoring for CaseStrainer" -Level "INFO"
    Write-Log "Environment: $Environment" -Level "INFO"
    Write-Log "Check Interval: $CheckInterval seconds" -Level "INFO"
    Write-Log "Log File: $LogFile" -Level "INFO"
    Write-Log "Press Ctrl+C to stop monitoring" -Level "INFO"
    Write-Log "========================================" -Level "INFO"
    
    while ($script:MonitoringActive) {
        $script:CheckCount++
        $currentTime = Get-Date
        
        Write-Log "Health check #$($script:CheckCount) at $($currentTime.ToString('HH:mm:ss'))" -Level "DEBUG"
        
        # Test primary health endpoint
        $healthResult = Test-ServiceHealth -Url $HealthCheckUrl
        
        if (-not $healthResult.Healthy) {
            # Try backup endpoint
            $backupResult = Test-ServiceHealth -Url $BackupHealthUrl
            
            if (-not $backupResult.Healthy) {
                $script:FailureCount++
                $script:LastFailureTime = $currentTime
                
                $errorMsg = "Both health endpoints failed. Primary: $($healthResult.Error), Backup: $($backupResult.Error)"
                Write-Log $errorMsg -Level "ERROR"
                
                # Test Docker services
                $dockerResult = Test-DockerServices
                if (-not $dockerResult.Healthy) {
                    Write-Log "Docker services also unhealthy: $($dockerResult.Error)" -Level "ERROR"
                }
                
                # Test Redis
                $redisResult = Test-RedisConnection
                if (-not $redisResult.Healthy) {
                    Write-Log "Redis connection failed: $($redisResult.Error)" -Level "ERROR"
                }
                
                # Send alert
                Send-Alert "Service health check failed. Docker: $($dockerResult.Healthy), Redis: $($redisResult.Healthy)" -Level "ERROR"
            } else {
                Write-Log "Primary endpoint failed but backup is healthy" -Level "WARN"
            }
        } else {
            Write-Log "Health check passed (Response time: $($healthResult.ResponseTime)ms)" -Level "DEBUG"
        }
        
        # Show statistics every 10 checks
        if ($script:CheckCount % 10 -eq 0) {
            Show-Statistics
        }
        
        # Wait for next check
        Start-Sleep -Seconds $CheckInterval
    }
}

# Main execution
try {
    # Create log directory
    if (-not (Test-Path $LogDirectory)) {
        New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
    }
    
    if ($TestMode) {
        Write-Log "Running in test mode - single health check" -Level "INFO"
        $healthResult = Test-ServiceHealth -Url $HealthCheckUrl
        Write-Log "Health check result: $($healthResult.Healthy)" -Level "INFO"
        if (-not $healthResult.Healthy) {
            Write-Log "Error: $($healthResult.Error)" -Level "ERROR"
        }
        exit
    }
    
    Start-ExternalMonitoring
    
} catch [System.Management.Automation.PipelineStoppedException] {
    Write-Log "Received stop signal, shutting down..." -Level "INFO"
} catch {
    Write-Log "Monitoring failed: $($_.Exception.Message)" -Level "ERROR"
    Send-Alert "External monitoring script failed: $($_.Exception.Message)" -Level "ERROR"
    exit 1
} finally {
    Show-Statistics
    Write-Log "External monitoring stopped" -Level "INFO"
} 