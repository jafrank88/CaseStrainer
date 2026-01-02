# Test Script for CaseStrainer Admin Notifications
# This script allows you to test notification functionality without triggering actual failures

param(
    [string]$TestType = "all",  # Options: "email", "slack", "teams", "all"
    [string]$Email = $(if ($env:CASESTRAINER_ADMIN_EMAIL) { $env:CASESTRAINER_ADMIN_EMAIL } else { "jafrank@uw.edu" }),
    [switch]$DryRun = $false  # If true, only shows what would be sent without actually sending
)

Write-Host "=== CaseStrainer Notification Test Script ===" -ForegroundColor Cyan
Write-Host ""

# Load cslaunch.ps1 functions
$cslaunchPath = Join-Path $PSScriptRoot ".." "cslaunch.ps1"
if (-not (Test-Path $cslaunchPath)) {
    Write-Host "ERROR: Could not find cslaunch.ps1 at $cslaunchPath" -ForegroundColor Red
    exit 1
}

# Set up required variables and functions
$script:LastNotificationTime = @{}
$crashLogPath = Join-Path $PSScriptRoot ".." "logs" "crash.log"
$dockerDaemonLogPath = Join-Path $PSScriptRoot ".." "logs" "docker_daemon.log"
$notificationLogPath = Join-Path $PSScriptRoot ".." "logs" "notifications.log"

# Ensure log directories exist
$logDir = Split-Path $crashLogPath -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Set up environment variables if not already set
if (-not $env:CASESTRAINER_ADMIN_EMAIL) {
    $env:CASESTRAINER_ADMIN_EMAIL = $Email
}

# Set up notification parameters (required by Send-AdminNotification)
$EnableNotifications = $true
$NotificationEmail = $env:CASESTRAINER_ADMIN_EMAIL
$SlackWebhook = $env:CASESTRAINER_SLACK_WEBHOOK
$TeamsWebhook = $env:CASESTRAINER_TEAMS_WEBHOOK
$NotificationCooldownMinutes = 60
$script:DryRun = $DryRun  # Make DryRun available to functions

# Simple logging function
function Write-DockerDaemonLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $dockerDaemonLogPath -Value $logEntry -ErrorAction SilentlyContinue
    Write-Host "[$Level] $Message"
}

# Load Send-AdminNotification function from cslaunch.ps1
# We'll use dot-sourcing but prevent execution by wrapping in a try-catch
# and checking for a test mode parameter
try {
    # Create a test mode flag that cslaunch.ps1 can check
    $env:CSLAUNCH_TEST_MODE = "true"
    
    # Dot-source cslaunch.ps1 - but we need to prevent it from executing
    # The script will define functions but we'll catch any execution errors
    $ErrorActionPreference = "SilentlyContinue"
    . $cslaunchPath -WhatIf 2>$null
    $ErrorActionPreference = "Continue"
    
    # Check if function is available
    if (Get-Command Send-AdminNotification -ErrorAction SilentlyContinue) {
        Write-Host "✓ Loaded Send-AdminNotification function from cslaunch.ps1" -ForegroundColor Green
    } else {
        throw "Function not found"
    }
} catch {
    Write-Host "WARNING: Could not load function from cslaunch.ps1, using embedded version" -ForegroundColor Yellow
    
    # Embedded version of Send-AdminNotification (simplified for testing)
    function Send-AdminNotification {
        param(
            [string]$Subject,
            [string]$Message,
            [string]$Severity = "ERROR",
            [string]$IssueType = "general"
        )
        
        if (-not $EnableNotifications) { return }
        
        # Check cooldown
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
        $script:LastNotificationTime[$IssueType] = $now
        
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
        
        # Send email
        if ($NotificationEmail -and -not $script:DryRun) {
            try {
                $smtpServer = if ($env:SMTP_SERVER) { $env:SMTP_SERVER } else { "localhost" }
                $smtpPort = if ($env:SMTP_PORT) { [int]$env:SMTP_PORT } else { 25 }
                $useSsl = ($env:SMTP_USE_TLS -eq "true" -or $env:SMTP_USE_SSL -eq "true")
                
                $emailParams = @{
                    To = $NotificationEmail
                    Subject = "[CaseStrainer] $Subject"
                    Body = $fullMessage
                    From = "CaseStrainer Monitor <noreply@casestrainer.local>"
                    SmtpServer = $smtpServer
                    Port = $smtpPort
                }
                
                if ($useSsl) { $emailParams['UseSsl'] = $true }
                if ($env:SMTP_USERNAME -and $env:SMTP_PASSWORD) {
                    $securePassword = ConvertTo-SecureString $env:SMTP_PASSWORD -AsPlainText -Force
                    $credential = New-Object System.Management.Automation.PSCredential($env:SMTP_USERNAME, $securePassword)
                    $emailParams['Credential'] = $credential
                }
                
                Send-MailMessage @emailParams -ErrorAction Stop
                Write-DockerDaemonLog "Email notification sent to $NotificationEmail" "INFO"
                Add-Content -Path $notificationLogPath -Value "[$timestamp] EMAIL SENT: $Subject to $NotificationEmail"
            } catch {
                Write-DockerDaemonLog "Failed to send email: $($_.Exception.Message)" "ERROR"
                Add-Content -Path $notificationLogPath -Value "[$timestamp] EMAIL FAILED: $($_.Exception.Message)"
            }
        }
        
        # Send Slack
        if ($SlackWebhook -and -not $script:DryRun) {
            try {
                $slackColor = switch ($Severity) {
                    "CRITICAL" { "danger" }
                    "ERROR" { "danger" }
                    "WARN" { "warning" }
                    default { "good" }
                }
                $slackPayload = @{
                    text = "*CaseStrainer Alert - $Severity*"
                    attachments = @(
                        @{
                            color = $slackColor
                            fields = @(
                                @{title = "Time"; value = $timestamp; short = $true},
                                @{title = "Issue Type"; value = $IssueType; short = $true},
                                @{title = "Message"; value = $Message; short = $false}
                            )
                            footer = "CaseStrainer Monitoring"
                            ts = [DateTimeOffset]::Now.ToUnixTimeSeconds()
                        }
                    )
                } | ConvertTo-Json -Depth 10
                Invoke-RestMethod -Uri $SlackWebhook -Method Post -Body $slackPayload -ContentType "application/json" -ErrorAction Stop
                Write-DockerDaemonLog "Slack notification sent" "INFO"
                Add-Content -Path $notificationLogPath -Value "[$timestamp] SLACK SENT: $Subject"
            } catch {
                Write-DockerDaemonLog "Failed to send Slack: $($_.Exception.Message)" "ERROR"
                Add-Content -Path $notificationLogPath -Value "[$timestamp] SLACK FAILED: $($_.Exception.Message)"
            }
        }
        
        # Send Teams
        if ($TeamsWebhook -and -not $script:DryRun) {
            try {
                $teamsThemeColor = switch ($Severity) {
                    "CRITICAL" { "FF0000" }
                    "ERROR" { "FF0000" }
                    "WARN" { "FFA500" }
                    default { "00FF00" }
                }
                $teamsMessage = if ($Message.Length -gt 2000) { $Message.Substring(0, 1997) + "..." } else { $Message }
                $teamsPayload = @{
                    "@type" = "MessageCard"
                    "@context" = "https://schema.org/extensions"
                    themeColor = $teamsThemeColor
                    summary = "[CaseStrainer] $Subject"
                    sections = @(
                        @{
                            activityTitle = "CaseStrainer Alert - $Severity"
                            activitySubtitle = $timestamp
                            facts = @(
                                @{name = "Issue Type"; value = $IssueType},
                                @{name = "Severity"; value = $Severity}
                            )
                            text = $teamsMessage
                        }
                    )
                } | ConvertTo-Json -Depth 10
                Invoke-RestMethod -Uri $TeamsWebhook -Method Post -Body $teamsPayload -ContentType "application/json" -ErrorAction Stop
                Write-DockerDaemonLog "Teams notification sent" "INFO"
                Add-Content -Path $notificationLogPath -Value "[$timestamp] TEAMS SENT: $Subject"
            } catch {
                Write-DockerDaemonLog "Failed to send Teams: $($_.Exception.Message)" "ERROR"
                Add-Content -Path $notificationLogPath -Value "[$timestamp] TEAMS FAILED: $($_.Exception.Message)"
            }
        }
    }
}

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Admin Email: $env:CASESTRAINER_ADMIN_EMAIL"
Write-Host "  SMTP Server: $($env:SMTP_SERVER ?? 'Not configured')"
Write-Host "  SMTP Port: $($env:SMTP_PORT ?? 'Not configured')"
Write-Host "  Slack Webhook: $(if ($env:CASESTRAINER_SLACK_WEBHOOK) { 'Configured' } else { 'Not configured' })"
Write-Host "  Teams Webhook: $(if ($env:CASESTRAINER_TEAMS_WEBHOOK) { 'Configured' } else { 'Not configured' })"
Write-Host "  Dry Run: $DryRun"
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN MODE: Notifications will NOT be sent" -ForegroundColor Yellow
    Write-Host ""
}

# Test function
function Test-Notification {
    param(
        [string]$Subject,
        [string]$Message,
        [string]$Severity = "WARN",
        [string]$IssueType = "test"
    )
    
    Write-Host "Testing $Severity notification..." -ForegroundColor Cyan
    Write-Host "  Subject: $Subject"
    Write-Host "  Issue Type: $IssueType"
    Write-Host ""
    
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would send notification:" -ForegroundColor Yellow
        Write-Host "    To: $env:CASESTRAINER_ADMIN_EMAIL"
        Write-Host "    Subject: [CaseStrainer] $Subject"
        Write-Host "    Severity: $Severity"
        Write-Host "    Message: $Message"
        Write-Host ""
        return
    }
    
    try {
        Send-AdminNotification `
            -Subject $Subject `
            -Message $Message `
            -Severity $Severity `
            -IssueType $IssueType
        
        Write-Host "  ✓ Notification sent successfully!" -ForegroundColor Green
        Write-Host ""
    } catch {
        Write-Host "  ✗ Failed to send notification: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}

# Run tests based on TestType
if ($TestType -eq "all" -or $TestType -eq "email") {
    Write-Host "=== Test 1: Email Notification (WARN) ===" -ForegroundColor Green
    Test-Notification `
        -Subject "Test Warning Notification" `
        -Message "This is a test warning notification from CaseStrainer. If you receive this, email notifications are working correctly." `
        -Severity "WARN" `
        -IssueType "test_warning"
    
    Start-Sleep -Seconds 2
}

if ($TestType -eq "all" -or $TestType -eq "email") {
    Write-Host "=== Test 2: Email Notification (ERROR) ===" -ForegroundColor Green
    Test-Notification `
        -Subject "Test Error Notification" `
        -Message "This is a test error notification from CaseStrainer. If you receive this, email notifications are working correctly." `
        -Severity "ERROR" `
        -IssueType "test_error"
    
    Start-Sleep -Seconds 2
}

if ($TestType -eq "all" -or $TestType -eq "email") {
    Write-Host "=== Test 3: Email Notification (CRITICAL) ===" -ForegroundColor Green
    Test-Notification `
        -Subject "Test Critical Notification" `
        -Message "This is a test critical notification from CaseStrainer. If you receive this, email notifications are working correctly.

This simulates a critical failure scenario that would require immediate attention." `
        -Severity "CRITICAL" `
        -IssueType "test_critical"
    
    Start-Sleep -Seconds 2
}

if ($TestType -eq "all" -or $TestType -eq "slack") {
    if ($env:CASESTRAINER_SLACK_WEBHOOK) {
        Write-Host "=== Test 4: Slack Notification ===" -ForegroundColor Green
        Test-Notification `
            -Subject "Test Slack Notification" `
            -Message "This is a test Slack notification from CaseStrainer. If you see this in Slack, Slack notifications are working correctly." `
            -Severity "WARN" `
            -IssueType "test_slack"
    } else {
        Write-Host "=== Test 4: Slack Notification (SKIPPED - No webhook configured) ===" -ForegroundColor Yellow
    }
    Write-Host ""
}

if ($TestType -eq "all" -or $TestType -eq "teams") {
    if ($env:CASESTRAINER_TEAMS_WEBHOOK) {
        Write-Host "=== Test 5: Teams Notification ===" -ForegroundColor Green
        Test-Notification `
            -Subject "Test Teams Notification" `
            -Message "This is a test Teams notification from CaseStrainer. If you see this in Teams, Teams notifications are working correctly." `
            -Severity "WARN" `
            -IssueType "test_teams"
    } else {
        Write-Host "=== Test 5: Teams Notification (SKIPPED - No webhook configured) ===" -ForegroundColor Yellow
    }
    Write-Host ""
}

Write-Host "=== Test 6: Cooldown Period Test ===" -ForegroundColor Green
Write-Host "Sending two notifications with same IssueType to test cooldown..."
Test-Notification `
    -Subject "Cooldown Test - First Notification" `
    -Message "This is the first notification. The second one should be suppressed by cooldown." `
    -Severity "WARN" `
    -IssueType "cooldown_test"

Write-Host "Waiting 2 seconds, then sending second notification (should be suppressed)..."
Start-Sleep -Seconds 2

Test-Notification `
    -Subject "Cooldown Test - Second Notification" `
    -Message "This notification should be suppressed due to cooldown period (default: 60 minutes)." `
    -Severity "WARN" `
    -IssueType "cooldown_test"

Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Check the following:" -ForegroundColor Yellow
Write-Host "  1. Email inbox at: $env:CASESTRAINER_ADMIN_EMAIL"
Write-Host "  2. Slack channel (if configured)"
Write-Host "  3. Teams channel (if configured)"
Write-Host "  4. Notification log: $notificationLogPath"
Write-Host ""
Write-Host "To view notification logs:" -ForegroundColor Yellow
Write-Host "  Get-Content '$notificationLogPath' -Tail 20"
Write-Host ""

