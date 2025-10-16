#!/usr/bin/env python3
"""
Test async workers with a function that actually exists in the container
"""
import time
from redis import Redis
from rq import Queue

redis_conn = Redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@localhost:6380/0')
queue = Queue('casestrainer', connection=redis_conn)

print("="*60)
print("ASYNC WORKER TEST - Real Function")
print("="*60)

# Use a function that exists in the container: src.progress_manager.process_citation_task_direct
print("\n1. Enqueueing job to process_citation_task_direct...")

test_text = "This is a test citation: 123 Wn.2d 456"
job = queue.enqueue(
    'src.progress_manager.process_citation_task_direct',
    args=('test-async-job-001', 'text', {'text': test_text}),
    job_timeout=60,
    result_ttl=300
)

print(f"   Job ID: {job.id}")
print(f"   Initial status: {job.get_status()}")

# Poll for result
print("\n2. Polling for result (60 seconds max)...")
for i in range(60):
    time.sleep(1)
    
    try:
        job.refresh()
        status = job.get_status()
        
        if i % 5 == 0:  # Print every 5 seconds
            print(f"   [{i+1}s] Status: {status}")
        
        if status == 'finished':
            print(f"\n✅ SUCCESS! Worker processed the job.")
            print(f"   Result type: {type(job.result)}")
            if isinstance(job.result, dict):
                print(f"   Citations found: {len(job.result.get('citations', []))}")
                print(f"   Success: {job.result.get('success')}")
            break
        elif status == 'failed':
            print(f"\n❌ FAILED!")
            print(f"   Error: {job.exc_info[-500:]}")
            break
            
    except Exception as e:
        print(f"\n   Error: {e}")
        break
else:
    print(f"\n⏱️ TIMEOUT after 60 seconds")
    print(f"   Final status: {job.get_status()}")

# Queue stats
from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry

print(f"\n3. Final Queue Stats:")
print(f"   Queue length: {len(queue)}")
print(f"   Started: {StartedJobRegistry(queue=queue).count}")
print(f"   Finished: {FinishedJobRegistry(queue=queue).count}")
print(f"   Failed: {FailedJobRegistry(queue=queue).count}")

print("\n" + "="*60)
