# cslaunch Prevention Features

## New Functionality Added

Yes! I've added **automatic detection and prevention** to prevent Redis bloat from happening again.

---

## 1. Automatic AOF Size Monitoring

### What It Does

Every time you run `./cslaunch`, it now **checks Redis AOF size** and warns you when maintenance is needed.

### Thresholds

| AOF Size | Warning Level | Action |
|----------|---------------|--------|
| **< 100 MB** | ✅ OK | No warning |
| **100 MB - 1 GB** | ⚠️ Warning | Maintenance recommended |
| **> 1 GB** | 🚨 Critical | Maintenance needed NOW |

### Example Output

**When maintenance needed:**
```powershell
[SUCCESS] RESTART COMPLETE - All services ready!
  Your Python changes are now active (volume mounts)
  Application: http://localhost

⚠️  Redis AOF is large (813M) - maintenance recommended
  Run: .\scripts\redis_maintenance.ps1
```

**When critical:**
```powershell
🚨 Redis AOF is very large (2.1G) - maintenance needed!
  Run: .\scripts\redis_maintenance.ps1 -Force
```

---

## 2. Redis Maintenance Script

### Location

`scripts/redis_maintenance.ps1`

### What It Does

1. **Cleans old RQ jobs** (older than 7 days)
   - Finished jobs
   - Failed jobs
   - Canceled jobs

2. **Compacts Redis AOF** file
   - Removes deleted data
   - Rewrites file efficiently
   - Reduces size by 10-1000x

### Usage

**Interactive mode:**
```powershell
.\scripts\redis_maintenance.ps1
```

You'll see:
```
📊 Current Redis Status:
   Keys: 37165
   Memory: 1.62M
   AOF Size: 813M

⚠️  This will:
   1. Clean RQ jobs older than 7 days
   2. Compact Redis AOF file
   3. May take 30-60 seconds

Continue? (y/n)
```

**Force mode (no prompts):**
```powershell
.\scripts\redis_maintenance.ps1 -Force
```

### Before/After Example

```
📊 Current Redis Status:
   Keys: 37165
   Memory: 1.62M
   AOF Size: 813M

[STEP 1/2] Cleaning old RQ jobs...
  ✅ Cleaned 35000+ old jobs

[STEP 2/2] Compacting Redis AOF...
  ✅ AOF rewrite completed

📊 After Maintenance:
   Keys: 25
   Memory: 1.65M
   AOF Size: 54.1K
```

---

## 3. Accurate Service Status Reporting

### Before

```powershell
⚠️  Redis not ready after 60s
⚠️  Backend not responding
⚠️  Some services not fully ready

[SUCCESS] RESTART COMPLETE - All services ready!  ← WRONG!
```

### After

```powershell
⚠️  Redis not ready after 60s
⚠️  Backend not responding
⚠️  Some services not fully ready

[PARTIAL SUCCESS] Containers restarted but some services need more time
  ⚠️  Some services may take a few more minutes to be fully ready
```

---

## Recommended Maintenance Schedule

### Option 1: Manual (When Warned)

Just run maintenance when `cslaunch` warns you:
```powershell
# cslaunch will tell you when needed
./cslaunch

# If you see the warning:
.\scripts\redis_maintenance.ps1
```

### Option 2: Weekly Manual

Run maintenance once a week:
```powershell
# Every Monday morning
.\scripts\redis_maintenance.ps1 -Force
```

### Option 3: Windows Task Scheduler (Automated)

**Create automated weekly maintenance:**

1. Open Task Scheduler
2. Create Basic Task:
   - Name: "CaseStrainer Redis Maintenance"
   - Trigger: Weekly, Sunday 2:00 AM
   - Action: Start a program
   - Program: `powershell.exe`
   - Arguments: `-NoProfile -ExecutionPolicy Bypass -File "D:\dev\casestrainer\scripts\redis_maintenance.ps1" -Force`
   - Start in: `D:\dev\casestrainer`

**Or use PowerShell to create it:**
```powershell
$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument '-NoProfile -ExecutionPolicy Bypass -File "D:\dev\casestrainer\scripts\redis_maintenance.ps1" -Force' `
    -WorkingDirectory 'D:\dev\casestrainer'

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am

Register-ScheduledTask -Action $action -Trigger $trigger `
    -TaskName "CaseStrainer Redis Maintenance" `
    -Description "Weekly Redis cleanup to prevent bloat"
```

---

## Why This Prevents Future Problems

### Problem: Redis Bloat

**What happened:**
- RQ (Redis Queue) stores all job history
- Over time: 37,165 old jobs accumulated
- Result: 813 MB of deleted data in AOF
- Impact: 94+ second startup time

### Solution: Automatic Prevention

1. **Early Detection**
   - cslaunch warns at 100 MB (before it's critical)
   - You can fix it before startup gets slow

2. **Easy Cleanup**
   - One command: `.\scripts\redis_maintenance.ps1`
   - Takes 30-60 seconds
   - Reduces AOF by 10-1000x

3. **Accurate Monitoring**
   - cslaunch checks every time
   - No manual monitoring needed
   - Catch problems early

---

## What to Do Now

### Immediate Actions

✅ **Done**: Redis already compacted (813 MB → 54 KB)  
✅ **Done**: cslaunch now monitors AOF size  
✅ **Done**: Maintenance script created

### Recommended Next Steps

1. **Test the new cslaunch:**
   ```powershell
   ./cslaunch
   ```
   - Should start fast (2-5 seconds for Redis)
   - Should report accurate status
   - Should NOT show AOF warning (we just cleaned it)

2. **Bookmark maintenance command:**
   ```powershell
   # For when you see the warning:
   .\scripts\redis_maintenance.ps1
   ```

3. **Optional: Set up automation**
   - Use Windows Task Scheduler (see above)
   - Or just run manually when warned

---

## Monitoring Redis Health

### Quick Check

```powershell
# Check current AOF size
docker exec casestrainer-redis-prod du -sh /data/appendonlydir

# Check number of keys
docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** DBSIZE

# Check memory usage
docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** INFO memory | Select-String "used_memory_human"
```

### Healthy Values

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| **AOF Size** | < 100 MB | 100 MB - 1 GB | > 1 GB |
| **Keys** | < 1000 | 1000 - 10000 | > 10000 |
| **Memory** | < 100 MB | 100 MB - 1 GB | > 1 GB |
| **Startup Time** | < 10s | 10-30s | > 30s |

---

## Troubleshooting

### "Redis not ready after 60s"

**Likely cause**: AOF too large

**Solution:**
```powershell
# Wait for Redis to finish loading (may take 2-3 minutes)
# Then immediately run:
.\scripts\redis_maintenance.ps1 -Force
```

### "Maintenance script not found"

**Solution:**
```powershell
# Script should be in scripts/ directory
# If missing, re-download or check git
ls scripts/redis_maintenance.ps1
```

### "Permission denied"

**Solution:**
```powershell
# Run PowerShell as Administrator
# Or set execution policy:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Summary

✅ **Automatic detection** - cslaunch warns when maintenance needed  
✅ **Easy fix** - One command to clean and compact  
✅ **Accurate status** - No more false success messages  
✅ **Prevention** - Run weekly to keep Redis fast  
✅ **Monitoring** - Built into cslaunch, no extra work  

**This will prevent the 813 MB / 94-second startup problem from happening again!** 🎯
