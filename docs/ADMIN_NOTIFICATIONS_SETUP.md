# Admin Notifications Setup Guide

## Overview

CaseStrainer can now send admin notifications when Docker daemon or containers fail and cannot be automatically restarted. This ensures you're immediately alerted to critical issues requiring manual intervention.

## Notification Triggers

### Critical Alerts (CRITICAL severity)

1. **Docker Daemon Restart Failed**
   - Triggered when: Docker daemon restart attempt fails
   - After: 2+ consecutive health check failures
   - Action: Immediate notification

2. **Container Unrecoverable**
   - Triggered when: Container fails 3 consecutive restart attempts
   - Action: Immediate notification, monitoring stops

### Warning Alerts (WARN severity)

1. **Docker Daemon Rate Limit Reached**
   - Triggered when: Docker daemon restart rate limit exceeded
   - After: Max restarts per hour reached
   - Action: Notification with investigation recommendations

## Configuration

### Environment Variables

Set these environment variables to enable notifications:

```powershell
# Email Configuration
# Note: Default admin email is jafrank@uw.edu (configured in config.env)
# Override via environment variable if needed:
$env:CASESTRAINER_ADMIN_EMAIL = "admin@example.com"  # Optional - defaults to jafrank@uw.edu
$env:SMTP_SERVER = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "your-email@gmail.com"
$env:SMTP_PASSWORD = "your-app-password"
$env:SMTP_USE_TLS = "true"

# Slack Configuration (optional)
$env:CASESTRAINER_SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Microsoft Teams Configuration (optional)
$env:CASESTRAINER_TEAMS_WEBHOOK = "https://outlook.office.com/webhook/YOUR/WEBHOOK/URL"
```

### Command-Line Parameters

```powershell
# Enable/disable notifications (default: enabled)
.\cslaunch.ps1 -EnableNotifications:$false

# Set admin email
.\cslaunch.ps1 -NotificationEmail "admin@example.com"

# Set Slack webhook
.\cslaunch.ps1 -SlackWebhook "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Set Teams webhook
.\cslaunch.ps1 -TeamsWebhook "https://outlook.office.com/webhook/YOUR/WEBHOOK/URL"

# Adjust notification cooldown (default: 60 minutes)
.\cslaunch.ps1 -NotificationCooldownMinutes 30
```

### Persistent Configuration

Create a `.env` file or set environment variables in your system:

**Windows (PowerShell):**
```powershell
# Set for current session
$env:CASESTRAINER_ADMIN_EMAIL = "admin@example.com"
$env:SMTP_SERVER = "smtp.gmail.com"
$env:SMTP_PORT = "587"

# Set permanently (requires admin)
[System.Environment]::SetEnvironmentVariable("CASESTRAINER_ADMIN_EMAIL", "admin@example.com", "Machine")
```

**Windows (System Properties):**
1. Right-click "This PC" → Properties
2. Advanced system settings → Environment Variables
3. Add new system variables

## Email Setup

### Gmail Setup

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password:**
   - Go to Google Account → Security
   - 2-Step Verification → App passwords
   - Generate password for "Mail"
3. **Configure:**
   ```powershell
   $env:CASESTRAINER_ADMIN_EMAIL = "your-email@gmail.com"
   $env:SMTP_SERVER = "smtp.gmail.com"
   $env:SMTP_PORT = "587"
   $env:SMTP_USERNAME = "your-email@gmail.com"
   $env:SMTP_PASSWORD = "your-16-char-app-password"
   $env:SMTP_USE_TLS = "true"
   ```

### Office 365 / Outlook Setup

```powershell
$env:CASESTRAINER_ADMIN_EMAIL = "admin@yourdomain.com"
$env:SMTP_SERVER = "smtp.office365.com"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "admin@yourdomain.com"
$env:SMTP_PASSWORD = "your-password"
$env:SMTP_USE_TLS = "true"
```

### SendGrid Setup

```powershell
$env:CASESTRAINER_ADMIN_EMAIL = "admin@example.com"
$env:SMTP_SERVER = "smtp.sendgrid.net"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "apikey"
$env:SMTP_PASSWORD = "your-sendgrid-api-key"
$env:SMTP_USE_TLS = "true"
```

## Slack Setup

1. **Create Slack Webhook:**
   - Go to https://api.slack.com/apps
   - Create new app or select existing
   - Incoming Webhooks → Activate
   - Add New Webhook to Workspace
   - Copy webhook URL

2. **Configure:**
   ```powershell
   $env:CASESTRAINER_SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   ```

3. **Test:**
   ```powershell
   # Test notification
   .\cslaunch.ps1 -Monitor
   # Then trigger a failure to test
   ```

## Microsoft Teams Setup

1. **Create Teams Incoming Webhook:**
   - Open Microsoft Teams
   - Go to the channel where you want notifications
   - Click the three dots (⋯) next to the channel name
   - Select "Connectors"
   - Search for "Incoming Webhook"
   - Click "Configure"
   - Give it a name (e.g., "CaseStrainer Alerts")
   - Optionally upload an image
   - Click "Create"
   - Copy the webhook URL (starts with `https://outlook.office.com/webhook/`)

2. **Configure:**
   ```powershell
   $env:CASESTRAINER_TEAMS_WEBHOOK = "https://outlook.office.com/webhook/YOUR/WEBHOOK/URL"
   ```

3. **Test:**
   ```powershell
   # Test notification
   .\cslaunch.ps1 -Monitor
   # Then trigger a failure to test
   ```

**Note:** Teams webhooks use MessageCard format with color-coded severity:
- 🔴 Red: CRITICAL/ERROR
- 🟠 Orange: WARN
- 🟢 Green: INFO

## Notification Cooldown

To prevent notification spam, notifications for the same issue type are rate-limited:

- **Default:** 60 minutes between notifications for same issue
- **Configurable:** `-NotificationCooldownMinutes` parameter
- **Per Issue Type:** Each issue type (docker_daemon_unrecoverable, container_X_unrecoverable, etc.) tracked separately

**Example:**
```powershell
# Reduce cooldown to 30 minutes
.\cslaunch.ps1 -NotificationCooldownMinutes 30

# Disable cooldown (not recommended)
.\cslaunch.ps1 -NotificationCooldownMinutes 0
```

## Notification Logs

All notifications are logged to:
```
logs\notifications.log
```

**Log Format:**
```
[2025-12-08 18:54:47] EMAIL SENT: CRITICAL: Docker Daemon Unrecoverable to admin@example.com
[2025-12-08 18:54:48] SLACK SENT: CRITICAL: Docker Daemon Unrecoverable
[2025-12-08 18:54:49] TEAMS SENT: CRITICAL: Docker Daemon Unrecoverable
[2025-12-08 19:00:00] EMAIL FAILED: Connection timeout
```

## Testing Notifications

### Test Email Notification

```powershell
# Set test email
$env:CASESTRAINER_ADMIN_EMAIL = "your-email@example.com"
$env:SMTP_SERVER = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "your-email@gmail.com"
$env:SMTP_PASSWORD = "your-app-password"
$env:SMTP_USE_TLS = "true"

# Start monitoring and trigger a failure
.\cslaunch.ps1 -Monitor
```

### Test Slack Notification

```powershell
# Set Slack webhook
$env:CASESTRAINER_SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Start monitoring
.\cslaunch.ps1 -Monitor
```

### Test Teams Notification

```powershell
# Set Teams webhook
$env:CASESTRAINER_TEAMS_WEBHOOK = "https://outlook.office.com/webhook/YOUR/WEBHOOK/URL"

# Start monitoring
.\cslaunch.ps1 -Monitor
```

### Manual Test

You can manually trigger a test notification by creating a test script:

```powershell
# test_notification.ps1
$env:CASESTRAINER_ADMIN_EMAIL = "admin@example.com"
$env:SMTP_SERVER = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "your-email@gmail.com"
$env:SMTP_PASSWORD = "your-app-password"
$env:SMTP_USE_TLS = "true"

. .\cslaunch.ps1

Send-AdminNotification `
    -Subject "Test Notification" `
    -Message "This is a test notification from CaseStrainer monitoring system." `
    -Severity "WARN" `
    -IssueType "test"
```

## Notification Examples

### Email Notification Example

**Subject:** `[CaseStrainer] CRITICAL: Docker Daemon Unrecoverable`

**Body:**
```
CaseStrainer Alert - CRITICAL

Time: 2025-12-08 18:54:47
Issue Type: docker_daemon_unrecoverable

Docker daemon restart FAILED after 2 consecutive health check failures.

Recovery attempts exhausted. Manual intervention required.

Details:
- Health checks failed: 2 times
- Restart attempted but failed
- Docker daemon is unresponsive

Action Required:
1. Check Docker Desktop status
2. Review logs: logs\docker_daemon_monitor.log
3. Manually restart Docker Desktop
4. Verify containers are running: docker ps

Recent restart history: 3 restarts in last 24 hours

---
This is an automated alert from CaseStrainer monitoring system.
Logs: logs\crash_log.txt
Docker Daemon Logs: logs\docker_daemon_monitor.log
```

### Slack Notification Example

**Message:**
```
CaseStrainer Alert - CRITICAL

Time: 2025-12-08 18:54:47
Issue Type: docker_daemon_unrecoverable
Message: Docker daemon restart FAILED after 2 consecutive health check failures...
```

### Teams Notification Example

**Card Format:** MessageCard with color-coded severity

**Appearance:**
- 🔴 **Red card** for CRITICAL/ERROR
- 🟠 **Orange card** for WARN
- 🟢 **Green card** for INFO

**Card Content:**
- Title: "CaseStrainer Alert - CRITICAL"
- Severity, Issue Type, Time displayed as facts
- Full message in text section
- Action button to view logs

**Visual:** Teams displays as a rich card with color coding and structured information

## Troubleshooting

### Notifications Not Sending

1. **Check environment variables:**
   ```powershell
   $env:CASESTRAINER_ADMIN_EMAIL
   $env:SMTP_SERVER
   $env:CASESTRAINER_SLACK_WEBHOOK
   ```

2. **Check notification logs:**
   ```powershell
   Get-Content logs\notifications.log -Tail 20
   ```

3. **Check cooldown:**
   - Notifications are rate-limited
   - Wait for cooldown period or reduce `NotificationCooldownMinutes`

4. **Test SMTP connection:**
   ```powershell
   Test-NetConnection -ComputerName smtp.gmail.com -Port 587
   ```

### Email Authentication Issues

- **Gmail:** Use App Password, not regular password
- **Office 365:** May require modern authentication
- **Check firewall:** Port 587/465 may be blocked

### Slack Webhook Issues

- **Verify webhook URL:** Must start with `https://hooks.slack.com/services/`
- **Check app permissions:** Incoming Webhooks must be enabled
- **Test webhook:** Use curl or Postman to test directly

### Teams Webhook Issues

- **Verify webhook URL:** Must start with `https://outlook.office.com/webhook/`
- **Check connector:** Ensure Incoming Webhook connector is configured in Teams channel
- **Test webhook:** Use curl or Postman to test directly
- **Message format:** Teams uses MessageCard format (automatically handled)

## Best Practices

1. **Use App Passwords:** Never use your main account password
2. **Separate Email:** Use dedicated email for monitoring alerts
3. **Slack Channel:** Create dedicated #casestrainer-alerts channel
4. **Test Regularly:** Test notifications monthly
5. **Monitor Logs:** Check `logs\notifications.log` regularly
6. **Cooldown Settings:** Adjust based on your needs (30-120 minutes recommended)

## Disabling Notifications

```powershell
# Disable all notifications
.\cslaunch.ps1 -EnableNotifications:$false

# Or via environment variable
$env:CASESTRAINER_DISABLE_NOTIFICATIONS = "true"
```

## Security Considerations

1. **Credentials:** Store SMTP passwords securely (use Windows Credential Manager or environment variables)
2. **Webhook URLs:** Keep Slack webhook URLs secret
3. **Email Security:** Use TLS/SSL for SMTP connections
4. **Access Control:** Limit who receives notifications

