#!/usr/bin/env python3
"""Check RQ job arguments"""
import sys
sys.path.insert(0, '/app')

from redis import Redis
import os
from rq.job import Job

# Connect to Redis
redis_url = os.getenv('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
r = Redis.from_url(redis_url)

# Get job
job_id = 'client-1761104810033-m1fyuhwhq'

try:
    j = Job.fetch(job_id, connection=r)
    
    print(f"\n{'='*80}")
    print(f"JOB INPUT FOR: {job_id}")
    print(f"{'='*80}")
    print(f"Function: {j.func_name}")
    print(f"Args Count: {len(j.args)}")
    print(f"Kwargs Count: {len(j.kwargs)}")
    
    print(f"\nArgs:")
    for i, arg in enumerate(j.args):
        arg_type = type(arg).__name__
        if isinstance(arg, str):
            print(f"  [{i}] {arg_type}: {arg[:200]}...")  # First 200 chars
        elif isinstance(arg, dict):
            print(f"  [{i}] {arg_type}: {list(arg.keys())}")
            if 'url' in arg:
                print(f"      url: {arg.get('url')}")
            if 'text' in arg:
                text_len = len(arg.get('text', ''))
                print(f"      text length: {text_len} chars")
                print(f"      text preview: {arg.get('text', '')[:200]}...")
        else:
            print(f"  [{i}] {arg_type}: {arg}")
    
    print(f"\nKwargs:")
    for key, val in j.kwargs.items():
        print(f"  {key}: {type(val).__name__} = {val}")
        
    print(f"\n{'='*80}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
