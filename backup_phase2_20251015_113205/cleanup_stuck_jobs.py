#!/usr/bin/env python
"""Clean up stuck RQ jobs"""
from rq import Queue
from rq.registry import StartedJobRegistry, FailedJobRegistry
from rq.job import Job
from redis import Redis
import os

redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
redis_conn = Redis.from_url(redis_url)

print("Cleaning up stuck and failed jobs...")

q = Queue('casestrainer', connection=redis_conn)
started_reg = StartedJobRegistry('casestrainer', connection=redis_conn)
failed_reg = FailedJobRegistry('casestrainer', connection=redis_conn)

# Cancel stuck jobs
print(f"\nCanceling {len(started_reg)} stuck jobs...")
for job_id in list(started_reg.get_job_ids()):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        job.cancel()
        started_reg.remove(job)
        print(f"  ✓ Canceled: {job_id[:20]}...")
    except Exception as e:
        print(f"  ✗ Error canceling {job_id[:20]}...: {e}")

# Clear failed jobs registry
print(f"\nClearing {len(failed_reg)} failed jobs...")
for job_id in list(failed_reg.get_job_ids()):
    try:
        failed_reg.remove(job_id, delete_job=True)
        print(f"  ✓ Removed: {job_id[:20]}...")
    except Exception as e:
        print(f"  ✗ Error removing {job_id[:20]}...: {e}")

# Clear queue
print(f"\nClearing {len(q)} queued jobs...")
q.empty()

print("\n✓ Cleanup complete!")
