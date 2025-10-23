# CRITICAL: Redis Job Storage Bug - Oct 18, 2025 7:30pm

## **Problem:**

Processing completes successfully but results cannot be retrieved by frontend.

**Symptoms:**
- Progress shows: "Full pipeline: 6 citations, 2 clusters" ✅
- Job completes: `progress: 100.0, status: 'Complete'` ✅
- Frontend polls `/task_status/[id]`: **404 NOT FOUND** ❌
- Error: "Job [id] not found in queue" ❌

## **Root Cause:**

The async job result is not being stored in Redis properly. The job runs, completes, updates progress, but when the frontend tries to retrieve the results, the job ID isn't found in the RQ queue.

**Evidence from logs (7:29pm):**
```
2025-10-19 02:29:02 - Found 0 jobs in queue. Job IDs: []
2025-10-19 02:29:02 - WARNING - Job 3bd25887-b586-4eda-9410-60a9351e3d2b not found in queue
2025-10-19 02:29:02 - [Progress API] Found progress in global manager: {...'message': 'Full pipeline: 6 citations, 2 clusters'...}
```

**The paradox:**
- ✅ Progress manager HAS the result ("6 citations, 2 clusters")
- ❌ RQ queue does NOT have the job
- ❌ Frontend can't retrieve results (404)

## **Impact:**

**THIS AFFECTS ALL PROCESSING** - not just Fix #8:
- ✅ Citations ARE being extracted (6 found in test)
- ✅ Fix #8 code IS deployed
- ❌ But results NEVER make it to the frontend
- ❌ Users see spinning loader forever

## **Why We Didn't Notice Earlier:**

The cached PDF results from 11am were being returned successfully because they were processed BEFORE this bug appeared (or they're being served from a different code path).

## **What Needs to be Fixed:**

### **File:** `src/vue_api_endpoints_updated.py` or RQ worker setup

**Problem area:** Job result storage/retrieval mechanism

**Options:**
1. Job is completing but not being marked as "finished" in Redis
2. Job is being deleted from queue too quickly
3. Job result TTL is too short
4. Wrong queue name being used for storage vs retrieval

### **Immediate Workaround:**

Try processing with sync (small text input) instead of async to bypass the RQ queue entirely.

## **To Debug Tomorrow:**

1. Check RQ worker logs for job completion
2. Verify job is being enqueued properly
3. Check job result TTL settings
4. Verify queue names match between enqueue and fetch
5. Check if results are being stored with correct key format

## **Test Case:**

File: `test_fix8.txt` (405 bytes)
- Processed successfully: 6 citations, 2 clusters
- But frontend gets 404 on task_status

## **Current Status:**

- ❌ **BLOCKING:** Cannot test ANY fixes (including Fix #8) because results don't return
- ✅ **CODE:** Fix #8 is deployed and in container
- ✅ **PROCESSING:** Citations are being extracted
- ❌ **DELIVERY:** Results not reaching frontend

**Priority:** CRITICAL - System is non-functional for users

---

**Created:** Oct 18, 2025 7:30pm
**Session:** Today's 8 fixes (all blocked by this bug)
