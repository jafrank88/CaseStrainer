#!/usr/bin/env python3
"""
Clear all jobs from started registry to reset RQ state
"""
from redis import Redis
from rq import Queue
from rq.registry import StartedJobRegistry

r = Redis(host='casestrainer-redis-prod', port=6379, password='***REDACTED_REDIS_PASSWORD***', db=0, decode_responses=True)
q = Queue('casestrainer', connection=r)

print("Clearing started registry...")

started_registry = StartedJobRegistry(queue=q)

job_ids = started_registry.get_job_ids()
print(f"Found {len(job_ids)} jobs in started registry")

for job_id in job_ids:
    print(f"  Removing: {job_id}")
    # Force remove from sorted set
    r.zrem(f'rq:wip:{q.name}', job_id)
    # Delete job data
    r.delete(f'rq:job:{job_id}')
    # Delete progress data
    r.delete(f'job_progress:{job_id}')

print(f"\n✓ Cleared {len(job_ids)} jobs from started registry")
print(f"Queue length now: {len(q)}")
print(f"Started jobs now: {started_registry.count}")
