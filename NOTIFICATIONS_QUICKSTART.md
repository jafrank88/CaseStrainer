# Admin Notifications - Quick Start

## Enable Notifications in 2 Minutes

### 1. Set Environment Variables

**For Gmail:**
```powershell
# Admin email defaults to jafrank@uw.edu (configured in config.env)
# Override if needed:
$env:CASESTRAINER_ADMIN_EMAIL = "your-email@gmail.com"  # Optional
$env:SMTP_SERVER = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "your-email@gmail.com"
$env:SMTP_PASSWORD = "your-16-char-app-password"  # Use App Password, not regular password
$env:SMTP_USE_TLS = "true"
```

**For Slack (optional):**
```powershell
$env:CASESTRAINER_SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**For Microsoft Teams (optional):**
```powershell
$env:CASESTRAINER_TEAMS_WEBHOOK = "https://outlook.office.com/webhook/YOUR/WEBHOOK/URL"
```

### 2. Get Gmail App Password

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to App passwords → Generate
4. Select "Mail" → Copy the 16-character password

### 3. Test It

```powershell
# Start monitoring - notifications will be sent automatically
.\cslaunch.ps1 -Monitor
```

## When You'll Get Notified

### Critical Alerts (Immediate)
- ✅ Docker daemon restart failed
- ✅ Container failed 3 restart attempts

### Warning Alerts (Rate-limited)
- ⚠️ Docker daemon restart rate limit reached

## Notification Channels

- **Email** - Configured via `CASESTRAINER_ADMIN_EMAIL`
- **Slack** - Configured via `CASESTRAINER_SLACK_WEBHOOK` (optional)
- **Microsoft Teams** - Configured via `CASESTRAINER_TEAMS_WEBHOOK` (optional)

## Quick Commands

```powershell
# Check if notifications are configured
$env:CASESTRAINER_ADMIN_EMAIL
$env:CASESTRAINER_SLACK_WEBHOOK
$env:CASESTRAINER_TEAMS_WEBHOOK

# View notification logs
Get-Content logs\notifications.log -Tail 20

# Disable notifications
.\cslaunch.ps1 -EnableNotifications:$false
```

## Full Documentation

See `docs\ADMIN_NOTIFICATIONS_SETUP.md` for complete setup guide.

