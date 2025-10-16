import redis
from rq import Queue
from rq.job import Job

try:
    # Connect to Redis
    r = redis.Redis(host='localhost', port=6379, db=0, password='***REDACTED_REDIS_PASSWORD***')
    print(f"✓ Redis ping: {r.ping()}")
    
    # Check queue
    q = Queue('casestrainer', connection=r)
    print(f"\nQueue Stats:")
    print(f"  - Active jobs in queue: {len(q)}")
    print(f"  - Failed jobs: {len(q.failed_job_registry)}")
    
    # Check specific job
    task_id = 'bcf3bd5d-2290-4eff-87b9-70754e5bd803'
    try:
        job = Job.fetch(task_id, connection=r)
        print(f"\nJob {task_id}:")
        print(f"  - Status: {job.get_status()}")
        print(f"  - Is finished: {job.is_finished}")
        print(f"  - Is failed: {job.is_failed}")
        
        if job.is_failed:
            print(f"  - Error: {job.exc_info}")
        
        if job.is_finished and job.result:
            print(f"  - Result type: {type(job.result)}")
            if isinstance(job.result, dict):
                print(f"  - Result keys: {list(job.result.keys())}")
                citations = job.result.get('citations', [])
                print(f"  - Citations found: {len(citations)}")
                
    except Exception as e:
        print(f"\nError fetching job: {e}")
        
except redis.ConnectionError as e:
    print(f"✗ Could not connect to Redis: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
