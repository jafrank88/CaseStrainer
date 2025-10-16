#!/usr/bin/env python3
"""
Check what's actually stored in Redis for the completed job
"""
import os
os.environ['REDIS_URL'] = 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0'

from rq import Queue
from redis import Redis
import json

# The job ID from our test
task_id = "56fa947d-f29e-4883-8470-1e2643170891"

redis_conn = Redis.from_url(os.environ['REDIS_URL'])
queue = Queue('casestrainer', connection=redis_conn)

job = queue.fetch_job(task_id)

if not job:
    print(f"❌ Job {task_id} not found")
    exit(1)

print("=" * 80)
print(f"JOB RESULT INSPECTION: {task_id}")
print("=" * 80)
print()

print(f"Status: {job.get_status()}")
print(f"Finished: {job.is_finished}")
print(f"Failed: {job.is_failed}")
print()

if job.is_finished:
    result = job.result
    print("Result Type:", type(result))
    print()
    
    if isinstance(result, dict):
        print("Result Keys:", list(result.keys()))
        print()
        
        # Check for citations
        if 'citations' in result:
            citations = result['citations']
            print(f"✅ Found 'citations' key: {len(citations)} citations")
            if citations:
                print(f"   First citation: {citations[0]}")
        else:
            print("❌ NO 'citations' key in result")
        
        # Check for nested result
        if 'result' in result:
            nested = result['result']
            print(f"✅ Found nested 'result' key")
            if isinstance(nested, dict):
                print(f"   Nested keys: {list(nested.keys())}")
                if 'citations' in nested:
                    citations = nested['citations']
                    print(f"   ✅ Nested citations: {len(citations)}")
        
        # Check metadata
        if 'metadata' in result:
            metadata = result['metadata']
            print(f"✅ Metadata: {metadata}")
        
        # Print full structure (truncated)
        print()
        print("Full Result Structure:")
        print(json.dumps(result, indent=2, default=str)[:2000])
        
    else:
        print(f"Result is not dict: {result}")
        
else:
    print("Job not finished yet")
    if hasattr(job, 'meta'):
        print("Job meta:", job.meta)
