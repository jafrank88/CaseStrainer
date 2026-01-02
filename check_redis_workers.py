#!/usr/bin/env python3
"""
Check Redis connection and RQ worker status
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from redis import Redis
from rq import Queue, Worker
from rq.registry import StartedJobRegistry, FailedJobRegistry

def check_redis_workers():
    """Check Redis connection and RQ worker status"""
    
    print(f"=== Redis & RQ Worker Status Check ===")
    
    # Redis connection
    redis_url = os.environ.get('REDIS_URL', 'redis://:caseStrainerRedis123@casestrainer-redis-prod:6379/0')
    print(f"Redis URL: {redis_url}")
    
    try:
        redis_conn = Redis.from_url(redis_url)
        redis_conn.ping()
        print(f"✅ Redis connection successful")
        
        # Check Redis info
        info = redis_conn.info()
        print(f"Redis version: {info['redis_version']}")
        print(f"Connected clients: {info['connected_clients']}")
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return
    
    # RQ Queue status
    try:
        queue = Queue('casestrainer', connection=redis_conn)
        print(f"\n=== Queue Status ===")
        print(f"Queue name: {queue.name}")
        print(f"Queue length: {len(queue)}")
        
        # Show queued jobs
        if len(queue) > 0:
            print(f"Queued jobs:")
            for i, job in enumerate(queue[:5]):  # Show first 5
                print(f"  {i+1}. Job ID: {job.id}")
                print(f"     Created: {job.created_at}")
                print(f"     Status: {job.get_status()}")
                print(f"     Args: {job.args}")
        
    except Exception as e:
        print(f"❌ Queue check failed: {e}")
    
    # Worker status
    try:
        print(f"\n=== Worker Status ===")
        workers = Worker.all(connection=redis_conn, queue=queue)
        print(f"Total workers: {len(workers)}")
        
        for i, worker in enumerate(workers):
            print(f"Worker {i+1}:")
            print(f"  Name: {worker.name}")
            print(f"  State: {worker.state}")
            print(f"  Current job: {worker.get_current_job_id()}")
            print(f"  Birth date: {worker.birth_date}")
            
    except Exception as e:
        print(f"❌ Worker check failed: {e}")
    
    # Failed jobs registry
    try:
        print(f"\n=== Failed Jobs ===")
        failed_registry = FailedJobRegistry(queue=queue, connection=redis_conn)
        print(f"Failed jobs count: {len(failed_registry)}")
        
        if len(failed_registry) > 0:
            print(f"Recent failed jobs:")
            for i, job in enumerate(list(failed_registry)[:3]):  # Show first 3
                print(f"  {i+1}. Job ID: {job.id}")
                print(f"     Failed: {job.exc_info}")
                
    except Exception as e:
        print(f"❌ Failed jobs check failed: {e}")

if __name__ == "__main__":
    check_redis_workers()
