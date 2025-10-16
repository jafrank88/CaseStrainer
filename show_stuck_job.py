#!/usr/bin/env python3
from redis import Redis
from rq import Queue
from rq.registry import StartedJobRegistry
from rq.job import Job

r = Redis(host='casestrainer-redis-prod', port=6379, password='***REDACTED_REDIS_PASSWORD***', db=0, decode_responses=True)
q = Queue('casestrainer', connection=r)

started_registry = StartedJobRegistry(queue=q)
job_ids = started_registry.get_job_ids()

print(f"Stuck jobs in started registry: {len(job_ids)}")
for job_id in job_ids:
    print(f"\nJob ID: {job_id}")
    
    # Try to get basic info without deserializing
    job_key = f'rq:job:{job_id}'
    if r.exists(job_key):
        created_at = r.hget(job_key, 'created_at')
        status = r.hget(job_key, 'status')
        print(f"  Status: {status}")
        print(f"  Created: {created_at}")
        
        # Force remove
        print(f"  Removing...")
        r.zrem(f'rq:wip:{q.name}', job_id)
        r.delete(job_key)
        r.delete(f'job_progress:{job_id}')
        print(f"  ✓ Removed")
    else:
        print(f"  Job data doesn't exist - cleaning registry entry")
        r.zrem(f'rq:wip:{q.name}', job_id)

print(f"\n✓ Cleanup complete")
print(f"Started jobs now: {StartedJobRegistry(queue=q).count}")
