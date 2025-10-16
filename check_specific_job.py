#!/usr/bin/env python3
"""
Check specific job status
"""
import sys
from redis import Redis
from rq import Queue
from rq.job import Job

if len(sys.argv) < 2:
    print("Usage: python check_specific_job.py <job_id>")
    sys.exit(1)

job_id = sys.argv[1]

redis_conn = Redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@localhost:6380/0')
queue = Queue('casestrainer', connection=redis_conn)

print(f"Checking job: {job_id}\n")

try:
    job = Job.fetch(job_id, connection=redis_conn)
    print(f"Status: {job.get_status()}")
    print(f"Created: {job.created_at}")
    print(f"Function: {job.func_name}")
    print(f"Is finished: {job.is_finished}")
    print(f"Is failed: {job.is_failed}")
    print(f"Is started: {job.is_started}")
    print(f"Is queued: {job.is_queued}")
    
    if job.is_failed:
        print(f"\nError info:")
        print(job.exc_info[-500:] if job.exc_info else "No error info")
    
    if job.result:
        print(f"\nResult type: {type(job.result)}")
        if isinstance(job.result, dict):
            print(f"Success: {job.result.get('success')}")
            print(f"Citations: {len(job.result.get('citations', []))}")
            
except Exception as e:
    print(f"Error fetching job: {e}")
    print(f"Error type: {type(e).__name__}")
