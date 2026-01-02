# Persistent Logging System

## Overview

CaseStrainer now includes a persistent logging system that **survives container restarts**. This allows you to diagnose what happened before the system stopped, even after a crash or forced restart.

## What Gets Logged

### 1. **Event Log** (`casestrainer-backend_events.log`)
Never rotates - keeps all startup/shutdown events forever:
- 🚀 Application startups (with system info, memory status)
- 🛑 Normal shutdowns (with uptime)
- ⚠️ Signal-based shutdowns (SIGTERM, SIGINT)
- 💥 Application crashes

### 2. **Crash Log** (`casestrainer-backend_crashes.log`)
Never rotates - keeps all crash diagnostics:
- Full exception tracebacks
- Exception type and message
- Session information
- Timestamp of crash

### 3. **Main Application Log** (`casestrainer-backend.log`)
Rotates (keeps last 10 files of 5MB each):
- General application logging
- Request/response logging
- Health check results
- Memory warnings

### 4. **Session Files** (`session_YYYYMMDD_HHMMSS.json`)
One per application startup:
- Session ID
- Start timestamp
- System information (Python version, platform, memory)
- Environment variables (sanitized)
- Shutdown/crash information (added on exit)

## Log Location

All logs are stored in: **`d:\dev\casestrainer\logs\`**

This directory is mounted as a volume in Docker, so logs persist even when containers are recreated.

## Analyzing Logs

### Quick Analysis Script

Run this to see what happened:

```powershell
.\scripts\analyze-persistent-logs.ps1
```

**Output shows:**
- Recent 5 sessions with uptime and exit status
- Normal shutdowns vs crashes vs unexplained stops
- Memory usage at startup
- Summary analysis

### Show All Crashes

```powershell
.\scripts\analyze-persistent-logs.ps1 -ShowCrashes
```

### Show All Events

```powershell
.\scripts\analyze-persistent-logs.ps1 -ShowEvents
```

### Investigate Specific Time

```powershell
.\scripts\analyze-persistent-logs.ps1 -Before "2025-12-09 16:00:00" -ShowEvents
```

Shows what happened before 4pm on December 9th.

### Show More Sessions

```powershell
.\scripts\analyze-persistent-logs.ps1 -LastSessions 10
```

## Understanding Exit Types

### ✅ Normal Shutdown
```
🛑 NORMAL SHUTDOWN - Session: 20251209_160000
Uptime: 2:15:30
```
Application shut down cleanly (likely via `cslaunch` restart).

### ⚠️ Signal Shutdown
```
⚠️ SIGNAL RECEIVED: SIGTERM (15)
Session: 20251209_160000
```
Container stopped by Docker (docker stop, docker-compose down).

### 💥 Crash (Uncaught Exception)
```
💥 UNCAUGHT EXCEPTION - Session: 20251209_160000
Exception Type: MemoryError
Exception Value: Unable to allocate 2.34 GiB
```
Application crashed due to uncaught exception.

### ❌ Unexplained Stop (OOM Kill)
```
Status: ⚠️ No clean shutdown recorded (possible kill/OOM)
```
Container was killed without shutdown signal - likely OOM (Out of Memory) killer.

## Common Patterns

### Pattern 1: OOM Kills
**Symptoms:**
- Multiple unexplained stops
- Session files without shutdown_time or crash_time
- Docker logs show "Killed" or exit code 137

**Solution:**
```yaml
# In docker-compose.prod.yml, increase memory limits:
mem_limit: 6g  # Increase from 4g
mem_reservation: 3g  # Increase from 2g
```

### Pattern 2: Repeated Crashes
**Symptoms:**
- crash_log shows same exception repeatedly
- Quick restart cycles

**Solution:**
1. Check crash log for exception details:
   ```powershell
   Get-Content logs\casestrainer-backend_crashes.log -Tail 50
   ```

2. Fix the underlying code issue

### Pattern 3: Frequent Restarts via cslaunch
**Symptoms:**
- Many normal shutdowns
- Short uptimes (< 1 minute)

**Solution:**
- Check if auto-deploy is triggering too often
- Verify source code isn't changing unexpectedly

## Manual Log Review

### View Recent Events
```powershell
Get-Content logs\casestrainer-backend_events.log -Tail 50
```

### View Recent Crashes
```powershell
Get-Content logs\casestrainer-backend_crashes.log -Tail 100
```

### View Latest Session
```powershell
Get-ChildItem logs\session_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content | ConvertFrom-Json
```

### Search for Specific Error
```powershell
Select-String -Path logs\casestrainer-backend.log* -Pattern "MemoryError" -Context 5
```

## Log Rotation

- **Event Log**: Never rotates (append-only)
- **Crash Log**: Never rotates (append-only)
- **Main Log**: Rotates after 5MB, keeps 10 backups (50MB total)
- **Session Files**: Accumulate indefinitely (cleanup manually if needed)

### Clean Old Sessions
```powershell
# Keep only last 30 days
Get-ChildItem logs\session_*.json | 
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | 
    Remove-Item
```

## Integration with Monitoring

The persistent logging system automatically:
- ✅ Logs every startup with system diagnostics
- ✅ Logs every shutdown with uptime
- ✅ Catches and logs uncaught exceptions
- ✅ Handles OS signals (SIGTERM, SIGINT)
- ✅ Records memory usage at startup
- ✅ Creates session tracking files

## Troubleshooting

### Logs Not Being Created

**Check volume mount:**
```powershell
docker inspect casestrainer-backend-prod | Select-String "Mounts" -Context 0,20
```

Should show: `./logs:/app/logs`

### Permissions Issues

```powershell
# Fix permissions on Windows
icacls logs /grant Everyone:F /T
```

### Disk Space Issues

```powershell
# Check log directory size
Get-ChildItem logs -Recurse | Measure-Object -Property Length -Sum | 
    Select-Object @{Name="SizeMB";Expression={[math]::Round($_.Sum/1MB,2)}}
```

## Best Practices

1. **Regular Reviews**: Check logs weekly for patterns
2. **Before Changes**: Review logs before making system changes
3. **After Outages**: Always run analysis script after system comes back up
4. **Archive Old Logs**: Archive (don't delete) logs older than 90 days
5. **Monitor Disk**: Ensure log volume has sufficient space (recommend 5GB+)

## Example Workflow After Outage

```powershell
# 1. System is back up, investigate what happened
cd d:\dev\casestrainer

# 2. Run analysis script
.\scripts\analyze-persistent-logs.ps1

# 3. If unexplained stops found, check for OOM
.\scripts\analyze-persistent-logs.ps1 -ShowEvents

# 4. Check Docker stats
docker stats --no-stream

# 5. Review specific time window
.\scripts\analyze-persistent-logs.ps1 -Before "2025-12-09 16:00:00" -ShowEvents

# 6. Check for crashes
.\scripts\analyze-persistent-logs.ps1 -ShowCrashes

# 7. If OOM issue, increase memory limits in docker-compose.prod.yml
# Then redeploy:
.\cslaunch.ps1
```

## See Also

- `CRASH_MONITORING.md` - Docker container monitoring with auto-restart
- `MONITORING_QUICK_START.md` - Overall monitoring guide
- `scripts/analyze-crash-logs.ps1` - Docker-level crash analysis
