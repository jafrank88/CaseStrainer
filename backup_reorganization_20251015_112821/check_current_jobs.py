"""Check what's currently being processed"""
import redis
from rq import Queue
from rq.job import Job
from rq.registry import StartedJobRegistry
import os

redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
r = redis.from_url(redis_url)
q = Queue('casestrainer', connection=r)

print("Checking ALL jobs in the system...")
print("=" * 60)

# Check started jobs
started_registry = StartedJobRegistry(queue=q)
if started_registry.count > 0:
    print(f"\n🔄 STARTED JOBS ({started_registry.count}):")
    for job_id in started_registry.get_job_ids():
        try:
            job = Job.fetch(job_id, connection=r)
            print(f"\nJob ID: {job_id}")
            print(f"  Function: {job.func_name}")
            print(f"  Status: {job.get_status()}")
            print(f"  Created: {job.created_at}")
            print(f"  Args: {job.args[:2] if len(job.args) > 2 else job.args}")  # Truncate long args
        except Exception as e:
            print(f"  Error fetching job: {e}")
else:
    print("\n✅ No started jobs")

# Check queued jobs
if len(q) > 0:
    print(f"\n📋 QUEUED JOBS ({len(q)}):")
    for job in q.jobs[:5]:  # Show first 5
        print(f"  - {job.id[:8]}... {job.func_name}")
else:
    print("\n✅ No queued jobs")

print("\n" + "=" * 60)
print(f"SUMMARY:")
print(f"  Queued: {len(q)}")
print(f"  Started: {started_registry.count}")
print(f"  Failed: {q.failed_job_registry.count}")
print(f"  Finished: {q.finished_job_registry.count}")
