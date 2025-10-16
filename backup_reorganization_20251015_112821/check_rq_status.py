"""Check RQ queue status"""
import redis
from rq import Queue
from rq.job import Job
from rq.registry import StartedJobRegistry, FailedJobRegistry
import os

redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
r = redis.from_url(redis_url)
q = Queue('casestrainer', connection=r)

print("=" * 60)
print("RQ QUEUE STATUS")
print("=" * 60)
print(f"Queue name: {q.name}")
print(f"Queued jobs: {len(q)}")
print(f"Started jobs: {q.started_job_registry.count}")
print(f"Failed jobs: {q.failed_job_registry.count}")
print(f"Finished jobs: {q.finished_job_registry.count}")
print(f"Deferred jobs: {q.deferred_job_registry.count}")

# Check started jobs (these might be stuck)
started_registry = StartedJobRegistry(queue=q)
if started_registry.count > 0:
    print(f"\n⚠️  Found {started_registry.count} STARTED (potentially stuck) jobs:")
    for job_id in started_registry.get_job_ids():
        try:
            job = Job.fetch(job_id, connection=r)
            print(f"  - {job_id[:8]}... Status: {job.get_status()} Created: {job.created_at}")
        except Exception as e:
            print(f"  - {job_id[:8]}... Error: {e}")

# Check failed jobs
failed_registry = FailedJobRegistry(queue=q)
if failed_registry.count > 0:
    print(f"\n❌ Found {failed_registry.count} FAILED jobs:")
    for job_id in failed_registry.get_job_ids()[:5]:  # Show first 5
        try:
            job = Job.fetch(job_id, connection=r)
            print(f"  - {job_id[:8]}... Error: {job.exc_info[:200] if job.exc_info else 'Unknown'}")
        except Exception as e:
            print(f"  - {job_id[:8]}... Error: {e}")
