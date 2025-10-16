import redis
from rq.job import Job
from datetime import datetime

r = redis.from_url('redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')

# Find jobs starting with a32df2a5
all_keys = r.keys('rq:job:a32df2a5*')

if not all_keys:
    print("No jobs found starting with a32df2a5")
else:
    for key in all_keys:
        job_id = key.decode('utf-8').replace('rq:job:', '')
        try:
            job = Job.fetch(job_id, connection=r)
            
            print(f"\n{'='*60}")
            print(f"Job ID: {job.id}")
            print(f"Status: {job.get_status()}")
            print(f"Function: {job.func_name}")
            print(f"Created: {job.created_at}")
            print(f"Started: {job.started_at}")
            
            if job.started_at and job.created_at:
                duration = datetime.utcnow() - job.started_at.replace(tzinfo=None)
                print(f"Duration: {duration.total_seconds()/60:.1f} minutes")
            
            print(f"\nMeta data:")
            for key, value in job.meta.items():
                if len(str(value)) > 100:
                    print(f"  {key}: {str(value)[:100]}...")
                else:
                    print(f"  {key}: {value}")
                    
            print(f"\nArgs: {job.args[:2] if len(job.args) > 2 else job.args}")
            
        except Exception as e:
            print(f"Error fetching job {job_id}: {e}")
