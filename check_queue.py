from redis import Redis
from rq import Queue
from rq.job import Job

r = Redis(host='casestrainer-redis-prod', port=6379, password='***REDACTED_REDIS_PASSWORD***', db=0, decode_responses=True)
q = Queue('casestrainer', connection=r)

print(f'Queue length: {len(q)}')
print(f'Started jobs: {q.started_job_registry.count}')
print(f'Failed jobs: {q.failed_job_registry.count}')
print(f'Finished jobs: {q.finished_job_registry.count}')

# Check if our specific job exists
job_id = '99f5911f-5382-4921-8139-625d9fd7e20e'
try:
    job = Job.fetch(job_id, connection=r)
    print(f'\nJob {job_id}:')
    print(f'  Status: {job.get_status()}')
    print(f'  Is finished: {job.is_finished}')
    print(f'  Is failed: {job.is_failed}')
    print(f'  Result: {job.result}')
except Exception as e:
    print(f'Job not found or error: {e}')
