# Async Processing Troubleshooting Guide

## Overview

CaseStrainer uses RQ (Redis Queue) workers for async processing of large documents. This guide helps troubleshoot common async issues.

## Fixed Issues

### ✅ Infinite Retry Loop on Rate Limits (Fixed)

**Problem**: Workers got stuck retrying CourtListener API calls that returned HTTP 429 (rate limit exceeded), causing jobs to never complete.

**Fix Applied**: Added graceful rate limit handling in `src/unified_verification_master.py`. Workers now skip citations that hit rate limits instead of retrying forever.

**Files Modified**:
- `src/unified_verification_master.py` - Added HTTP 429 handling for both lookup and search APIs

## Common Issues & Solutions

### Jobs Stuck in "Processing" State

**Symptoms**:
- Jobs never complete
- Progress stuck at same percentage
- Workers show as "busy" but not making progress

**Solution**:
```powershell
# Check for stuck jobs
.\scripts\cleanup-rq-jobs.ps1

# Clean up stuck jobs
.\scripts\cleanup-rq-jobs.ps1 -Force

# Or restart with cleanup
.\cslaunch -CleanupJobs
```

### Rate Limit Errors (HTTP 429)

**Symptoms**:
- Error logs show "429 Too Many Requests"
- Citations not being verified
- URL extraction returning minimal content

**Solution**:
1. **Wait for rate limits to reset** (~1 hour for CourtListener)
2. **Use force_mode sync** to skip async processing:
   ```json
   {
     "type": "url",
     "url": "your-url",
     "force_mode": "sync"
   }
   ```
3. **Test with direct text** instead of URLs

### Workers Not Picking Up Jobs

**Check worker status**:
```powershell
docker logs casestrainer-rqworker1-prod --tail=50
docker logs casestrainer-rqworker2-prod --tail=50
docker logs casestrainer-rqworker3-prod --tail=50
```

**Restart workers**:
```powershell
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart rqworker1 rqworker2 rqworker3
```

## Usage Examples

### Normal Restart (picks up code changes automatically)
```powershell
.\cslaunch
```

### Restart with Job Cleanup
```powershell
.\cslaunch -CleanupJobs
```

### Force Full Rebuild
```powershell
.\cslaunch -Build -Force
```

### Manual Job Cleanup
```powershell
# Check status
.\scripts\cleanup-rq-jobs.ps1

# Clean up
.\scripts\cleanup-rq-jobs.ps1 -Force
```

## Diagnostic Commands

### Check Redis connection from worker:
```powershell
docker exec casestrainer-rqworker1-prod python -c "import redis; r = redis.Redis(host='casestrainer-redis-prod', port=6379, password='***REDACTED_REDIS_PASSWORD***'); print('Redis OK:', r.ping())"
```

### Check queue status:
```powershell
docker exec casestrainer-rqworker1-prod python -c "from rq import Queue; from redis import Redis; r = Redis(host='casestrainer-redis-prod', port=6379, password='***REDACTED_REDIS_PASSWORD***'); q = Queue('casestrainer', connection=r); print(f'Queue: {len(q)} jobs')"
```

### Check worker processes:
```powershell
docker ps --filter "name=rqworker"
```

## Architecture Notes

### Why Jobs Get Stuck

1. **Rate Limits**: External APIs (CourtListener, etc.) return 429 errors
2. **Infinite Retries**: Before the fix, code would retry forever
3. **Worker Crashes**: Workers can crash mid-job leaving jobs in "started" state

### How the Fix Works

1. **Rate Limit Detection**: Code now catches `requests.exceptions.HTTPError` with status 429
2. **Graceful Skip**: Returns `verified=False` with error message instead of retrying
3. **Job Completion**: Job completes successfully even if some citations couldn't be verified

### Volume Mounts

Code changes in `src/` are automatically picked up on restart because of Docker volume mounts:
```yaml
volumes:
  - ./src:/app/src  # ← Changes here = instant pickup
```

**This means**: You don't need to rebuild containers for Python code changes, just restart!

## Prevention

### Best Practices

1. **Use CleanupJobs flag** when restarting after crashes:
   ```powershell
   .\cslaunch -CleanupJobs
   ```

2. **Monitor rate limits** - CourtListener free tier: ~100 requests/hour

3. **Check worker health** periodically:
   ```powershell
   docker ps --filter "name=rqworker"
   ```

4. **Keep workers updated** - Restart picks up code fixes automatically

## Rate Limit Information

### CourtListener API Limits
- **Free tier**: ~100 requests/hour
- **Paid tier**: Higher limits available
- **Reset time**: Typically 1 hour

### Handling Rate Limits in Your Tool

If your tool hits rate limits, you can:

1. **Wait and retry** after ~1 hour
2. **Use sync mode** to process without verification:
   ```json
   {"type": "text", "text": "...", "force_mode": "sync"}
   ```
3. **Reduce verification** - Fewer citations = fewer API calls

## Troubleshooting Checklist

- [ ] Check if containers are running: `docker ps`
- [ ] Check Redis is healthy: Health check in worker logs
- [ ] Check for stuck jobs: `.\scripts\cleanup-rq-jobs.ps1`
- [ ] Check rate limits: Look for "429" in logs
- [ ] Check worker logs: `docker logs casestrainer-rqworker1-prod`
- [ ] Try cleanup restart: `.\cslaunch -CleanupJobs`
- [ ] Last resort: `.\cslaunch -Build -Force`

## Related Files

- `src/unified_verification_master.py` - Verification with rate limit handling
- `src/rq_worker.py` - RQ worker implementation
- `src/progress_manager.py` - Job processing logic
- `docker-compose.prod.yml` - Worker container configuration
- `scripts/cleanup-rq-jobs.ps1` - Job cleanup utility
- `cslaunch.ps1` - Main launcher with cleanup option
