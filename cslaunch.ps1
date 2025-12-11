# cslaunch.ps1 - Quick restart wrapper for production environment
# This is optimized for fast Python code updates without rebuilding Docker images

param(
    [switch]$Build,
    [switch]$Force,
    [switch]$NoCache,
    [switch]$Monitor,     # Continuous monitoring mode with auto-restart (foreground)
    [switch]$NoMonitor,    # Disable automatic background monitoring (monitoring enabled by default)
    [switch]$ConfigureAutostart,  # Configure Docker autostart on boot
    [int]$MonitorInterval = 30,  # Health check interval in seconds (default: 30)
    [switch]$EnableDockerDaemonMonitor = $true,  # Enable Docker daemon monitoring (default: true)
    [int]$DockerDaemonTimeout = 15,  # Docker daemon freeze timeout in seconds (default: 15)
    [int]$MaxDockerRestartsPerHour = 3,  # Maximum Docker daemon restarts per hour (default: 3)
    [bool]$EnableNotifications = $false  # Notifications disabled - using external WHM monitoring
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

# Check and configure Docker autostart on boot (non-blocking, only if not configured)
try {
    if (-not (Test-DockerAutostartConfigured)) {
        # Try to install silently (will fail if not admin, which is OK)
        $autostartInstalled = Install-DockerAutostart -Silent
        if ($autostartInstalled) {
            Write-Host "[INFO] Docker autostart configured - containers will start on boot" -ForegroundColor Green
        }
    }
} catch {
    # Silently ignore - autostart is optional
}

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
                $securePassword = ConvertTo-SecureString $env:SMTP_PASSWORD -AsPlainText -Force
                $credential = New-Object System.Management.Automation.PSCredential($env:SMTP_USERNAME, $securePassword)
                $emailParams['Credential'] = $credential
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
        
        $autostartScript | Out-File -FilePath $autostartScript -Encoding UTF8 -Force
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
        
        # Create the principal
        $Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
            -LogonType Interactive `
            -RunLevel Highest
        
        # Create settings
        $Settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RestartCount 3 `
            -RestartInterval (New-TimeSpan -Minutes 5)
        
        # Register the task
        Register-ScheduledTask -TaskName $TaskName `
            -Action $Action `
            -Trigger $Trigger `
            -Principal $Principal `
            -Settings $Settings `
            -Description $TaskDescription | Out-Null
        
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
        
        # Step 2: Stop Docker service
        Write-DockerDaemonLog "Stopping Docker service..." "INFO"
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        if ($service) {
            Stop-Service -Name "com.docker.service" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        # Step 3: Kill any remaining Docker processes
        Write-DockerDaemonLog "Cleaning up remaining Docker processes..." "INFO"
        Get-Process | Where-Object { 
            $_.ProcessName -like "*docker*" -or 
            $_.ProcessName -like "*com.docker*" 
        } | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        
        # Step 4: Start Docker service
        Write-DockerDaemonLog "Starting Docker service..." "INFO"
        Start-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        
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
                        # Check restart rate limit
                        $now = Get-Date
                        $recentRestarts = $dockerRestartHistory | Where-Object { ($now - $_).TotalHours -lt 1 }
                        
                        if ($recentRestarts.Count -lt $MaxDockerRestartsPerHour) {
                            Write-DockerDaemonLog "Attempting Docker daemon restart (${dockerDaemonFailures} consecutive failures)" "WARN"
                            Write-Host "[$timestamp] ⚠️  Docker daemon appears frozen - attempting restart..." -ForegroundColor Yellow
                            
                            $restartSuccess = Restart-DockerDaemon -Reason "Health check failed ($dockerDaemonFailures consecutive failures)"
                            
                            if ($restartSuccess) {
                                $dockerRestartHistory += Get-Date
                                $dockerDaemonFailures = 0
                                
                                # Clean up old restart history (keep last 24 hours)
                                $dockerRestartHistory = $dockerRestartHistory | Where-Object { ($now - $_).TotalHours -lt 24 }
                                
                                Write-Host "[$timestamp] ✅ Docker daemon restarted successfully" -ForegroundColor Green
                                
                                # Wait a bit for Docker to stabilize before continuing
                                Start-Sleep -Seconds 10
                            } else {
                                Write-Host "[$timestamp] ❌ Docker daemon restart failed - manual intervention may be required" -ForegroundColor Red
                                Write-Host "  Check logs: $dockerDaemonLogPath" -ForegroundColor Yellow
                                
                                # Send critical notification
                                $notificationMessage = @"
Docker daemon restart FAILED after ${dockerDaemonFailures} consecutive health check failures.

Recovery attempts exhausted. Manual intervention required.

Details:
- Health checks failed: $dockerDaemonFailures times
- Restart attempted but failed
- Docker daemon is unresponsive

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
                            Write-DockerDaemonLog "Restart rate limit reached ($($recentRestarts.Count) restarts in last hour) - skipping restart" "WARN"
                            Write-Host "[$timestamp] ⚠️  Docker daemon frozen but restart rate limit reached" -ForegroundColor Red
                            Write-Host "  Recent restarts: $($recentRestarts.Count) in last hour" -ForegroundColor Yellow
                            
                            # Send warning notification about rate limit
                            $notificationMessage = @"
Docker daemon restart rate limit reached.

The Docker daemon has been restarted $($recentRestarts.Count) times in the last hour.
Automatic restart has been disabled to prevent restart loops.

Current Status:
- Docker daemon health checks failing
- Restart attempts: $($recentRestarts.Count) in last hour
- Rate limit: $MaxDockerRestartsPerHour per hour
- Manual intervention recommended

Action Required:
1. Investigate root cause of Docker daemon freezes
2. Check system resources (CPU, memory, disk)
3. Review Docker process CPU usage
4. Consider reducing container resource limits
5. Check for conflicting software (antivirus, VPN)

Logs: $dockerDaemonLogPath
"@
                            Send-AdminNotification `
                                -Subject "WARNING: Docker Daemon Restart Rate Limit Reached" `
                                -Message $notificationMessage `
                                -Severity "WARN" `
                                -IssueType "docker_daemon_rate_limit"
                        }
                    } else {
                        Write-Host "[$timestamp] ⚠️  Docker daemon health check failed ($dockerDaemonFailures/2)" -ForegroundColor Yellow
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
        return
    }
    
    Write-Host "[INFO] Starting background Docker daemon monitoring..." -ForegroundColor Cyan
    
    # Create a lightweight background monitoring script block
    $monitorScriptBlock = {
        param(
            $ScriptRoot,
            $MonitorInterval,
            $DockerDaemonTimeout,
            $MaxDockerRestartsPerHour
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
        
        Write-DaemonLog "=== BACKGROUND DOCKER DAEMON MONITOR STARTED ===" "SUCCESS"
        Write-DaemonLog "Check interval: ${MonitorInterval}s" "INFO"
        Write-DaemonLog "Freeze timeout: ${DockerDaemonTimeout}s" "INFO"
        
        $dockerDaemonFailures = 0
        $lastDockerCheck = $null
        $dockerRestartHistory = @()
        
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
                                $now = Get-Date
                                $recentRestarts = $dockerRestartHistory | Where-Object { ($now - $_).TotalHours -lt 1 }
                                
                                if ($recentRestarts.Count -lt $MaxDockerRestartsPerHour) {
                                    Write-DaemonLog "Docker daemon appears frozen - manual restart recommended" "WARN"
                                    Write-DaemonLog "Run: .\cslaunch.ps1 -Monitor for full monitoring with auto-restart" "INFO"
                                    
                                    # Send notification (background monitoring can't auto-restart)
                                    $notificationMessage = @"
Docker daemon health check failed ${dockerDaemonFailures} consecutive times.

Background monitoring detected Docker daemon issues but cannot auto-restart
(requires admin privileges and foreground monitoring mode).

Current Status:
- Health checks failed: $dockerDaemonFailures times
- Background monitoring active (limited capabilities)
- Manual intervention recommended

Action Required:
1. Run full monitoring: .\cslaunch.ps1 -Monitor
2. Or manually restart Docker Desktop
3. Check logs: $dockerDaemonLogPath

Note: Background monitoring provides alerts only. Use -Monitor flag for auto-restart.
"@
                                    
                                    # Use a simple notification function for background monitoring
                                    try {
                                        if ($env:CASESTRAINER_ADMIN_EMAIL) {
                                            $emailBody = "[CaseStrainer Background Monitor]`n`n$notificationMessage"
                                            Send-MailMessage `
                                                -To $env:CASESTRAINER_ADMIN_EMAIL `
                                                -Subject "[CaseStrainer] Docker Daemon Health Check Failed" `
                                                -Body $emailBody `
                                                -From "CaseStrainer Monitor <noreply@casestrainer.local>" `
                                                -SmtpServer (if ($env:SMTP_SERVER) { $env:SMTP_SERVER } else { "localhost" }) `
                                                -Port (if ($env:SMTP_PORT) { [int]$env:SMTP_PORT } else { 25 }) `
                                                -ErrorAction SilentlyContinue
                                        }
                                    } catch {
                                        # Silently fail in background monitoring
                                    }
                                    
                                    $dockerRestartHistory += Get-Date
                                    $dockerDaemonFailures = 0
                                } else {
                                    Write-DaemonLog "Restart rate limit reached - skipping alert" "WARN"
                                }
                            }
                    } else {
                        if ($dockerDaemonFailures -gt 0) {
                            Write-DaemonLog "Docker daemon recovered after $dockerDaemonFailures failures" "SUCCESS"
                            $dockerDaemonFailures = 0
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
        -ArgumentList $PSScriptRoot, $MonitorInterval, $DockerDaemonTimeout, $MaxDockerRestartsPerHour
    
    Write-Host "[OK] Background monitoring started (job ID: $($job.Id))" -ForegroundColor Green
    Write-Host "  View logs: Get-Content logs\docker_daemon_monitor.log -Tail 50 -Wait" -ForegroundColor Gray
    Write-Host "  Stop monitoring: Stop-Job -Name CaseStrainer-Monitor; Remove-Job -Name CaseStrainer-Monitor" -ForegroundColor Gray
    
    # Notifications disabled - using external WHM monitoring
    Write-Host "  Monitoring: Docker daemon monitoring enabled (external WHM handles alerts)" -ForegroundColor Cyan
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
                
                # Quick rebuild with cache for backend+workers
                $sw2 = [System.Diagnostics.Stopwatch]::StartNew()
                docker-compose -f docker-compose.prod.yml up -d --build backend rqworker1 rqworker2 rqworker3
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
        
        # SMART DETECTION: Check if source files are newer than Docker images
        Write-Host '[DETECT] Checking if Python source files changed...' -ForegroundColor Yellow
        $needsNoCacheRebuild = $false
        
        try {
            # Get newest Python file in src/
            $srcFiles = Get-ChildItem -Path "src" -Recurse -Filter "*.py" -File -ErrorAction SilentlyContinue
            if ($srcFiles) {
                $newestSrcFile = ($srcFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1)
                $newestSrcTime = $newestSrcFile.LastWriteTime
                
                # Get Docker image creation time for backend
                # USER FIX: Check actual Docker Compose image name (casestrainer_backend or casestrainer-backend)
                $imageCreated = $null
                $imageName = $null
                
                # Try common Docker Compose image naming patterns
                $possibleImageNames = @(
                    "casestrainer_backend",
                    "casestrainer-backend", 
                    "casestrainer_backend:latest",
                    "casestrainer-backend:latest"
                )
                
                foreach ($name in $possibleImageNames) {
                    $testCreated = docker inspect $name --format='{{.Created}}' 2>$null
                    if ($testCreated) {
                        $imageCreated = $testCreated
                        $imageName = $name
                        break
                    }
                }
                
                if ($imageCreated) {
                    $imageTime = [DateTime]::Parse($imageCreated)
                    
                    if ($newestSrcTime -gt $imageTime) {
                        $timeDiff = ($newestSrcTime - $imageTime).TotalMinutes
                        Write-Host "  [!] Source files changed $([math]::Round($timeDiff, 1)) minutes after last build" -ForegroundColor Yellow
                        Write-Host "  [*] Newest: $($newestSrcFile.Name) (modified: $($newestSrcTime.ToString('HH:mm:ss')))" -ForegroundColor Gray
                        Write-Host "  [*] Image: $imageName built at $($imageTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
                        Write-Host "  [WARN] FORCING --no-cache rebuild to ensure fresh code" -ForegroundColor Red
                        $needsNoCacheRebuild = $true
                    } else {
                        Write-Host "  [OK] Source files unchanged since last build ($imageName) - using cached layers" -ForegroundColor Green
                    }
                } else {
                    Write-Host "  [WARN] Could not find backend image - forcing --no-cache rebuild for safety" -ForegroundColor Yellow
                    Write-Host "  [*] Tried: $($possibleImageNames -join ', ')" -ForegroundColor Gray
                    $needsNoCacheRebuild = $true
                }
            }
        } catch {
            Write-Host "  [WARN] Detection failed: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "  [WARN] Forcing --no-cache rebuild for safety" -ForegroundColor Yellow
            $needsNoCacheRebuild = $true
        }
        Write-Host ""
        
        # REBUILD backend AND workers with smart caching
        if ($needsNoCacheRebuild) {
            Write-Host '[FULL REBUILD] Building backend + workers with --no-cache (6-7 minutes)...' -ForegroundColor Red
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            docker-compose -f docker-compose.prod.yml build --no-cache backend rqworker1 rqworker2 rqworker3
            docker-compose -f docker-compose.prod.yml up -d backend rqworker1 rqworker2 rqworker3
            $sw.Stop()
        } else {
            Write-Host '[QUICK REBUILD] Rebuilding backend + workers with cache (10-15 seconds)...' -ForegroundColor Yellow
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            docker-compose -f docker-compose.prod.yml up -d --build backend rqworker1 rqworker2 rqworker3
            $sw.Stop()
        }
        
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
    
    Start-BackgroundMonitoring
} else {
    Write-Host "[DEBUG] Deployment failed (exit code: $deployExitCode), skipping startup notification" -ForegroundColor Yellow
}

exit $deployExitCode
