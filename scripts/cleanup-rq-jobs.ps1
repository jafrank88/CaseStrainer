# cleanup-rq-jobs.ps1
# Clean up stuck RQ worker jobs
# Usage: .\scripts\cleanup-rq-jobs.ps1

param(
    [switch]$Force
)

Write-Host "`n=== RQ Job Cleanup ===" -ForegroundColor Cyan

# Check if workers are running
$workers = @(docker ps --format '{{.Names}}' | Where-Object { $_ -match 'rqworker' })

if ($workers.Count -eq 0) {
    Write-Host "[SKIP] No RQ workers running" -ForegroundColor Yellow
    exit 0
}

Write-Host "[INFO] Found $($workers.Count) RQ workers" -ForegroundColor Green

# Check for stuck jobs
Write-Host "`nChecking for stuck jobs..." -ForegroundColor Yellow

$checkResult = docker exec casestrainer-rqworker1-prod python -c @"
from rq.registry import StartedJobRegistry
from redis import Redis
import os

redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
redis_conn = Redis.from_url(redis_url)
started_reg = StartedJobRegistry('casestrainer', connection=redis_conn)
print(len(started_reg))
"@ 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Could not check job status" -ForegroundColor Red
    exit 1
}

$stuckCount = [int]$checkResult

if ($stuckCount -eq 0) {
    Write-Host "[OK] No stuck jobs found" -ForegroundColor Green
    exit 0
}

Write-Host "[WARNING] Found $stuckCount stuck job(s)" -ForegroundColor Yellow

if (-not $Force) {
    Write-Host "`nTo clean up stuck jobs, run:" -ForegroundColor Cyan
    Write-Host "  .\scripts\cleanup-rq-jobs.ps1 -Force" -ForegroundColor White
    Write-Host "`nThis will cancel stuck jobs and clear the failed jobs registry." -ForegroundColor Gray
    exit 0
}

# Perform cleanup
Write-Host "`n[CLEANUP] Cleaning up stuck and failed jobs..." -ForegroundColor Yellow

docker exec casestrainer-rqworker1-prod python -c @"
from rq import Queue
from rq.registry import StartedJobRegistry, FailedJobRegistry
from rq.job import Job
from redis import Redis
import os

redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
redis_conn = Redis.from_url(redis_url)

q = Queue('casestrainer', connection=redis_conn)
started_reg = StartedJobRegistry('casestrainer', connection=redis_conn)
failed_reg = FailedJobRegistry('casestrainer', connection=redis_conn)

# Cancel stuck jobs
stuck_count = 0
for job_id in list(started_reg.get_job_ids()):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        job.cancel()
        started_reg.remove(job)
        stuck_count += 1
    except:
        pass

# Clear failed jobs
failed_count = 0
for job_id in list(failed_reg.get_job_ids()):
    try:
        failed_reg.remove(job_id, delete_job=True)
        failed_count += 1
    except:
        pass

# Clear queue
queue_count = len(q)
q.empty()

print(f'{stuck_count},{failed_count},{queue_count}')
"@

if ($LASTEXITCODE -eq 0 -and $checkResult) {
    $counts = $checkResult -split ','
    Write-Host "`n[SUCCESS] Cleanup complete:" -ForegroundColor Green
    Write-Host "  - Canceled stuck jobs: $($counts[0])" -ForegroundColor Gray
    Write-Host "  - Removed failed jobs: $($counts[1])" -ForegroundColor Gray
    Write-Host "  - Cleared queued jobs: $($counts[2])" -ForegroundColor Gray
    
    # Restart workers to clear any in-memory state
    Write-Host "`n[RESTART] Restarting workers to clear state..." -ForegroundColor Yellow
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart rqworker1 rqworker2 rqworker3 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] Workers restarted" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Worker restart may have failed" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[ERROR] Cleanup failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
