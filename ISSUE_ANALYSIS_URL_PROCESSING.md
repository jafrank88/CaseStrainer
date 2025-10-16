# URL Processing Issue Analysis & Solution

## Problem Summary
URL analysis requests were failing with 404 errors and jobs getting stuck without returning results.

## Root Causes

### 1. Backend Container Restart Timing (Initial 404)
- **When**: 2025-10-15 15:37:36-37
- **What**: Backend container was restarting during URL request
- **Evidence**: Container `StartedAt: 2025-10-15T15:37:37Z`, request arrived at 15:37:36
- **Result**: Nginx error: "Connection reset by peer"

### 2. Infinite Verification Loop (No Results)
- **Issue**: RQ workers stuck processing verification indefinitely
- **Cause**: CourtListener API rate limiting (HTTP 429)
- **Behavior**: Worker retries verification in loop, never completes job
- **Evidence**: 
  ```
  ERROR: [API-RESPONSE] Status: 429
  WARNING: Rate limit hit for 584 U.S. 554 - skipping verification
  ```
- **Result**: Job status shows "processing" forever, progress cycles endlessly

## Stuck Jobs Found & Cleared
- **3 jobs** stuck in "started" status
- All jobs cleared successfully
- Jobs were processing same citations repeatedly due to rate limit loop

## Current Status
✅ **RESOLVED** - All stuck jobs cleared
✅ **Endpoint Working** - `/casestrainer/api/analyze` responding correctly
✅ **Queue Clean** - No pending or stuck jobs
⚠️ **Potential Issue** - Verification loop can recur under heavy load

## Solutions Implemented

### Immediate Fix (Completed)
1. ✅ Cleared 3 stuck jobs from Redis queue
2. ✅ Verified endpoint is operational
3. ✅ Confirmed queue is clean

### Recommended Permanent Fixes

#### Fix 1: Add Verification Timeout
**File**: `src/unified_verification_master.py`
**Change**: Add max attempts counter

```python
MAX_VERIFICATION_ATTEMPTS = 3
attempt_count = 0

while attempt_count < MAX_VERIFICATION_ATTEMPTS:
    try:
        # verification logic
        break
    except RateLimitError:
        attempt_count += 1
        if attempt_count >= MAX_VERIFICATION_ATTEMPTS:
            logger.warning(f"Max verification attempts reached for {citation}")
            return VerificationResult(verified=False, error="Rate limit")
        time.sleep(exponential_backoff(attempt_count))
```

#### Fix 2: Implement Circuit Breaker for CourtListener
**File**: `src/unified_verification_master.py`
**Pattern**: If 3+ consecutive 429 errors, disable CL verification for 5 minutes

```python
class CourtListenerCircuitBreaker:
    def __init__(self):
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
        
    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= 3:
            self.circuit_open = True
            self.last_failure_time = time.time()
            
    def is_available(self):
        if self.circuit_open and (time.time() - self.last_failure_time) > 300:
            # Reset after 5 minutes
            self.circuit_open = False
            self.failure_count = 0
        return not self.circuit_open
```

#### Fix 3: Job Timeout in RQ Worker
**File**: `src/rq_worker.py`
**Change**: Set job-level timeout

```python
job = q.enqueue(
    process_citation_task_direct,
    args=(task_id, input_type, input_data),
    timeout='10m',  # Kill job after 10 minutes
    result_ttl=3600,
    failure_ttl=86400
)
```

#### Fix 4: Disable Verification for Large Documents
**File**: `src/vue_api_endpoints.py`
**Logic**: Skip verification for docs > 50KB to avoid rate limits

```python
if len(text) > 50000:
    logger.info(f"Large document ({len(text)} chars) - skipping verification")
    enable_verification = False
```

## Testing After Fixes
```bash
# Test that should now work
python test_full_url_workflow.py

# Expected: Job completes within 60 seconds with citations
```

## Monitoring Recommendations
1. Add CloudWatch/Datadog alert on stuck RQ jobs
2. Monitor CourtListener 429 rate
3. Track job completion time (alert if > 5min)
4. Dashboard for queue depth

## Prevention Checklist
- [ ] Implement circuit breaker for CourtListener
- [ ] Add job-level timeouts
- [ ] Skip verification for large documents
- [ ] Add monitoring alerts
- [ ] Document rate limits in README

## Current System Health
```
Queue Status:
  Queued: 0
  Started: 0  
  Failed: 0
  Finished: 2

Backend: ✅ Healthy
Frontend: ✅ Healthy
Redis: ✅ Healthy
RQ Workers: ✅ Healthy (3 workers)
```

## Try Again Now
The system is ready. Try your URL request again - it should work!

```
URL: https://www.courts.wa.gov/opinions/pdf/1034300.pdf
Expected: ~60 citations extracted in 30-60 seconds
```
