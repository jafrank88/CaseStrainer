# cslaunch - Now With Automatic Maintenance!

## What Changed

**cslaunch now maintains itself automatically!** 🎉

Someone who knows nothing about Redis can just run `./cslaunch` and it will:
1. ✅ Start CaseStrainer
2. ✅ Check Redis health
3. ✅ **Automatically clean up if needed**
4. ✅ Keep startup fast forever

---

## How It Works

### Every time you run cslaunch:

```powershell
./cslaunch
```

**It automatically:**

1. **Checks Redis AOF size**
2. **If > 200MB** → Runs maintenance automatically
3. **Shows progress** but no action needed from you
4. **Completes in seconds**

---

## What You'll See

### Normal Startup (AOF < 200MB)

```powershell
[SUCCESS] RESTART COMPLETE - All services ready!
  Your Python changes are now active (volume mounts)
  Application: http://localhost
```

No maintenance needed - just starts normally.

### Automatic Maintenance (AOF > 200MB)

```powershell
[SUCCESS] RESTART COMPLETE - All services ready!
  Your Python changes are now active (volume mounts)
  Application: http://localhost

[MAINTENANCE] Redis AOF is large (813M) - running automatic cleanup...
  ✅ Cleaned old RQ jobs
  ✅ Started AOF compaction (will complete in background)
  📊 Redis maintenance complete (AOF: 813M → 54.1K)
```

Maintenance runs automatically - no action needed!

---

## Zero Configuration Required

### For Someone Who Knows Nothing:

Just run:
```powershell
./cslaunch
```

That's it! Everything is automatic:
- ✅ No prompts
- ✅ No decisions
- ✅ No manual commands
- ✅ No task scheduler setup
- ✅ No maintenance scripts to remember

**It just works!** 🎯

---

## Why 200MB Threshold?

| Threshold | Why |
|-----------|-----|
| **< 200 MB** | OK - startup still fast |
| **> 200 MB** | Automatic cleanup - prevent problems |
| **> 1 GB** | Would cause very slow startup |

**We catch it early** at 200MB before it becomes a problem.

---

## What Gets Cleaned

### Automatic cleanup removes:

1. **Old RQ jobs** (older than 7 days)
   - Finished jobs
   - Failed jobs
   - Canceled jobs

2. **Deleted data** from Redis AOF
   - Compacts the append-only file
   - Removes old history
   - Keeps only active data

---

## Technical Details

### Before This Fix

**Problem:**
- Redis accumulated 37,165 old job keys
- AOF grew to 813 MB
- Startup took 94+ seconds
- User had to manually clean it

**Required user action:**
- Understand Redis
- Know about AOF files
- Run maintenance scripts
- Monitor system health

### After This Fix

**Solution:**
- cslaunch checks AOF size automatically
- Runs cleanup when > 200MB
- Keeps startup fast (< 10 seconds)
- Zero user intervention needed

**Required user action:**
- Run `./cslaunch`
- That's it!

---

## Benefits

### For Developers

✅ **Just works** - no maintenance to remember  
✅ **Fast startup** - never waits for Redis  
✅ **Self-healing** - fixes problems automatically  
✅ **Transparent** - shows what it's doing  

### For Non-Technical Users

✅ **No knowledge required** - run cslaunch, done  
✅ **No manual steps** - everything automatic  
✅ **No configuration** - works out of the box  
✅ **No problems** - prevents issues before they happen  

---

## Maintenance Schedule

### Automatic (Built-in)

**Trigger**: AOF > 200MB  
**Action**: Clean + compact automatically  
**Frequency**: As needed (usually every few weeks)  
**User action**: None - runs during cslaunch

### Optional (Manual)

**If you want to force it:**
```powershell
.\scripts\redis_maintenance.ps1 -Force
```

**But you don't need to** - cslaunch handles it.

---

## Edge Cases

### "What if maintenance fails?"

- cslaunch continues normally
- Doesn't block startup
- Will try again next time

### "What if I want to disable it?"

Currently no option to disable (by design - it's always beneficial).  
If needed, we could add a flag in the future.

### "What if AOF grows very quickly?"

Shouldn't happen in normal use, but:
- cslaunch runs on every restart
- Catches it at 200MB before critical
- Worst case: startup is slow once, then auto-fixed

---

## Summary

**Before:** User had to monitor Redis and run maintenance  
**After:** cslaunch does everything automatically  

**Knowledge required:** None  
**Manual steps:** None  
**Configuration:** None  

**Just run `./cslaunch` and it keeps itself healthy!** 🎉

---

## For Technical Users

If you want to monitor what's happening:

```powershell
# Check current AOF size
docker exec casestrainer-redis-prod du -sh /data/appendonlydir

# Check number of keys
docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** DBSIZE

# Force maintenance manually
.\scripts\redis_maintenance.ps1 -Force
```

But you don't need to - cslaunch handles it all.
