"""Clear stuck RQ jobs"""
import redis
from rq import Queue
from rq.job import Job
from rq.registry import StartedJobRegistry
import os

redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
r = redis.from_url(redis_url)
q = Queue('casestrainer', connection=r)

print("Clearing stuck jobs...")
started_registry = StartedJobRegistry(queue=q)

stuck_count = 0
for job_id in started_registry.get_job_ids():
    try:
        job = Job.fetch(job_id, connection=r)
        print(f"  Canceling job {job_id[:8]}...")
        job.cancel()
        job.delete()
        stuck_count += 1
    except Exception as e:
        print(f"  Error canceling {job_id[:8]}: {e}")

print(f"\n✅ Cleared {stuck_count} stuck jobs")

# Verify
print(f"\nNew status:")
print(f"  Queued: {len(q)}")
print(f"  Started: {q.started_job_registry.count}")
print(f"  Failed: {q.failed_job_registry.count}")
