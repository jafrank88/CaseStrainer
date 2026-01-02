# Testing CaseStrainer Notifications - Quick Start

## Quick Test (Recommended)

Run the test script to verify all notification channels:

```powershell
# Test all notification types
.\scripts\test_notifications.ps1

# Test only email
.\scripts\test_notifications.ps1 -TestType email

# Dry run (see what would be sent without actually sending)
.\scripts\test_notifications.ps1 -DryRun
```

## Prerequisites

Before testing, ensure you have:

1. **Email configured** (for email tests):
   ```powershell
   $env:CASESTRAINER_ADMIN_EMAIL = "jafrank@uw.edu"  # Already set in config.env
   $env:SMTP_SERVER = "smtp.gmail.com"
   $env:SMTP_PORT = "587"
   $env:SMTP_USERNAME = "your-email@gmail.com"
   $env:SMTP_PASSWORD = "your-app-password"
   $env:SMTP_USE_TLS = "true"
   ```

2. **Slack webhook** (optional, for Slack tests):
   ```powershell
   $env:CASESTRAINER_SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   ```

3. **Teams webhook** (optional, for Teams tests):
   ```powershell
   $env:CASESTRAINER_TEAMS_WEBHOOK = "https://outlook.office.com/webhook/YOUR/WEBHOOK/URL"
   ```

## What Gets Tested

The test script sends:

1. **WARN notification** - Test warning level alert
2. **ERROR notification** - Test error level alert  
3. **CRITICAL notification** - Test critical level alert
4. **Slack notification** (if configured)
5. **Teams notification** (if configured)
6. **Cooldown test** - Verifies duplicate notifications are suppressed

## Verify Results

After running tests, check:

1. **Email inbox** at `jafrank@uw.edu` (or your configured email)
2. **Slack channel** (if configured)
3. **Teams channel** (if configured)
4. **Notification log**:
   ```powershell
   Get-Content logs\notifications.log -Tail 20
   ```

## Testing Real Scenarios

### Test Docker Daemon Monitoring

```powershell
# Start monitoring
.\cslaunch.ps1 -Monitor

# In another terminal (as admin), stop Docker service
Stop-Service docker

# Wait for notification (should trigger after health checks fail)
# Then restart Docker
Start-Service docker
```

### Test Container Failure

```powershell
# Start monitoring
.\cslaunch.ps1 -Monitor

# Stop container multiple times to trigger failure threshold
docker stop casestrainer-backend
docker start casestrainer-backend
docker stop casestrainer-backend
docker start casestrainer-backend
docker stop casestrainer-backend

# After 3 consecutive failures, notification should be sent
```

## Troubleshooting

### Email Not Sending?

1. Check SMTP configuration:
   ```powershell
   $env:SMTP_SERVER
   $env:SMTP_PORT
   $env:SMTP_USERNAME
   $env:SMTP_PASSWORD
   ```

2. For Gmail, use **App Password** (not regular password):
   - Enable 2-Factor Authentication
   - Generate App Password at https://myaccount.google.com/apppasswords

3. Check notification log:
   ```powershell
   Get-Content logs\notifications.log | Select-String "EMAIL"
   ```

### Slack/Teams Not Sending?

1. Verify webhook URL is correct
2. Test webhook manually:
   ```powershell
   $body = @{text="Test"} | ConvertTo-Json
   Invoke-RestMethod -Uri $env:CASESTRAINER_SLACK_WEBHOOK -Method Post -Body $body -ContentType "application/json"
   ```

## Full Documentation

For complete testing guide, see:
- `docs\TESTING_NOTIFICATIONS.md` - Comprehensive testing guide
- `docs\ADMIN_NOTIFICATIONS_SETUP.md` - Setup instructions
- `NOTIFICATIONS_QUICKSTART.md` - Quick reference










