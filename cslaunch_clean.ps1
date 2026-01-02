# cslaunch.ps1 - Quick restart wrapper for production environment
# This is optimized for fast Python code updates without rebuilding Docker images

param(
    [switch]$Build,
    [switch]$Force,
    [switch]$NoCache,
    [switch]$Monitor,     # Continuous monitoring mode with auto-restart (foreground)
    [switch]$NoMonitor,    # Disable automatic background monitoring (monitoring enabled by default)
    [switch]$ConfigureAutostart,  # Configure Docker autostart on boot
    [switch]$NoAutostart,  # Disable automatic autostart configuration (autostart enabled by default)
    [switch]$ConfigurePeriodicHealthCheck,  # Configure Windows Task Scheduler backup health check (every 2 hours)
    [switch]$RemovePeriodicHealthCheck,  # Remove the periodic health check task
    [int]$MonitorInterval = 30,  # Health check interval in seconds (default: 30)
    [switch]$EnableDockerDaemonMonitor,  # Enable Docker daemon monitoring
    [int]$DockerDaemonTimeout = 15,  # Docker daemon freeze timeout in seconds (default: 15)
    [int]$MaxDockerRestartsPerHour = 8,  # Maximum Docker daemon restarts per hour (default: 8, increased from 6)
    [int]$ExtendedDowntimeMinutes = 15,  # After this many minutes of downtime, bypass rate limit (nuclear option, reduced from 30)
    [bool]$EnableNotifications = $false,  # Notifications disabled - using external WHM monitoring
    
    # Enhanced Monitoring Parameters (for recurring 24-48 hour crash prevention)
    [switch]$EnableEnhancedMonitoring,  # Enable comprehensive monitoring system
    [switch]$EnableSelfHealthMonitoring,  # Enable monitoring self-health checks
    [switch]$EnableSystemRecoveryLogging,  # Enable system reboot detection and recovery logging
    [switch]$EnableEscalationManager,  # Enable external monitoring and escalation
    [switch]$EnableResourceMonitoring,  # Enable Docker resource monitoring
    [switch]$EnableAutoRecovery,  # Enable automatic recovery actions
    [int]$MemoryThreshold = 85,  # Memory usage warning threshold (%)
    [int]$CpuThreshold = 90,  # CPU usage warning threshold (%)
    [int]$EnhancedCheckInterval = 60,  # Enhanced monitoring check interval (seconds)
    [switch]$DeepCleanRestart,  # Perform deep cleanup during Docker restarts
    [switch]$MemoryOptimizeRestart  # Optimize memory before Docker restarts
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CaseStrainer Quick Restart (./cslaunch)" -ForegroundColor Cyan  
Write-Host "========================================`n" -ForegroundColor Cyan

# Setup crash logging
$crashLogPath = Join-Path $PSScriptRoot "logs\crash_log.txt"
$dockerDaemonLogPath = Join-Path $PSScriptRoot "logs\docker_daemon_monitor.log"
$notificationLogPath = Join-Path $PSScriptRoot "logs\notifications.log"
$logsDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# Notification tracking (prevent spam)
$script:LastNotificationTime = @{}  # Track last notification time per issue type

# Remove broken DockerHealthCheck task from archived scripts (if it exists)
try {
    $removed = Remove-BrokenDockerHealthTask
    if ($removed) {
        Write-Host "[CLEANUP] Removed broken DockerHealthCheck task" -ForegroundColor Yellow
    }
} catch {
    # Silently ignore - cleanup is optional
}

function Write-CrashLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $crashLogPath -Value $logEntry
    
    switch ($Level) {
        "ERROR" { Write-Host $Message -ForegroundColor Red }
        "WARN"  { Write-Host $Message -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $Message -ForegroundColor Green }
        default { Write-Host $Message }
    }
}

# Startup notifications disabled - using external WHM monitoring instead
function Send-StartupNotification {
    param([string]$StartupType = "normal")
    # Notifications disabled - external WHM handles monitoring
    return
}

# Admin notifications disabled - using external WHM monitoring instead
function Send-AdminNotification {
    param(
        [string]$Subject,
        [string]$Message,
        [string]$Severity = "ERROR",
        [string]$IssueType = "general"
    )
    # Notifications disabled - external WHM handles monitoring
    return
    
    # Check cooldown period
    $now = Get-Date
    if ($script:LastNotificationTime.ContainsKey($IssueType)) {
        $lastNotification = $script:LastNotificationTime[$IssueType]
        $minutesSinceLastNotification = ($now - $lastNotification).TotalMinutes
        
        if ($minutesSinceLastNotification -lt $NotificationCooldownMinutes) {
            $remainingMinutes = [math]::Round($NotificationCooldownMinutes - $minutesSinceLastNotification)
            Write-DockerDaemonLog "Notification suppressed (cooldown: ${remainingMinutes} minutes remaining)" "INFO"
            return
        }
    }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $fullMessage = @"
CaseStrainer Alert - $Severity

Time: $timestamp
Issue Type: $IssueType

$Message

---
This is an automated alert from CaseStrainer monitoring system.
Logs: $crashLogPath
Docker Daemon Logs: $dockerDaemonLogPath
"@
    
    $notificationsSent = 0
    
    # Send email notification
    if ($NotificationEmail) {
        try {
            $smtpServer = if ($env:SMTP_SERVER) { $env:SMTP_SERVER } else { "localhost" }
            $smtpPort = if ($env:SMTP_PORT) { [int]$env:SMTP_PORT } else { 25 }
            $useSsl = ($env:SMTP_USE_TLS -eq "true" -or $env:SMTP_USE_SSL -eq "true")
            
            # Build email parameters
            $emailParams = @{
                To = $NotificationEmail
                Subject = "[CaseStrainer] $Subject"
                Body = $fullMessage
                From = "CaseStrainer Monitor <noreply@casestrainer.local>"
                SmtpServer = $smtpServer
                Port = $smtpPort
            }
            
            # Add SSL/TLS if configured
            if ($useSsl) {
                $emailParams['UseSsl'] = $true
            }
            
            # Add authentication if provided
            if ($env:SMTP_USERNAME -and $env:SMTP_PASSWORD) {
                # Use encrypted secure string instead of plaintext
                try {
                    # Try to use encrypted password from environment variable or secure storage
                    $securePassword = $null
                    if ($env:SMTP_PASSWORD_ENCRYPTED) {
                        # Use pre-encrypted password if available
                        $securePassword = ConvertTo-SecureString $env:SMTP_PASSWORD_ENCRYPTED
                    } elseif ($env:SMTP_PASSWORD) {
                        # Fallback to plaintext with security warning
                        Write-DockerDaemonLog "WARNING: Using plaintext SMTP password - consider using encrypted credentials" "WARN"
                        $securePassword = ConvertTo-SecureString $env:SMTP_PASSWORD -AsPlainText -Force
                    }
                    
                    if ($securePassword) {
                        $credential = New-Object System.Management.Automation.PSCredential($env:SMTP_USERNAME, $securePassword)
                        $emailParams['Credential'] = $credential
                    }
                } catch {
                    Write-DockerDaemonLog "Failed to create SMTP credentials: $($_.Exception.Message)" "ERROR"
                }
            }
            
            Send-MailMessage @emailParams -ErrorAction Stop
            Write-DockerDaemonLog "Email notification sent to $NotificationEmail" "INFO"
            Add-Content -Path $notificationLogPath -Value "[$timestamp] EMAIL SENT: $Subject to $NotificationEmail"
            $notificationsSent++
        } catch {
            Write-DockerDaemonLog "Failed to send email notification: $($_.Exception.Message)" "ERROR"
            Add-Content -Path $notificationLogPath -Value "[$timestamp] EMAIL FAILED: $($_.Exception.Message)"
            # Don't fail the script if notification fails
        }
    }
    
    # Send Slack notification
    if ($SlackWebhook) {
        try {
            $slackColor = switch ($Severity) {
                "CRITICAL" { "danger" }
                "ERROR" { "danger" }
                "WARN" { "warning" }
                "INFO" { "good" }
                default { "good" }
            }
            
            $slackPayload = @{
                text = "*CaseStrainer Alert - $Severity*"
                attachments = @(
                    @{
                        color = $slackColor
                        fields = @(
                            @{
                                title = "Time"
                                value = $timestamp
                                short = $true
                            },
                            @{
                                title = "Issue Type"
                                value = $IssueType
                                short = $true
                            },
                            @{
                                title = "Message"
                                value = $Message
                                short = $false
                            }
                        )
                        footer = "CaseStrainer Monitoring"
                        ts = [DateTimeOffset]::Now.ToUnixTimeSeconds()
                    }
                )
            } | ConvertTo-Json -Depth 10
            
            Invoke-RestMethod -Uri $SlackWebhook -Method Post -Body $slackPayload -ContentType "application/json" -ErrorAction Stop
            Write-DockerDaemonLog "Slack notification sent" "INFO"
            Add-Content -Path $notificationLogPath -Value "[$timestamp] SLACK SENT: $Subject"
            $notificationsSent++
        } catch {
            Write-DockerDaemonLog "Failed to send Slack notification: $($_.Exception.Message)" "ERROR"
            Add-Content -Path $notificationLogPath -Value "[$timestamp] SLACK FAILED: $($_.Exception.Message)"
        }
    }
    
    # Send Microsoft Teams notification
    if ($TeamsWebhook) {
        try {
            # Teams uses a different format - MessageCard or Adaptive Card
            # Using MessageCard format (simpler and widely supported)
            $teamsThemeColor = switch ($Severity) {
                "CRITICAL" { "FF0000" }  # Red
                "ERROR" { "FF0000" }     # Red
                "WARN" { "FFA500" }      # Orange
                "INFO" { "00FF00" }      # Green
                default { "00FF00" }     # Green
            }
            
            # Truncate message if too long (Teams has limits)
            $teamsMessage = $Message
            if ($teamsMessage.Length -gt 2000) {
                $teamsMessage = $teamsMessage.Substring(0, 1997) + "..."
            }
            
            $teamsPayload = @{
                "@type" = "MessageCard"
                "@context" = "https://schema.org/extensions"
                "summary" = "CaseStrainer Alert - $Severity"
                "themeColor" = $teamsThemeColor
                "title" = "CaseStrainer Alert - $Severity"
                "sections" = @(
                    @{
                        "activityTitle" = "CaseStrainer Monitoring System"
                        "activitySubtitle" = $timestamp
                        "facts" = @(
                            @{
                                "name" = "Severity"
                                "value" = $Severity
                            },
                            @{
                                "name" = "Issue Type"
                                "value" = $IssueType
                            },
                            @{
                                "name" = "Time"
                                "value" = $timestamp
                            }
                        )
                        "text" = $teamsMessage
                    }
                )
                "potentialAction" = @(
                    @{
                        "@type" = "OpenUri"
                        "name" = "View Logs"
                        "targets" = @(
                            @{
                                "os" = "default"
                                "uri" = "file:///$($crashLogPath.Replace('\', '/'))"
                            }
                        )
                    }
                )
            } | ConvertTo-Json -Depth 10
            
            Invoke-RestMethod -Uri $TeamsWebhook -Method Post -Body $teamsPayload -ContentType "application/json" -ErrorAction Stop
            Write-DockerDaemonLog "Microsoft Teams notification sent" "INFO"
            Add-Content -Path $notificationLogPath -Value "[$timestamp] TEAMS SENT: $Subject"
            $notificationsSent++
        } catch {
            Write-DockerDaemonLog "Failed to send Teams notification: $($_.Exception.Message)" "ERROR"
            Add-Content -Path $notificationLogPath -Value "[$timestamp] TEAMS FAILED: $($_.Exception.Message)"
        }
    }
    
    # Update last notification time
    if ($notificationsSent -gt 0) {
        $script:LastNotificationTime[$IssueType] = $now
        Write-DockerDaemonLog "Notification sent via $notificationsSent channel(s)" "INFO"
    } else {
        # Check if channels are configured but failed vs not configured at all
        $configuredChannels = @()
        if ($NotificationEmail) { $configuredChannels += "Email" }
        if ($SlackWebhook) { $configuredChannels += "Slack" }
        if ($TeamsWebhook) { $configuredChannels += "Teams" }
        
        if ($configuredChannels.Count -gt 0) {
            Write-DockerDaemonLog "Notification channels configured but all failed: $($configuredChannels -join ', ')" "WARN"
        } else {
            Write-DockerDaemonLog "No notification channels configured - set CASESTRAINER_ADMIN_EMAIL, CASESTRAINER_SLACK_WEBHOOK, or CASESTRAINER_TEAMS_WEBHOOK" "WARN"
        }
    }
}

function Get-ContainerStatus {
    param([string]$ContainerName)
    
    $status = docker inspect $ContainerName --format='{{.State.Status}}' 2>$null
    $exitCode = docker inspect $ContainerName --format='{{.State.ExitCode}}' 2>$null
    $restartCount = docker inspect $ContainerName --format='{{.RestartCount}}' 2>$null
    $health = docker inspect $ContainerName --format='{{.State.Health.Status}}' 2>$null
    
    return @{
        Status = $status
        ExitCode = $exitCode
        RestartCount = $restartCount
        Health = $health
    }
}

function Get-ContainerCrashInfo {
    param([string]$ContainerName)
    
    Write-CrashLog "Analyzing crash for container: $ContainerName" "WARN"
    
    # Get container status details
    $info = Get-ContainerStatus $ContainerName
    Write-CrashLog "  Status: $($info.Status), Exit Code: $($info.ExitCode), Restart Count: $($info.RestartCount)" "INFO"
    
    # Get last 100 lines of logs (increased for better diagnostics)
    Write-CrashLog "  Fetching last 100 log lines..." "INFO"
    $logs = docker logs --tail 100 $ContainerName 2>&1
    
    # Get container resource limits
    Write-CrashLog "  Checking container resource limits..." "INFO"
    $memLimit = docker inspect $ContainerName --format='{{.HostConfig.Memory}}' 2>$null
    $cpuLimit = docker inspect $ContainerName --format='{{.HostConfig.CpuQuota}}' 2>$null
    if ($memLimit -and $memLimit -ne '0') {
        $memLimitMB = [math]::Round([int]$memLimit / 1MB, 2)
        Write-CrashLog "  Memory Limit: ${memLimitMB} MB" "INFO"
    }
    if ($cpuLimit -and $cpuLimit -ne '0') {
        Write-CrashLog "  CPU Limit: $cpuLimit" "INFO"
    }
    
    # Get container uptime before crash
    $startedAt = docker inspect $ContainerName --format='{{.State.StartedAt}}' 2>$null
    $finishedAt = docker inspect $ContainerName --format='{{.State.FinishedAt}}' 2>$null
    if ($startedAt -and $finishedAt -and $startedAt -ne $finishedAt) {
        Write-CrashLog "  Container started at: $startedAt" "INFO"
        Write-CrashLog "  Container finished at: $finishedAt" "INFO"
    }
    
    # Look for common error patterns
    $errorPatterns = @(
        # Memory and resource issues
        @{Pattern='Out of memory'; Description='Memory limit exceeded'},
        @{Pattern='Cannot allocate memory'; Description='System memory exhausted'},
        @{Pattern='Killed'; Description='Process killed (likely OOM)'},
        @{Pattern='MemoryError'; Description='Python memory error'},
        @{Pattern='Resource temporarily unavailable'; Description='System resource exhaustion'},
        
        # Network and connection issues
        @{Pattern='Connection refused'; Description='Service connection failed'},
        @{Pattern='Connection reset'; Description='Connection was reset by peer'},
        @{Pattern='Connection timed out'; Description='Connection timeout'},
        @{Pattern='Address already in use'; Description='Port conflict'},
        @{Pattern='ECONNREFUSED'; Description='Connection refused error'},
        @{Pattern='ETIMEDOUT'; Description='Connection timeout error'},
        
        # Redis specific errors
        @{Pattern='redis.exceptions'; Description='Redis connection issue'},
        @{Pattern='Error.*connecting to.*6379'; Description='Redis connection failure'},
        @{Pattern='redis.*ConnectionError'; Description='Redis connection error'},
        @{Pattern='redis.*TimeoutError'; Description='Redis timeout'},
        @{Pattern='NOAUTH.*authentication required'; Description='Redis authentication failed'},
        
        # Python errors
        @{Pattern='ModuleNotFoundError'; Description='Missing Python dependency'},
        @{Pattern='ImportError'; Description='Python import error'},
        @{Pattern='SyntaxError'; Description='Python syntax error'},
        @{Pattern='IndentationError'; Description='Python indentation error'},
        @{Pattern='AttributeError'; Description='Python attribute error'},
        @{Pattern='TypeError'; Description='Python type error'},
        @{Pattern='KeyError'; Description='Python key error'},
        @{Pattern='ValueError'; Description='Python value error'},
        @{Pattern='FileNotFoundError'; Description='File not found'},
        @{Pattern='PermissionError'; Description='File permission denied'},
        
        # Flask/WSGI errors
        @{Pattern='werkzeug.exceptions'; Description='Flask/WSGI error'},
        @{Pattern='500 Internal Server Error'; Description='Internal server error'},
        @{Pattern='502 Bad Gateway'; Description='Bad gateway (upstream error)'},
        @{Pattern='503 Service Unavailable'; Description='Service unavailable'},
        @{Pattern='RequestEntityTooLarge'; Description='Request too large'},
        
        # RQ (Redis Queue) errors
        @{Pattern='rq.*Worker'; Description='RQ worker error'},
        @{Pattern='Job.*failed'; Description='RQ job failure'},
        @{Pattern='No such job'; Description='RQ job not found'},
        
        # Database errors
        @{Pattern='sqlite3.*'; Description='SQLite database error'},
        @{Pattern='OperationalError'; Description='Database operational error'},
        @{Pattern='Database.*locked'; Description='Database locked'},
        
        # Docker/Container errors
        @{Pattern='container.*not found'; Description='Container not found'},
        @{Pattern='Cannot connect to the Docker daemon'; Description='Docker daemon not accessible'},
        @{Pattern='OCI runtime create failed'; Description='Container runtime error'},
        
        # System errors
        @{Pattern='FATAL'; Description='Fatal error occurred'},
        @{Pattern='panic'; Description='Application panic'},
        @{Pattern='segmentation fault'; Description='Memory access violation'},
        @{Pattern='SIGSEGV'; Description='Segmentation fault signal'},
        @{Pattern='SIGKILL'; Description='Process killed'},
        @{Pattern='SIGTERM'; Description='Process terminated'},
        
        # Application-specific errors
        @{Pattern='CaseStrainerError'; Description='CaseStrainer application error'},
        @{Pattern='CitationExtractionError'; Description='Citation extraction failed'},
        @{Pattern='CitationClusteringError'; Description='Citation clustering failed'},
        @{Pattern='Timeout.*exceeded'; Description='Operation timeout'},
        @{Pattern='Rate limit'; Description='API rate limit exceeded'},
        @{Pattern='429 Too Many Requests'; Description='Rate limit exceeded'},
        
        # SSL/TLS errors
        @{Pattern='SSL.*error'; Description='SSL/TLS error'},
        @{Pattern='certificate.*verify failed'; Description='SSL certificate verification failed'},
        @{Pattern='CERTIFICATE_VERIFY_FAILED'; Description='Certificate verification failed'}
    )
    
    $foundErrors = @()
    foreach ($pattern in $errorPatterns) {
        if ($logs -match $pattern.Pattern) {
            $foundErrors += $pattern.Description
            Write-CrashLog "  FOUND: $($pattern.Description)" "ERROR"
        }
    }
    
    # Get detailed resource usage if container is still running
    $memStats = docker stats $ContainerName --no-stream --format "{{.MemUsage}}" 2>$null
    $cpuStats = docker stats $ContainerName --no-stream --format "{{.CPUPerc}}" 2>$null
    if ($memStats) {
        Write-CrashLog "  Current Memory Usage: $memStats" "INFO"
    }
    if ($cpuStats) {
        Write-CrashLog "  Current CPU Usage: $cpuStats" "INFO"
    }
    
    # Analyze exit code for common issues
    if ($info.ExitCode -ne '0' -and $info.ExitCode) {
        $exitCodeMeaning = switch ([int]$info.ExitCode) {
            1 { 'General error' }
            2 { 'Misuse of shell command' }
            126 { 'Command invoked cannot execute' }
            127 { 'Command not found' }
            128 { 'Invalid argument to exit' }
            130 { 'Script terminated by Ctrl+C' }
            137 { 'Process killed (SIGKILL) - likely OOM killer' }
            143 { 'Process terminated (SIGTERM)' }
            default { 'Unknown exit code' }
        }
        Write-CrashLog "  Exit Code $($info.ExitCode): $exitCodeMeaning" "ERROR"
    }
    
    # Check if container is in restart loop
    if ([int]$info.RestartCount -gt 5) {
        Write-CrashLog "  WARNING: Container has restarted $($info.RestartCount) times - possible restart loop!" "ERROR"
    }
    
    # Save comprehensive crash report
    $errorSummary = if ($foundErrors.Count -gt 0) { $foundErrors -join "; " } else { "None detected" }
    $exitCodeMeaning = if ($info.ExitCode -ne '0' -and $info.ExitCode) {
        switch ([int]$info.ExitCode) {
            1 { 'General error' }
            2 { 'Misuse of shell command' }
            126 { 'Command invoked cannot execute' }
            127 { 'Command not found' }
            128 { 'Invalid argument to exit' }
            130 { 'Script terminated by Ctrl+C' }
            137 { 'Process killed (SIGKILL) - likely OOM killer' }
            143 { 'Process terminated (SIGTERM)' }
            default { 'Unknown exit code' }
        }
    } else { 'N/A' }
    
    $crashReport = @"

========== CRASH REPORT: $ContainerName ==========
Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Status: $($info.Status)
Exit Code: $($info.ExitCode) ($exitCodeMeaning)
Restart Count: $($info.RestartCount)
Health: $($info.Health)
Started At: $startedAt
Finished At: $finishedAt
Memory Limit: $memLimitMB MB
CPU Limit: $cpuLimit
Current Memory: $memStats
Current CPU: $cpuStats

--- Detected Error Patterns ---
$errorSummary

--- Last 100 Log Lines ---
$($logs | Out-String)
==========================================

"@
    
    Add-Content -Path $crashLogPath -Value $crashReport
    
    return @{
        Status = $info.Status
        ExitCode = $info.ExitCode
        RestartCount = $info.RestartCount
        Health = $info.Health
        Errors = $foundErrors
        LastLogs = $logs
    }
}

function Test-DockerAutostartConfigured {
    <#
    .SYNOPSIS
        Checks if Docker autostart is configured for system boot.
    #>
    $TaskName = "CaseStrainer-Docker-AutoStart"
    $Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    return ($Task -ne $null)
}

function Remove-BrokenDockerHealthTask {
    <#
    .SYNOPSIS
        Removes the broken DockerHealthCheck scheduled task from old scripts.
        This task was created by archived scripts and references non-existent files.
    #>
    param(
        [switch]$Silent
    )
    
    try {
        $BrokenTaskName = "DockerHealthCheck"
        $Task = Get-ScheduledTask -TaskName $BrokenTaskName -ErrorAction SilentlyContinue
        
        if ($Task) {
            Unregister-ScheduledTask -TaskName $BrokenTaskName -Confirm:$false -ErrorAction Stop
            
            if (-not $Silent) {
                Write-Host "[CLEANUP] Removed broken '$BrokenTaskName' task (references archived scripts)" -ForegroundColor Yellow
            }
            return $true
        }
    } catch {
        if (-not $Silent) {
            Write-Host "[WARN] Could not remove broken task: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        return $false
    }
    
    return $false
}

function Install-DockerAutostart {
    <#
    .SYNOPSIS
        Installs Docker autostart configuration for system boot.
    #>
    param(
        [switch]$Silent
    )
    
    if (-not $Silent) {
        Write-Host "`n[CONFIG] Configuring Docker autostart on boot..." -ForegroundColor Yellow
    }
    
    # Check if already configured
    if (Test-DockerAutostartConfigured) {
        if (-not $Silent) {
            Write-Host "  [OK] Docker autostart already configured" -ForegroundColor Green
        }
        return $true
    }
    
    # Check if running as administrator
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if (-not $isAdmin) {
        if (-not $Silent) {
            Write-Host "  [WARN] Administrator privileges required to configure autostart" -ForegroundColor Yellow
            Write-Host "         Run as Administrator to enable automatic startup on boot" -ForegroundColor Gray
        }
        return $false
    }
    
    # Create autostart script if it doesn't exist
    $autostartScript = Join-Path $PSScriptRoot "scripts\docker-autostart.ps1"
    if (-not (Test-Path $autostartScript)) {
        if (-not $Silent) {
            Write-Host "  [*] Creating autostart script..." -ForegroundColor Gray
        }
        
        $composeFile = Join-Path $PSScriptRoot "docker-compose.prod.yml"
        $startupScriptContent = @"
# CaseStrainer Auto-Start Script
# This script waits for Docker to be ready, then starts containers

`$ErrorActionPreference = "SilentlyContinue"
`$ProjectPath = "$PSScriptRoot"
`$ComposeFile = Join-Path `$ProjectPath "docker-compose.prod.yml"
`$LogFile = Join-Path `$ProjectPath "logs\autostart.log"

# Create logs directory if it doesn't exist
`$LogDir = Split-Path `$LogFile
if (-not (Test-Path `$LogDir)) {
    New-Item -ItemType Directory -Path `$LogDir -Force | Out-Null
}

function Write-Log {
    param([string]`$Message)
    `$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    `$LogMessage = "[`$Timestamp] `$Message"
    Add-Content -Path `$LogFile -Value `$LogMessage
}

Write-Log "=== CaseStrainer Auto-Start ==="
Write-Log "Waiting for Docker to be ready..."

# Wait for Docker daemon (max 5 minutes)
`$MaxWait = 300
`$Waited = 0
`$DockerReady = `$false

while (`$Waited -lt `$MaxWait) {
    `$DockerInfo = docker info 2>&1
    if (`$LASTEXITCODE -eq 0) {
        `$DockerReady = `$true
        Write-Log "Docker is ready!"
        break
    }
    Start-Sleep -Seconds 10
    `$Waited += 10
    Write-Log "Still waiting for Docker... (`$Waited seconds)"
}

if (-not `$DockerReady) {
    Write-Log "[ERROR] Docker did not become ready within `$MaxWait seconds"
    exit 1
}

# Additional wait for Docker Desktop to fully initialize
Write-Log "Waiting for Docker Desktop to fully initialize..."
Start-Sleep -Seconds 30

# Start containers
Write-Log "Starting CaseStrainer containers..."
Push-Location `$ProjectPath
docker-compose -f `$ComposeFile up -d 2>&1 | Tee-Object -FilePath (Join-Path `$ProjectPath "logs\docker-startup.log")

if (`$LASTEXITCODE -eq 0) {
    Write-Log "[SUCCESS] Containers started successfully"
} else {
    Write-Log "[ERROR] Failed to start containers (exit code: `$LASTEXITCODE)"
    exit 1
}

Pop-Location
Write-Log "=== Auto-Start Complete ==="
"@
        
        $startupScriptContent | Out-File -FilePath $autostartScript -Encoding UTF8 -Force
    }
    
    # Create Docker Desktop startup shortcut
    $dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path $dockerDesktopPath)) {
        $dockerDesktopPath = "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
    }
    
    if (Test-Path $dockerDesktopPath) {
        $startupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
        $shortcutPath = Join-Path $startupFolder "Docker Desktop.lnk"
        
        if (-not (Test-Path $shortcutPath)) {
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut($shortcutPath)
            $Shortcut.TargetPath = $dockerDesktopPath
            $Shortcut.WorkingDirectory = Split-Path $dockerDesktopPath
            $Shortcut.Save()
        }
    }
    
    # Create scheduled task
    $TaskName = "CaseStrainer-Docker-AutoStart"
    $TaskDescription = "Automatically starts CaseStrainer Docker containers on system boot"
    
    try {
        # Remove existing task if it exists
        $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($ExistingTask) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        }
        
        # Create the action
        $Action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
            -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$autostartScript`"" `
            -WorkingDirectory $PSScriptRoot
        
        # Create the trigger (on system startup, with delay)
        $Trigger = New-ScheduledTaskTrigger -AtStartup
        $Trigger.Delay = "PT2M"  # Wait 2 minutes after boot
        
        # Create settings
        $Settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RestartCount 3 `
            -RestartInterval (New-TimeSpan -Minutes 5)
        
        # Register the task as current user with password (allows starting Docker Desktop)
        # This requires the user to enter their password
        Write-Host "  [*] Registering task to run as current user..." -ForegroundColor Gray
        Write-Host "      You may be prompted for your Windows password." -ForegroundColor Yellow
        
        # Use schtasks to register with /RU current user - this prompts for password
        $taskXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
      <Delay>PT2M</Delay>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$env:USERDOMAIN\$env:USERNAME</UserId>
      <LogonType>Password</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT5M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>PowerShell.exe</Command>
      <Arguments>-NoProfile -ExecutionPolicy Bypass -File "$autostartScript"</Arguments>
      <WorkingDirectory>$PSScriptRoot</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@
        
        $taskXmlPath = Join-Path $PSScriptRoot "scripts\task-config.xml"
        $taskXml | Out-File -FilePath $taskXmlPath -Encoding Unicode -Force
        
        # Register using schtasks which will prompt for password
        $result = schtasks /Create /TN $TaskName /XML $taskXmlPath /RU "$env:USERDOMAIN\$env:USERNAME" /F 2>&1
        Remove-Item $taskXmlPath -Force -ErrorAction SilentlyContinue
        
        if (-not $Silent) {
            Write-Host "  [OK] Docker autostart configured successfully" -ForegroundColor Green
            Write-Host "       Containers will start automatically 2 minutes after boot" -ForegroundColor Gray
        }
        return $true
    } catch {
        if (-not $Silent) {
            Write-Host "  [ERROR] Failed to configure autostart: $($_.Exception.Message)" -ForegroundColor Red
        }
        return $false
    }
}

function Configure-PeriodicHealthCheck {
    <#
    .SYNOPSIS
    Creates a Windows Task Scheduler job that runs every 30 minutes to check Docker health
    and restart if needed. This is a backup safety net in case the main monitoring stops.
    Enhanced to run more frequently (every 30 min instead of 2 hours) to catch extended outages.
    #>
    param(
        [switch]$Remove,
        [switch]$Silent
    )
    
    $TaskName = "CaseStrainer-Docker-HealthCheck"
    $TaskDescription = "Periodic Docker health check - backup for main monitoring (runs every 30 minutes)"
    
    if ($Remove) {
        $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            if (-not $Silent) {
                Write-Host "  [OK] Removed periodic health check task" -ForegroundColor Green
            }
        } else {
            if (-not $Silent) {
                Write-Host "  [INFO] Periodic health check task not found" -ForegroundColor Gray
            }
        }
        return $true
    }
    
    try {
        # Create a simple health check script inline
        $healthCheckScript = @'
# CaseStrainer Periodic Health Check
# This runs every 2 hours as a backup to the main monitoring

$ErrorActionPreference = "Continue"
$logFile = Join-Path $PSScriptRoot "logs\periodic_health_check.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $entry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $logFile -Value $entry -ErrorAction SilentlyContinue
}

Write-Log "=== PERIODIC HEALTH CHECK STARTED ===" "INFO"

# Check if Docker is responding
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Docker info failed - Docker may be frozen" "ERROR"
        
        # Try to restart Docker Desktop
        Write-Log "Attempting Docker Desktop restart..." "WARN"
        Get-Process "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 60
        
        # Start containers
        Write-Log "Starting containers..." "INFO"
        Set-Location $PSScriptRoot
        docker-compose -f docker-compose.prod.yml up -d 2>&1
        Write-Log "Containers started" "SUCCESS"
    } else {
        # Check if containers are running
        $containers = docker ps --format "{{.Names}}" 2>&1
        $expectedContainers = @("casestrainer-backend-prod", "casestrainer-nginx-prod", "casestrainer-redis-prod")
        $allRunning = $true
        
        foreach ($expected in $expectedContainers) {
            if ($containers -notcontains $expected) {
                Write-Log "Container $expected not running" "WARN"
                $allRunning = $false
            }
        }
        
        if (-not $allRunning) {
            Write-Log "Some containers not running - starting..." "WARN"
            Set-Location $PSScriptRoot
            docker-compose -f docker-compose.prod.yml up -d 2>&1
            Write-Log "Containers started" "SUCCESS"
        } else {
            Write-Log "All containers healthy" "SUCCESS"
        }
    }
} catch {
    Write-Log "Health check error: $($_.Exception.Message)" "ERROR"
}

Write-Log "=== PERIODIC HEALTH CHECK COMPLETED ===" "INFO"
'@
        
        $healthCheckScriptPath = Join-Path $PSScriptRoot "scripts\periodic_health_check.ps1"
        $healthCheckScript | Out-File -FilePath $healthCheckScriptPath -Encoding UTF8 -Force
        
        # Remove existing task
        $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        }
        
        # Create task XML for repeating every 30 minutes (enhanced safety net)
        $taskXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <Repetition>
        <Interval>PT30M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2025-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$env:USERDOMAIN\$env:USERNAME</UserId>
      <LogonType>Password</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>true</WakeToRun>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>PowerShell.exe</Command>
      <Arguments>-NoProfile -ExecutionPolicy Bypass -File "$healthCheckScriptPath"</Arguments>
      <WorkingDirectory>$PSScriptRoot</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@
        
        $taskXmlPath = Join-Path $PSScriptRoot "scripts\health-check-task.xml"
        $taskXml | Out-File -FilePath $taskXmlPath -Encoding Unicode -Force
        
        # Register the task
        if (-not $Silent) {
            Write-Host "  [*] Registering periodic health check task..." -ForegroundColor Gray
            Write-Host "      You may be prompted for your Windows password." -ForegroundColor Yellow
        }
        
        $result = schtasks /Create /TN $TaskName /XML $taskXmlPath /RU "$env:USERDOMAIN\$env:USERNAME" /F 2>&1
        Remove-Item $taskXmlPath -Force -ErrorAction SilentlyContinue
        
        if ($LASTEXITCODE -eq 0) {
            if (-not $Silent) {
                Write-Host "  [OK] Periodic health check task created successfully" -ForegroundColor Green
                Write-Host "       Docker health will be checked every 2 hours as a backup" -ForegroundColor Gray
                Write-Host "       Script: $healthCheckScriptPath" -ForegroundColor Gray
            }
            return $true
        } else {
            if (-not $Silent) {
                Write-Host "  [ERROR] Failed to create task: $result" -ForegroundColor Red
            }
            return $false
        }
    } catch {
        if (-not $Silent) {
            Write-Host "  [ERROR] Failed to configure periodic health check: $($_.Exception.Message)" -ForegroundColor Red
        }
        return $false
    }
}

function Write-DockerDaemonLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $dockerDaemonLogPath -Value $logEntry
    
    switch ($Level) {
        "ERROR" { Write-Host $Message -ForegroundColor Red }
        "WARN"  { Write-Host $Message -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $Message -ForegroundColor Green }
        default { Write-Host $Message }
    }
}

function Test-DockerDaemonHealth {
    param([int]$TimeoutSeconds = 15)
    
    $healthChecks = @{
        DockerInfo = $false
        DockerVersion = $false
        DockerPs = $false
        DockerService = $false
    }
    
    # Check 1: Docker info (most basic check)
    try {
        $job = Start-Job -ScriptBlock { docker info 2>&1 }
        if (Wait-Job $job -Timeout $TimeoutSeconds) {
            $output = Receive-Job $job
            Remove-Job $job -Force
            if ($LASTEXITCODE -eq 0) {
                $healthChecks.DockerInfo = $true
            }
        } else {
            Stop-Job $job -ErrorAction SilentlyContinue
            Remove-Job $job -Force -ErrorAction SilentlyContinue
            Write-DockerDaemonLog "Docker info check timed out after ${TimeoutSeconds}s" "WARN"
        }
    } catch {
        Write-DockerDaemonLog "Docker info check failed: $($_.Exception.Message)" "WARN"
    }
    
    # Check 2: Docker version (quick check)
    if ($healthChecks.DockerInfo) {
        try {
            $job = Start-Job -ScriptBlock { docker version --format '{{.Server.Version}}' 2>&1 }
            if (Wait-Job $job -Timeout 5) {
                $output = Receive-Job $job
                Remove-Job $job -Force
                if ($LASTEXITCODE -eq 0 -and $output) {
                    $healthChecks.DockerVersion = $true
                }
            } else {
                Stop-Job $job -ErrorAction SilentlyContinue
                Remove-Job $job -Force -ErrorAction SilentlyContinue
            }
        } catch {
            # Non-critical
        }
    }
    
    # Check 3: Docker ps (list containers)
    if ($healthChecks.DockerInfo) {
        try {
            $job = Start-Job -ScriptBlock { docker ps --format '{{.Names}}' 2>&1 }
            if (Wait-Job $job -Timeout 10) {
                $output = Receive-Job $job
                Remove-Job $job -Force
                if ($LASTEXITCODE -eq 0) {
                    $healthChecks.DockerPs = $true
                }
            } else {
                Stop-Job $job -ErrorAction SilentlyContinue
                Remove-Job $job -Force -ErrorAction SilentlyContinue
            }
        } catch {
            # Non-critical
        }
    }
    
    # Check 4: Docker service status (Windows)
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($service -and $service.Status -eq 'Running') {
            $healthChecks.DockerService = $true
        }
    } catch {
        # Service might not exist or be accessible
    }
    
    return $healthChecks
}

function Get-DockerProcessStats {
    $stats = @{
        Processes = @()
        TotalMemoryMB = 0
        HighCPUProcesses = @()
    }
    
    try {
        $dockerProcesses = Get-Process | Where-Object { 
            $_.ProcessName -like "*docker*" -or 
            $_.ProcessName -like "*com.docker*" 
        } | Select-Object ProcessName, Id, @{Name='CPU';Expression={$_.CPU}}, @{Name='MemoryMB';Expression={[math]::Round($_.WorkingSet64/1MB,2)}}
        
        foreach ($proc in $dockerProcesses) {
            $stats.Processes += $proc
            $stats.TotalMemoryMB += $proc.MemoryMB
            
            # Check for high CPU (if CPU > 100, it's likely a problem)
            if ($proc.CPU -gt 100) {
                $stats.HighCPUProcesses += $proc
            }
        }
    } catch {
        Write-DockerDaemonLog "Failed to get Docker process stats: $($_.Exception.Message)" "WARN"
    }
    
    return $stats
}

function Restart-DockerDaemon {
    param([string]$Reason = "Freeze detected")
    
    Write-DockerDaemonLog "=== DOCKER DAEMON RESTART INITIATED ===" "WARN"
    Write-DockerDaemonLog "Reason: $Reason" "WARN"
    Write-CrashLog "Docker daemon restart initiated: $Reason" "WARN"
    
    # Get process stats before restart
    $beforeStats = Get-DockerProcessStats
    Write-DockerDaemonLog "Process stats before restart:" "INFO"
    Write-DockerDaemonLog "  Total Memory: $($beforeStats.TotalMemoryMB) MB" "INFO"
    Write-DockerDaemonLog "  High CPU Processes: $($beforeStats.HighCPUProcesses.Count)" "INFO"
    foreach ($proc in $beforeStats.HighCPUProcesses) {
        Write-DockerDaemonLog "    - $($proc.ProcessName) (PID: $($proc.Id)) CPU: $($proc.CPU)" "WARN"
    }
    
    try {
        # Step 1: Stop Docker Desktop gracefully
        Write-DockerDaemonLog "Stopping Docker Desktop..." "INFO"
        $dockerDesktop = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        if ($dockerDesktop) {
            $dockerDesktop | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 3
        }
        
        # Step 2: Stop Docker service (requires admin privileges)
        Write-DockerDaemonLog "Stopping Docker service..." "INFO"
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($service) {
            try {
                Stop-Service -Name "com.docker.service" -Force -ErrorAction Stop
                Start-Sleep -Seconds 2
            } catch {
                Write-DockerDaemonLog "Failed to stop Docker service (may require admin privileges): $($_.Exception.Message)" "WARN"
                Write-DockerDaemonLog "Attempting to restart Docker Desktop without service restart..." "INFO"
            }
        }
        
        # Step 3: Kill any remaining Docker processes
        Write-DockerDaemonLog "Cleaning up remaining Docker processes..." "INFO"
        Get-Process | Where-Object { 
            $_.ProcessName -like "*docker*" -or 
            $_.ProcessName -like "*com.docker*" 
        } | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        
        # Step 4: Start Docker service (requires admin privileges)
        Write-DockerDaemonLog "Starting Docker service..." "INFO"
        try {
            Start-Service -Name "com.docker.service" -ErrorAction Stop
            Start-Sleep -Seconds 3
        } catch {
            Write-DockerDaemonLog "Failed to start Docker service (may require admin privileges): $($_.Exception.Message)" "WARN"
            Write-DockerDaemonLog "Docker Desktop may start the service automatically..." "INFO"
            Start-Sleep -Seconds 3
        }
        
        # Step 5: Start Docker Desktop
        Write-DockerDaemonLog "Starting Docker Desktop..." "INFO"
        $dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
        if (-not (Test-Path $dockerDesktopPath)) {
            $dockerDesktopPath = "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
        }
        
        if (Test-Path $dockerDesktopPath) {
            Start-Process -FilePath $dockerDesktopPath -ErrorAction SilentlyContinue
        } else {
            Write-DockerDaemonLog "Docker Desktop executable not found at expected location" "ERROR"
            return $false
        }
        
        # Step 6: Wait for Docker to be ready
        Write-DockerDaemonLog "Waiting for Docker to become ready..." "INFO"
        $maxWait = 120  # 2 minutes
        $startTime = Get-Date
        $dockerReady = $false
        
        while (((Get-Date) - $startTime).TotalSeconds -lt $maxWait) {
            $health = Test-DockerDaemonHealth -TimeoutSeconds 5
            if ($health.DockerInfo -and $health.DockerPs) {
                $dockerReady = $true
                break
            }
            Start-Sleep -Seconds 5
            Write-Host "." -NoNewline
        }
        
        if ($dockerReady) {
            Write-DockerDaemonLog "=== DOCKER DAEMON RESTART SUCCESSFUL ===" "SUCCESS"
            $recoveryTime = [math]::Round(((Get-Date) - $startTime).TotalSeconds)
            Write-DockerDaemonLog "Recovery completed in ${recoveryTime} seconds" "SUCCESS"
            Write-CrashLog "Docker daemon restart successful (recovery time: ${recoveryTime}s)" "SUCCESS"
            
            # Get Docker version
            try {
                $version = docker version --format '{{.Server.Version}}' 2>&1
                if ($version) {
                    Write-DockerDaemonLog "Docker version: $version" "INFO"
                }
            } catch {
                # Non-critical
            }
            
            return $true
        } else {
            Write-DockerDaemonLog "=== DOCKER DAEMON RESTART FAILED ===" "ERROR"
            Write-DockerDaemonLog "Docker did not become ready within $maxWait seconds" "ERROR"
            Write-CrashLog "Docker daemon restart failed - manual intervention required" "ERROR"
            return $false
        }
        
    } catch {
        Write-DockerDaemonLog "Error during Docker restart: $($_.Exception.Message)" "ERROR"
        Write-DockerDaemonLog "Stack trace: $($_.ScriptStackTrace)" "ERROR"
        Write-CrashLog "Docker daemon restart error: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Start-ContainerMonitoring {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "MONITORING MODE - Press Ctrl+C to stop" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    Write-Host "Container Check Interval: $MonitorInterval seconds" -ForegroundColor Gray
    Write-Host "Crash log: $crashLogPath" -ForegroundColor Gray
    if ($EnableDockerDaemonMonitor) {
        Write-Host "Docker Daemon Monitor: ENABLED" -ForegroundColor Green
        Write-Host "  - Freeze timeout: ${DockerDaemonTimeout}s" -ForegroundColor Gray
        Write-Host "  - Max restarts/hour: $MaxDockerRestartsPerHour" -ForegroundColor Gray
        Write-Host "  - Nuclear option: Force restart after ${ExtendedDowntimeMinutes} min downtime" -ForegroundColor Gray
        Write-Host "  - Daemon log: $dockerDaemonLogPath" -ForegroundColor Gray
    } else {
        Write-Host "Docker Daemon Monitor: DISABLED" -ForegroundColor Yellow
    }
    Write-Host ""
    
    $containers = @(
        'casestrainer-nginx-prod',
        'casestrainer-backend-prod',
        'casestrainer-frontend-prod',
        'casestrainer-redis-prod',
        'casestrainer-rqworker1-prod',
        'casestrainer-rqworker2-prod',
        'casestrainer-rqworker3-prod',
        'casestrainer-job-health-monitor-prod'
    )
    
    $previousStatus = @{}
    $failureCount = @{}
    $dockerDaemonFailures = 0
    $lastDockerCheck = $null
    $dockerRestartHistory = @()  # Track restart times for rate limiting
    $dockerFirstFailureTime = $null  # Track when Docker first became unhealthy (for nuclear option)
    
    # Initialize status tracking
    foreach ($container in $containers) {
        $previousStatus[$container] = $null
        $failureCount[$container] = 0
    }
    
    Write-CrashLog "Started monitoring mode at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "SUCCESS"
    if ($EnableDockerDaemonMonitor) {
        Write-DockerDaemonLog "=== DOCKER DAEMON MONITOR STARTED ===" "SUCCESS"
        Write-DockerDaemonLog "Check interval: ${MonitorInterval}s" "INFO"
        Write-DockerDaemonLog "Freeze timeout: ${DockerDaemonTimeout}s" "INFO"
        Write-DockerDaemonLog "Max restarts per hour: $MaxDockerRestartsPerHour" "INFO"
        Write-DockerDaemonLog "Extended downtime threshold: ${ExtendedDowntimeMinutes} minutes (nuclear option)" "INFO"
        Write-Host "[INFO] Docker daemon monitoring enabled" -ForegroundColor Cyan
    } else {
        Write-Host "[INFO] Docker daemon monitoring disabled" -ForegroundColor Gray
    }
    
    while ($true) {
        $timestamp = Get-Date -Format "HH:mm:ss"
        $allHealthy = $true
        
        # Check Docker daemon health (if enabled)
        if ($EnableDockerDaemonMonitor) {
            # Check every 2 cycles to avoid overhead, or if we had previous failures
            $shouldCheckDocker = ($null -eq $lastDockerCheck -or 
                                 ((Get-Date) - $lastDockerCheck).TotalSeconds -ge ($MonitorInterval * 2) -or
                                 $dockerDaemonFailures -gt 0)
            
            if ($shouldCheckDocker) {
                $health = Test-DockerDaemonHealth -TimeoutSeconds $DockerDaemonTimeout
                $lastDockerCheck = Get-Date
                
                # Determine overall health
                $isHealthy = $health.DockerInfo -and $health.DockerPs
                
                if ($isHealthy) {
                    if ($dockerDaemonFailures -gt 0) {
                        Write-DockerDaemonLog "Docker daemon recovered after $dockerDaemonFailures consecutive failures" "SUCCESS"
                        Write-CrashLog "[$timestamp] Docker daemon recovered after $dockerDaemonFailures failures" "SUCCESS"
                        $dockerDaemonFailures = 0
                        $dockerFirstFailureTime = $null  # Reset nuclear option timer
                    }
                    
                    # Log periodic health status (every 10 checks)
                    if ($null -eq $lastDockerCheck -or ((Get-Date) - $lastDockerCheck).TotalMinutes -ge 5) {
                        Write-DockerDaemonLog "Docker daemon health check: OK (Info: $($health.DockerInfo), Ps: $($health.DockerPs), Service: $($health.DockerService))" "INFO"
                    }
                } else {
                    $dockerDaemonFailures++
                    Write-DockerDaemonLog "Docker daemon health check FAILED (attempt $dockerDaemonFailures)" "ERROR"
                    Write-DockerDaemonLog "  DockerInfo: $($health.DockerInfo), DockerPs: $($health.DockerPs), DockerService: $($health.DockerService)" "ERROR"
                    Write-CrashLog "[$timestamp] WARNING: Docker daemon health check failed ($dockerDaemonFailures consecutive failures)" "ERROR"
                    
                    # Get process stats for diagnostics
                    $stats = Get-DockerProcessStats
                    Write-DockerDaemonLog "  Process stats: $($stats.Processes.Count) processes, $($stats.TotalMemoryMB) MB memory" "INFO"
                    
                    # If multiple consecutive failures, attempt restart
                    if ($dockerDaemonFailures -ge 2) {
                        # Track first failure time for nuclear option
                        if ($null -eq $dockerFirstFailureTime) {
                            $dockerFirstFailureTime = Get-Date
                            Write-DockerDaemonLog "First consecutive failure detected at $($dockerFirstFailureTime.ToString('yyyy-MM-dd HH:mm:ss'))" "WARN"
                        }
                        
                        # Check restart rate limit
                        $now = Get-Date
                        $recentRestarts = $dockerRestartHistory | Where-Object { ($now - $_).TotalHours -lt 1 }
                        
                        # NUCLEAR OPTION: If Docker has been down for extended time, bypass rate limit
                        $downtimeMinutes = if ($dockerFirstFailureTime) { ($now - $dockerFirstFailureTime).TotalMinutes } else { 0 }
                        $bypassRateLimit = $downtimeMinutes -ge $ExtendedDowntimeMinutes
                        
                        if ($bypassRateLimit) {
                            Write-DockerDaemonLog "NUCLEAR OPTION: Docker down for $([math]::Round($downtimeMinutes, 1)) minutes - bypassing rate limit" "WARN"
                            Write-Host "[$timestamp] as?i,?  NUCLEAR OPTION: Docker down for $([math]::Round($downtimeMinutes, 1)) min - forcing restart" -ForegroundColor Magenta
                        }
                        
                        if ($recentRestarts.Count -lt $MaxDockerRestartsPerHour -or $bypassRateLimit) {
                            $restartReason = if ($bypassRateLimit) {
                                "NUCLEAR: Extended downtime ($([math]::Round($downtimeMinutes, 1)) min) - bypassing rate limit"
                            } else {
                                "Health check failed ($dockerDaemonFailures consecutive failures)"
                            }
                            Write-DockerDaemonLog "Attempting Docker daemon restart ($restartReason)" "WARN"
                            Write-Host "[$timestamp] as?i,?  Docker daemon appears frozen - attempting restart..." -ForegroundColor Yellow
                            
                            $restartSuccess = Restart-DockerDaemon -Reason $restartReason
                            
                            if ($restartSuccess) {
                                $dockerRestartHistory += Get-Date
                                $dockerDaemonFailures = 0
                                $dockerFirstFailureTime = $null  # Reset nuclear option timer
                                
                                # Clean up old restart history (keep last 24 hours)
                                $dockerRestartHistory = $dockerRestartHistory | Where-Object { ($now - $_).TotalHours -lt 24 }
                                
                                Write-Host "[$timestamp] ao. Docker daemon restarted successfully" -ForegroundColor Green
                                
                                # Wait a bit for Docker to stabilize before continuing
                                Start-Sleep -Seconds 10
                            } else {
                                Write-Host "[$timestamp] a?O Docker daemon restart failed - manual intervention may be required" -ForegroundColor Red
                                Write-Host "  Check logs: $dockerDaemonLogPath" -ForegroundColor Yellow
                                
                                # Send critical notification
                                $notificationMessage = @"
Docker daemon restart FAILED after ${dockerDaemonFailures} consecutive health check failures.

Recovery attempts exhausted. Manual intervention required.

Details:
- Health checks failed: $dockerDaemonFailures times
- Restart attempted but failed
- Docker daemon is unresponsive
- Downtime: $([math]::Round($downtimeMinutes, 1)) minutes

Action Required:
1. Check Docker Desktop status
2. Review logs: $dockerDaemonLogPath
3. Manually restart Docker Desktop
4. Verify containers are running: docker ps

Recent restart history: $($dockerRestartHistory.Count) restarts in last 24 hours
"@
                                Send-AdminNotification `
                                    -Subject "CRITICAL: Docker Daemon Unrecoverable" `
                                    -Message $notificationMessage `
                                    -Severity "CRITICAL" `
                                    -IssueType "docker_daemon_unrecoverable"
                            }
                        } else {
                            Write-DockerDaemonLog "Restart rate limit reached ($($recentRestarts.Count) restarts in last hour) - waiting for nuclear option at $ExtendedDowntimeMinutes min" "WARN"
                            Write-Host "[$timestamp] as?i,?  Docker daemon frozen but restart rate limit reached" -ForegroundColor Red
                            Write-Host "  Recent restarts: $($recentRestarts.Count) in last hour" -ForegroundColor Yellow
                            Write-Host "  Downtime: $([math]::Round($downtimeMinutes, 1)) min (nuclear option at $ExtendedDowntimeMinutes min)" -ForegroundColor Yellow
                            
                            # Only send notification once per rate limit hit (not every check)
                            $shouldNotify = $dockerDaemonFailures -eq 2  # First time hitting rate limit
                            if ($shouldNotify) {
                                $notificationMessage = @"
Docker daemon restart rate limit reached.

The Docker daemon has been restarted $($recentRestarts.Count) times in the last hour.
Rate limit is temporarily pausing restarts.

NUCLEAR OPTION: Automatic restart will be forced after $ExtendedDowntimeMinutes minutes of continuous downtime.

Current Status:
- Docker daemon health checks failing
- Restart attempts: $($recentRestarts.Count) in last hour
- Rate limit: $MaxDockerRestartsPerHour per hour
- Current downtime: $([math]::Round($downtimeMinutes, 1)) minutes
- Nuclear option will trigger at: $ExtendedDowntimeMinutes minutes

The system will automatically attempt recovery after extended downtime.
Manual intervention may still be helpful if available.

Logs: $dockerDaemonLogPath
"@
                                Send-AdminNotification `
                                    -Subject "WARNING: Docker Daemon Restart Rate Limit Reached (Nuclear option in $([math]::Round($ExtendedDowntimeMinutes - $downtimeMinutes, 0)) min)" `
                                    -Message $notificationMessage `
                                    -Severity "WARN" `
                                    -IssueType "docker_daemon_rate_limit"
                            }
                        }
                    } else {
                        Write-Host "[$timestamp] as?i,?  Docker daemon health check failed ($dockerDaemonFailures/2)" -ForegroundColor Yellow
                    }
                }
            }
        }
        
        foreach ($container in $containers) {
            $info = Get-ContainerStatus $container
            $currentStatus = "$($info.Status)|$($info.Health)"
            
            # Check for status change
            if ($previousStatus[$container] -ne $currentStatus) {
                if ($info.Status -ne 'running' -or ($info.Health -and $info.Health -ne 'healthy' -and $info.Health -ne 'starting')) {
                    Write-CrashLog "[$timestamp] ALERT: $container changed to $($info.Status) (Health: $($info.Health))" "ERROR"
                    
                    # Get crash details
                    $crashInfo = Get-ContainerCrashInfo $container
                    
                    # Increment failure count
                    $failureCount[$container]++
                    
                    # Auto-restart logic
                    if ($failureCount[$container] -le 3) {
                        Write-CrashLog "Attempting auto-restart ($($failureCount[$container])/3)..." "WARN"
                        
                        try {
                            # Try to restart the specific container
                            docker-compose -f docker-compose.prod.yml restart $container 2>&1 | Out-Null
                            Start-Sleep -Seconds 5
                            
                            # Check if restart was successful
                            $newInfo = Get-ContainerStatus $container
                            if ($newInfo.Status -eq 'running') {
                                Write-CrashLog "Successfully restarted $container" "SUCCESS"
                            } else {
                                Write-CrashLog "Restart failed for $container - status: $($newInfo.Status)" "ERROR"
                            }
                        } catch {
                            Write-CrashLog "Auto-restart failed: $($_.Exception.Message)" "ERROR"
                        }
                    } else {
                        Write-CrashLog "$container has failed 3 times - manual intervention required" "ERROR"
                        Write-Host "`n[CRITICAL] Multiple failures detected. Stopping monitor." -ForegroundColor Red
                        Write-Host "Check crash log: $crashLogPath" -ForegroundColor Yellow
                        
                        # Send critical notification
                        $containerInfo = Get-ContainerCrashInfo $container
                        $notificationMessage = @"
Container $container has failed 3 consecutive restart attempts.

Container Status:
- Status: $($containerInfo.Status)
- Exit Code: $($containerInfo.ExitCode)
- Restart Count: $($containerInfo.RestartCount)
- Health: $($containerInfo.Health)

Auto-restart has been disabled. Manual intervention required.

Detected Errors:
$($containerInfo.Errors -join "`n")

Action Required:
1. Review container logs: docker logs $container
2. Check crash log: $crashLogPath
3. Investigate root cause
4. Manually restart container: docker restart $container
5. If issue persists, rebuild container: .\cslaunch.ps1 -Build

Last 5 log lines:
$($containerInfo.LastLogs | Select-Object -Last 5 | Out-String)
"@
                        Send-AdminNotification `
                            -Subject "CRITICAL: Container $container Unrecoverable" `
                            -Message $notificationMessage `
                            -Severity "CRITICAL" `
                            -IssueType "container_$($container)_unrecoverable"
                        
                        return
                    }
                    
                    $allHealthy = $false
                } elseif ($previousStatus[$container] -and $previousStatus[$container] -ne $currentStatus) {
                    # Container recovered
                    Write-CrashLog "[$timestamp] RECOVERED: $container is now $($info.Status) (Health: $($info.Health))" "SUCCESS"
                    $failureCount[$container] = 0  # Reset failure count on recovery
                }
                
                $previousStatus[$container] = $currentStatus
            }
        }
        
        # Periodic status update
        if ($allHealthy) {
            Write-Host "[$timestamp] All services healthy" -ForegroundColor Green
        } else {
            Write-Host "[$timestamp] Issues detected - check crash log" -ForegroundColor Yellow
        }
        
        Start-Sleep -Seconds $MonitorInterval
    }
}

# If explicit monitoring mode is enabled, start foreground monitoring
if ($Monitor) {
    # First ensure containers are running
    $containers = @(docker ps --format '{{.Names}}' | Where-Object { $_ -match 'casestrainer-' })
    
    if ($containers.Count -eq 0) {
        Write-Host "[WARN] No containers running. Starting containers first..." -ForegroundColor Yellow
        Write-Host ""
        
        # Start containers using full deployment
        $fullScriptPath = Join-Path $PSScriptRoot 'scripts\cslaunch.ps1'
        if (Test-Path $fullScriptPath) {
            & $fullScriptPath -Command 'prod'
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] Failed to start containers" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "[ERROR] Could not find deployment script" -ForegroundColor Red
            exit 1
        }
        
        Write-Host ""
        Write-Host "[OK] Containers started. Beginning monitoring..." -ForegroundColor Green
        
        # Send startup notification
        Send-StartupNotification -StartupType "monitor_mode"
        
        Start-Sleep -Seconds 10
    }
    
    # Start foreground monitoring (blocks until Ctrl+C)
    Start-ContainerMonitoring
    exit 0
}

# Function to start watchdog that monitors the monitoring job (checks every 5 minutes)
function Start-MonitoringWatchdog {
    $watchdogJobName = "CaseStrainer-Monitor-Watchdog"
    
    # Check if watchdog already exists
    $existingWatchdog = Get-Job -Name $watchdogJobName -ErrorAction SilentlyContinue
    if ($existingWatchdog) {
        Write-Host "[INFO] Monitoring watchdog already running (job ID: $($existingWatchdog.Id))" -ForegroundColor Cyan
        return
    }
    
    # Check if running as administrator (required for Docker restart capability)
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    Write-Host "[INFO] Starting monitoring watchdog (checks every 5 minutes)..." -ForegroundColor Cyan
    
    if (-not $isAdmin) {
        Write-Host "[WARN] Monitoring watchdog starting WITHOUT Administrator privileges" -ForegroundColor Yellow
        Write-Host "  as?i,?  Docker restart functionality will be LIMITED" -ForegroundColor Yellow
        Write-Host "  as?i,?  The watchdog can monitor and log, but cannot restart Docker service" -ForegroundColor Yellow
        Write-Host "  ?Y'! To enable full auto-recovery, run cslaunch as Administrator" -ForegroundColor Cyan
        Write-Host "     Right-click PowerShell -> Run as Administrator, then run: .\cslaunch" -ForegroundColor Gray
        Write-Host ""
    } else {
        Write-Host "[OK] Running as Administrator - full auto-recovery enabled" -ForegroundColor Green
    }
    
    $watchdogScriptBlock = {
        param(
            $ScriptRoot,
            $MonitorInterval,
            $DockerDaemonTimeout,
            $MaxDockerRestartsPerHour,
            $ExtendedDowntimeMinutes
        )
        
        $ErrorActionPreference = "Continue"
        $watchdogLogPath = Join-Path $ScriptRoot "logs\monitoring_watchdog.log"
        $monitorJobName = "CaseStrainer-Monitor"
        
        function Write-WatchdogLog {
            param([string]$Message, [string]$Level = "INFO")
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logEntry = "[$timestamp] [$Level] $Message"
            Add-Content -Path $watchdogLogPath -Value $logEntry -ErrorAction SilentlyContinue
        }
        
        Write-WatchdogLog "=== MONITORING WATCHDOG STARTED ===" "SUCCESS"
        Write-WatchdogLog "Check interval: 5 minutes" "INFO"
        Write-WatchdogLog "Monitored job: $monitorJobName" "INFO"
        
        # Main watchdog loop - checks every 5 minutes
        while ($true) {
            try {
                $monitorJob = Get-Job -Name $monitorJobName -ErrorAction SilentlyContinue
                
                if (-not $monitorJob) {
                    Write-WatchdogLog "Monitoring job not found - recreating..." "WARN"
                    
                    # Recreate monitoring job by invoking cslaunch.ps1 in a separate process
                    # This will call Start-BackgroundMonitoring which recreates the monitoring job
                    try {
                        $cslaunchPath = Join-Path $ScriptRoot "cslaunch.ps1"
                        if (Test-Path $cslaunchPath) {
                            $scriptArgs = @(
                                "-NoProfile",
                                "-ExecutionPolicy", "Bypass",
                                "-File", "`"$cslaunchPath`"",
                                "-NoMonitor:`$false"
                            )
                            Start-Process powershell.exe -ArgumentList $scriptArgs -WindowStyle Hidden -ErrorAction SilentlyContinue
                            Write-WatchdogLog "Monitoring job recreation initiated via cslaunch.ps1" "INFO"
                        } else {
                            Write-WatchdogLog "cslaunch.ps1 not found at $cslaunchPath" "ERROR"
                        }
                    } catch {
                        Write-WatchdogLog "Failed to recreate monitoring job: $($_.Exception.Message)" "ERROR"
                    }
                } elseif ($monitorJob.State -eq 'Failed' -or $monitorJob.State -eq 'Stopped') {
                    Write-WatchdogLog "Monitoring job is $($monitorJob.State) - removing and recreating..." "WARN"
                    
                    # Remove failed job
                    Remove-Job -Job $monitorJob -Force -ErrorAction SilentlyContinue
                    
                    # Recreate it (same as above)
                    try {
                        $cslaunchPath = Join-Path $ScriptRoot "cslaunch.ps1"
                        if (Test-Path $cslaunchPath) {
                            $scriptArgs = @(
                                "-NoProfile",
                                "-ExecutionPolicy", "Bypass",
                                "-File", "`"$cslaunchPath`"",
                                "-NoMonitor:`$false"
                            )
                            Start-Process powershell.exe -ArgumentList $scriptArgs -WindowStyle Hidden -ErrorAction SilentlyContinue
                            Write-WatchdogLog "Monitoring job recreation initiated via cslaunch.ps1" "INFO"
                        } else {
                            Write-WatchdogLog "cslaunch.ps1 not found at $cslaunchPath" "ERROR"
                        }
                    } catch {
                        Write-WatchdogLog "Failed to recreate monitoring job: $($_.Exception.Message)" "ERROR"
                    }
                } else {
                    # Job is running - log status periodically (every 10 checks = 50 minutes)
                    $checkCount = (Get-Date).Minute % 10
                    if ($checkCount -eq 0) {
                        Write-WatchdogLog "Monitoring job healthy (State: $($monitorJob.State), ID: $($monitorJob.Id))" "INFO"
                    }
                }
            } catch {
                Write-WatchdogLog "Error in watchdog loop: $($_.Exception.Message)" "ERROR"
            }
            
            # Check every 5 minutes
            Start-Sleep -Seconds 300
        }
    }
    
    # Start the watchdog job
    $watchdogJob = Start-Job -Name $watchdogJobName -ScriptBlock $watchdogScriptBlock `
        -ArgumentList $PSScriptRoot, $MonitorInterval, $DockerDaemonTimeout, $MaxDockerRestartsPerHour, $ExtendedDowntimeMinutes
    
    Write-Host "[OK] Monitoring watchdog started (job ID: $($watchdogJob.Id))" -ForegroundColor Green
    Write-Host "  - Checks every 5 minutes for monitoring job health" -ForegroundColor Cyan
    Write-Host "  - Auto-restarts monitoring job if it crashes" -ForegroundColor Cyan
    if (-not $isAdmin) {
        Write-Host "  - [WARNING] Limited: Cannot restart Docker (requires admin)" -ForegroundColor Yellow
    } else {
        Write-Host "  - [OK] Full auto-recovery enabled (admin privileges)" -ForegroundColor Green
    }
    Write-Host "  - Watchdog log: logs\monitoring_watchdog.log" -ForegroundColor Gray
}

# Enhanced Monitoring Functions for 24-48 Hour Crash Prevention
function Start-EnhancedMonitoringSuite {
    <#
    .SYNOPSIS
    Start the comprehensive enhanced monitoring suite to prevent recurring Docker crashes
    #>
    
    Write-Host "[ENHANCED] Starting comprehensive monitoring suite..." -ForegroundColor Cyan
    
    $scriptsDir = Join-Path $PSScriptRoot "scripts"
    $monitoringJobs = @()
    
    # 1. Enhanced Docker Monitor
    if ($EnableEnhancedMonitoring) {
        Write-Host "[ENHANCED] Starting enhanced Docker monitor..." -ForegroundColor Green
        $enhancedMonitorScript = Join-Path $scriptsDir "enhanced_docker_monitor.ps1"
        
        if (Test-Path $enhancedMonitorScript) {
            try {
                $scriptArgs = @(
                    "-CheckInterval", $EnhancedCheckInterval,
                    "-DockerTimeout", $DockerDaemonTimeout,
                    "-MemoryThreshold", $MemoryThreshold,
                    "-CpuThreshold", $CpuThreshold
                )
                
                if ($EnableAutoRecovery) { $scriptArgs += "-EnableAutoRecovery" }
                if ($EnableResourceMonitoring) { $scriptArgs += "-EnableResourceMonitoring" }
                
                $job = Start-Job -Name "Enhanced-Docker-Monitor" -ScriptBlock {
                    param($ScriptPath, $ScriptArgs)
                    & $ScriptPath @ScriptArgs
                } -ArgumentList $enhancedMonitorScript, $scriptArgs
                
                $monitoringJobs += $job
                Write-Host "[ENHANCED] Enhanced Docker monitor started (Job ID: $($job.Id))" -ForegroundColor Green
            } catch {
                Write-Host "[ENHANCED] Failed to start enhanced Docker monitor: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "[ENHANCED] Enhanced Docker monitor script not found" -ForegroundColor Yellow
        }
    }
    
    # 2. Self-Health Monitor
    if ($EnableSelfHealthMonitoring) {
        Write-Host "[ENHANCED] Starting self-health monitor..." -ForegroundColor Green
        $selfHealthScript = Join-Path $scriptsDir "monitor_self_health.ps1"
        
        if (Test-Path $selfHealthScript) {
            try {
                $scriptArgs = @(
                    "-MonitorScript", "enhanced_docker_monitor.ps1"
                )
                
                $job = Start-Job -Name "Self-Health-Monitor" -ScriptBlock {
                    param($ScriptPath, $ScriptArgs)
                    & $ScriptPath @ScriptArgs
                } -ArgumentList $selfHealthScript, $scriptArgs
                
                $monitoringJobs += $job
                Write-Host "[ENHANCED] Self-health monitor started (Job ID: $($job.Id))" -ForegroundColor Green
            } catch {
                Write-Host "[ENHANCED] Failed to start self-health monitor: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "[ENHANCED] Self-health monitor script not found" -ForegroundColor Yellow
        }
    }
    
    # 3. System Recovery Logger
    if ($EnableSystemRecoveryLogging) {
        Write-Host "[ENHANCED] Starting system recovery logger..." -ForegroundColor Green
        $recoveryLoggerScript = Join-Path $scriptsDir "system_recovery_logger.ps1"
        
        if (Test-Path $recoveryLoggerScript) {
            try {
                $job = Start-Job -Name "System-Recovery-Logger" -ScriptBlock {
                    param($ScriptPath)
                    & $ScriptPath
                } -ArgumentList $recoveryLoggerScript
                
                $monitoringJobs += $job
                Write-Host "[ENHANCED] ao" System recovery logger started (Job ID: $($job.Id))" -ForegroundColor Green
            } catch {
                Write-Host "[ENHANCED] Failed to start system recovery logger: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "[ENHANCED] System recovery logger script not found" -ForegroundColor Yellow
        }
    }
    
    # 4. Escalation Manager
    if ($EnableEscalationManager) {
        Write-Host "[ENHANCED] Starting escalation manager..." -ForegroundColor Green
        $escalationScript = Join-Path $scriptsDir "escalation_manager.ps1"
        
        if (Test-Path $escalationScript) {
            try {
                $job = Start-Job -Name "Escalation-Manager" -ScriptBlock {
                    param($ScriptPath)
                    & $ScriptPath
                } -ArgumentList $escalationScript
                
                $monitoringJobs += $job
                Write-Host "[ENHANCED] ao" Escalation manager started (Job ID: $($job.Id))" -ForegroundColor Green
            } catch {
                Write-Host "[ENHANCED] ao- Failed to start escalation manager: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "[ENHANCED] ao- Escalation manager script not found" -ForegroundColor Yellow
        }
    }
    
    # Summary
    Write-Host "[ENHANCED] Enhanced monitoring suite started with $($monitoringJobs.Count) components" -ForegroundColor Cyan
    Write-Host "[ENHANCED] Active monitoring jobs:" -ForegroundColor Gray
    foreach ($job in $monitoringJobs) {
        Write-Host "[ENHANCED]   - $($job.Name) (ID: $($job.Id))" -ForegroundColor Gray
    }
    
    Write-Host "[ENHANCED] Enhanced logs location: logs\enhanced_*.log" -ForegroundColor Gray
    Write-Host "[ENHANCED] Use 'Get-Job' to monitor job status" -ForegroundColor Gray
    
    return $monitoringJobs
}

function Restart-DockerEnhanced {
    <#
    .SYNOPSIS
    Enhanced Docker restart with deep cleanup and memory optimization
    #>
    
    param([string]$Reason = "Manual enhanced restart")
    
    Write-Host "[ENHANCED] Starting enhanced Docker restart..." -ForegroundColor Yellow
    Write-Host "[ENHANCED] Reason: $Reason" -ForegroundColor Gray
    
    $enhancedRestartScript = Join-Path $PSScriptRoot "scripts\enhanced_docker_restart.ps1"
    
    if (Test-Path $enhancedRestartScript) {
        try {
            $restartArgs = @()
            if ($Force) { $restartArgs += "-Force" }
            if ($DeepCleanRestart) { $restartArgs += "-DeepClean" }
            if ($MemoryOptimizeRestart) { $restartArgs += "-MemoryOptimize" }
            
            Write-Host "[ENHANCED] Executing enhanced restart with args: $($restartArgs -join ' ')" -ForegroundColor Gray
            
            $process = Start-Process powershell.exe -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$enhancedRestartScript`"" + $restartArgs -Wait -PassThru
            
            if ($process.ExitCode -eq 0) {
                Write-Host "[ENHANCED] ao" Enhanced Docker restart completed successfully" -ForegroundColor Green
                return $true
            } else {
                Write-Host "[ENHANCED] ao- Enhanced Docker restart failed (exit code: $($process.ExitCode))" -ForegroundColor Red
                return $false
            }
        } catch {
            Write-Host "[ENHANCED] Enhanced restart failed: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "[ENHANCED] Enhanced restart script not found at $enhancedRestartScript" -ForegroundColor Yellow
        return $false
    }
}

function Show-EnhancedMonitoringStatus {
    <#
    .SYNOPSIS
    Show status of all enhanced monitoring components
    #>
    
    Write-Host "`n[ENHANCED] Enhanced Monitoring Status" -ForegroundColor Cyan
    Write-Host "[ENHANCED] ===========================" -ForegroundColor Cyan
    
    # Check monitoring jobs
    $enhancedJobs = Get-Job | Where-Object { $_.Name -match "Enhanced|Self-Health|System-Recovery|Escalation" }
    
    if ($enhancedJobs.Count -gt 0) {
        Write-Host "[ENHANCED] Active monitoring jobs: $($enhancedJobs.Count)" -ForegroundColor Green
        foreach ($job in $enhancedJobs) {
            $status = switch ($job.State) {
                "Running" { "RUNNING" }
                "Failed" { "FAILED" }
                "Stopped" { "STOPPED" }
                default { "$($job.State.ToUpper())" }
            }
            Write-Host "[ENHANCED]   $($job.Name): $status (ID: $($job.Id))" -ForegroundColor Gray
        }
    } else {
        Write-Host "[ENHANCED] No enhanced monitoring jobs running" -ForegroundColor Yellow
    }
    
    # Check log files
    $logsDir = Join-Path $PSScriptRoot "logs"
    $enhancedLogs = @(
        "enhanced_monitor.log",
        "self_health_monitor.log", 
        "system_recovery.log",
        "escalation.log"
    )
    
    Write-Host "[ENHANCED]`nLog file status:" -ForegroundColor Gray
    foreach ($logFile in $enhancedLogs) {
        $logPath = Join-Path $logsDir $logFile
        if (Test-Path $logPath) {
            $file = Get-Item $logPath
            $timeSince = (Get-Date) - $file.LastWriteTime
            $status = if ($timeSince.TotalMinutes -lt 30) { "ACTIVE" } 
                     elseif ($timeSince.TotalMinutes -lt 120) { "RECENT" } 
                     else { "STALE" }
            Write-Host "[ENHANCED]   $logFile`: $status (Last: $($timeSince.TotalMinutes.ToString('F0'))m ago)" -ForegroundColor Gray
        } else {
            Write-Host "[ENHANCED]   $logFile`: NOT FOUND" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
}

# Function to start background monitoring (lightweight - Docker daemon only)
function Start-BackgroundMonitoring {
    if ($NoMonitor) {
        Write-Host "[INFO] Background monitoring disabled (NoMonitor flag)" -ForegroundColor Gray
        return
    }
    
    # Don't start background monitoring if we're already in Monitor mode
    if ($Monitor) {
        return
    }
    
    # Check if monitoring job already exists
    $existingJob = Get-Job -Name "CaseStrainer-Monitor" -ErrorAction SilentlyContinue
    if ($existingJob) {
        Write-Host "[INFO] Background monitoring already running (job ID: $($existingJob.Id))" -ForegroundColor Cyan
        # Still start watchdog to ensure it stays running
        Start-MonitoringWatchdog
        return
    }
    
    Write-Host "[INFO] Starting background Docker daemon monitoring..." -ForegroundColor Cyan
    
    # Check if running as administrator (for Docker restart capability)
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if (-not $isAdmin) {
        Write-Host "[WARN] Background monitoring starting WITHOUT Administrator privileges" -ForegroundColor Yellow
        Write-Host "  as?i,?  Docker auto-restart will be LIMITED (can detect issues but cannot restart Docker service)" -ForegroundColor Yellow
        Write-Host "  ?Y'! To enable full auto-recovery, run cslaunch as Administrator" -ForegroundColor Cyan
        Write-Host "     Right-click PowerShell -> Run as Administrator, then run: .\cslaunch" -ForegroundColor Gray
        Write-Host ""
    } else {
        Write-Host "[OK] Running as Administrator - Docker auto-restart enabled" -ForegroundColor Green
    }
    
    # Create a lightweight background monitoring script block
    # UPDATED: Now includes nuclear option and auto-restart capability
    $monitorScriptBlock = {
        param(
            $ScriptRoot,
            $MonitorInterval,
            $DockerDaemonTimeout,
            $MaxDockerRestartsPerHour,
            $ExtendedDowntimeMinutes
        )
        
        $ErrorActionPreference = "Continue"
        $dockerDaemonLogPath = Join-Path $ScriptRoot "logs\docker_daemon_monitor.log"
        
        function Write-DaemonLog {
            param([string]$Message, [string]$Level = "INFO")
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logEntry = "[$timestamp] [$Level] $Message"
            Add-Content -Path $dockerDaemonLogPath -Value $logEntry -ErrorAction SilentlyContinue
        }
        
        function Test-DockerHealth {
            param([int]$TimeoutSeconds = 15)
            try {
                $job = Start-Job -ScriptBlock { docker info 2>&1 }
                if (Wait-Job $job -Timeout $TimeoutSeconds) {
                    $output = Receive-Job $job
                    Remove-Job $job -Force
                    return ($LASTEXITCODE -eq 0)
                } else {
                    Stop-Job $job -ErrorAction SilentlyContinue
                    Remove-Job $job -Force -ErrorAction SilentlyContinue
                    return $false
                }
            } catch {
                return $false
            }
        }
        
        function Restart-DockerDaemonBackground {
            param([string]$Reason = "Background auto-restart")
            
            Write-DaemonLog "=== BACKGROUND DOCKER RESTART INITIATED ===" "WARN"
            Write-DaemonLog "Reason: $Reason" "WARN"
            
            try {
                # Step 1: Stop Docker Desktop gracefully
                Write-DaemonLog "Stopping Docker Desktop..." "INFO"
                $dockerDesktop = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
                if ($dockerDesktop) {
                    $dockerDesktop | Stop-Process -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Seconds 3
                }
                
                # Step 2: Stop Docker service (requires admin privileges)
                Write-DaemonLog "Stopping Docker service..." "INFO"
                $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
                if ($service) {
                    try {
                        Stop-Service -Name "com.docker.service" -Force -ErrorAction Stop
                        Start-Sleep -Seconds 2
                    } catch {
                        Write-DaemonLog "Failed to stop Docker service (may require admin privileges): $($_.Exception.Message)" "WARN"
                        Write-DaemonLog "Attempting to restart Docker Desktop without service restart..." "INFO"
                    }
                }
                
                # Step 3: Kill remaining Docker processes
                Write-DaemonLog "Cleaning up Docker processes..." "INFO"
                Get-Process | Where-Object { 
                    $_.ProcessName -like "*docker*" -or 
                    $_.ProcessName -like "*com.docker*" 
                } | Stop-Process -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
                
                # Step 4: Start Docker service (requires admin privileges)
                Write-DaemonLog "Starting Docker service..." "INFO"
                try {
                    Start-Service -Name "com.docker.service" -ErrorAction Stop
                    Start-Sleep -Seconds 3
                } catch {
                    Write-DaemonLog "Failed to start Docker service (may require admin privileges): $($_.Exception.Message)" "WARN"
                    Write-DaemonLog "Docker Desktop may start the service automatically..." "INFO"
                    Start-Sleep -Seconds 3
                }
                
                # Step 5: Start Docker Desktop
                Write-DaemonLog "Starting Docker Desktop..." "INFO"
                $dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
                if (-not (Test-Path $dockerDesktopPath)) {
                    $dockerDesktopPath = "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
                }
                
                if (Test-Path $dockerDesktopPath) {
                    Start-Process -FilePath $dockerDesktopPath -ErrorAction SilentlyContinue
                } else {
                    Write-DaemonLog "Docker Desktop not found at expected location" "ERROR"
                    return $false
                }
                
                # Step 6: Wait for Docker to be ready
                Write-DaemonLog "Waiting for Docker to become ready..." "INFO"
                $maxWait = 120
                $startTime = Get-Date
                $dockerReady = $false
                
                while (((Get-Date) - $startTime).TotalSeconds -lt $maxWait) {
                    if (Test-DockerHealth -TimeoutSeconds 10) {
                        $dockerReady = $true
                        break
                    }
                    Start-Sleep -Seconds 5
                }
                
                if ($dockerReady) {
                    $recoveryTime = [math]::Round(((Get-Date) - $startTime).TotalSeconds)
                    Write-DaemonLog "=== BACKGROUND DOCKER RESTART SUCCESSFUL ===" "SUCCESS"
                    Write-DaemonLog "Recovery completed in ${recoveryTime} seconds" "SUCCESS"
                    
                    # Also restart containers
                    Write-DaemonLog "Restarting CaseStrainer containers..." "INFO"
                    $composeFile = Join-Path $ScriptRoot "docker-compose.prod.yml"
                    if (Test-Path $composeFile) {
                        docker compose -f $composeFile up -d 2>&1 | ForEach-Object { Write-DaemonLog $_ "INFO" }
                    }
                    
                    return $true
                } else {
                    Write-DaemonLog "=== BACKGROUND DOCKER RESTART FAILED ===" "ERROR"
                    Write-DaemonLog "Docker did not become ready within $maxWait seconds" "ERROR"
                    return $false
                }
            } catch {
                Write-DaemonLog "Error during background restart: $($_.Exception.Message)" "ERROR"
                return $false
            }
        }
        
        Write-DaemonLog "=== BACKGROUND DOCKER DAEMON MONITOR STARTED (ENHANCED) ===" "SUCCESS"
        Write-DaemonLog "Check interval: ${MonitorInterval}s" "INFO"
        Write-DaemonLog "Freeze timeout: ${DockerDaemonTimeout}s" "INFO"
        Write-DaemonLog "Max restarts per hour: $MaxDockerRestartsPerHour" "INFO"
        Write-DaemonLog "Nuclear option threshold: ${ExtendedDowntimeMinutes} minutes" "INFO"
        
        $dockerDaemonFailures = 0
        $lastDockerCheck = $null
        $dockerRestartHistory = @()
        $dockerFirstFailureTime = $null  # For nuclear option tracking
        
        while ($true) {
            try {
                $shouldCheck = ($null -eq $lastDockerCheck -or 
                               ((Get-Date) - $lastDockerCheck).TotalSeconds -ge ($MonitorInterval * 2))
                
                if ($shouldCheck) {
                    $isHealthy = Test-DockerHealth -TimeoutSeconds $DockerDaemonTimeout
                    $lastDockerCheck = Get-Date
                    
                    if (-not $isHealthy) {
                        $dockerDaemonFailures++
                        Write-DaemonLog "Docker daemon health check FAILED (attempt $dockerDaemonFailures)" "ERROR"
                        
                        if ($dockerDaemonFailures -ge 2) {
                            # Track first failure time for nuclear option
                            if ($null -eq $dockerFirstFailureTime) {
                                $dockerFirstFailureTime = Get-Date
                                Write-DaemonLog "First consecutive failure at $($dockerFirstFailureTime.ToString('yyyy-MM-dd HH:mm:ss'))" "WARN"
                            }
                            
                            $now = Get-Date
                            $recentRestarts = $dockerRestartHistory | Where-Object { ($now - $_).TotalHours -lt 1 }
                            
                            # NUCLEAR OPTION: Bypass rate limit after extended downtime
                            $downtimeMinutes = if ($dockerFirstFailureTime) { ($now - $dockerFirstFailureTime).TotalMinutes } else { 0 }
                            $bypassRateLimit = $downtimeMinutes -ge $ExtendedDowntimeMinutes
                            
                            if ($bypassRateLimit) {
                                Write-DaemonLog "NUCLEAR OPTION TRIGGERED: Docker down for $([math]::Round($downtimeMinutes, 1)) minutes - bypassing rate limit" "WARN"
                            }
                            
                            if ($recentRestarts.Count -lt $MaxDockerRestartsPerHour -or $bypassRateLimit) {
                                $restartReason = if ($bypassRateLimit) {
                                    "NUCLEAR: Extended downtime ($([math]::Round($downtimeMinutes, 1)) min) - bypassing rate limit"
                                } else {
                                    "Health check failed ($dockerDaemonFailures consecutive failures)"
                                }
                                
                                Write-DaemonLog "Attempting Docker daemon restart: $restartReason" "WARN"
                                
                                $restartSuccess = Restart-DockerDaemonBackground -Reason $restartReason
                                
                                if ($restartSuccess) {
                                    $dockerRestartHistory += Get-Date
                                    $dockerDaemonFailures = 0
                                    $dockerFirstFailureTime = $null  # Reset nuclear timer
                                    
                                    # Clean up old restart history
                                    $dockerRestartHistory = $dockerRestartHistory | Where-Object { ($now - $_).TotalHours -lt 24 }
                                    
                                    Write-DaemonLog "Docker daemon restarted successfully" "SUCCESS"
                                } else {
                                    Write-DaemonLog "Docker daemon restart FAILED - manual intervention may be required" "ERROR"
                                }
                            } else {
                                Write-DaemonLog "Restart rate limit reached ($($recentRestarts.Count) restarts in last hour)" "WARN"
                                Write-DaemonLog "Nuclear option will trigger at $ExtendedDowntimeMinutes min (current: $([math]::Round($downtimeMinutes, 1)) min)" "INFO"
                            }
                        }
                    } else {
                        if ($dockerDaemonFailures -gt 0) {
                            Write-DaemonLog "Docker daemon recovered after $dockerDaemonFailures failures" "SUCCESS"
                            $dockerDaemonFailures = 0
                            $dockerFirstFailureTime = $null  # Reset nuclear timer on recovery
                        }
                    }
                }
            } catch {
                Write-DaemonLog "Error in monitoring loop: $($_.Exception.Message)" "ERROR"
            }
            
            Start-Sleep -Seconds $MonitorInterval
        }
    }
    
    # Start the monitoring job
    $job = Start-Job -Name "CaseStrainer-Monitor" -ScriptBlock $monitorScriptBlock `
        -ArgumentList $PSScriptRoot, $MonitorInterval, $DockerDaemonTimeout, $MaxDockerRestartsPerHour, $ExtendedDowntimeMinutes
    
    Write-Host "[OK] Background monitoring started (job ID: $($job.Id))" -ForegroundColor Green
    Write-Host "  - Auto-restart: ENABLED (including nuclear option after ${ExtendedDowntimeMinutes} min)" -ForegroundColor Cyan
    Write-Host "  - View logs: Get-Content logs\docker_daemon_monitor.log -Tail 50 -Wait" -ForegroundColor Gray
    Write-Host "  - Stop monitoring: Stop-Job -Name CaseStrainer-Monitor; Remove-Job -Name CaseStrainer-Monitor" -ForegroundColor Gray
    Write-Host "  - External WHM monitoring also active" -ForegroundColor Cyan
    
    # Start watchdog to ensure monitoring job stays running (enabled by default)
    Start-MonitoringWatchdog
}

# ====================================================================
# AUTOSTART CONFIGURATION (Must be AFTER function definitions)
# ====================================================================

# Handle autostart configuration request
if ($ConfigureAutostart) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Docker Autostart Configuration" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    if (Install-DockerAutostart) {
        Write-Host "`n[SUCCESS] Docker autostart configured!" -ForegroundColor Green
        Write-Host "Containers will automatically start on system boot." -ForegroundColor Gray
        Write-Host "`nTo test: Restart your computer and check logs\autostart.log" -ForegroundColor Yellow
        exit 0
    } else {
        Write-Host "`n[ERROR] Failed to configure autostart" -ForegroundColor Red
        Write-Host "Please run this script as Administrator to enable autostart." -ForegroundColor Yellow
        exit 1
    }
}

# Handle periodic health check configuration
if ($ConfigurePeriodicHealthCheck) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Periodic Health Check Configuration" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    Write-Host "This creates a Windows Task Scheduler job that runs every 30 minutes" -ForegroundColor White
    Write-Host "to check Docker health and restart containers if needed." -ForegroundColor White
    Write-Host "This is a backup safety net in case the main monitoring stops or crashes." -ForegroundColor Gray
    Write-Host "(Enhanced: runs every 30 min instead of 2 hours to catch extended outages)" -ForegroundColor Gray
    Write-Host ""
    
    if (Configure-PeriodicHealthCheck) {
        Write-Host "`n[SUCCESS] Periodic health check configured!" -ForegroundColor Green
        Write-Host "Docker will be checked every 30 minutes as a safety net." -ForegroundColor Gray
        Write-Host "`nTo view logs: Get-Content logs\periodic_health_check.log" -ForegroundColor Yellow
        Write-Host "To remove: .\cslaunch.ps1 -RemovePeriodicHealthCheck" -ForegroundColor Yellow
        exit 0
    } else {
        Write-Host "`n[ERROR] Failed to configure periodic health check" -ForegroundColor Red
        Write-Host "Please run this script as Administrator." -ForegroundColor Yellow
        exit 1
    }
}

# Handle periodic health check removal
if ($RemovePeriodicHealthCheck) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Removing Periodic Health Check" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    Configure-PeriodicHealthCheck -Remove
    exit 0
}

# Check and configure Docker autostart on boot (enabled by default)
if (-not $NoAutostart) {
    try {
        if (-not (Test-DockerAutostartConfigured)) {
            Write-Host "[AUTOSTART] Docker autostart not configured - attempting setup..." -ForegroundColor Yellow
            
            # Check if running as administrator
            $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
            
            if ($isAdmin) {
                # We have admin rights - configure autostart
                $autostartInstalled = Install-DockerAutostart
                if ($autostartInstalled) {
                    Write-Host "[SUCCESS] Docker autostart configured - containers will auto-start on boot" -ForegroundColor Green
                    Write-Host "          Run with -NoAutostart to disable this feature" -ForegroundColor Gray
                } else {
                    Write-Host "[WARN] Autostart configuration failed" -ForegroundColor Yellow
                }
            } else {
                # Not admin - inform user how to enable
                Write-Host "[INFO] Docker autostart not configured (requires Administrator privileges)" -ForegroundColor Yellow
                Write-Host "       To enable autostart, run as Administrator once:" -ForegroundColor Gray
                Write-Host "       .\cslaunch.ps1 -ConfigureAutostart" -ForegroundColor Cyan
                Write-Host "       Or run with -NoAutostart to suppress this message" -ForegroundColor Gray
            }
        } else {
            # Already configured - show status on first run or Monitor mode
            if ($Monitor -or $ConfigureAutostart) {
                Write-Host "[OK] Docker autostart is configured - containers will auto-start on boot" -ForegroundColor Green
            }
        }
    } catch {
        # Silently ignore errors - autostart is optional
    }
} else {
    Write-Host "[INFO] Docker autostart disabled (NoAutostart flag)" -ForegroundColor Gray
}

# ====================================================================
# MAIN CONTAINER STARTUP LOGIC
# ====================================================================

# STARTUP: Check Docker daemon health and restart if frozen
Write-Host "[DOCKER] Checking Docker daemon..." -ForegroundColor Yellow

$dockerResponsive = $false
$dockerCheckAttempts = 0
$maxDockerAttempts = 2  # Try twice (second attempt after restart)

while (-not $dockerResponsive -and $dockerCheckAttempts -lt $maxDockerAttempts) {
    $dockerCheckAttempts++
    
    # Use .NET Process with timeout - more reliable than Start-Job
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "docker"
        $psi.Arguments = "info"
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $psi
        $process.Start() | Out-Null
        
        # Wait up to 10 seconds
        $completed = $process.WaitForExit(10000)
        
        if ($completed -and $process.ExitCode -eq 0) {
            $dockerResponsive = $true
            Write-Host "[OK] Docker daemon is responsive" -ForegroundColor Green
        } else {
            if (-not $completed) {
                $process.Kill()
                Write-Host "[WARN] Docker daemon not responding (attempt $dockerCheckAttempts/$maxDockerAttempts)" -ForegroundColor Yellow
            } else {
                Write-Host "[WARN] Docker daemon returned error (attempt $dockerCheckAttempts/$maxDockerAttempts)" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "[WARN] Docker check failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # If not responsive and we have attempts left, try to restart Docker
    if (-not $dockerResponsive -and $dockerCheckAttempts -lt $maxDockerAttempts) {
        Write-Host "[DOCKER] Attempting to restart Docker daemon..." -ForegroundColor Yellow
        
        try {
            # Use the existing Restart-DockerDaemon function
            $restartSuccess = Restart-DockerDaemon -Reason "Frozen at startup"
            
            if ($restartSuccess) {
                Write-Host "[OK] Docker daemon restarted successfully" -ForegroundColor Green
            } else {
                Write-Host "[WARN] Docker restart may have failed - will retry check" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[ERROR] Failed to restart Docker: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

if (-not $dockerResponsive) {
    Write-Host "[ERROR] Docker daemon is not responding after $maxDockerAttempts attempts" -ForegroundColor Red
    Write-Host "        Please manually start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Check if containers are already running
$containers = @(docker ps --format '{{.Names}}' | Where-Object { $_ -match 'casestrainer-' })

if ($containers.Count -gt 0 -and -not $Build -and -not $Force) {
    Write-Host "[OK] Found $($containers.Count) running containers" -ForegroundColor Green
    
    # Check if Vue source files are newer than dist files
    $needsVueBuild = $false
    if (Test-Path "casestrainer-vue-new\src") {
        $vueSourceFiles = Get-ChildItem -Path "casestrainer-vue-new\src" -Recurse -File -Include "*.vue","*.js" -ErrorAction SilentlyContinue
        $distIndexPath = "casestrainer-vue-new\dist\index.html"
        
        if (Test-Path $distIndexPath) {
            $distTime = (Get-Item $distIndexPath).LastWriteTime
            $newestSource = $vueSourceFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            
            if ($newestSource -and $newestSource.LastWriteTime -gt $distTime) {
                Write-Host "[DETECT] Vue source files changed - rebuild needed" -ForegroundColor Yellow
                $needsVueBuild = $true
            }
        } else {
            # No dist folder exists, need to build
            Write-Host "[DETECT] No dist folder found - initial build needed" -ForegroundColor Yellow
            $needsVueBuild = $true
        }
    }
    
    # Build Vue frontend if needed
    if ($needsVueBuild) {
        Write-Host "[VUE BUILD] Building Vue frontend..." -ForegroundColor Yellow
        Write-Host ""
        
        Push-Location "casestrainer-vue-new"
        $vueBuildStart = [System.Diagnostics.Stopwatch]::StartNew()
        
        try {
            & npm run build
            $vueBuildStart.Stop()
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "`n[OK] Vue build completed in $([math]::Round($vueBuildStart.Elapsed.TotalSeconds, 1)) seconds" -ForegroundColor Green
            } else {
                Write-Host "`n[ERROR] Vue build failed" -ForegroundColor Red
                Pop-Location
                exit 1
            }
        } catch {
            Write-Host "`n[ERROR] Vue build failed: $($_.Exception.Message)" -ForegroundColor Red
            Pop-Location
            exit 1
        }
        
        Pop-Location
        Write-Host ""
    }
    
    # Check if frontend container needs rebuilding (Vue dist files changed)
    $needsFrontendRebuild = $false
    if (Test-Path "casestrainer-vue-new\dist\index.html") {
        # Check the actual dist folder that Docker uses
        $vueDistTime = (Get-Item "casestrainer-vue-new\dist\index.html" -ErrorAction SilentlyContinue).LastWriteTime
        $containerDistTime = docker exec casestrainer-frontend-prod stat -c %Y /usr/share/nginx/html/index.html 2>$null
        
        if ($vueDistTime -and $containerDistTime) {
            $containerTime = [DateTimeOffset]::FromUnixTimeSeconds([long]$containerDistTime).LocalDateTime
            if ($vueDistTime -gt $containerTime) {
                Write-Host "[DETECT] Vue dist files updated - Docker rebuild needed" -ForegroundColor Yellow
                $needsFrontendRebuild = $true
            }
        } elseif ($needsVueBuild) {
            # Just built Vue, so definitely need Docker rebuild
            $needsFrontendRebuild = $true
        }
    }
    
    if ($needsFrontendRebuild) {
        Write-Host "[FRONTEND REBUILD] Rebuilding frontend container with latest Vue files..." -ForegroundColor Yellow
        Write-Host ""
        
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        docker-compose -f docker-compose.prod.yml up -d --build frontend-prod
        $sw.Stop()
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n[OK] Frontend rebuilt in $([math]::Round($sw.Elapsed.TotalSeconds, 1)) seconds" -ForegroundColor Green
            
            # NEW: Always restart backend + workers after a frontend rebuild so API picks up new Python code
            Write-Host "[BACKEND RESTART] Restarting backend API and workers to load latest code..." -ForegroundColor Yellow
            try {
                # Clear Python caches on host
                Get-ChildItem -Path "src" -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
                Get-ChildItem -Path "src" -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue }
                
                # ALWAYS rebuild without cache to ensure Python code changes are picked up
                # (Docker layer caching can miss file changes on Windows)
                $sw2 = [System.Diagnostics.Stopwatch]::StartNew()
                docker-compose -f docker-compose.prod.yml build --no-cache backend rqworker1 rqworker2 rqworker3
                docker-compose -f docker-compose.prod.yml up -d backend rqworker1 rqworker2 rqworker3
                $sw2.Stop()
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  [OK] Backend + workers restarted in $([math]::Round($sw2.Elapsed.TotalSeconds, 1)) seconds" -ForegroundColor Green
                    # Clear caches inside container (best-effort)
                    docker exec casestrainer-backend-prod find /app/src -type d -name '__pycache__' -exec rm -rf {} + 2>$null | Out-Null
                    docker exec casestrainer-backend-prod find /app/src -name '*.pyc' -delete 2>$null | Out-Null
                } else {
                    Write-Host "  [WARN] Backend restart returned non-zero exit code" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "  [WARNING] Backend restart failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
            # Reload reverse-proxy to ensure API routing is up-to-date
            try {
                docker exec casestrainer-nginx-prod nginx -s reload > $null 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  [OK] Nginx configuration reloaded successfully" -ForegroundColor Green
                } else {
                    Write-Host "  [WARN] Could not reload nginx config (container may not exist)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "  [WARNING] Nginx reload step failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
            # Wait for services to be ready
            Write-Host "`n[WAIT] Ensuring services are ready..." -ForegroundColor Yellow
            try {
                $waitScript = Join-Path $PSScriptRoot 'scripts\wait-for-services.py'
                if (Test-Path $waitScript) {
                    docker cp $waitScript casestrainer-backend-prod:/app/wait-for-services.py 2>$null
                    $output = docker exec casestrainer-backend-prod python /app/wait-for-services.py 2>&1
                    $output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
                }
            } catch {
                Write-Host "  [WARNING] Service check failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
            # Clear caches after frontend rebuild
            Write-Host "`n[CACHE CLEAR] Clearing Redis cache..." -ForegroundColor Yellow
            docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** FLUSHALL 2>&1 | Out-Null
            Write-Host "  [OK] Redis cache cleared" -ForegroundColor Green
            
            Write-Host "`n[RQ WORKERS] Restarting workers..." -ForegroundColor Yellow
            docker-compose -f docker-compose.prod.yml restart rqworker1 rqworker2 rqworker3 2>&1 | Out-Null
            Write-Host "  [OK] Workers restarted" -ForegroundColor Green
            Write-Host "`n  [REMINDER] Clear browser cache (Ctrl+Shift+Delete)!" -ForegroundColor Magenta
            
            Write-Host "`n[SUCCESS] Frontend rebuild complete - All services ready!" -ForegroundColor Green
            Write-Host "  Vue changes are now active" -ForegroundColor DarkGray
            Write-Host "  Application: http://localhost" -ForegroundColor Cyan
            
            # Send startup notification
            Send-StartupNotification -StartupType "quick_restart"
            
            # Start background monitoring after successful restart
            Start-BackgroundMonitoring
            
            exit 0
        } else {
            Write-Host "`n[ERROR] Frontend rebuild failed" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host '[QUICK RESTART] Restarting containers (10-15 seconds)...' -ForegroundColor Yellow
        Write-Host ""
        
        # CRITICAL: Clear Python bytecode cache before restart to ensure code changes are picked up
        Write-Host "[CACHE CLEAR] Clearing Python bytecode cache..." -ForegroundColor Yellow
        try {
            # Clear __pycache__ on HOST (volume mount)
            Get-ChildItem -Path "src" -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object {
                Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            }
            
            # Clear .pyc files on HOST
            Get-ChildItem -Path "src" -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | ForEach-Object {
                Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
            }
            
            # ALSO clear cache INSIDE container before restart
            Write-Host "  Clearing cache inside containers..." -ForegroundColor Yellow
            docker exec casestrainer-backend-prod find /app/src -type d -name '__pycache__' -exec rm -rf {} + 2>$null
            docker exec casestrainer-backend-prod find /app/src -name '*.pyc' -delete 2>$null
            
            Write-Host "  [OK] Python cache cleared (host + containers)" -ForegroundColor Green
        } catch {
            Write-Host "  [WARNING] Could not clear all cache: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        Write-Host ""
        
        # ALWAYS rebuild without cache to ensure Python code changes are picked up
        # (Docker layer caching can miss file changes on Windows, causing stale code issues)
        Write-Host '[REBUILD] Building backend + workers with --no-cache (ensures fresh code)...' -ForegroundColor Yellow
        Write-Host '  [INFO] Using --no-cache to guarantee Python changes are picked up' -ForegroundColor Gray
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        docker-compose -f docker-compose.prod.yml build --no-cache backend rqworker1 rqworker2 rqworker3
        docker-compose -f docker-compose.prod.yml up -d backend rqworker1 rqworker2 rqworker3
        $sw.Stop()
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n[OK] Backend + workers rebuilt and deployed in $([math]::Round($sw.Elapsed.TotalSeconds, 1)) seconds" -ForegroundColor Green
            
            # CRITICAL: Reload nginx configuration to pick up any changes
            Write-Host "`n[NGINX] Reloading nginx configuration..." -ForegroundColor Yellow
            docker exec casestrainer-nginx-prod nginx -s reload > $null 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [OK] Nginx configuration reloaded successfully" -ForegroundColor Green
            } else {
                Write-Host "  [WARN] Could not reload nginx config (container may not exist)" -ForegroundColor Yellow
            }
            
            # NOW wait for services to be ready (after restart)
            Write-Host "`n[WAIT] Ensuring services are ready..." -ForegroundColor Yellow
            $servicesReady = $false
            try {
                $waitScript = Join-Path $PSScriptRoot 'scripts\wait-for-services.py'
                if (Test-Path $waitScript) {
                    docker cp $waitScript casestrainer-backend-prod:/app/wait-for-services.py 2>$null
                    $output = docker exec casestrainer-backend-prod python /app/wait-for-services.py 2>&1
                    $output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
                    
                    # Check exit code
                    if ($LASTEXITCODE -eq 0) {
                        $servicesReady = $true
                    }
                }
            } catch {
                Write-Host "  [WARNING] Service check failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
            # Clean up stuck RQ jobs (only if services are ready)
            if ($servicesReady) {
                Write-Host "`n[CLEANUP] Cleaning up any stuck RQ jobs..." -ForegroundColor Yellow
                try {
                    $cleanupScript = Join-Path $PSScriptRoot 'scripts\cleanup-stuck-jobs.py'
                    if (Test-Path $cleanupScript) {
                        docker cp $cleanupScript casestrainer-backend-prod:/app/cleanup-stuck-jobs.py 2>$null
                        $output = docker exec casestrainer-backend-prod python /app/cleanup-stuck-jobs.py 2>&1
                        $output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
                    }
                } catch {
                    Write-Host "  [WARNING] Cleanup failed: $($_.Exception.Message)" -ForegroundColor Yellow
                }
                
                # USER REQUESTED: Clear all caches for fresh testing
                Write-Host "`n[CACHE CLEAR] Clearing Redis and file caches..." -ForegroundColor Yellow
                try {
                    # Clear Redis cache (ALL databases - 0: RQ queue, 1: citation cache, 2: URL cache, 3: session data)
                    Write-Host "  [*] Clearing Redis caches (databases 0, 1, 2, 3)..." -ForegroundColor Gray
                    
                    # Clear ALL Redis databases with FLUSHALL (much faster!)
                    docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** FLUSHALL 2>&1 | Out-Null
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "  [OK] Redis caches cleared (all databases)" -ForegroundColor Green
                    } else {
                        Write-Host "  [WARN] Redis clear failed" -ForegroundColor Yellow
                    }
                    
                    # Clear file-based caches
                    Write-Host "  [*] Clearing file caches and databases..." -ForegroundColor Gray
                    
                    # Clear cache directories
                    $cacheDirs = @('citation_cache', 'correction_cache')
                    $clearedFiles = 0
                    foreach ($dir in $cacheDirs) {
                        if (Test-Path $dir) {
                            $files = Get-ChildItem -Path $dir -File -ErrorAction SilentlyContinue
                            $clearedFiles += $files.Count
                            $files | Remove-Item -Force -ErrorAction SilentlyContinue
                        }
                    }
                    
                    # Clear SQLite cache databases (CRITICAL for fresh extraction)
                    $cacheDb = @(
                        'data\citations.db',
                        'src\data\citations.db',
                        'legal_search_cache.db',
                        'data\legal_search_cache.db',
                        'data\langsearch_cache.db',
                        'src\data\legal_search_cache.db'
                    )
                    $clearedDbs = 0
                    foreach ($db in $cacheDb) {
                        if (Test-Path $db) {
                            Remove-Item -Path $db -Force -ErrorAction SilentlyContinue
                            $clearedDbs++
                        }
                    }
                    
                    if ($clearedFiles -gt 0 -or $clearedDbs -gt 0) {
                        Write-Host "  [OK] Cleared $clearedFiles cache files + $clearedDbs SQLite databases" -ForegroundColor Green
                    } else {
                        Write-Host "  [OK] File caches already empty" -ForegroundColor Green
                    }
                } catch {
                    Write-Host "  [WARN] Could not clear all caches: $($_.Exception.Message)" -ForegroundColor Yellow
                }
                
                # Restart workers to clear in-memory caches
                Write-Host "`n[RQ WORKERS] Restarting workers..." -ForegroundColor Yellow
                docker-compose -f docker-compose.prod.yml restart rqworker1 rqworker2 rqworker3 2>&1 | Out-Null
                Write-Host "  [OK] Workers restarted" -ForegroundColor Green
                Write-Host "`n  [REMINDER] Clear browser cache (Ctrl+Shift+Delete)!" -ForegroundColor Magenta
            }
            
            # Report actual status
            if ($servicesReady) {
                Write-Host "`n[SUCCESS] RESTART COMPLETE - All services ready!" -ForegroundColor Green
                Write-Host "  Python cache cleared - all code changes active" -ForegroundColor DarkGray
                Write-Host "  Application: http://localhost" -ForegroundColor Cyan
                
                # Send startup notification
                Send-StartupNotification -StartupType "quick_restart"
            } else {
                Write-Host "`n[PARTIAL SUCCESS] Containers restarted but some services need more time" -ForegroundColor Yellow
                Write-Host "  Python cache cleared - all code changes active" -ForegroundColor DarkGray
                Write-Host "  Application: http://localhost" -ForegroundColor Cyan
                Write-Host "  [WARN] Some services may take a few more minutes to be fully ready" -ForegroundColor Yellow
                
                # Send startup notification even for partial success
                Send-StartupNotification -StartupType "quick_restart"
            }
            
            # Automatic Redis maintenance to prevent bloat
            try {
                $aofSizeOutput = docker exec casestrainer-redis-prod du -sh /data/appendonlydir 2>$null
                if ($aofSizeOutput) {
                    $aofSize = ($aofSizeOutput -split '\s+')[0]
                    $needsMaintenance = $false
                    
                    # Check if maintenance is needed (>200MB)
                    if ($aofSize -match '(\d+)M' -and [int]$matches[1] -gt 200) {
                        $needsMaintenance = $true
                    } elseif ($aofSize -match '(\d+\.?\d*)G') {
                        $needsMaintenance = $true
                    }
                    
                    if ($needsMaintenance) {
                        Write-Host "`n[MAINTENANCE] Redis AOF is large (${aofSize}) - running automatic cleanup..." -ForegroundColor Yellow
                        
                        # Run cleanup script
                        $cleanupScript = Join-Path $PSScriptRoot 'scripts\clean_redis_old_jobs.py'
                        if (Test-Path $cleanupScript) {
                            docker cp $cleanupScript casestrainer-backend-prod:/app/ 2>$null
                            docker exec casestrainer-backend-prod python /app/clean_redis_old_jobs.py 2>&1 | Out-Null
                            Write-Host '  Cleaned old RQ jobs' -ForegroundColor Green
                        }
                        
                        # Compact AOF
                        $compactResult = docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** BGREWRITEAOF 2>&1 | Select-Object -Last 1
                        if ($compactResult -like '*Background*') {
                            Write-Host '  Started AOF compaction (will complete in background)' -ForegroundColor Green
                        }
                        
                        # Show result
                        Start-Sleep -Seconds 2
                        $newSize = docker exec casestrainer-redis-prod du -sh /data/appendonlydir 2>$null | ForEach-Object { ($_ -split '\s+')[0] }
                        $aofMsg = '  Redis maintenance complete (AOF: ' + $aofSize + ' -> ' + $newSize + ')'
                        Write-Host $aofMsg -ForegroundColor Cyan
                    }
                }
            } catch {
                # Silently ignore errors - don't block startup
            }
            
            # Send startup notification
            Send-StartupNotification -StartupType "quick_restart"
            
            # Start enhanced monitoring suite (if enabled), then background monitoring
            if ($EnableEnhancedMonitoring -or $EnableSelfHealthMonitoring -or $EnableSystemRecoveryLogging -or $EnableEscalationManager) {
                Write-Host "[ENHANCED] Starting enhanced monitoring suite..." -ForegroundColor Cyan
                Start-EnhancedMonitoringSuite
            }
            
            # Start background monitoring after successful restart
            Start-BackgroundMonitoring
            
            exit 0
        } else {
            Write-Host ''
            Write-Host '[ERROR] Restart failed, falling back to full deployment...' -ForegroundColor Red
            $exitCode = $LASTEXITCODE
            $restartMsg = 'Quick restart failed - exit code: ' + $exitCode
            Write-CrashLog $restartMsg 'ERROR'
        }
    }
}

# Log the deployment attempt
$deployTime = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$deployMsg = 'Starting full deployment at ' + $deployTime
Write-CrashLog $deployMsg 'INFO'

# Fall back to full deployment
Write-Host '[FULL DEPLOY] Running full deployment (containers not found or rebuild requested)...' -ForegroundColor Yellow
$fullScriptPath = Join-Path $PSScriptRoot 'scripts\cslaunch.ps1'

if (-not (Test-Path $fullScriptPath)) {
    Write-Host '[ERROR] Could not find scripts\cslaunch.ps1' -ForegroundColor Red
    exit 1
}

# Forward parameters using hashtable for proper splatting
$scriptParams = @{
    Command = 'prod'
}
if ($Build) { $scriptParams['Build'] = $true }
if ($Force) { $scriptParams['Force'] = $true }
if ($NoCache) { $scriptParams['NoCache'] = $true }
if ($NoMonitor) { $scriptParams['NoMonitor'] = $true }

& $fullScriptPath @scriptParams
$deployExitCode = $LASTEXITCODE

# Start background monitoring after deployment (if successful)
Write-Host "[DEBUG] Full deployment exit code: $deployExitCode" -ForegroundColor Gray
if ($deployExitCode -eq 0) {
    Write-Host "[DEBUG] Deployment successful, sending startup notification..." -ForegroundColor Gray
    # Send startup notification
    Send-StartupNotification -StartupType "full_deploy"
    
    # Start enhanced monitoring suite (if enabled), then background monitoring
    if ($EnableEnhancedMonitoring -or $EnableSelfHealthMonitoring -or $EnableSystemRecoveryLogging -or $EnableEscalationManager) {
        Write-Host "[ENHANCED] Starting enhanced monitoring suite after full deployment..." -ForegroundColor Cyan
        Start-EnhancedMonitoringSuite
    }
    
    # Start legacy background monitoring
    Start-BackgroundMonitoring
} else {
    Write-Host "[DEBUG] Deployment failed (exit code: $deployExitCode), skipping startup notification" -ForegroundColor Yellow
}

exit $deployExitCode

