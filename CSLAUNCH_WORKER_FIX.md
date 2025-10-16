# cslaunch Worker Rebuild Fix - October 15, 2025

## ❌ The Problem

**User Question:** "Will using cslaunch correctly update the containers now?"

**Answer:** NO - not before this fix!

### What Was Wrong

The old `cslaunch.ps1` only rebuilt the **backend** container:

```powershell
docker-compose -f docker-compose.prod.yml up -d --build backend
```

**But verification code runs in WORKERS, not just backend!**

### Impact

When you make verification code changes:
- ✅ Backend gets new code (via cslaunch)
- ❌ Workers still have OLD code
- ❌ Async jobs use old verification logic
- ❌ Fallback verification doesn't work for async jobs

## ✅ The Fix

### Changed Line 98 in `cslaunch.ps1`

**OLD:**
```powershell
docker-compose -f docker-compose.prod.yml up -d --build backend
```

**NEW:**
```powershell
docker-compose -f docker-compose.prod.yml up -d --build backend rqworker1 rqworker2 rqworker3
```

### What This Does

Now `cslaunch` rebuilds:
1. ✅ `casestrainer-backend-prod` (sync processing)
2. ✅ `casestrainer-rqworker1-prod` (async processing)
3. ✅ `casestrainer-rqworker2-prod` (async processing)
4. ✅ `casestrainer-rqworker3-prod` (async processing)

## 📊 Comparison

### Before Fix

```
./cslaunch
├─ Clear bytecode cache ✅
├─ Rebuild backend ✅
├─ Restart workers ❌ (restart only, no rebuild)
└─ Result: Workers have OLD code!
```

### After Fix

```
./cslaunch
├─ Clear bytecode cache ✅
├─ Rebuild backend ✅
├─ Rebuild worker1 ✅
├─ Rebuild worker2 ✅
├─ Rebuild worker3 ✅
└─ Result: Everything has NEW code!
```

## 🎯 Why This Matters

### Verification Code Runs in Workers

**For async jobs (large documents):**
- PDF URL submitted → Queued to Redis
- **Worker picks up job** ← This is where verification runs!
- Worker calls `unified_verification_master.py`
- Fallback verification happens HERE

**If workers aren't rebuilt:**
- Backend has new code, workers have old code
- Fallback verification still has old timeout bug
- No improvement for async jobs!

## 🚀 Now You Can Use `cslaunch`!

### Quick Update Command

```powershell
./cslaunch
```

**What it does now:**
1. Clears Python bytecode cache (host + containers)
2. Rebuilds backend with latest code
3. **Rebuilds all 3 workers with latest code** ← NEW!
4. Waits for services to be ready
5. Cleans up stuck jobs
6. Runs Redis maintenance

**Time:** ~15-20 seconds (slightly longer due to worker rebuilds)

## 📝 Usage

### When You Make Code Changes

**OLD Workflow (Manual):**
```powershell
# Had to manually rebuild workers
docker-compose -f docker-compose.prod.yml build backend rqworker1 rqworker2 rqworker3
docker-compose -f docker-compose.prod.yml up -d backend rqworker1 rqworker2 rqworker3
```

**NEW Workflow (Automatic):**
```powershell
# Just use cslaunch - it does everything!
./cslaunch
```

### What Gets Updated

| Container | Code Type | Updated by cslaunch |
|-----------|-----------|---------------------|
| **backend** | API endpoints, sync processing | ✅ YES |
| **rqworker1** | Async jobs, verification | ✅ YES (NEW!) |
| **rqworker2** | Async jobs, verification | ✅ YES (NEW!) |
| **rqworker3** | Async jobs, verification | ✅ YES (NEW!) |
| **frontend** | Vue.js UI | Only if dist changed |
| **nginx** | Proxy config | Only if config changed |
| **redis** | Data store | Never rebuilt |

## ✅ Verification

To verify cslaunch is working correctly:

```powershell
# Run cslaunch
./cslaunch

# Check output - should see:
# "[REBUILD] Rebuilding backend + workers for clean deployment..."
# "✅ Backend + workers rebuilt and deployed in XX seconds"
```

## 🎓 Technical Details

### Why Workers Need Rebuilding

**Docker container layers:**
```
Container Startup
├─ Base Image (python:3.10-slim)
├─ Dependencies (requirements.txt)
├─ Application Code (/app/src/) ← Changes here!
└─ Entrypoint (rq worker)
```

**When you change code:**
- Source files on host change
- Docker copies them during build
- Container runs from copied files
- **Must rebuild to update copied files!**

### Why Restart Isn't Enough

**Restart:**
- Stops container
- Starts same container again
- **Still has OLD code from last build!**

**Rebuild:**
- Stops container
- Rebuilds image with NEW code
- Starts NEW container
- **Has FRESH code!**

## 🎉 Summary

**Question:** "Will using cslaunch correctly update the containers now?"

**Answer:** ✅ **YES! (After this fix)**

`cslaunch` now:
- ✅ Rebuilds backend
- ✅ Rebuilds all 3 workers ← NEW!
- ✅ Clears bytecode cache
- ✅ Ensures fresh code everywhere
- ✅ Fast deployment (15-20s)

**You can now use `./cslaunch` for all code updates!** 🚀

---

**Status:** ✅ FIXED  
**Date:** October 15, 2025 @ 6:52 PM  
**Impact:** cslaunch now properly updates ALL containers that run Python code
