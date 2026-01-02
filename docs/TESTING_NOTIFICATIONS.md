# Testing CaseStrainer Notifications

This guide explains how to test the admin notification system to ensure it's working correctly.

## Quick Test

The easiest way to test notifications is using the provided test script:

```powershell
# Test all notification types
.\scripts\test_notifications.ps1

# Test only email
.\scripts\test_notifications.ps1 -TestType email

# Test only Slack
.\scripts\test_notifications.ps1 -TestType slack

# Dry run (shows what would be sent without actually sending)
.\scripts\test_notifications.ps1 -DryRun
```

## Manual Testing Methods

### Method 1: Test Email Notification Directly

Create a simple PowerShell script to test email:

```powershell
# test_email.ps1
$env:CASESTRAINER_ADMIN_EMAIL = "jafrank@uw.edu"
$env:SMTP_SERVER = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "your-email@gmail.com"
$env:SMTP_PASSWORD = "your-app-password"
$env:SMTP_USE_TLS = "true"

# Load cslaunch.ps1 functions
. .\cslaunch.ps1

# Initialize required variables
$script:LastNotificationTime = @{}
$crashLogPath = "logs\crash.log"
$dockerDaemonLogPath = "logs\docker_daemon.log"
$notificationLogPath = "logs\notifications.log"

# Send test notification
Send-AdminNotification `
    -Subject "Test Email Notification" `
    -Message "This is a test notification from CaseStrainer. If you receive this, email notifications are working correctly." `
    -Severity "WARN" `
    -IssueType "test"
```

### Method 2: Test via Docker Daemon Monitoring

Test by simulating a Docker daemon freeze:

```powershell
# 1. Start monitoring
.\cslaunch.ps1 -Monitor

# 2. In another terminal, stop Docker service (requires admin)
Stop-Service docker

# 3. Wait for monitoring to detect the issue and send notification
# (This will trigger after Docker daemon health checks fail)

# 4. Restart Docker service
Start-Service docker
```

**Note:** This requires administrator privileges and will temporarily stop Docker.

### Method 3: Test via Container Failure

Test by stopping a container multiple times:

```powershell
# 1. Start monitoring
.\cslaunch.ps1 -Monitor

# 2. Stop a container multiple times to trigger failure threshold
docker stop casestrainer-backend
docker start casestrainer-backend
docker stop casestrainer-backend
docker start casestrainer-backend
docker stop casestrainer-backend

# 3. After 3 consecutive failures, notification should be sent
```

### Method 4: Test Cooldown Period

Test that notifications respect the cooldown period:

```powershell
# Set short cooldown for testing (1 minute)
.\cslaunch.ps1 -NotificationCooldownMinutes 1 -Monitor

# Trigger a notification
# Then trigger another notification with the same IssueType within 1 minute
# The second notification should be suppressed
```

## Testing Different Notification Types

### Email Testing

**Prerequisites:**
- SMTP server configured (Gmail, Office 365, SendGrid, etc.)
- Admin email set: `$env:CASESTRAINER_ADMIN_EMAIL = "jafrank@uw.edu"`

**Test:**
```powershell
.\scripts\test_notifications.ps1 -TestType email
```

**Expected Result:**
- Email received at `jafrank@uw.edu`
- Subject: `[CaseStrainer] Test Warning Notification`
- Body contains test message and system information

### Slack Testing

**Prerequisites:**
- Slack webhook URL configured: `$env:CASESTRAINER_SLACK_WEBHOOK = "https://hooks.slack.com/services/..."`

**Test:**
```powershell
.\scripts\test_notifications.ps1 -TestType slack
```

**Expected Result:**
- Message appears in configured Slack channel
- Message includes severity, timestamp, and details

### Teams Testing

**Prerequisites:**
- Teams webhook URL configured: `$env:CASESTRAINER_TEAMS_WEBHOOK = "https://outlook.office.com/webhook/..."`

**Test:**
```powershell
.\scripts\test_notifications.ps1 -TestType teams
```

**Expected Result:**
- Message appears in configured Teams channel
- Message formatted as Teams card with details

## Verification Checklist

After running tests, verify:

- [ ] **Email received** at configured admin email address
- [ ] **Email subject** includes `[CaseStrainer]` prefix
- [ ] **Email body** contains:
  - Severity level (WARN/ERROR/CRITICAL)
  - Timestamp
  - Issue type
  - Detailed message
  - Log file paths
- [ ] **Slack message** appears (if configured)
- [ ] **Teams message** appears (if configured)
- [ ] **Notification log** contains entries:
  ```powershell
  Get-Content logs\notifications.log -Tail 20
  ```
- [ ] **Cooldown works** - second notification with same IssueType is suppressed

## Testing Notification Scenarios

### Scenario 1: Docker Daemon Freeze

**Steps:**
1. Start monitoring: `.\cslaunch.ps1 -Monitor`
2. Simulate freeze by stopping Docker service
3. Wait for health checks to fail (default: 2 failures)
4. Notification should be sent

**Expected:**
- CRITICAL severity notification
- IssueType: "docker_daemon_freeze"
- Message includes Docker daemon status

### Scenario 2: Container Restart Loop

**Steps:**
1. Start monitoring: `.\cslaunch.ps1 -Monitor`
2. Stop container 3 times consecutively
3. Notification should be sent after 3rd failure

**Expected:**
- CRITICAL severity notification
- IssueType: "container_unrecoverable"
- Message includes container name and restart count

### Scenario 3: Rate Limit Reached

**Steps:**
1. Start monitoring with low rate limit: `.\cslaunch.ps1 -MaxDockerRestartsPerHour 2 -Monitor`
2. Trigger Docker daemon restarts multiple times
3. Notification should be sent when limit reached

**Expected:**
- WARN severity notification
- IssueType: "docker_daemon_rate_limit"
- Message includes restart count and recommendations

## Troubleshooting

### Email Not Sending

**Check:**
1. SMTP server configuration:
   ```powershell
   $env:SMTP_SERVER
   $env:SMTP_PORT
   $env:SMTP_USERNAME
   $env:SMTP_PASSWORD
   $env:SMTP_USE_TLS
   ```

2. Gmail App Password (if using Gmail):
   - Must use App Password, not regular password
   - 2-Factor Authentication must be enabled

3. Firewall/Network:
   - SMTP port (587 for TLS) must be open
   - Corporate firewall may block SMTP

4. Notification log:
   ```powershell
   Get-Content logs\notifications.log -Tail 20
   ```

### Slack/Teams Not Sending

**Check:**
1. Webhook URL is correct:
   ```powershell
   $env:CASESTRAINER_SLACK_WEBHOOK
   $env:CASESTRAINER_TEAMS_WEBHOOK
   ```

2. Webhook is active (test manually):
   ```powershell
   $body = @{text="Test"} | ConvertTo-Json
   Invoke-RestMethod -Uri $env:CASESTRAINER_SLACK_WEBHOOK -Method Post -Body $body -ContentType "application/json"
   ```

3. Notification log for errors:
   ```powershell
   Get-Content logs\notifications.log | Select-String "SLACK\|TEAMS"
   ```

### Notifications Not Triggering

**Check:**
1. Monitoring is enabled:
   ```powershell
   # Should show monitoring is active
   Get-Process | Where-Object {$_.ProcessName -like "*powershell*"}
   ```

2. Docker daemon monitoring is active:
   ```powershell
   Get-Content logs\docker_daemon.log -Tail 20
   ```

3. Health checks are running:
   - Check logs for "Docker daemon health check" entries
   - Should see checks every 30 seconds (default)

### Cooldown Not Working

**Check:**
1. Cooldown period setting:
   ```powershell
   # Default is 60 minutes
   # Check if overridden: -NotificationCooldownMinutes
   ```

2. IssueType must be the same:
   - Different IssueTypes bypass cooldown
   - Same IssueType respects cooldown

3. Time since last notification:
   ```powershell
   # Check notification log timestamps
   Get-Content logs\notifications.log | Select-String "test"
   ```

## Test Script Options

The test script (`scripts\test_notifications.ps1`) supports:

- `-TestType`: `"email"`, `"slack"`, `"teams"`, or `"all"` (default)
- `-Email`: Override admin email (default: from env or `jafrank@uw.edu`)
- `-DryRun`: Show what would be sent without actually sending

**Examples:**
```powershell
# Test everything
.\scripts\test_notifications.ps1

# Test only email with custom address
.\scripts\test_notifications.ps1 -TestType email -Email "test@example.com"

# Dry run to see what would be sent
.\scripts\test_notifications.ps1 -DryRun
```

## Best Practices

1. **Test in development first** before deploying to production
2. **Use dry run** to verify configuration without sending actual notifications
3. **Test each channel separately** to isolate issues
4. **Verify cooldown** to prevent notification spam
5. **Check logs** after each test to verify behavior
6. **Test with actual failure scenarios** to ensure real-world reliability

## Next Steps

After successful testing:

1. Configure production SMTP settings
2. Set up Slack/Teams webhooks for production
3. Enable monitoring: `.\cslaunch.ps1 -Monitor`
4. Monitor notification logs: `Get-Content logs\notifications.log -Tail 20 -Wait`

For more information, see:
- `docs\ADMIN_NOTIFICATIONS_SETUP.md` - Complete setup guide
- `NOTIFICATIONS_QUICKSTART.md` - Quick reference










