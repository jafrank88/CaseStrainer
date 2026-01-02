# CaseStrainer Automatic Monitoring

## Overview

CaseStrainer now includes **automatic monitoring** that works out of the box. No flags or configuration needed - just run `cslaunch` and monitoring is automatically set up.

## What It Does

- **Monitors Docker daemon** every 60 seconds
- **Auto-restarts Docker** if it crashes
- **Survives system reboots** (with admin privileges)
- **Logs all activities** for troubleshooting

## How to Use

### Option 1: PowerShell (Recommended)

```powershell
.\cslaunch.ps1
```

### Option 2: Batch File (Easiest)

Double-click `START_CASESTRAINER.bat` or run:

```cmd
START_CASESTRAINER.bat
```

## What Happens Automatically

### When You Run cslaunch

1. **Sets up monitoring** - Creates scheduled tasks for monitoring
2. **Starts Docker** - Launches Docker Desktop if needed
3. **Starts containers** - Brings up all CaseStrainer services
4. **Enables monitoring** - Background monitoring begins

### Monitoring Tasks Created

- **CaseStrainer-DockerStartup** (System level - runs at boot)
  - Requires admin privileges
  - Starts Docker and monitoring without login
- **CaseStrainer-PersistentMonitor** (User level - backup)
  - Runs when user logs in
  - Always works as backup

## Log Files

- `logs\docker_daemon_monitor.log` - Docker health checks
- `logs\docker_events.log` - All Docker events
- `logs\autostart.log` - Startup activities

## Admin vs Non-Admin

### With Admin Privileges

✅ Full unattended operation  
✅ Runs at system startup  
✅ No login required  

### Without Admin

✅ Monitoring works when you log in  
⚠ Requires user login to start  

## Troubleshooting

### Check Monitoring Status

```powershell
Get-ScheduledTask | Where-Object {$_.TaskName -like "*CaseStrainer*"}
```

### View Logs

```powershell
Get-Content "logs\docker_daemon_monitor.log" -Tail 20
```

### Manually Start Monitoring

```powershell
Start-ScheduledTask -TaskName "CaseStrainer-PersistentMonitor"
```

## Technical Details

The monitoring system:

1. Checks Docker daemon health every 60 seconds
2. Attempts to restart Docker if unhealthy
3. Uses exponential backoff for restart attempts
4. Bypasses rate limits after extended downtime
5. Logs all activities for audit trail

## Recovery from Crashes

When Docker crashes:

1. Monitoring detects failure within 60 seconds
2. Attempts graceful restart
3. If restart fails, waits and retries
4. Logs all attempts for troubleshooting
5. Eventually recovers automatically

No manual intervention needed!
