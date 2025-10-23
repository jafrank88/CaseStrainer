#!/usr/bin/env python3
"""Check if RQ job is stuck"""
import sys
sys.path.insert(0, '/app')

from redis import Redis
import os
from rq import Queue
from rq.job import Job
from datetime import datetime

# Connect to Redis
redis_url = os.getenv('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
r = Redis.from_url(redis_url)

# Get job
job_id = 'client-1761104810033-m1fyuhwhq'

try:
    j = Job.fetch(job_id, connection=r)
    
    print(f"\n{'='*80}")
    print(f"JOB DIAGNOSTICS: {job_id}")
    print(f"{'='*80}")
    print(f"Job Status: {j.get_status()}")
    print(f"Started At: {j.started_at}")
    print(f"Ended At: {j.ended_at}")
    print(f"Enqueued At: {j.enqueued_at}")
    print(f"Meta: {j.meta}")
    print(f"Result: {j.result}")
    print(f"Exc Info: {j.exc_info}")
    print(f"Timeout: {j.timeout}")
    print(f"TTL: {j.ttl}")
    
    # Check how long it's been running
    if j.started_at:
        elapsed = datetime.now(j.started_at.tzinfo) - j.started_at
        print(f"\n⏱️  ELAPSED TIME: {elapsed.total_seconds():.1f} seconds")
        
        if elapsed.total_seconds() > 60:
            print(f"🚨 JOB IS STUCK! Running for {elapsed.total_seconds():.1f}s with no progress")
    
    # Check worker
    print(f"\nWorker Name: {j.worker_name}")
    
    # Check if worker is still alive
    from rq.worker import Worker
    workers = Worker.all(connection=r)
    worker_names = [w.name for w in workers]
    print(f"\nActive Workers: {len(workers)}")
    for w in workers:
        print(f"  - {w.name}: {w.state}")
    
    if j.worker_name and j.worker_name not in worker_names:
        print(f"\n🚨 WORKER '{j.worker_name}' IS DEAD! Job is orphaned.")
    
    print(f"\n{'='*80}")
    
except Exception as e:
    print(f"❌ Error checking job: {e}")
    import traceback
    traceback.print_exc()
