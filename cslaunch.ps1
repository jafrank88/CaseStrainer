# cslaunch.ps1 - Quick restart wrapper for production environment
# This is optimized for fast Python code updates without rebuilding Docker images

[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
param(
    [Parameter()]
    [switch]$Build,
    
    [Parameter()]
    [switch]$NoCache,
    
    [Parameter()]
    [switch]$Force,
    
    [Parameter()]
    [switch]$NoMonitor,    # Disable automatic background monitoring (monitoring is enabled by default)
    
    [Parameter()]
    [switch]$Monitor,      # Enable monitoring mode (default behavior)
    
    [Parameter()]
    [switch]$ConfigureAutostart,  # Configure Docker autostart on boot
    
    [Parameter()]
    [switch]$NoAutostart,  # Disable automatic autostart configuration (autostart enabled by default)
    
    [Parameter()]
    [switch]$ConfigurePeriodicHealthCheck,  # Configure Windows Task Scheduler backup health check (every 2 hours)
    
    [Parameter()]
    [switch]$RemovePeriodicHealthCheck,  # Remove the periodic health check task
    
    [Parameter()]
    [int]$MonitorInterval = 60,  # Default: 60 seconds # TODO: Pass to monitoring modules
    
    [Parameter()]
    [int]$DockerDaemonTimeout = 15,  # Docker daemon freeze timeout in seconds (default: 15) # TODO: Implement timeout logic
    
    [Parameter()]
    [int]$MaxDockerRestartsPerHour = 5,  # Maximum Docker daemon restarts per hour (default: 5) # TODO: Implement rate limiting
    
    [Parameter()]
    [int]$ExtendedDowntimeMinutes = 15,  # After this many minutes of downtime, bypass rate limit # TODO: Implement bypass logic
    
    [Parameter()]
    [switch]$EmergencyRecovery,  # Perform deep emergency recovery of Docker
    
    [Parameter()]
    [switch]$ConfigureServiceRecovery,  # Configure Windows service recovery actions
    
    [Parameter()]
    [switch]$RemoveServiceRecovery,  # Remove Windows service recovery actions
    
    [Parameter()]
    [switch]$CleanupDocker,  # Clean up Docker resources (prune unused images, containers, etc.)
    
    [Parameter()]
    [switch]$AutoCleanup,  # Enable automatic Docker cleanup when disk space is low
    
    [Parameter()]
    [switch]$ScheduleCleanup,  # Schedule weekly automatic cleanup
    
    [Parameter()]
    [switch]$RemoveCleanupSchedule,  # Remove the weekly cleanup schedule
    
    [Parameter()]
    [switch]$Service  # Install/Manage CaseStrainer-Docker-Service for unattended operation
)

# Internal configuration
$EnableNotifications = $false  # Notifications disabled - using external WHM monitoring

# Helper function to test admin privileges
function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CaseStrainer Quick Restart (./cslaunch)" -ForegroundColor Cyan  

Write-Host "`n========================================" -ForegroundColor Cyan

# Start auto-monitoring if no flags provided
if (-not $Build -and -not $Monitor -and -not $ConfigureAutostart -and -not $NoAutostart -and -not $ConfigurePeriodicHealthCheck -and -not $RemovePeriodicHealthCheck -and -not $DeepCleanRestart -and -not $MemoryOptimizeRestart -and -not $NoCache -and -not $Force -and -not $EmergencyRecovery -and -not $ConfigureServiceRecovery -and -not $RemoveServiceRecovery -and -not $CleanupDocker -and -not $Service) {
    Write-Host "[AUTO] Starting unattended monitoring setup..." -ForegroundColor Cyan
    
    # Check if CaseStrainer-Docker-Service is installed
    $serviceTask = Get-ScheduledTask -TaskName "CaseStrainer-Docker-Service" -ErrorAction SilentlyContinue
    if ($serviceTask) {
        Write-Host "[SUCCESS] CaseStrainer-Docker-Service is already installed!" -ForegroundColor Green
        Write-Host "  - Docker will auto-restart without user login" -ForegroundColor Gray
        Write-Host "  - Service runs as SYSTEM account" -ForegroundColor Gray
        Write-Host "  - Survives reboots and logoffs" -ForegroundColor Gray
        
        # Check if service is running
        if ($serviceTask.State -eq "Running") {
            Write-Host "  - Status: Running" -ForegroundColor Green
        } else {
            Write-Host "  - Status: $($serviceTask.State)" -ForegroundColor Yellow
            Write-Host "  - Will start on next boot or manually" -ForegroundColor Gray
        }
    } else {
        # Service not installed - offer to install it
        Write-Host "[INFO] CaseStrainer-Docker-Service is not installed" -ForegroundColor Yellow
        Write-Host "  This service provides unattended Docker auto-restart without user login" -ForegroundColor Gray
        Write-Host "  It runs as a Windows service and survives reboots and logoffs" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Would you like to install the CaseStrainer-Docker-Service?" -ForegroundColor Cyan
        Write-Host "Enter 'y' to install, 'n' to use legacy monitoring, any other key to skip" -ForegroundColor Gray
        
        $response = Read-Host "Install service? [y/n/skip]"
        
        if ($response -eq 'y') {
            Write-Host "`n[INFO] Installing CaseStrainer-Docker-Service..." -ForegroundColor Yellow
            
            # Check if running as administrator
            $isAdmin = Test-AdminPrivileges
            
            if (-not $isAdmin) {
                Write-Host "[WARN] Administrator privileges required for service installation" -ForegroundColor Yellow
                Write-Host "Please run PowerShell as Administrator and try again" -ForegroundColor Gray
                Write-Host "Or run: .\cslaunch.ps1 -Service" -ForegroundColor Cyan
                
                # Fall back to legacy monitoring
                Write-Host "`n[FALLBACK] Using legacy monitoring instead..." -ForegroundColor Yellow
                $modulePath = Join-Path $PSScriptRoot "scripts\modules\UnattendedMonitoring.psm1"
                if (Test-Path $modulePath) {
                    Import-Module $modulePath -Force
                    SetUnattendedMonitoring
                    Write-Host "[SUCCESS] Legacy monitoring configured (requires user login)" -ForegroundColor Green
                } else {
                    Write-Host "[WARN] Unattended monitoring module not found, using legacy monitoring..." -ForegroundColor Yellow
                    & (Join-Path $PSScriptRoot "auto_monitor.ps1") -ScriptRoot $PSScriptRoot
                }
            } else {
                # Run the service creation script
                $serviceScript = Join-Path $PSScriptRoot "Create-DockerService.ps1"
                if (Test-Path $serviceScript) {
                    & $serviceScript
                    Write-Host "[SUCCESS] CaseStrainer-Docker-Service installed!" -ForegroundColor Green
                    Write-Host "Docker will now auto-restart without user login" -ForegroundColor Gray
                } else {
                    Write-Host "[ERROR] Service creation script not found: $serviceScript" -ForegroundColor Red
                    Write-Host "Falling back to legacy monitoring..." -ForegroundColor Yellow
                    
                    # Fall back to legacy monitoring
                    $modulePath = Join-Path $PSScriptRoot "scripts\modules\UnattendedMonitoring.psm1"
                    if (Test-Path $modulePath) {
                        Import-Module $modulePath -Force
                        SetUnattendedMonitoring
                        Write-Host "[SUCCESS] Legacy monitoring configured (requires user login)" -ForegroundColor Green
                    } else {
                        Write-Host "[WARN] Unattended monitoring module not found, using legacy monitoring..." -ForegroundColor Yellow
                        & (Join-Path $PSScriptRoot "auto_monitor.ps1") -ScriptRoot $PSScriptRoot
                    }
                }
            }
        } elseif ($response -eq 'n') {
            Write-Host "`n[INFO] Using legacy monitoring (requires user login)..." -ForegroundColor Yellow
            # Import and run unattended monitoring setup
            $modulePath = Join-Path $PSScriptRoot "scripts\modules\UnattendedMonitoring.psm1"
            if (Test-Path $modulePath) {
                Import-Module $modulePath -Force
                SetUnattendedMonitoring
                Write-Host "[SUCCESS] Legacy monitoring is now configured and will survive reboots!" -ForegroundColor Green
            } else {
                # Fallback to old auto-monitor
                Write-Host "[WARN] Unattended monitoring module not found, using legacy monitoring..." -ForegroundColor Yellow
                & (Join-Path $PSScriptRoot "auto_monitor.ps1") -ScriptRoot $PSScriptRoot
            }
        } else {
            Write-Host "[INFO] Skipped - no monitoring configured" -ForegroundColor Yellow
            Write-Host "To install service later, run: .\cslaunch.ps1 -Service" -ForegroundColor Gray
            Write-Host "To configure legacy monitoring, run: .\cslaunch.ps1 -Monitor" -ForegroundColor Gray
        }
    }
}

# Function to implement exponential backoff for restart attempts
function Get-BackoffDelay {
    param(
        [int]$AttemptNumber,
        [int]$BaseDelay = 30,
        [int]$MaxDelay = 300
    )
    
    $delay = [math]::Min($BaseDelay * [math]::Pow(2, $AttemptNumber - 1), $MaxDelay)
    return $delay
}

# Enhanced function to capture Docker events
function Start-DockerEventMonitoring {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
    param()
    
    $eventLogPath = Join-Path $PSScriptRoot "logs\docker_events.log"
    
    $eventScriptBlock = {
        param($LogPath)
        
        function Write-DockerEventLog {
            param([string]$Message)
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logEntry = "[$timestamp] $Message"
            Add-Content -Path $LogPath -Value $logEntry
        }
        
        try {
            Write-DockerEventLog "=== DOCKER EVENT MONITORING STARTED ==="
            docker events 2>&1 | ForEach-Object {
                if ($_ -and $_.Trim()) {
                    Write-DockerEventLog $_
                }
            }
        } catch {
            Write-DockerEventLog "ERROR: Docker event monitoring failed: $($_.Exception.Message)"
        }
    }
    
    if ($PSCmdlet.ShouldProcess("Docker event monitoring", "Start")) {
        $eventJob = Start-Job -Name "Docker-Event-Monitor" -ScriptBlock $eventScriptBlock -ArgumentList $eventLogPath
        
        Write-Host "[EVENTS] Docker event monitoring started (job ID: $($eventJob.Id))" -ForegroundColor Cyan
        Write-Host "  - Event log: $eventLogPath" -ForegroundColor Gray
        
        return $eventJob
    }
}
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
    $removed = Remove-BrokenDockerHealthTask -ErrorAction Stop
    if ($removed) {
        Write-Host "[CLEANUP] Removed broken DockerHealthCheck task" -ForegroundColor Yellow
    }
} catch {
    Write-Verbose "Optional cleanup of DockerHealthCheck task failed: $_"
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

# Admin notification function with external monitoring fallback
function Send-AdminNotification {
    [CmdletBinding()]
    param(
        [string]$Subject,
        [string]$Message,
        [string]$Severity = "ERROR",
        [string]$IssueType = "general"
    )
    
    # Skip if notifications are explicitly disabled
    if (-not $EnableNotifications) {
        Write-Verbose "Notifications are disabled. Skipping notification."
        return
    }
    
    # Check cooldown period
    $now = Get-Date
    $NotificationCooldownMinutes = 60  # Default cooldown of 60 minutes
    
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
    
    # Send email notification if enabled
    if ($NotificationEmail -and $EnableNotifications) {
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
            if ($env:SMTP_USERNAME) {
                # Secure SMTP credential handling with encrypted password
                try {
                    # Require encrypted password - no plaintext fallback
                    if (-not $env:SMTP_PASSWORD_ENCRYPTED) {
                        Write-Error "SMTP_PASSWORD_ENCRYPTED environment variable is not set. Please configure encrypted SMTP credentials."
                        Write-Host @"
SETUP INSTRUCTIONS:
1. Run the following command in an elevated (admin) PowerShell window:

   `$securePass = Read-Host "Enter your SMTP password" -AsSecureString
   `$encrypted = ConvertFrom-SecureString -SecureString `$securePass
   [System.Environment]::SetEnvironmentVariable('SMTP_PASSWORD_ENCRYPTED', `$encrypted, 'Machine')
   [System.Environment]::SetEnvironmentVariable('SMTP_USERNAME', 'your_smtp_username', 'Machine')

2. Restart your application for the changes to take effect.

Note: The password is encrypted using the current user's credentials and can only be decrypted by the same user on the same machine.
"@
                        return
                    }

                    try {
                        $securePassword = ConvertTo-SecureString -String $env:SMTP_PASSWORD_ENCRYPTED -ErrorAction Stop
                        Write-Debug "Successfully decrypted SMTP password from SMTP_PASSWORD_ENCRYPTED"
                    } catch {
                        Write-Error "Failed to decrypt SMTP_PASSWORD_ENCRYPTED: $($_.Exception.Message)"
                        Write-Host "Please regenerate your encrypted password using the instructions above."
                        return
                    }
                    
                    $credential = New-Object System.Management.Automation.PSCredential($env:SMTP_USERNAME, $securePassword)
                    $emailParams['Credential'] = $credential
                    Write-Debug "SMTP credentials configured successfully"
                } catch {
                    Write-DockerDaemonLog "Failed to create SMTP credentials: $($_.Exception.Message)" "ERROR"
                    return
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
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$ContainerName
    )
    
    try {
        $inspect = docker inspect $ContainerName 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Container '$ContainerName' not found or Docker daemon not running"
        }
        
        $containerInfo = $inspect | ConvertFrom-Json -ErrorAction Stop
        
        return @{
            Status = $containerInfo.State.Status
            ExitCode = $containerInfo.State.ExitCode
            RestartCount = $containerInfo.RestartCount
            Health = $containerInfo.State.Health.Status
        }
    } catch {
        Write-Verbose "Failed to inspect container $ContainerName : $_"
        return @{
            Status = "unknown"
            ExitCode = -1
            RestartCount = 0
            Health = "unknown"
        }
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

function Test-IsDockerAutostartEnabled {
    <#
    .SYNOPSIS
        Checks if Docker autostart is configured for system boot.
    #>
    $TaskName = "CaseStrainer-Docker-AutoStart"
    $Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    return ($null -ne $Task)
}

function Get-ContainerCrashInfo {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$ContainerName
    )
    
    Write-CrashLog "Analyzing crash for container: $ContainerName" "WARN"
    
    try {
        # Get container info
        $info = Get-ContainerStatus -ContainerName $ContainerName
        
        # Get container logs (last 50 lines)
        $logs = docker logs --tail 50 $ContainerName 2>&1 | Out-String
        
        # Check for common error patterns
        $foundErrors = @()
        
        # Check for out of memory errors
        if ($logs -match "out of memory" -or $logs -match "OOM") {
            $foundErrors += "Container ran out of memory"
        }
        
        # Check for port conflicts
        if ($logs -match "address already in use" -or $logs -match "port is already allocated") {
            $foundErrors += "Port conflict detected"
        }
        
        # Check for missing dependencies
        if ($logs -match "connection refused" -or $logs -match "no such host") {
            $foundErrors += "Dependency service unavailable"
        }
        
        # Create crash report
        $crashReport = @"
=== CONTAINER CRASH REPORT ===
Time: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Container: $ContainerName
Status: $($info.Status)
Exit Code: $($info.ExitCode)
Restart Count: $($info.RestartCount)
Health: $($info.Health)

ERRORS DETECTED:
$($foundErrors -join "`n")

LAST 50 LINES OF LOGS:
$logs

=== END OF REPORT ===
"@
        
        # Save crash report to log file
        Add-Content -Path $crashLogPath -Value $crashReport
        
        return @{
            Status = $info.Status
            ExitCode = $info.ExitCode
            RestartCount = $info.RestartCount
            Health = $info.Health
            Errors = $foundErrors
            LastLogs = $logs
        }
    } catch {
        Write-Error "Failed to get crash info for container $ContainerName : $_"
        return @{
            Status = "error"
            ExitCode = -1
            RestartCount = 0
            Health = "unknown"
            Errors = @("Failed to analyze crash: $_")
            LastLogs = ""
        }
    }
}

function Remove-BrokenDockerHealthTask {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='High')]
    param()
    
    <#
    .SYNOPSIS
        Removes any broken Docker health check tasks from previous versions.
        
        .DESCRIPTION
            This function removes scheduled tasks related to Docker health checks that may have been created
            by previous versions of the script. It supports -WhatIf and -Confirm parameters.
        #>
        
        $taskName = "DockerHealthCheck"
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        
        if ($task) {
            if ($PSCmdlet.ShouldProcess("Task '$taskName'", "Remove scheduled task")) {
                try {
                    Write-Verbose "Removing scheduled task: $taskName"
                    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
                    Write-Verbose "Successfully removed scheduled task: $taskName"
                    return $true
                } catch {
                    Write-Error "Failed to remove broken Docker health check task: $_"
                    return $false
                }
            } else {
                # WhatIf scenario
                return $true
            }
        }
        
        Write-Verbose "No broken Docker health check task found to remove"
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
        if (Test-IsDockerAutostartEnabled) {
            if (-not $Silent) {
                Write-Host "  [OK] Docker autostart already configured" -ForegroundColor Green
            }
            return $true
        }
        
        # Rest of the function implementation...
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
        
        # Configure service recovery actions
        try {
            $serviceName = "com.docker.service"
            $recoveryScript = Join-Path $PSScriptRoot "scripts\docker_emergency_recovery.ps1"
            
            # Configure service recovery
            sc.exe failure $serviceName reset= 86400 actions= restart/5000/run/15000/restart/30000 command= "`"$recoveryScript`" -Force" 2>$null
            sc.exe config $serviceName start= auto 2>$null
            
            if (-not $Silent) {
                Write-Host "  [OK] Service recovery configured" -ForegroundColor Green
                Write-Host "       Docker service will auto-restart on failure" -ForegroundColor Gray
            }
        } catch {
            if (-not $Silent) {
                Write-Host "  [WARN] Could not configure service recovery (requires admin)" -ForegroundColor Yellow
            }
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
            # Non-critical - ignore
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
            # Non-critical - ignore
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

function Test-AdminPrivileges {
    try {
        $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
        return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        Write-Verbose "Failed to check admin privileges: $_"
        return $false
    }
}

function Restart-DockerEnhanced {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='High')]
    param(
        [string]$Reason = "Auto-restart triggered",
        [int]$MaxRetries = 3,
        [int]$RetryDelay = 30
    )

    Write-Host "[DOCKER] Starting enhanced Docker restart..." -ForegroundColor Cyan
    Write-DockerDaemonLog "=== ENHANCED DOCKER RESTART INITIATED ===" "WARN"
    Write-DockerDaemonLog "Reason: $Reason" "WARN"

    $attempt = 1
    $success = $false
    $isAdmin = Test-AdminPrivileges

    while ($attempt -le $MaxRetries -and -not $success) {
        Write-Host "[DOCKER] Attempt $attempt of $MaxRetries..." -ForegroundColor Cyan
        Write-DockerDaemonLog "Restart attempt $attempt of $MaxRetries" "INFO"
        
        try {
            # Stop Docker processes more aggressively
            Write-Host "[DOCKER] Stopping Docker processes..." -ForegroundColor Yellow
            Get-Process | Where-Object { 
                $_.ProcessName -like "*docker*" -or 
                $_.ProcessName -like "*com.docker*" -or
                $_.ProcessName -like "*vpnkit*" -or
                $_.ProcessName -like "*wsl*" -or
                $_.ProcessName -like "*wslservice*"
            } | Stop-Process -Force -ErrorAction SilentlyContinue

            # Stop Docker service if running as admin
            if ($isAdmin) {
                $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
                if ($service) {
                    Stop-Service -Name "com.docker.service" -Force -ErrorAction Stop
                    Start-Sleep -Seconds 5
                }
                
                # Also stop WSL if it's running
                $wslService = Get-Service -Name "LxssManager" -ErrorAction SilentlyContinue
                if ($wslService -and $wslService.Status -eq 'Running') {
                    Stop-Service -Name "LxssManager" -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Seconds 2
                }
            }

            # Clear Docker's internal state
            $dockerDataPath = Join-Path $env:ProgramData "Docker"
            if (Test-Path "$dockerDataPath\com.docker.backend.pid") {
                Remove-Item "$dockerDataPath\com.docker.backend.pid" -Force -ErrorAction SilentlyContinue
            }

            # Start Docker service if running as admin
            if ($isAdmin) {
                # Start WSL first if it was stopped
                $wslService = Get-Service -Name "LxssManager" -ErrorAction SilentlyContinue
                if ($wslService -and $wslService.Status -ne 'Running') {
                    Start-Service -Name "LxssManager" -ErrorAction SilentlyContinue
                    Start-Sleep -Seconds 5
                }
                
                Start-Service -Name "com.docker.service" -ErrorAction Stop
                Start-Sleep -Seconds 10
            }

            # Start Docker Desktop
            $dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
            if (-not (Test-Path $dockerDesktopPath)) {
                $dockerDesktopPath = "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
            }

            if (Test-Path $dockerDesktopPath) {
                # Kill any existing Docker Desktop processes first
                Get-Process | Where-Object { $_.Path -like "*Docker Desktop.exe" } | Stop-Process -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
                
                # Start Docker Desktop with a fresh instance
                $process = Start-Process -FilePath $dockerDesktopPath -PassThru -ErrorAction Stop
                Write-DockerDaemonLog "Started Docker Desktop (PID: $($process.Id))" "INFO"
            } else {
                throw "Docker Desktop executable not found at $dockerDesktopPath"
            }

            # Wait for Docker to be ready with increased timeout
            $maxWait = 300  # 5 minutes
            $startTime = Get-Date
            $dockerReady = $false

            while (((Get-Date) - $startTime).TotalSeconds -lt $maxWait) {
                $health = Test-DockerDaemonHealth -TimeoutSeconds 10
                if ($health.DockerInfo -and $health.DockerPs) {
                    $dockerReady = $true
                    break
                }
                Start-Sleep -Seconds 5
                Write-Host "." -NoNewline
            }

            if ($dockerReady) {
                $recoveryTime = [math]::Round(((Get-Date) - $startTime).TotalSeconds)
                Write-Host "`n[DOCKER] Docker restarted successfully in ${recoveryTime}s!" -ForegroundColor Green
                Write-DockerDaemonLog "Docker restart successful after ${recoveryTime}s" "SUCCESS"
                $success = $true
                return $true
            } else {
                throw "Docker did not become ready within $maxWait seconds"
            }
        }
        catch {
            $errorMsg = $_.Exception.Message
            Write-Host "[DOCKER] Attempt $attempt failed: $errorMsg" -ForegroundColor Red
            Write-DockerDaemonLog "Restart attempt $attempt failed: $errorMsg" "ERROR"
            Write-DockerDaemonLog $_.ScriptStackTrace "DEBUG"
            
            $attempt++
            if ($attempt -le $MaxRetries) {
                $retryTime = Get-Date
                Write-Host "[DOCKER] Retrying in $RetryDelay seconds..." -ForegroundColor Yellow
                Write-DockerDaemonLog "Will retry Docker restart at $($retryTime.AddSeconds($RetryDelay))" "WARN"
                Start-Sleep -Seconds $RetryDelay
            }
        }
    }

    if (-not $success) {
        $errorMsg = "Failed to restart Docker after $MaxRetries attempts"
        Write-Host "[DOCKER] $errorMsg" -ForegroundColor Red
        Write-DockerDaemonLog $errorMsg "ERROR"
        
        # Try one last emergency restart method
        try {
            Write-Host "[DOCKER] Attempting emergency restart method..." -ForegroundColor Yellow
            if ($isAdmin) {
                Start-Process "shutdown.exe" -ArgumentList "/r", "/t", "30", "/c", "Emergency Docker recovery restart" -Verb RunAs
            } else {
                Write-Host "[DOCKER] Admin privileges required for emergency restart" -ForegroundColor Red
            }
            return $false
        }
        catch {
            Write-Host "[DOCKER] Emergency restart failed: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    }
}

function Restart-DockerDaemon {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='High')]
    param()
    
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
        if (-not $PSCmdlet.ShouldProcess("Docker Desktop service", "Restart")) {
            Write-Host "[INFO] Docker restart was cancelled by user" -ForegroundColor Yellow
            return $false
        }

        Write-Host "[INFO] Stopping Docker Desktop..." -ForegroundColor Cyan
        & "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe" -shutdown
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
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
    param(
        [int]$Interval = 60,
        [int]$Timeout = 15,
        [int]$MaxRestarts = 5,
        [int]$DowntimeMinutes = 15
    )
    
    <#
    .SYNOPSIS
        Starts continuous monitoring of Docker containers and Docker daemon health.
    
    .DESCRIPTION
        This function monitors the status of Docker containers and optionally the Docker daemon.
        It can automatically restart containers that have crashed and handle Docker daemon freezes.
        Supports -WhatIf and -Confirm parameters for safety.
    #>
    
    if (-not $PSCmdlet.ShouldProcess("Start container monitoring", "Begin monitoring Docker containers and daemon health?", "Start monitoring")) {
        Write-Host "Container monitoring was not started (user cancelled)." -ForegroundColor Yellow
        return
    }
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "MONITORING MODE - Press Ctrl+C to stop" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # Show monitoring configuration
    Write-Host "Container Check Interval: $Interval seconds" -ForegroundColor Gray
    Write-Host "Crash log: $crashLogPath" -ForegroundColor Gray
    
    if ($EnableDockerDaemonMonitor) {
        Write-Host "Docker Daemon Monitor: ENABLED" -ForegroundColor Green
        Write-Host "  - Freeze timeout: ${Timeout}s" -ForegroundColor Gray
        Write-Host "  - Max restarts per hour: $MaxRestarts" -ForegroundColor Gray
        Write-Host "  - Extended downtime threshold: ${DowntimeMinutes} minutes (nuclear option)" -ForegroundColor Gray
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
                                 ((Get-Date) - $lastDockerCheck).TotalSeconds -ge ($Interval * 2) -or
                                 $dockerDaemonFailures -gt 0)
            
            if ($shouldCheckDocker) {
                $health = Test-DockerDaemonHealth -TimeoutSeconds $Timeout
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
                        
                        # Check disk space periodically (every 5 minutes)
                        if ($AutoCleanup) {
                            $systemDrive = Get-CimInstance -ClassName Win32_LogicalDisk | Where-Object {$_.DeviceID -eq "C:"}
                            $freeSpaceGB = [math]::Round($systemDrive.FreeSpace / 1GB, 2)
                            
                            if ($freeSpaceGB -lt 30) {
                                Write-DockerDaemonLog "Low disk space detected: $freeSpaceGB GB free" "WARN"
                                Write-Host "[WARN] Low disk space: $freeSpaceGB GB free - running automatic cleanup" -ForegroundColor Yellow
                                Invoke-DockerCleanup -Auto
                            }
                        }
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
                        $bypassRateLimit = $downtimeMinutes -ge $DowntimeMinutes
                        
                        if ($bypassRateLimit) {
                            Write-DockerDaemonLog "NUCLEAR OPTION: Docker down for $([math]::Round($downtimeMinutes, 1)) minutes - bypassing rate limit" "WARN"
                            Write-Host "[$timestamp] as?i,?  NUCLEAR OPTION: Docker down for $([math]::Round($downtimeMinutes, 1)) min - forcing restart" -ForegroundColor Magenta
                        }
                        
                        if ($recentRestarts.Count -lt $MaxRestarts -or $bypassRateLimit) {
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
    Start-ContainerMonitoring -Interval $MonitorInterval -Timeout $DockerDaemonTimeout -MaxRestarts $MaxDockerRestartsPerHour -DowntimeMinutes $ExtendedDowntimeMinutes
    exit 0
}

# Function to start watchdog that monitors the monitoring job (checks every 5 minutes)
function Start-MonitoringWatchdog {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
    param()
    
    <#
    .SYNOPSIS
        Starts a watchdog that monitors the main monitoring job.
    
    .DESCRIPTION
        This function starts a background job that periodically checks if the main monitoring job
        is still running. If the monitoring job has stopped unexpectedly, the watchdog will
        attempt to restart it. The watchdog runs with elevated privileges if available.
        
        Supports -WhatIf and -Confirm parameters for safety.
    #>
    
    $watchdogJobName = "CaseStrainer-Monitor-Watchdog"
    
    # Check if watchdog already exists
    $existingWatchdog = Get-Job -Name $watchdogJobName -ErrorAction SilentlyContinue
    if ($existingWatchdog) {
        Write-Host "[INFO] Monitoring watchdog already running (job ID: $($existingWatchdog.Id))" -ForegroundColor Cyan
        return $true
    }
    
    # Check if running as administrator (required for Docker restart capability)
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
    
    if (-not $PSCmdlet.ShouldProcess("Start monitoring watchdog", 
                                    "Start a background watchdog to monitor the monitoring job?",
                                    "Start monitoring watchdog")) {
        Write-Host "Monitoring watchdog was not started (user cancelled)." -ForegroundColor Yellow
        return $false
    }
    
    Write-Host "[INFO] Starting monitoring watchdog (checks every 5 minutes)..." -ForegroundColor Cyan
    
    if (-not $isAdmin) {
        Write-Host "[WARN] Monitoring watchdog starting WITHOUT Administrator privileges" -ForegroundColor Yellow
        Write-Host "  [!!]  Docker restart functionality will be LIMITED" -ForegroundColor Yellow
        Write-Host "  [!!]  The watchdog can monitor and log, but cannot restart Docker service" -ForegroundColor Yellow
        Write-Host "  [!!]  To enable full auto-recovery, run cslaunch as Administrator" -ForegroundColor Cyan
        Write-Host "       Right-click PowerShell -> Run as Administrator, then run: .\cslaunch" -ForegroundColor Gray
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
                Write-Host "[ENHANCED] System recovery logger started (Job ID: $($job.Id))" -ForegroundColor Green
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
                Write-Host "[ENHANCED] Escalation manager started (Job ID: $($job.Id))" -ForegroundColor Green
            } catch {
                Write-Host "[ENHANCED] Failed to start escalation manager: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "[ENHANCED] Escalation manager script not found" -ForegroundColor Yellow
        }
    }
    
    # Summary
    Write-Host "[ENHANCED] Enhanced monitoring suite started with $($monitoringJobs.Count) components" -ForegroundColor Cyan
    Write-Host "[ENHANCED] Active monitoring jobs:" -ForegroundColor Gray
    foreach ($job in $monitoringJobs) {
        Write-Host "[ENHANCED]   - $($job.Name) (ID: $($job.Id))" -ForegroundColor Gray
    }
    
    Write-Host "[ENHANCED] Enhanced logs location: logs\enhanced_*.log" -ForegroundColor Cyan
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
                Write-Host "[ENHANCED] Enhanced Docker restart completed successfully" -ForegroundColor Green
                return $true
            } else {
                Write-Host "[ENHANCED] Enhanced Docker restart failed (exit code: $($process.ExitCode))" -ForegroundColor Red
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
            Write-Host ("[ENHANCED]   {0}: {1} (Last: {2}m ago)" -f $logFile, $status, [math]::Round($timeSince.TotalMinutes)) -ForegroundColor Gray
        } else {
            Write-Host ("[ENHANCED]   {0}: NOT FOUND" -f $logFile) -ForegroundColor Red
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
    
       # Start Docker event monitoring
    Write-Host "[INFO] Starting Docker event monitoring..." -ForegroundColor Cyan
    $eventJob = Start-DockerEventMonitoring
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
    # UPDATED: Now includes enhanced Docker restart with better error handling and logging
    $monitorScriptBlock = {
        param(
            $ScriptRoot,
            $MonitorInterval,
            $DockerDaemonTimeout,
            $MaxDockerRestartsPerHour,
            $ExtendedDowntimeMinutes
        )

        # Import common functions
        . (Join-Path $ScriptRoot "cslaunch.ps1" -ErrorAction Stop)

        function Write-DaemonLog {
            param(
                [string]$Message,
                [string]$Level = "INFO"
            )
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logMessage = "[$timestamp] [$Level] $Message"
            $logFile = Join-Path $ScriptRoot "logs\docker_daemon_monitor.log"
            try {
                # Ensure logs directory exists
                $logDir = Split-Path -Parent $logFile
                if (-not (Test-Path $logDir)) {
                    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
                }
                Add-Content -Path $logFile -Value $logMessage -ErrorAction Stop
            } catch {
                Write-Error "Failed to write to log file: $_"
            }
            
            if ($Level -eq "ERROR" -or $Level -eq "WARN") {
                Write-Error $logMessage
            } else {
                Write-Verbose $logMessage
            }
        }

        function Send-HealthNotification {
            param(
                [string]$Subject,
                [string]$Message,
                [string]$Severity = "INFO"
            )
            try {
                $fullMessage = "$Message`n`nTimestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
                $fullMessage += "Host: $env:COMPUTERNAME`n"
                $fullMessage += "User: $env:USERNAME`n"
                
                # Try to send notification using the main script's function if available
                if (Get-Command -Name Send-AdminNotification -ErrorAction SilentlyContinue) {
                    Send-AdminNotification -Subject $Subject -Message $fullMessage -Severity $Severity
                } else {
                    # Fallback to just logging if notification function isn't available
                    Write-DaemonLog "[NOTIFICATION] $Severity - $Subject`n$fullMessage" $Severity
                }
            } catch {
                Write-DaemonLog "Failed to send notification: $($_.Exception.Message)" "ERROR"
            }
        }

        # Initialize monitoring variables
        $lastDockerCheck = $null
        $dockerDaemonFailures = 0
        $lastRestartTime = $null
        $restartCount = 0
        $extendedDowntimeStart = $null
        $isAdmin = Test-AdminPrivileges
        $dockerRestartHistory = [System.Collections.Generic.List[DateTime]]::new()

        Write-DaemonLog "=== ENHANCED DOCKER MONITOR STARTED ===" "INFO"
        Write-DaemonLog "Check interval: ${MonitorInterval}s" "INFO"
        Write-DaemonLog "Freeze timeout: ${DockerDaemonTimeout}s" "INFO"
        Write-DaemonLog "Max restarts/hour: $MaxDockerRestartsPerHour" "INFO"
        Write-DaemonLog "Extended downtime threshold: ${ExtendedDowntimeMinutes} minutes" "INFO"
        Write-DaemonLog "Running as admin: $isAdmin" "INFO"

        # Main monitoring loop
        while ($true) {
            try {
                $currentTime = Get-Date
                $shouldCheck = ($null -eq $lastDockerCheck -or 
                             (($currentTime - $lastDockerCheck).TotalSeconds -ge $MonitorInterval))
                
                if ($shouldCheck) {
                    $health = Test-DockerDaemonHealth -TimeoutSeconds $DockerDaemonTimeout
                    $lastDockerCheck = $currentTime
                    
                    if ($health.DockerInfo -and $health.DockerPs) {
                        if ($dockerDaemonFailures -gt 0) {
                            $recoveryMsg = "Docker daemon recovered after $dockerDaemonFailures failures"
                            Write-DaemonLog $recoveryMsg "SUCCESS"
                            
                            # Send recovery notification if we had previous failures
                            if ($dockerDaemonFailures -ge 3) {
                                $notificationMsg = @"
Docker daemon has recovered after $dockerDaemonFailures failures.

Recovery details:
- Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- Docker Info: $($health.DockerInfo)
- Docker PS: $($health.DockerPs)
- Docker Service: $($health.DockerService)

System is now back to normal operation.
"@
                                Send-HealthNotification -Subject "Docker Daemon Recovered" -Message $notificationMsg -Severity "INFO"
                            }
                            
                            $dockerDaemonFailures = 0
                            $extendedDowntimeStart = $null
                            $dockerRestartHistory.Clear()
                        }
                    } else {
                        # Docker is not healthy
                        $dockerDaemonFailures++
                        $healthStatus = "DockerInfo: $($health.DockerInfo), DockerPs: $($health.DockerPs), DockerService: $($health.DockerService)"
                        Write-DaemonLog "Docker daemon health check FAILED (attempt $dockerDaemonFailures)" "ERROR"
                        Write-DaemonLog "  $healthStatus" "ERROR"
                        
                        # Track restart history for rate limiting
                        $now = Get-Date
                        $dockerRestartHistory.Add($now)
                        
                        # Remove restarts older than 1 hour
                        $oneHourAgo = $now.AddHours(-1)
                        $recentRestarts = $dockerRestartHistory | Where-Object { $_ -gt $oneHourAgo }
                        $dockerRestartHistory = [System.Collections.Generic.List[DateTime]]$recentRestarts
                        $restartCount = $dockerRestartHistory.Count
                        
                        # Extended downtime handling
                        if ($null -eq $extendedDowntimeStart) {
                            $extendedDowntimeStart = $now
                        }
                        $downtimeMinutes = [math]::Round(([DateTime]::Now - $extendedDowntimeStart).TotalMinutes, 1)
                        $extendedDowntime = $downtimeMinutes -ge $ExtendedDowntimeMinutes

                        # Check if we've exceeded the rate limit
                        if ($restartCount -gt $MaxDockerRestartsPerHour -and -not $extendedDowntime) {
                            $nextRestartTime = $dockerRestartHistory[0].AddHours(1)
                            $timeUntilNextRestart = $nextRestartTime - (Get-Date)
                            $minutesLeft = [math]::Ceiling($timeUntilNextRestart.TotalMinutes)
                            
                            $rateLimitMsg = "Restart rate limit reached. $restartCount restarts in the last hour. Next restart possible in $minutesLeft minutes"
                            Write-DaemonLog $rateLimitMsg "WARN"
                            
                            # Only send notification on first rate limit hit to avoid spam
                            if ($restartCount -eq ($MaxDockerRestartsPerHour + 1)) {
                                $notificationMsg = @"
Docker daemon restart rate limit reached.

Current status:
- Health check failures: $dockerDaemonFailures
- Restart attempts in last hour: $restartCount
- Next restart allowed: $($nextRestartTime.ToString('yyyy-MM-dd HH:mm:ss'))
- Current health: $healthStatus
- Downtime: $downtimeMinutes minutes

System will attempt to restart again in $minutesLeft minutes or when extended downtime threshold is reached.
"@
                                Send-HealthNotification -Subject "Docker Restart Rate Limit Reached" -Message $notificationMsg -Severity "WARNING"
                            }
                            
                            # Skip this check cycle
                            continue
                        }

                        # Attempt to restart Docker
                        $restartReason = if ($extendedDowntime) {
                            "Extended downtime detected (${downtimeMinutes} minutes). Bypassing rate limit."
                        } else {
                            "Health check failed (attempt $dockerDaemonFailures of $MaxDockerRestartsPerHour per hour)"
                        }

                        Write-DaemonLog "Attempting to restart Docker: $restartReason" "WARN"
                        $restartResult = Restart-DockerEnhanced -Reason $restartReason -MaxRetries 3 -RetryDelay 30

                        if ($restartResult) {
                            $recoveryMsg = "Docker restart successful after $dockerDaemonFailures failures"
                            Write-DaemonLog $recoveryMsg "SUCCESS"
                            
                            # Update restart history
                            $dockerRestartHistory.Add((Get-Date))
                            
                            # Send success notification if we had multiple failures
                            if ($dockerDaemonFailures -ge 3) {
                                $notificationMsg = @"
Docker daemon has been successfully restarted after $dockerDaemonFailures failures.

Recovery details:
- Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- Total downtime: $downtimeMinutes minutes
- Restart reason: $restartReason
- Admin privileges: $isAdmin

System is now back to normal operation.
"@
                                Send-HealthNotification -Subject "Docker Restart Successful" -Message $notificationMsg -Severity "INFO"
                            }
                            
                            $dockerDaemonFailures = 0
                            $extendedDowntimeStart = $null
                            
                            # Wait longer after a successful restart to allow services to stabilize
                            $stabilizationDelay = [math]::Min($MonitorInterval * 2, 300)  # Max 5 minutes
                            Write-DaemonLog "Waiting ${stabilizationDelay}s for Docker to stabilize after restart" "INFO"
                            Start-Sleep -Seconds $stabilizationDelay
                            continue
                        } else {
                            $errorMsg = "Docker restart failed (attempt $restartCount of $MaxDockerRestartsPerHour per hour)"
                            Write-DaemonLog $errorMsg "ERROR"
                            
                            # Send failure notification for first and every 3rd subsequent failure
                            if (($dockerDaemonFailures -eq 1) -or ($dockerDaemonFailures % 3 -eq 0)) {
                                $notificationMsg = @"
Failed to restart Docker daemon.

Failure details:
- Attempt: $dockerDaemonFailures
- Restart reason: $restartReason
- Health status: $healthStatus
- Running as admin: $isAdmin
- Next retry in: $MonitorInterval seconds

Please investigate the Docker service and logs for more details.
"@
                                Send-HealthNotification -Subject "Docker Restart Failed" -Message $notificationMsg -Severity "ERROR"
                            }
                        }
                    }
                }
            } catch {
                $errorMsg = "Error in monitoring loop: $($_.Exception.Message)"
                Write-DaemonLog $errorMsg "ERROR"
                Write-DaemonLog $_.ScriptStackTrace "DEBUG"
                
                # Only send notification for unhandled errors to avoid spam
                if ($dockerDaemonFailures % 5 -eq 0) {  # Every 5th error
                    $notificationMsg = @"
Unhandled error in Docker monitoring loop.

Error: $($_.Exception.Message)
Line: $($_.InvocationInfo.ScriptLineNumber)
Script: $($_.InvocationInfo.ScriptName)

Stack trace:
$($_.ScriptStackTrace)
"@
                    Send-HealthNotification -Subject "Docker Monitoring Error" -Message $notificationMsg -Severity "ERROR"
                }
            }

            # Wait before next check, with exponential backoff for repeated failures
            $backoffFactor = [math]::Min([math]::Pow(1.5, [math]::Min($dockerDaemonFailures, 5)), 10)  # Cap at 10x
            $actualDelay = [math]::Min($MonitorInterval * $backoffFactor, 900)  # Max 15 minutes
            
            if ($dockerDaemonFailures -gt 0) {
                Write-DaemonLog "Waiting ${actualDelay}s before next check (backoff factor: ${backoffFactor}x)" "INFO"
            }
            
            Start-Sleep -Seconds $actualDelay
        } # End while $true
    } # End of monitor script block
    
    # Start the monitoring job
    $job = Start-Job -Name "CaseStrainer-Monitor" -ScriptBlock $monitorScriptBlock `
        -ArgumentList $PSScriptRoot, $MonitorInterval, $DockerDaemonTimeout, $MaxDockerRestartsPerHour, $ExtendedDowntimeMinutes
    
    # Only try to access job ID if the job was created successfully
    if ($job) {
        Write-Host "[OK] Background monitoring started (job ID: $($job.Id))" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Background monitoring job may not have started correctly" -ForegroundColor Yellow
    }
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
                    
                    # Also configure service recovery by default when running as admin
                    Write-Host "[AUTOSTART] Configuring Docker service recovery actions..." -ForegroundColor Yellow
                    $serviceRecoveryConfigured = Set-DockerServiceRecovery
                    if ($serviceRecoveryConfigured) {
                        Write-Host "[SUCCESS] Service recovery configured - Docker will auto-restart on failure" -ForegroundColor Green
                    } else {
                        Write-Host "[WARN] Service recovery configuration failed" -ForegroundColor Yellow
                    }
                    
                    # Check if automatic cleanup should be performed
                    if ($AutoCleanup) {
                        Write-Host "[AUTOSTART] Checking disk space for automatic cleanup..." -ForegroundColor Yellow
                        Invoke-DockerCleanup -Auto
                    }
                } else {
                    Write-Host "[WARN] Autostart configuration failed" -ForegroundColor Yellow
                }
            } else {
                # Not admin - inform user how to enable
                Write-Host "[INFO] Docker autostart not configured (requires Administrator privileges)" -ForegroundColor Yellow
                Write-Host "       To enable autostart and service recovery, run as Administrator once:" -ForegroundColor Gray
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
        Write-Verbose "Autostart configuration error: $_"
    }
}

# ====================================================================
# DOCKER SERVICE CONFIGURATION
# ====================================================================

# Handle Service parameter
if ($Service) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "CaseStrainer Docker Service Management" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # Check if running as administrator
    $isAdmin = Test-AdminPrivileges
    
    if (-not $isAdmin) {
        Write-Host "[ERROR] Administrator privileges required to manage the Docker service!" -ForegroundColor Red
        Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
        exit 1
    }
    
    # Check current service status
    $serviceTask = Get-ScheduledTask -TaskName "CaseStrainer-Docker-Service" -ErrorAction SilentlyContinue
    
    if ($serviceTask) {
        Write-Host "[INFO] CaseStrainer-Docker-Service is already installed" -ForegroundColor Green
        Write-Host "Status: $($serviceTask.State)" -ForegroundColor Gray
        Write-Host "Last Run: $($serviceTask.LastRunTime)" -ForegroundColor Gray
        Write-Host "Next Run: $($serviceTask.NextRunTime)" -ForegroundColor Gray
        
        # Ask if user wants to reinstall/update
        Write-Host "`nWould you like to reinstall/update the service?" -ForegroundColor Cyan
        $response = Read-Host "Enter 'y' to reinstall, any other key to keep current"
        
        if ($response -eq 'y') {
            Write-Host "`n[INFO] Reinstalling service..." -ForegroundColor Yellow
            & (Join-Path $PSScriptRoot "Create-DockerService.ps1")
        }
    } else {
        Write-Host "[INFO] CaseStrainer-Docker-Service is not installed" -ForegroundColor Yellow
        Write-Host "Installing service for unattended operation..." -ForegroundColor Gray
        
        # Run the service creation script
        $serviceScript = Join-Path $PSScriptRoot "Create-DockerService.ps1"
        if (Test-Path $serviceScript) {
            & $serviceScript
        } else {
            Write-Host "[ERROR] Service creation script not found: $serviceScript" -ForegroundColor Red
            Write-Host "Please ensure Create-DockerService.ps1 exists in the project root" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`n[INFO] Service management complete" -ForegroundColor Green
    exit 0
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
        Write-Host "[QUICK RESTART] Restarting containers (10-15 seconds)..." -ForegroundColor Yellow
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
    
    # Setup unattended monitoring (works without user login)
    Write-Host "[SETUP] Configuring unattended monitoring..." -ForegroundColor Yellow
    
    # Import the unattended monitoring module
    $modulePath = Join-Path $PSScriptRoot "scripts\modules\UnattendedMonitoring.psm1"
    if (Test-Path $modulePath) {
        Import-Module $modulePath -Force
        SetUnattendedMonitoring
    } else {
        # Fallback to old method if module not available
        Write-Host "[WARN] Unattended monitoring module not found, using legacy method..." -ForegroundColor Yellow
        $task = Get-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" -ErrorAction SilentlyContinue
        if (-not $task) {
            Write-Host "[SETUP] Configuring persistent monitoring..." -ForegroundColor Yellow
            & (Join-Path $PSScriptRoot "install_persistent_monitoring.ps1")
        } elseif ($task.State -ne "Running") {
            Write-Host "[MONITOR] Starting persistent monitoring..." -ForegroundColor Cyan
            Start-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor" | Out-Null
            Write-Host "[OK] Persistent monitoring started" -ForegroundColor Green
        } else {
            Write-Host "[OK] Persistent monitoring is active" -ForegroundColor Green
        }
    }
    Write-Host "  - Logs: logs\docker_daemon_monitor.log" -ForegroundColor Gray
} else {
    Write-Host "[DEBUG] Deployment failed (exit code: $deployExitCode), skipping startup notification" -ForegroundColor Yellow
}

exit $deployExitCode

# Emergency Recovery Function
function Invoke-DockerEmergencyRecovery {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='High')]
    param()
    Write-Host "`n========================================" -ForegroundColor Red
    Write-Host "Docker Emergency Recovery" -ForegroundColor Red
    Write-Host "========================================`n" -ForegroundColor Red
    
    Write-Host "[WARN] This will perform a deep cleanup of Docker..." -ForegroundColor Yellow
    Write-Host "  - Stop all Docker processes" -ForegroundColor Gray
    Write-Host "  - Clear temporary files" -ForegroundColor Gray
    Write-Host "  - Reset WSL (if applicable)" -ForegroundColor Gray
    Write-Host "  - Reset network adapters" -ForegroundColor Gray
    
    if ($PSCmdlet.ShouldProcess("Docker Desktop", "Perform emergency recovery")) {
        try {
            # Import the emergency recovery script
            $recoveryScript = Join-Path $PSScriptRoot "scripts\docker_emergency_recovery.ps1"
            if (Test-Path $recoveryScript) {
                & $recoveryScript -Force
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "[SUCCESS] Emergency recovery completed" -ForegroundColor Green
                    return $true
                } else {
                    Write-Host "[ERROR] Emergency recovery failed" -ForegroundColor Red
                    return $false
                }
            } else {
                Write-Host "[ERROR] Emergency recovery script not found" -ForegroundColor Red
                return $false
            }
        } catch {
            Write-Host "[ERROR] Emergency recovery failed: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    }
}

# Service Recovery Configuration Function
function Set-DockerServiceRecovery {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
    param(
        [switch]$Remove
    )
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    if ($Remove) {
        Write-Host "Removing Docker Service Recovery" -ForegroundColor Cyan
    } else {
        Write-Host "Configuring Docker Service Recovery" -ForegroundColor Cyan
    }
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    $serviceName = "com.docker.service"
    
    $action = if ($Remove) { "Remove" } else { "Configure" }
    if (-not $PSCmdlet.ShouldProcess("Docker service recovery", $action)) {
        Write-Host "Operation cancelled by user." -ForegroundColor Yellow
        return $false
    }
    
    if (-not (Test-AdminPrivileges)) {
        Write-Host "[ERROR] Administrator privileges required" -ForegroundColor Red
        return $false
    }
    
    try {
        if ($Remove) {
            # Reset service recovery
            sc.exe failure $serviceName reset= actions= "" 2>$null
            Write-Host "[SUCCESS] Service recovery actions removed" -ForegroundColor Green
        } else {
            # Configure service recovery actions
            $recoveryScript = Join-Path $PSScriptRoot "scripts\docker_emergency_recovery.ps1"
            sc.exe failure $serviceName reset= 86400 actions= restart/5000/run/15000/restart/30000 command= "`"$recoveryScript`" -Force" 2>$null
            Write-Host "[SUCCESS] Service recovery configured:" -ForegroundColor Green
            Write-Host "  - First failure: Restart after 5 seconds" -ForegroundColor Gray
            Write-Host "  - Second failure: Run recovery script after 15 seconds" -ForegroundColor Gray
            Write-Host "  - Subsequent failures: Restart after 30 seconds" -ForegroundColor Gray
            Write-Host "  - Reset period: 24 hours" -ForegroundColor Gray
        }
        
        # Set service startup type
        sc.exe config $serviceName start= auto 2>$null
        Write-Host "[SUCCESS] Service set to automatic start" -ForegroundColor Green
        
        return $true
    } catch {
        Write-Host "[ERROR] Failed to configure service recovery: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Handle emergency recovery request
if ($EmergencyRecovery) {
    $success = Invoke-DockerEmergencyRecovery
    exit $(if ($success) { 0 } else { 1 })
}

# Handle service recovery configuration
if ($ConfigureServiceRecovery) {
    $success = Set-DockerServiceRecovery
    exit $(if ($success) { 0 } else { 1 })
}

# Handle service recovery removal
if ($RemoveServiceRecovery) {
    $success = Set-DockerServiceRecovery -Remove
    exit $(if ($success) { 0 } else { 1 })
}

# Handle Docker cleanup request
if ($CleanupDocker) {
    $success = Invoke-DockerCleanup -Force
    exit $(if ($success) { 0 } else { 1 })
}

# Handle cleanup scheduler request
if ($ScheduleCleanup -or $RemoveCleanupSchedule) {
    $schedulerScript = Join-Path $PSScriptRoot "scripts\docker_cleanup_scheduler.ps1"
    if (Test-Path $schedulerScript) {
        $args = @()
        if ($RemoveCleanupSchedule) { $args += "-Remove" }
        
        & powershell -NoProfile -ExecutionPolicy Bypass -File $schedulerScript @args
        exit $LASTEXITCODE
    } else {
        Write-Host "[ERROR] Cleanup scheduler script not found: $schedulerScript" -ForegroundColor Red
        exit 1
    }
}

function Invoke-DockerCleanup {
    <#
    .SYNOPSIS
        Cleans up Docker resources to free disk space.
    #>
    param(
        [switch]$Force,
        [switch]$Auto
    )
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Docker Cleanup" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    try {
        # Check current disk usage
        $dockerInfo = docker system df --format "{{json .}}" | ConvertFrom-Json
        $totalSize = [math]::Round($dockerInfo.LayersSize / 1GB, 2)
        
        Write-Host "Current Docker disk usage: $totalSize GB" -ForegroundColor Yellow
        
        # Check system disk space
        $systemDrive = Get-CimInstance -ClassName Win32_LogicalDisk | Where-Object {$_.DeviceID -eq "C:"}
        $freeSpaceGB = [math]::Round($systemDrive.FreeSpace / 1GB, 2)
        
        Write-Host "Free disk space on C: drive: $freeSpaceGB GB" -ForegroundColor Yellow
        
        $shouldCleanup = $false
        
        if ($Auto) {
            # Automatic cleanup if less than 30GB free
            if ($freeSpaceGB -lt 30) {
                $shouldCleanup = $true
                Write-Host "[AUTO] Disk space below 30GB threshold - initiating cleanup..." -ForegroundColor Yellow
            }
        } elseif ($Force -or $freeSpaceGB -lt 20) {
            # Force cleanup or if less than 20GB free
            $shouldCleanup = $true
            if ($freeSpaceGB -lt 20) {
                Write-Host "[WARNING] Disk space critically low (< 20GB) - cleanup required!" -ForegroundColor Red
            }
        }
        
        if ($shouldCleanup) {
            Write-Host "`n[CLEANUP] Removing unused Docker resources..." -ForegroundColor Yellow
            
            # Prune containers
            Write-Host "  - Removing stopped containers..." -ForegroundColor Gray
            $containerCleanup = docker container prune -f
            if ($LASTEXITCODE -eq 0) {
                $containersRemoved = ($containerCleanup | Select-String "Total reclaimed space:").ToString().Split(":")[1].Trim()
                Write-Host "    Reclaimed: $containersRemoved" -ForegroundColor Green
            }
            
            # Prune images
            Write-Host "  - Removing unused images..." -ForegroundColor Gray
            $imageCleanup = docker image prune -f
            if ($LASTEXITCODE -eq 0) {
                $imagesReclaimed = ($imageCleanup | Select-String "Total reclaimed space:").ToString().Split(":")[1].Trim()
                Write-Host "    Reclaimed: $imagesReclaimed" -ForegroundColor Green
            }
            
            # Prune build cache
            Write-Host "  - Cleaning build cache..." -ForegroundColor Gray
            $buildCleanup = docker builder prune -f
            if ($LASTEXITCODE -eq 0) {
                $buildReclaimed = ($buildCleanup | Select-String "Total reclaimed space:").ToString().Split(":")[1].Trim()
                Write-Host "    Reclaimed: $buildReclaimed" -ForegroundColor Green
            }
            
            # Full system prune
            Write-Host "  - Running full system prune..." -ForegroundColor Gray
            $systemCleanup = docker system prune -f
            if ($LASTEXITCODE -eq 0) {
                $systemReclaimed = ($systemCleanup | Select-String "Total reclaimed space:").ToString().Split(":")[1].Trim()
                Write-Host "    Reclaimed: $systemReclaimed" -ForegroundColor Green
            }
            
            # Check final disk space
            $finalFreeSpace = [math]::Round((Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DeviceID -eq "C:"}).FreeSpace / 1GB, 2)
            $spaceFreed = [math]::Round($finalFreeSpace - $freeSpaceGB, 2)
            
            Write-Host "`n[SUCCESS] Cleanup completed!" -ForegroundColor Green
            Write-Host "  - Free space before: $freeSpaceGB GB" -ForegroundColor Gray
            Write-Host "  - Free space after: $finalFreeSpace GB" -ForegroundColor Gray
            Write-Host "  - Space freed: $spaceFreed GB" -ForegroundColor Green
            
            # Log the cleanup
            $logPath = Join-Path $PSScriptRoot "logs\docker_cleanup.log"
            if (!(Test-Path (Split-Path $logPath -Parent))) {
                New-Item -ItemType Directory -Path (Split-Path $logPath -Parent) -Force | Out-Null
            }
            
            $logEntry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Docker cleanup completed. Space freed: $spaceFreed GB`n"
            Add-Content -Path $logPath -Value $logEntry
            
        } else {
            Write-Host "[INFO] No cleanup needed. Disk space is sufficient." -ForegroundColor Green
        }
        
    } catch {
        Write-Host "[ERROR] Docker cleanup failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    return $true
}



