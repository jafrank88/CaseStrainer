from redis import Redis
from rq import Worker

r = Redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
workers = Worker.all(connection=r)
print(f'Found {len(workers)} registered workers')

print('Deleting all workers...')
for w in workers:
    print(f'  Deleting {w.name}...')
    w.register_death()
    
print('Done - all workers cleared')
