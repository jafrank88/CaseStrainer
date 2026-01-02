#!/usr/bin/env python3
"""
Check Redis queue status
"""

import redis
import json

def check_redis_queue():
    """Check the status of Redis queues"""
    
    try:
        # Connect to Redis
        r = redis.Redis(
            host='casestrainer-redis-prod', 
            password='***REDACTED_REDIS_PASSWORD***', 
            port=6379, 
            db=0,
            decode_responses=True
        )
        
        print("🔍 Checking Redis queue status...")
        
        # Check queue lengths
        queue_length = r.llen('casestrainer')
        failed_length = r.llen('failed')
        deferred_length = r.llen('deferred')
        
        print(f"📊 Queue length: {queue_length}")
        print(f"📊 Failed jobs: {failed_length}")
        print(f"📊 Deferred jobs: {deferred_length}")
        
        # Check if there are any jobs in the main queue
        if queue_length > 0:
            print(f"\n📋 Jobs in queue:")
            for i in range(min(queue_length, 5)):
                job_data = r.lindex('casestrainer', i)
                try:
                    job = json.loads(job_data)
                    print(f"   Job {i+1}: {job.get('description', 'No description')}")
                except:
                    print(f"   Job {i+1}: {job_data[:100]}...")
        
        # Check failed jobs
        if failed_length > 0:
            print(f"\n❌ Failed jobs:")
            for i in range(min(failed_length, 3)):
                job_data = r.lindex('failed', i)
                try:
                    job = json.loads(job_data)
                    print(f"   Failed Job {i+1}: {job.get('description', 'No description')}")
                except:
                    print(f"   Failed Job {i+1}: {job_data[:100]}...")
        
        # Check worker stats
        print(f"\n👥 Worker stats:")
        workers = r.smembers('rq:workers')
        print(f"   Active workers: {len(workers)}")
        for worker in list(workers)[:3]:
            print(f"   - {worker}")
        
        return queue_length, failed_length, deferred_length
        
    except Exception as e:
        print(f"❌ Error checking Redis: {e}")
        return 0, 0, 0

if __name__ == "__main__":
    check_redis_queue()
