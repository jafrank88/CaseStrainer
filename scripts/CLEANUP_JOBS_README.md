# Automatic Stuck Job Cleanup

## Overview

`cslaunch` now automatically cleans up stuck RQ jobs on every production restart/deploy. This prevents jobs from getting stuck in infinite loops due to rate limiting or other issues.

## How It Works

1. **Automatic Cleanup**: Every time you run `cslaunch`, it will:
   - Check for jobs in "started" state older than 10 minutes
   - Cancel and remove these stuck jobs
   - Display cleanup results

2. **Non-Blocking**: Job cleanup is non-critical and won't prevent deployment if it fails

3. **Safe**: Only removes jobs that have been stuck for >10 minutes (configurable)

## Manual Cleanup

If you need to manually clean stuck jobs:

```powershell
# From inside backend container
docker exec casestrainer-backend-prod python /app/cleanup-stuck-jobs.py

# Force cleanup of ALL started jobs (no age check)
docker exec casestrainer-backend-prod python /app/cleanup-stuck-jobs.py --force

# Custom max age
docker exec casestrainer-backend-prod python /app/cleanup-stuck-jobs.py --max-age 5
```

## Files

- **`cleanup-stuck-jobs.py`**: Python script that does the actual cleanup
  - Located: `scripts/cleanup-stuck-jobs.py`
  - Copied to container: `/app/cleanup-stuck-jobs.py`
  - Called automatically by cslaunch

- **`cslaunch.ps1`** (root): Quick restart wrapper - runs cleanup on restart
- **`scripts/cslaunch.ps1`**: Full deployment script - runs cleanup after startup

## When Jobs Get Stuck

Jobs can get stuck due to:
- **CourtListener API rate limiting** (429 errors)
- **Infinite verification loops**
- **Worker crashes mid-processing**
- **Redis connection issues**

The automatic cleanup ensures these don't accumulate and block new jobs.

## Monitoring

To check queue status manually:

```python
# From backend container
import redis
from rq import Queue

r = redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
q = Queue('casestrainer', connection=r)

print(f"Queued: {len(q)}")
print(f"Started: {q.started_job_registry.count}")
print(f"Failed: {q.failed_job_registry.count}")
```

## Configuration

Edit `cleanup-stuck-jobs.py` to change:
- `max_age_minutes`: Default 10 minutes
- Cleanup behavior
- Logging verbosity

## Troubleshooting

**Cleanup fails silently**: This is by design - deployment continues even if cleanup fails

**Jobs still stuck after cleanup**: 
- Check if workers are processing
- Look for errors in `docker logs casestrainer-rqworker1-prod`
- Consider increasing `max_age_minutes`

**Want to disable automatic cleanup**: 
- Remove `Clear-StuckJobs` calls from cslaunch.ps1 files
- Or set `max_age_minutes` very high (e.g., 999999)
