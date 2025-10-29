#!/usr/bin/env python3
"""
Check RQ queue status
"""

import redis
import json

def check_queue_status():
    r = redis.Redis(host='casestrainer-redis-prod', port=6379, password='***REDACTED_REDIS_PASSWORD***', decode_responses=True)
    
    print("RQ QUEUE STATUS")
    print("=" * 50)
    
    # Check queue lengths
    queue_length = r.llen('casestrainer')
    failed_length = r.llen('failed')
    
    print(f"Main queue length: {queue_length}")
    print(f"Failed queue length: {failed_length}")
    
    # Check workers
    workers = r.smembers('rq:workers')
    print(f"Active workers: {len(workers)}")
    for worker in workers:
        print(f"  - {worker}")
    
    # Check current jobs
    jobs = r.lrange('rq:job:casestrainer', 0, -1)
    print(f"Current jobs in queue: {len(jobs)}")
    
    # Check worker stats
    for worker in workers:
        worker_key = f"rq:worker:{worker}"
        worker_data = r.hgetall(worker_key)
        if worker_data:
            print(f"\nWorker {worker}:")
            print(f"  State: {worker_data.get('state', 'unknown')}")
            print(f"  Current job: {worker_data.get('current_job', 'none')}")
            print(f"  Last heartbeat: {worker_data.get('last_heartbeat', 'unknown')}")

if __name__ == "__main__":
    check_queue_status()
