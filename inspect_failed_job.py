#!/usr/bin/env python3
"""
Inspect failed job details
"""
from redis import Redis
from rq import Queue
from rq.job import Job
from rq.registry import FailedJobRegistry

redis_conn = Redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@localhost:6380/0')
queue = Queue('casestrainer', connection=redis_conn)
failed_registry = FailedJobRegistry(queue=queue)

job_ids = failed_registry.get_job_ids()
print(f"Failed jobs: {len(job_ids)}\n")

# Get the most recent failed job
if job_ids:
    job_id = job_ids[-1]
    print(f"Inspecting job: {job_id}")
    
    try:
        # Try to fetch the job
        job = Job.fetch(job_id, connection=redis_conn)
        print(f"  Created: {job.created_at}")
        print(f"  Status: {job.get_status()}")
        print(f"  Function: {job.func_name}")
        print(f"  Args: {job.args}")
        print(f"  Kwargs: {job.kwargs}")
        
        if job.exc_info:
            print(f"\n  Exception Info:")
            print(job.exc_info[-500:])  # Last 500 chars
    except Exception as e:
        print(f"  Error fetching job: {e}")
        print(f"  Error type: {type(e).__name__}")
        
        # Try to get raw data from Redis
        print(f"\n  Attempting to get raw job data...")
        job_key = f'rq:job:{job_id}'
        
        try:
            job_data = redis_conn.hgetall(job_key)
            print(f"  Raw keys: {list(job_data.keys())[:10]}")
            
            # Try to decode specific fields
            if b'data' in job_data:
                data_bytes = job_data[b'data']
                print(f"  Data length: {len(data_bytes)} bytes")
                print(f"  First 50 bytes: {data_bytes[:50]}")
        except Exception as e2:
            print(f"  Error getting raw data: {e2}")
