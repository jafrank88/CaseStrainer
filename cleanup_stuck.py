from redis import Redis
from rq import Queue
from rq.registry import StartedJobRegistry

r = Redis(host='casestrainer-redis-prod', port=6379, password='***REDACTED_REDIS_PASSWORD***', db=0, decode_responses=True)
q = Queue('casestrainer', connection=r)

print('=== CLEANING STUCK JOBS ===')
started_registry = StartedJobRegistry(queue=q)

stuck_jobs = started_registry.get_job_ids()
print(f'Found {len(stuck_jobs)} stuck job(s) in started registry')

for job_id in stuck_jobs:
    print(f'Removing stuck job: {job_id}')
    started_registry.remove(job_id)
    # Also delete the job data
    r.delete(f'rq:job:{job_id}')
    print(f'  ✓ Removed')

print(f'\n✅ Cleanup complete!')
print(f'Queue length now: {len(q)}')
print(f'Started jobs now: {started_registry.count}')
