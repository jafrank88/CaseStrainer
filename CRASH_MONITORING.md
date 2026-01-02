# CaseStrainer Crash Monitoring & Auto-Restart

## Overview

The enhanced `cslaunch.ps1` script now includes comprehensive crash detection, logging, and automatic restart capabilities to help diagnose and recover from site outages.

## New Features

### 1. Monitoring Mode (`-Monitor`)

Continuously monitors all CaseStrainer containers and automatically restarts failed services.

**Usage:**
```powershell
# Start monitoring with default 30-second interval
.\cslaunch.ps1 -Monitor

# Start monitoring with custom interval (60 seconds)
.\cslaunch.ps1 -Monitor -MonitorInterval 60
```

**What it does:**
- Checks all containers every 30 seconds (or custom interval)
- Detects crashes, unhealthy states, and container exits
- Automatically restarts failed containers (up to 3 attempts per container)
- Logs detailed crash information including:
  - Exit codes
  - Last 50 log lines
  - Memory usage
  - Common error patterns (OOM, connection issues, etc.)
- Displays real-time status updates

**When to use:**
- After deploying to production
- When experiencing intermittent failures
- For continuous uptime monitoring
- During high-traffic periods

### 2. Crash Logging

All crashes and restarts are logged to `logs/crash_log.txt` with:
- Timestamp
- Container name
- Exit code and restart count
- Health status
- Last 50 log lines
- Detected error patterns
- Memory usage at time of crash

**Log Location:**
```
d:\dev\casestrainer\logs\crash_log.txt
```

### 3. Error Pattern Detection

The system automatically scans crash logs for common issues:

| Pattern | Meaning | Likely Cause |
|---------|---------|--------------|
| Out of memory | Memory limit exceeded | Container using too much RAM |
| Connection refused | Service connection failed | Redis/DB not available |
| Address already in use | Port conflict | Another process using the port |
| Cannot allocate memory | System memory exhausted | Host system out of RAM |
| ModuleNotFoundError | Missing Python dependency | Incomplete build |
| redis.exceptions | Redis connection issue | Redis crashed or network issue |
| Killed | Process killed | OOM killer activated |
| FATAL | Fatal error occurred | Critical application error |

### 4. Auto-Restart Logic

When a container fails:
1. **Detect:** Monitor detects status change or unhealthy state
2. **Analyze:** Captures crash details (logs, exit code, errors)
3. **Log:** Saves full crash report to `crash_log.txt`
4. **Restart:** Attempts to restart the container
5. **Verify:** Checks if restart was successful
6. **Repeat:** Will retry up to 3 times per container
7. **Escalate:** After 3 failures, stops monitoring and alerts for manual intervention

## Usage Examples

### Basic Monitoring
```powershell
# Start monitoring (runs indefinitely until Ctrl+C)
.\cslaunch.ps1 -Monitor
```

**Output:**
```
========================================
MONITORING MODE - Press Ctrl+C to stop
========================================
Interval: 30 seconds
Crash log: d:\dev\casestrainer\logs\crash_log.txt

[14:23:45] ✓ All services healthy
[14:24:15] ✓ All services healthy
[14:24:45] ⚠ Issues detected - check crash log
[2024-11-28 14:24:45] [ERROR] ALERT: casestrainer-backend-prod changed to exited (Health: unhealthy)
[2024-11-28 14:24:45] [WARN] Analyzing crash for container: casestrainer-backend-prod
[2024-11-28 14:24:45] [INFO]   Status: exited, Exit Code: 137, Restart Count: 1
[2024-11-28 14:24:45] [ERROR]   FOUND: Process killed (likely OOM)
[2024-11-28 14:24:45] [WARN] Attempting auto-restart (1/3)...
[2024-11-28 14:24:50] [SUCCESS] Successfully restarted casestrainer-backend-prod
```

### Quick Check After Deployment
```powershell
# Deploy and start monitoring
.\cslaunch.ps1
# Wait for deployment to finish, then in another terminal:
.\cslaunch.ps1 -Monitor -MonitorInterval 15  # Check every 15 seconds
```

### Custom Monitoring Interval
```powershell
# Check every minute (less verbose)
.\cslaunch.ps1 -Monitor -MonitorInterval 60

# Check every 10 seconds (aggressive monitoring)
.\cslaunch.ps1 -Monitor -MonitorInterval 10
```

## Crash Log Analysis

### Reading the Crash Log

Each crash entry includes:

```
========== CRASH REPORT: casestrainer-backend-prod ==========
Time: 2024-11-28 14:24:45
Status: exited
Exit Code: 137
Restart Count: 1
Health: unhealthy

--- Last 50 Log Lines ---
[Previous log lines...]
Traceback (most recent call last):
  File "/app/src/app_final_vue.py", line 45, in <module>
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
MemoryError: Unable to allocate 2.34 GiB
Killed
==========================================
```

### Common Exit Codes

| Exit Code | Meaning | Typical Cause |
|-----------|---------|---------------|
| 0 | Normal exit | Container stopped cleanly |
| 1 | General error | Application crash or exception |
| 137 | SIGKILL (OOM) | Out of memory, killed by system |
| 139 | Segmentation fault | Memory corruption or invalid access |
| 143 | SIGTERM | Gracefully terminated by Docker |

### Exit Code 137 (Most Common)

**Meaning:** Container was killed by the OOM (Out Of Memory) killer

**Solutions:**
1. Increase memory limits in `docker-compose.prod.yml`:
   ```yaml
   mem_limit: 6g  # Increase from 4g
   mem_reservation: 3g  # Increase from 2g
   ```

2. Check for memory leaks in application code

3. Reduce worker count or job concurrency

4. Add swap space to host system

## Integration with Existing Features

The monitoring mode works alongside existing features:

```powershell
# Normal quick restart (no monitoring)
.\cslaunch.ps1

# Force rebuild with monitoring afterward
.\cslaunch.ps1 -Force
# In another terminal:
.\cslaunch.ps1 -Monitor

# Full rebuild without cache
.\cslaunch.ps1 -NoCache -Build
```

## Troubleshooting

### Monitor Exits After 3 Failures

**Problem:** Container keeps failing despite restart attempts

**Solution:**
1. Check `logs/crash_log.txt` for error patterns
2. Review container logs: `docker logs casestrainer-backend-prod`
3. Check memory usage: `docker stats`
4. Verify dependencies are installed
5. Check for port conflicts
6. Review Docker resource limits

### Logs Not Created

**Problem:** `logs/crash_log.txt` doesn't exist

**Solution:**
The logs directory is created automatically. If it's missing:
```powershell
New-Item -ItemType Directory -Path "logs" -Force
```

### Monitoring Doesn't Detect Crashes

**Problem:** Container crashes but monitor doesn't catch it

**Possible causes:**
- Crash and restart happen within the monitoring interval
- Solution: Reduce `-MonitorInterval` to 10-15 seconds
- Container has `restart: always` in docker-compose (restarts too fast)

## Best Practices

1. **Run monitoring in production:**
   ```powershell
   # Start as a background job (PowerShell 7+)
   Start-Job -ScriptBlock { .\cslaunch.ps1 -Monitor }
   ```

2. **Check logs regularly:**
   ```powershell
   Get-Content logs\crash_log.txt -Tail 50 -Wait
   ```

3. **Set appropriate interval:**
   - Development: 10-15 seconds (catch issues quickly)
   - Production: 30-60 seconds (balance monitoring vs. load)
   - Stable systems: 120 seconds (minimal overhead)

4. **Review crash patterns:**
   ```powershell
   # Find all crash reports
   Select-String "CRASH REPORT" logs\crash_log.txt

   # Count crashes by container
   Select-String "CRASH REPORT: (.*) =" logs\crash_log.txt -AllMatches | 
       ForEach-Object { $_.Matches.Groups[1].Value } | 
       Group-Object | 
       Sort-Object Count -Descending
   ```

## Performance Impact

The monitoring mode has minimal performance impact:
- CPU: ~0.1% (only during health checks)
- Memory: ~10MB
- Network: Negligible (local Docker API calls)
- Disk I/O: ~1KB per check (only when logging crashes)

## Advanced: Running as a Service

To run monitoring continuously in the background on Windows:

1. Create a scheduled task:
   ```powershell
   $action = New-ScheduledTaskAction -Execute "powershell.exe" `
       -Argument "-NoProfile -ExecutionPolicy Bypass -File `"d:\dev\casestrainer\cslaunch.ps1`" -Monitor"
   
   $trigger = New-ScheduledTaskTrigger -AtStartup
   
   $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
   
   Register-ScheduledTask -TaskName "CaseStrainer Monitor" `
       -Action $action `
       -Trigger $trigger `
       -Principal $principal `
       -Description "Monitors CaseStrainer containers and auto-restarts on failure"
   ```

2. Start the task:
   ```powershell
   Start-ScheduledTask -TaskName "CaseStrainer Monitor"
   ```

## Support

If you experience persistent crashes:

1. Check `logs/crash_log.txt` for patterns
2. Review error patterns detected
3. Check system resources: `docker stats`
4. Verify Redis is healthy: `docker exec casestrainer-redis-prod redis-cli ping`
5. Check network connectivity between containers
6. Review recent code changes

For help, include:
- Last 100 lines of `logs/crash_log.txt`
- Output of `docker stats`
- Output of `docker ps -a`
- Specific error patterns from the crash log
