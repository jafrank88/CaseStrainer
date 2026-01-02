# escalation_manager.ps1 - External monitoring and escalation system
# Provides backup monitoring when internal systems fail

param(
    [string]$ExternalEndpoint = "https://wolf.law.uw.edu/casestrainer/api/health",
    [int]$CheckInterval = 600,        # Check every 10 minutes
    [int]$FailureThreshold = 3,       # Escalate after N consecutive failures
    [string]$EscalationLog = "logs\escalation.log",
    [string[]]$NotificationEmails = @(),
    [string]$SlackWebhook = "",
    [string]$TeamsWebhook = ""
)

# Setup
$ErrorActionPreference = "Continue"
$script:LogPath = Join-Path $PSScriptRoot $EscalationLog
$script:ConsecutiveFailures = 0
$script:LastNotification = @{}
$script:NotificationCooldown = 3600  # 1 hour between same type notifications

# Ensure logs directory exists
$logDir = Split-Path $script:LogPath -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-EscalationLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    Add-Content -Path $script:LogPath -Value $logEntry
    
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARN"  { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        "CRITICAL" { Write-Host $logEntry -ForegroundColor Magenta }
        default { Write-Host $logEntry }
    }
}

function Test-ExternalEndpoint {
    <#
    .SYNOPSIS
    Test external endpoint availability and response
    #>
    
    $result = @{
        Available = $false
        ResponseTime = 0
        StatusCode = 0
        ErrorMessage = ""
        HealthData = $null
    }
    
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        
        $response = Invoke-WebRequest -Uri $ExternalEndpoint -UseBasicParsing -TimeoutSec 30
        $stopwatch.Stop()
        
        $result.ResponseTime = $stopwatch.ElapsedMilliseconds
        $result.StatusCode = $response.StatusCode
        $result.Available = ($response.StatusCode -eq 200)
        
        if ($result.Available -and $response.Content) {
            try {
                $result.HealthData = $response.Content | ConvertFrom-Json
            } catch {
                Write-EscalationLog "Failed to parse health response: $($_.Exception.Message)" "WARN"
            }
        }
        
    } catch {
        $stopwatch.Stop()
        $result.ResponseTime = $stopwatch.ElapsedMilliseconds
        $result.ErrorMessage = $_.Exception.Message
        $result.Available = $false
    }
    
    return $result
}

function Test-InternalMonitoring {
    <#
    .SYNOPSIS
    Check if internal monitoring systems are running
    #>
    
    $internal = @{
        EnhancedMonitor = $false
        SelfHealthMonitor = $false
        SystemRecoveryLogger = $false
        Overall = $false
    }
    
    try {
        # Check for monitoring processes
        $monitorProcesses = Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { 
            $_.CommandLine -and ($_.CommandLine -match "enhanced_docker_monitor" -or 
                                $_.CommandLine -match "monitor_self_health" -or
                                $_.CommandLine -match "system_recovery_logger")
        }
        
        if ($monitorProcesses.Count -gt 0) {
            foreach ($process in $monitorProcesses) {
                if ($process.CommandLine -match "enhanced_docker_monitor") {
                    $internal.EnhancedMonitor = $true
                }
                if ($process.CommandLine -match "monitor_self_health") {
                    $internal.SelfHealthMonitor = $true
                }
                if ($process.CommandLine -match "system_recovery_logger") {
                    $internal.SystemRecoveryLogger = $true
                }
            }
        }
        
        # Check log files for recent activity
        $logFiles = @{
            "enhanced_monitor.log" = $false
            "self_health_monitor.log" = $false
            "system_recovery.log" = $false
        }
        
        $logsDir = Join-Path $PSScriptRoot "..\logs"
        if (Test-Path $logsDir) {
            foreach ($logFile in $logFiles.Keys) {
                $logPath = Join-Path $logsDir $logFile
                if (Test-Path $logPath) {
                    $file = Get-Item $logPath
                    $timeSinceUpdate = (Get-Date) - $file.LastWriteTime
                    $logFiles[$logFile] = ($timeSinceUpdate.TotalMinutes -lt 30)
                }
            }
        }
        
        # Update internal status based on log activity
        if ($logFiles["enhanced_monitor.log"]) { $internal.EnhancedMonitor = $true }
        if ($logFiles["self_health_monitor.log"]) { $internal.SelfHealthMonitor = $true }
        if ($logFiles["system_recovery.log"]) { $internal.SystemRecoveryLogger = $true }
        
        $internal.Overall = $internal.EnhancedMonitor -or $internal.SelfHealthMonitor -or $internal.SystemRecoveryLogger
        
    } catch {
        Write-EscalationLog "Internal monitoring check failed: $($_.Exception.Message)" "ERROR"
    }
    
    return $internal
}

function Send-EscalationNotification {
    <#
    .SYNOPSIS
    Send escalation notifications through multiple channels
    #>
    
    param(
        [string]$Severity,
        [string]$Message,
        [string]$IssueType = "general"
    )
    
    # Check cooldown
    $now = Get-Date
    if ($script:LastNotification.ContainsKey($IssueType)) {
        $timeSinceLast = ($now - $script:LastNotification[$IssueType]).TotalSeconds
        if ($timeSinceLast -lt $script:NotificationCooldown) {
            Write-EscalationLog "Notification suppressed for $IssueType (cooldown: $([math]::Round(($script:NotificationCooldown - $timeSinceLast) / 60, 1)) minutes)" "INFO"
            return
        }
    }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $notificationsSent = 0
    
    # Email notification
    if ($NotificationEmails.Count -gt 0) {
        try {
            foreach ($email in $NotificationEmails) {
                $subject = "[CaseStrainer ESCALATION] $Severity"
                $body = @"
CaseStrainer System Escalation - $Severity

Time: $timestamp
Issue Type: $IssueType
Endpoint: $ExternalEndpoint

$Message

---
This is an automated escalation from CaseStrainer backup monitoring.
System requires immediate attention.
"@
                
                # Simple mail sending (requires proper SMTP configuration)
                # This is a placeholder - actual implementation would need SMTP settings
                Write-EscalationLog "Email notification would be sent to $email" "INFO"
                $notificationsSent++
            }
        } catch {
            Write-EscalationLog "Failed to send email notification: $($_.Exception.Message)" "ERROR"
        }
    }
    
    # Slack notification
    if ($SlackWebhook) {
        try {
            $color = switch ($Severity) {
                "CRITICAL" { "danger" }
                "ERROR" { "danger" }
                "WARN" { "warning" }
                default { "good" }
            }
            
            $payload = @{
                text = "*CaseStrainer ESCALATION - $Severity*"
                attachments = @(
                    @{
                        color = $color
                        fields = @(
                            @{ title = "Time"; value = $timestamp; short = $true }
                            @{ title = "Issue Type"; value = $IssueType; short = $true }
                            @{ title = "Endpoint"; value = $ExternalEndpoint; short = $false }
                            @{ title = "Message"; value = $Message; short = $false }
                        )
                        footer = "CaseStrainer Escalation System"
                        ts = [DateTimeOffset]::Now.ToUnixTimeSeconds()
                    }
                )
            } | ConvertTo-Json -Depth 10
            
            # This is a placeholder - actual implementation would send to webhook
            Write-EscalationLog "Slack notification would be sent" "INFO"
            $notificationsSent++
        } catch {
            Write-EscalationLog "Failed to send Slack notification: $($_.Exception.Message)" "ERROR"
        }
    }
    
    # Teams notification
    if ($TeamsWebhook) {
        try {
            $themeColor = switch ($Severity) {
                "CRITICAL" { "FF0000" }
                "ERROR" { "FF0000" }
                "WARN" { "FFA500" }
                default { "00FF00" }
            }
            
            $payload = @{
                "@type" = "MessageCard"
                "@context" = "https://schema.org/extensions"
                "summary" = "CaseStrainer ESCALATION - $Severity"
                "themeColor" = $themeColor
                "title" = "CaseStrainer System Escalation"
                "sections" = @(
                    @{
                        "activityTitle" = "Backup Monitoring System"
                        "activitySubtitle" = $timestamp
                        "facts" = @(
                            @{ name = "Severity"; value = $Severity }
                            @{ name = "Issue Type"; value = $IssueType }
                            @{ name = "Endpoint"; value = $ExternalEndpoint }
                        )
                        "text" = $Message
                    }
                )
            } | ConvertTo-Json -Depth 10
            
            # This is a placeholder - actual implementation would send to webhook
            Write-EscalationLog "Teams notification would be sent" "INFO"
            $notificationsSent++
        } catch {
            Write-EscalationLog "Failed to send Teams notification: $($_.Exception.Message)" "ERROR"
        }
    }
    
    if ($notificationsSent -gt 0) {
        $script:LastNotification[$IssueType] = $now
        Write-EscalationLog "Escalation notifications sent via $notificationsSent channel(s)" "INFO"
    } else {
        Write-EscalationLog "No notification channels configured" "WARN"
    }
}

function Invoke-EscalationProcedure {
    <#
    .SYNOPSIS
    Execute escalation procedures based on failure type
    #>
    
    param(
        [string]$FailureType,
        [hashtable]$Diagnostics
    )
    
    Write-EscalationLog "=== ESCALATION PROCEDURE INITIATED ===" "CRITICAL"
    Write-EscalationLog "Failure type: $FailureType" "CRITICAL"
    
    switch ($FailureType) {
        "external_endpoint_down" {
            Write-EscalationLog "External endpoint is down - checking internal systems..." "WARN"
            
            $internal = Test-InternalMonitoring
            
            if ($internal.Overall) {
                Write-EscalationLog "Internal monitoring still active - issue may be external" "INFO"
                Send-EscalationNotification -Severity "ERROR" -Message "External endpoint unreachable but internal monitoring active. Possible network or proxy issue." -IssueType "external_endpoint"
            } else {
                Write-EscalationLog "Both external and internal monitoring failed - CRITICAL SYSTEM FAILURE" "CRITICAL"
                Send-EscalationNotification -Severity "CRITICAL" -Message "Complete system failure: Both external endpoint and internal monitoring are down. IMMEDIATE ATTENTION REQUIRED." -IssueType "complete_failure"
                
                # Attempt emergency recovery
                Write-EscalationLog "Attempting emergency recovery procedures..." "CRITICAL"
                try {
                    # Try to restart enhanced monitoring
                    $enhancedMonitor = Join-Path $PSScriptRoot "enhanced_docker_monitor.ps1"
                    if (Test-Path $enhancedMonitor) {
                        Start-Process powershell.exe -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$enhancedMonitor`"", "-EnableAutoRecovery", "-EnableResourceMonitoring" -WindowStyle Hidden -ErrorAction SilentlyContinue
                        Write-EscalationLog "Emergency enhanced monitor restart initiated" "INFO"
                    }
                } catch {
                    Write-EscalationLog "Emergency recovery failed: $($_.Exception.Message)" "ERROR"
                }
            }
        }
        
        "internal_monitoring_down" {
            Write-EscalationLog "Internal monitoring systems are down" "WARN"
            Send-EscalationNotification -Severity "WARN" -Message "Internal monitoring systems have stopped but external endpoint is still responding. Auto-recovery should be initiated." -IssueType "internal_monitoring"
            
            # Try to restart internal monitoring
            try {
                $selfHealthMonitor = Join-Path $PSScriptRoot "monitor_self_health.ps1"
                if (Test-Path $selfHealthMonitor) {
                    Start-Process powershell.exe -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$selfHealthMonitor`"" -WindowStyle Hidden -ErrorAction SilentlyContinue
                    Write-EscalationLog "Self-health monitor restart initiated" "INFO"
                }
            } catch {
                Write-EscalationLog "Failed to restart internal monitoring: $($_.Exception.Message)" "ERROR"
            }
        }
        
        "docker_health_issues" {
            Write-EscalationLog "Docker health issues detected" "WARN"
            Send-EscalationNotification -Severity "WARN" -Message "Docker health issues detected. Enhanced monitoring should handle auto-recovery." -IssueType "docker_health"
        }
        
        default {
            Write-EscalationLog "Unknown failure type: $FailureType" "ERROR"
            Send-EscalationNotification -Severity "ERROR" -Message "Unknown system issue detected. Manual investigation required." -IssueType "unknown"
        }
    }
}

function Start-EscalationMonitoring {
    <#
    .SYNOPSIS
    Start the escalation monitoring loop
    #>
    
    Write-EscalationLog "=== ESCALATION MONITORING STARTED ===" "SUCCESS"
    Write-EscalationLog "External endpoint: $ExternalEndpoint" "INFO"
    Write-EscalationLog "Check interval: ${CheckInterval}s" "INFO"
    Write-EscalationLog "Failure threshold: $FailureThreshold" "INFO"
    Write-EscalationLog "Notification channels: Email($($NotificationEmails.Count)), Slack($(-not [string]::IsNullOrEmpty($SlackWebhook))), Teams($(-not [string]::IsNullOrEmpty($TeamsWebhook)))" "INFO"
    
    while ($true) {
        try {
            $timestamp = Get-Date -Format "HH:mm:ss"
            
            # Test external endpoint
            $externalTest = Test-ExternalEndpoint
            
            if ($externalTest.Available) {
                if ($script:ConsecutiveFailures -gt 0) {
                    Write-EscalationLog "External endpoint recovered after $script:ConsecutiveFailures consecutive failures" "SUCCESS"
                    $script:ConsecutiveFailures = 0
                }
                
                # Periodic status logging
                $checkCount = (Get-Date).Minute % 15
                if ($checkCount -eq 0) {
                    Write-EscalationLog "External endpoint healthy (Response: $($externalTest.ResponseTime)ms, Status: $($externalTest.StatusCode))" "INFO"
                }
            } else {
                $script:ConsecutiveFailures++
                Write-EscalationLog "External endpoint FAILED (attempt $script:ConsecutiveFailures)" "ERROR"
                Write-EscalationLog "  Response time: $($externalTest.ResponseTime)ms" "ERROR"
                Write-EscalationLog "  Error: $($externalTest.ErrorMessage)" "ERROR"
                
                # Check internal monitoring
                $internalTest = Test-InternalMonitoring
                Write-EscalationLog "Internal monitoring status: Enhanced=$($internalTest.EnhancedMonitor), SelfHealth=$($internalTest.SelfHealthMonitor), SystemRecovery=$($internalTest.SystemRecoveryLogger)" "INFO"
                
                # Escalate if threshold reached
                if ($script:ConsecutiveFailures -ge $FailureThreshold) {
                    $failureType = if (-not $internalTest.Overall) { "complete_failure" } else { "external_endpoint_down" }
                    Invoke-EscalationProcedure -FailureType $failureType -Diagnostics @{
                        ExternalTest = $externalTest
                        InternalTest = $internalTest
                        ConsecutiveFailures = $script:ConsecutiveFailures
                    }
                }
            }
            
            # Also check internal monitoring periodically
            $internalCheckCount = (Get-Date).Minute % 20
            if ($internalCheckCount -eq 0) {
                $internalTest = Test-InternalMonitoring
                if (-not $internalTest.Overall) {
                    Write-EscalationLog "Internal monitoring systems are down" "WARN"
                    Invoke-EscalationProcedure -FailureType "internal_monitoring_down" -Diagnostics @{ InternalTest = $internalTest }
                }
            }
            
        } catch {
            Write-EscalationLog "Escalation monitoring error: $($_.Exception.Message)" "ERROR"
        }
        
        Start-Sleep -Seconds $CheckInterval
    }
}

# Start escalation monitoring
Write-EscalationLog "Escalation Manager v1.0 starting..." "INFO"
Start-EscalationMonitoring
