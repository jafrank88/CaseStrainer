#!/usr/bin/env python3
"""
Check failed jobs for error messages
"""
from redis import Redis
from rq import Queue
from rq.job import Job
from rq.registry import FailedJobRegistry

r = Redis(host='casestrainer-redis-prod', port=6379, password='***REDACTED_REDIS_PASSWORD***', db=0, decode_responses=True)
q = Queue('casestrainer', connection=r)

print("Checking failed jobs...")

failed_registry = FailedJobRegistry(queue=q)
job_ids = failed_registry.get_job_ids()

print(f"Found {len(job_ids)} failed jobs\n")

for i, job_id in enumerate(job_ids[-5:], 1):  # Last 5 failed jobs
    try:
        job = Job.fetch(job_id, connection=r)
        print(f"Failed Job {i}: {job_id}")
        print(f"  Created: {job.created_at}")
        print(f"  Function: {job.func_name}")
        
        if job.exc_info:
            lines = job.exc_info.split('\n')
            # Show last 10 lines of error
            print(f"  Error (last 10 lines):")
            for line in lines[-10:]:
                if line.strip():
                    print(f"    {line}")
        else:
            print(f"  Error: No exception info")
        print()
    except Exception as e:
        print(f"Failed Job {i}: {job_id}")
        print(f"  Error fetching: {e}\n")
