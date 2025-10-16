from redis import Redis
from rq import Queue

r = Redis(host='casestrainer-redis-prod', port=6379, password='***REDACTED_REDIS_PASSWORD***', db=0, decode_responses=True)
q = Queue('casestrainer', connection=r)

job_id = '99f5911f-5382-4921-8139-625d9fd7e20e'

print(f'=== FORCE REMOVING JOB {job_id} ===')

# Remove from started registry (it's a sorted set)
started_key = 'rq:wip:casestrainer'
removed_from_started = r.zrem(started_key, job_id)
print(f'Removed from started registry: {removed_from_started}')

# Delete job data
job_key = f'rq:job:{job_id}'
deleted = r.delete(job_key)
print(f'Deleted job data: {deleted}')

# Check progress key
progress_key = f'job_progress:{job_id}'
deleted_progress = r.delete(progress_key)
print(f'Deleted progress data: {deleted_progress}')

print(f'\n✅ Cleanup complete!')
print(f'Queue length now: {len(q)}')
