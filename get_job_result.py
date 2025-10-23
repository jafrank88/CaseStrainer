#!/usr/bin/env python3
"""Get RQ job result"""
import sys
sys.path.insert(0, '/app')

from redis import Redis
import os
from rq.job import Job
import json

# Connect to Redis
redis_url = os.getenv('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
r = Redis.from_url(redis_url)

# Get job
job_id = 'client-1761104810033-m1fyuhwhq'

try:
    j = Job.fetch(job_id, connection=r)
    
    print(f"\n{'='*80}")
    print(f"JOB RESULT FOR: {job_id}")
    print(f"{'='*80}")
    print(f"Status: {j.get_status()}")
    print(f"Is Finished: {j.is_finished}")
    print(f"Is Failed: {j.is_failed}")
    print(f"Result Type: {type(j.result)}")
    
    if j.result:
        print(f"\n✅ RESULT EXISTS!")
        if isinstance(j.result, dict):
            print(f"Result Keys: {list(j.result.keys())}")
            print(f"Citations Count: {len(j.result.get('citations', []))}")
            print(f"Clusters Count: {len(j.result.get('clusters', []))}")
            print(f"Success: {j.result.get('success')}")
        else:
            print(f"Result: {j.result}")
    else:
        print(f"\n❌ NO RESULT STORED")
        
    print(f"\n{'='*80}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
