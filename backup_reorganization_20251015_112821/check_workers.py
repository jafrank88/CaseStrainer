import redis
from rq import Worker

r = redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
workers = Worker.all(connection=r)

print(f"\nTotal workers registered: {len(workers)}\n")

for w in workers:
    current_job = w.get_current_job_id()
    state = w.get_state()
    
    print(f"Worker: {w.name}")
    print(f"  State: {state}")
    print(f"  Current Job: {current_job or 'None'}")
    print(f"  Last Heartbeat: {w.last_heartbeat}")
    print()
