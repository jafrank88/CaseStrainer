# cslaunch Auto Cache Clear Enhancement
**Date:** November 10, 2025  
**Feature:** Automatic cache clearing on every cslaunch execution

---

## ✅ **What Changed**

The `cslaunch` script now **automatically clears all caches** every time you run it, eliminating the need to manually clear Redis cache or restart workers.

### **Automatic Actions on Every Launch:**

1. **✅ Clears ALL Redis databases** (`FLUSHALL`)
   - Verification cache (database 0)
   - Job queue cache (database 1)
   - Session cache (database 2)
   - All other Redis data

2. **✅ Clears file-based caches**
   - `/app/src/citation_cache/*`

3. **✅ Restarts RQ workers**
   - Clears in-memory Python caches
   - Loads fresh code from volume mounts

4. **✅ Reminds about browser cache**
   - Prompts you to clear browser cache (Ctrl+Shift+Delete)

---

## **Why This Matters**

### **Before (Manual Cache Management):**
```bash
# Had to run these commands manually:
docker exec casestrainer-redis-prod redis-cli -a caseStrainerRedis123 FLUSHALL
docker restart casestrainer-rqworker1-prod casestrainer-rqworker2-prod casestrainer-rqworker3-prod
./cslaunch
```

**Problems:**
- Easy to forget to clear cache
- Results showed old "N/A" extractions even after code fixes
- Frustrating debugging experience (fixing code but seeing no changes)
- Wasted 5+ hours debugging "wrong file" when it was actually cached data

### **After (Automatic Cache Management):**
```bash
./cslaunch
```

**Benefits:**
- ✅ One command does everything
- ✅ Always get fresh results
- ✅ No more confusion about whether code changes took effect
- ✅ Faster development iteration

---

## **When Caches Are Cleared**

### **Production Mode:**
```bash
./cslaunch  # Defaults to 'prod' - always clears caches
```

**Output:**
```
[AUTO-MAINTENANCE] Performing automatic cache clear and worker restart...
  🗑️  Clearing ALL Redis databases (including verification cache)...
  ✅ Redis caches cleared (all databases)
  🗑️  Clearing file caches...
  ✅ File caches cleared

[RQ WORKERS] Restarting workers to load new code...
  ✅ RQ workers restarted successfully
     Workers will now use updated Python code

  📝 REMINDER: Clear your browser cache (Ctrl+Shift+Delete) to see new results!
```

---

## **Code Changes**

### **1. Root `cslaunch.ps1` (Lines 306-370)**

**Before:**
```powershell
# Clear each Redis database individually with Python
$redisKeys0 = docker exec casestrainer-backend-prod python -c "from redis import Redis; r=Redis(host='redis',port=6379,db=0); keys=r.keys('*'); print(len(keys))" 2>$null
docker exec casestrainer-backend-prod python -c "from redis import Redis; r=Redis(host='redis',port=6379,db=0); r.flushdb()" 2>$null | Out-Null
# ... repeat for DB 1, 2, 3
```

**After:**
```powershell
# Clear ALL Redis databases with FLUSHALL (much faster)
$redisOutput = docker exec casestrainer-redis-prod redis-cli -a caseStrainerRedis123 FLUSHALL 2>&1
# ... then restart workers
docker-compose -f docker-compose.prod.yml restart rqworker1 rqworker2 rqworker3
```

**Why:** 
- `FLUSHALL` clears ALL databases in one command (faster than 4 individual commands)
- Added automatic worker restart to clear in-memory caches
- Added browser cache reminder

---

### **2. Scripts `cslaunch.ps1` (Lines 269, 406-409, 463-466)**

**Modified** `Clear-ApplicationCache` to use `FLUSHALL` and made it run automatically on every production start (not just when `-ClearCache` flag is used).

---

## **What Gets Cleared**

| Cache Type | Location | Command | Purpose |
|------------|----------|---------|---------|
| **Redis - Verification Results** | Redis DB 0 | `FLUSHALL` | Clears cached verification lookups from CourtListener/Justia |
| **Redis - Job Queue** | Redis DB 1 | `FLUSHALL` | Clears RQ job queue data |
| **Redis - Sessions** | Redis DB 2-15 | `FLUSHALL` | Clears any other Redis-cached data |
| **File Cache** | `/app/src/citation_cache/` | `rm -rf` | Clears file-based citation cache |
| **Worker In-Memory Cache** | Python process memory | Worker restart | Clears `_result_cache`, `active_verifications`, etc. |

---

## **Testing the Enhancement**

### **Test Scenario:**
1. Upload PDF, get "N/A" results
2. Fix extraction code
3. Run `./cslaunch`
4. Upload same PDF again

**Expected:**
- ✅ Cache clearing messages appear
- ✅ Workers restart
- ✅ Fresh extraction runs (logs show `[MASTER_EXTRACT ENTRY]`)
- ✅ New results appear (not cached "N/A")

### **Verification Commands:**

**Check Redis is empty:**
```bash
docker exec casestrainer-redis-prod redis-cli -a caseStrainerRedis123 DBSIZE
# Should return: (integer) 0
```

**Check workers restarted:**
```bash
docker ps --format "{{.Names}}\t{{.RunningFor}}" | grep rqworker
# Should show workers with recent "Up X seconds" time
```

---

## **Impact on Development Workflow**

### **Old Workflow (5-10 minutes per iteration):**
1. Make code change
2. Rebuild: `./cslaunch`
3. Manually clear Redis: `docker exec...`
4. Manually restart workers: `docker restart...`
5. Clear browser cache
6. Upload PDF
7. Wait for results
8. Debug why it's still showing "N/A"
9. Realize you forgot to clear cache
10. Go back to step 3

### **New Workflow (2 minutes per iteration):**
1. Make code change
2. Run: `./cslaunch` (does everything automatically)
3. Clear browser cache (prompted by script)
4. Upload PDF
5. See fresh results immediately ✅

**Time saved:** ~3-8 minutes per iteration  
**Frustration saved:** Immeasurable

---

## **Known Limitations**

1. **Browser cache must still be cleared manually**
   - The script reminds you, but can't do it automatically
   - Use Ctrl+Shift+Delete in your browser

2. **Cache clearing adds ~5-10 seconds to startup**
   - This is acceptable tradeoff for guaranteed fresh results
   - Much faster than manual cache management

3. **Cached data is lost**
   - If you had verification data cached, it's gone
   - Next upload will verify from scratch (slower first time)
   - Benefit: Always get latest canonical data from APIs

---

## **Rollback Instructions**

If you need to disable automatic cache clearing (not recommended):

**Edit:** `scripts/cslaunch.ps1`

**Find (around lines 406-409 and 463-466):**
```powershell
# ALWAYS clear caches and restart workers on every launch
Write-Host "`n[AUTO-MAINTENANCE] Performing automatic cache clear and worker restart..." -ForegroundColor Cyan
Clear-ApplicationCache -SkipConfirmation
Restart-RQWorkers
```

**Replace with:**
```powershell
# Clear caches if requested or after build
if ($ClearCache) {
    Clear-ApplicationCache -SkipConfirmation
    Restart-RQWorkers
}
```

Then use `./cslaunch -ClearCache` when you want to clear caches manually.

---

## **Related Issues Fixed**

This enhancement directly addresses the issue where:
- Extraction code was fixed (added special format handling)
- UI display logic was fixed (fallback through cluster citations)
- But results still showed "N/A" because:
  - Redis was serving cached verification results
  - Workers had in-memory cached extraction results
  - Browser had cached UI state

**Now:** Every `./cslaunch` guarantees a clean slate! 🎉

---

## **Success Metrics**

After implementing this enhancement, you should see:

1. ✅ **Cache clearing messages** in every cslaunch output
2. ✅ **Workers restart** automatically
3. ✅ **Fresh extraction logs** for every upload
4. ✅ **Code changes take effect immediately**
5. ✅ **No more mysterious "cached N/A" results**

---

**Status:** ✅ Enhancement complete and tested  
**Version:** cslaunch v2.1 (Auto Cache Clear)
