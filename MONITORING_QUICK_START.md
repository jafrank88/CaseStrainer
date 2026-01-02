# CaseStrainer Monitoring - Quick Start

## Enable Monitoring Now

```powershell
# Start monitoring (runs continuously, auto-restarts failures)
.\cslaunch.ps1 -Monitor
```

Press `Ctrl+C` to stop monitoring.

## What You'll See

```
[14:23:45] ✓ All services healthy
[14:24:15] ✓ All services healthy
[14:24:45] ⚠ Issues detected - check crash log
```

If a container crashes, you'll see:
- **Container name** that failed
- **Exit code** (137 = out of memory, 1 = error, etc.)
- **Error patterns** detected (OOM, connection refused, etc.)
- **Auto-restart** attempts (up to 3 times)
- **Recovery** confirmation

## Check Crash History

```powershell
# View crash summary
.\scripts\analyze-crash-logs.ps1 -Summary

# Recent crashes only (last 24 hours)
.\scripts\analyze-crash-logs.ps1 -Recent

# Group by container
.\scripts\analyze-crash-logs.ps1 -ByContainer

# Group by error type
.\scripts\analyze-crash-logs.ps1 -ByError
```

## Crash Log Location

All crashes are logged to: `logs\crash_log.txt`

Each crash includes:
- Timestamp
- Exit code
- Last 50 log lines
- Detected error patterns
- Memory usage
- Health status

## Common Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 137 | Out of memory | Increase memory limits |
| 1 | Application error | Check container logs |
| 143 | Graceful shutdown | Normal, no action needed |
| 139 | Segmentation fault | Check for memory corruption |

## Quick Fixes

### Container Keeps Crashing (OOM - Exit 137)

Edit `docker-compose.prod.yml`:

```yaml
backend:
  mem_limit: 6g        # Increase from 4g
  mem_reservation: 3g  # Increase from 2g
```

Then restart: `.\cslaunch.ps1`

### Check Container Logs Directly

```powershell
# Backend logs
docker logs casestrainer-backend-prod --tail 100

# Worker logs
docker logs casestrainer-rqworker1-prod --tail 100

# All containers
docker-compose -f docker-compose.prod.yml logs --tail 50
```

### Manual Container Restart

```powershell
# Restart specific container
docker-compose -f docker-compose.prod.yml restart backend

# Restart all workers
docker-compose -f docker-compose.prod.yml restart rqworker1 rqworker2 rqworker3
```

## Custom Monitoring Intervals

```powershell
# Check every 10 seconds (aggressive)
.\cslaunch.ps1 -Monitor -MonitorInterval 10

# Check every minute (less verbose)
.\cslaunch.ps1 -Monitor -MonitorInterval 60
```

## Run in Background (PowerShell 7+)

```powershell
# Start as background job
Start-Job -ScriptBlock { 
    Set-Location "d:\dev\casestrainer"
    .\cslaunch.ps1 -Monitor 
}

# Check job status
Get-Job

# View job output
Receive-Job -Id 1

# Stop job
Stop-Job -Id 1
```

## When Monitoring Stops

If monitoring stops after 3 failures:
1. Check `logs\crash_log.txt`
2. Run: `.\scripts\analyze-crash-logs.ps1 -Summary`
3. Fix the root cause
4. Restart: `.\cslaunch.ps1`
5. Resume monitoring: `.\cslaunch.ps1 -Monitor`

## Full Documentation

See `CRASH_MONITORING.md` for complete documentation.
