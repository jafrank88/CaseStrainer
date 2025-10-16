from redis import Redis
from rq import Queue
from rq.job import Job
from rq.registry import FailedJobRegistry, StartedJobRegistry

r = Redis(host='casestrainer-redis-prod', port=6379, password='***REDACTED_REDIS_PASSWORD***', db=0, decode_responses=True)
q = Queue('casestrainer', connection=r)

print('=== FAILED JOBS ===')
failed_registry = FailedJobRegistry(queue=q)
for job_id in failed_registry.get_job_ids():
    try:
        job = Job.fetch(job_id, connection=r)
        print(f'\nJob {job_id}:')
        print(f'  Exc info: {job.exc_info[:200] if job.exc_info else "None"}...')
    except Exception as e:
        print(f'  Error fetching: {e}')

print('\n\n=== STARTED JOBS ===')
started_registry = StartedJobRegistry(queue=q)
for job_id in started_registry.get_job_ids():
    print(f'\nStarted job: {job_id}')
    try:
        # Try to get job info from Redis directly
        job_key = f'rq:job:{job_id}'
        exists = r.exists(job_key)
        print(f'  Redis key exists: {exists}')
        if exists:
            status = r.hget(job_key, 'status')
            print(f'  Status in Redis: {status}')
    except Exception as e:
        print(f'  Error: {e}')
