# ✅ Automatic Stuck Job Cleanup Feature

## What Changed

`cslaunch` now **automatically cleans up stuck RQ jobs** every time you run it!

## Why This Matters

Your URL processing issue revealed that jobs can get stuck in infinite loops due to:
- CourtListener API rate limiting (429 errors)
- Verification retries without timeouts
- Worker crashes mid-processing

These stuck jobs prevent new jobs from completing and cause the "no results" issue you experienced.

## How It Works

### Automatic Cleanup on Every Launch

When you run `cslaunch`:

```powershell
./cslaunch          # Quick restart
./cslaunch -Build   # Full rebuild
```

It will automatically:
1. ✅ Check for jobs stuck in "started" state >10 minutes
2. ✅ Cancel and remove these stuck jobs
3. ✅ Display cleanup results
4. ✅ Continue with deployment

### Example Output

```
=== Cleaning up stuck RQ jobs ===
🔍 Checking 3 started job(s)...
  🧹 Cleaning stuck job d8b87dbb... (age: 0:15:23)
  🧹 Cleaning stuck job 84879d30... (age: 0:12:10)
  ⏳ Job a1b2c3d4... still processing (2.3m old)

✅ Cleaned 2 stuck job(s)
[OK] Job cleanup complete
```

## Files Added

1. **`scripts/cleanup-stuck-jobs.py`**: The cleanup script
   - Finds stuck jobs
   - Cancels and removes them
   - Configurable age threshold (default: 10 min)

2. **Updated `cslaunch.ps1`** (root): Runs cleanup on quick restart

3. **Updated `scripts/cslaunch.ps1`**: Runs cleanup after full startup

4. **`scripts/CLEANUP_JOBS_README.md`**: Detailed documentation

## Manual Cleanup

If needed, run cleanup manually:

```powershell
# Normal cleanup (>10 min old)
docker exec casestrainer-backend-prod python /app/cleanup-stuck-jobs.py

# Force cleanup ALL started jobs
docker exec casestrainer-backend-prod python /app/cleanup-stuck-jobs.py --force

# Custom age threshold
docker exec casestrainer-backend-prod python /app/cleanup-stuck-jobs.py --max-age 5
```

## Configuration

Edit age threshold in `scripts/cleanup-stuck-jobs.py`:

```python
def cleanup_stuck_jobs(max_age_minutes=10):  # Change this number
```

## Benefits

✅ **No more stuck jobs** accumulating over time  
✅ **Automatic prevention** of the "no results" issue  
✅ **Non-blocking** - won't stop deployment if cleanup fails  
✅ **Safe** - only removes jobs stuck >10 minutes  
✅ **Visible** - shows what it cleaned up

## Testing

The cleanup is already integrated. Next time you run `cslaunch`, you'll see:

```
[CLEANUP] Cleaning up any stuck RQ jobs...
  ✅ No stuck jobs found
[OK] Job cleanup complete
```

Or if there are stuck jobs:

```
[CLEANUP] Cleaning up any stuck RQ jobs...
  🧹 Cleaning stuck job abc123...
✅ Cleaned 1 stuck job(s)
```

## What This Fixes

This addresses the root issue from your URL processing bug:
- Jobs getting stuck in verification loops → **Now cleaned automatically**
- Queue filling with dead jobs → **Now cleared on restart**
- "No results" from stuck processing → **Now prevented**

## Next Steps

1. ✅ **Immediate**: Jobs are now automatically cleaned
2. 🔜 **Recommended**: Add timeout to verification (prevent stuck jobs from forming)
3. 🔜 **Optional**: Circuit breaker for CourtListener rate limits

The automatic cleanup is your **safety net** - it handles stuck jobs that do form, while the timeout/circuit breaker fixes will **prevent** them from forming in the first place.
