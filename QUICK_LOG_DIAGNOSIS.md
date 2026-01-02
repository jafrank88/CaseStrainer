# Quick Log Diagnosis Guide

## When the System Stops Working

### Step 1: Run Analysis Script
```powershell
cd d:\dev\casestrainer
.\scripts\analyze-persistent-logs.ps1
```

### Step 2: Look at Summary

**If you see "Unexplained Stops":**
```
Unexplained Stops: 3 (possibly OOM kills or forcekilled)
```
→ This is an **Out of Memory (OOM) kill**
→ **Solution**: Increase memory in `docker-compose.prod.yml`

**If you see crashes:**
```
Crashes: 2
```
→ Run: `.\scripts\analyze-persistent-logs.ps1 -ShowCrashes`
→ Read the exception details

**If you see only normal shutdowns:**
```
Normal Shutdowns: 5
```
→ Someone restarted the system manually (this is normal)

### Step 3: Check What Happened Before Restart

```powershell
# See events before specific time
.\scripts\analyze-persistent-logs.ps1 -Before "2025-12-09 16:30:00" -ShowEvents
```

This shows all startup/shutdown/crash events before that timestamp.

## Log Files Quick Reference

All logs are in: `d:\dev\casestrainer\logs\`

| File | What It Contains | Rotates? |
|------|------------------|----------|
| `casestrainer-backend_events.log` | Startup/shutdown/crashes | ❌ Never |
| `casestrainer-backend_crashes.log` | Full crash tracebacks | ❌ Never |
| `casestrainer-backend.log` | General app logging | ✅ Yes (5MB) |
| `session_*.json` | Per-session tracking | ❌ Never |

## Common Scenarios

### Scenario 1: System Unreachable, Comes Back After Login
**Likely Cause**: OOM (Out of Memory) kill
**How to Confirm**: Check for "Unexplained Stops" in analysis
**Solution**: Edit `docker-compose.prod.yml`:
```yaml
mem_limit: 6g  # Change from 4g
mem_reservation: 3g  # Change from 2g
```
Then: `.\cslaunch.ps1`

### Scenario 2: System Crashes with Error
**Likely Cause**: Python exception
**How to Confirm**: Check crash log
**Solution**: Fix the code issue shown in traceback

### Scenario 3: Frequent Restarts
**Likely Cause**: Auto-deploy or manual restarts
**How to Confirm**: Many "Normal Shutdowns" with short uptimes
**Solution**: This might be expected behavior

## View Raw Logs

```powershell
# Last 50 events
Get-Content logs\casestrainer-backend_events.log -Tail 50

# Last 100 crash entries
Get-Content logs\casestrainer-backend_crashes.log -Tail 100

# Latest session info
Get-ChildItem logs\session_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content | ConvertFrom-Json | ConvertTo-Json
```

## After Fixing Issues

1. Deploy fix: `.\cslaunch.ps1`
2. Monitor for ~10 minutes
3. Check session is stable: `.\scripts\analyze-persistent-logs.ps1`

## Need More Info?

- Full documentation: `PERSISTENT_LOGGING.md`
- Docker monitoring: `CRASH_MONITORING.md`
- Monitor mode: `.\cslaunch.ps1 -Monitor`
