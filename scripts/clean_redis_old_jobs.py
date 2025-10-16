"""
Clean old RQ jobs from Redis to reduce startup time
"""
import redis
import os
from datetime import datetime, timedelta
from rq import Queue
from rq.job import Job
from rq.registry import (
    StartedJobRegistry,
    FinishedJobRegistry,
    FailedJobRegistry,
    DeferredJobRegistry,
    ScheduledJobRegistry,
    CanceledJobRegistry
)

# Connect to Redis
redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
r = redis.from_url(redis_url)

print("="*80)
print("REDIS JOB CLEANUP")
print("="*80)

# Get current stats
info = r.info('keyspace')
print(f"\n📊 Current Redis stats:")
print(f"   Total keys: {r.dbsize()}")
print(f"   Memory: {r.info('memory')['used_memory_human']}")

# Get all queues
queue_names = ['default', 'high', 'low']
print(f"\n🔍 Checking queues: {', '.join(queue_names)}")

total_cleaned = 0
keep_days = 7  # Keep jobs from last 7 days

for queue_name in queue_names:
    try:
        queue = Queue(queue_name, connection=r)
        
        # Clean finished jobs older than keep_days
        finished = FinishedJobRegistry(queue_name, connection=r)
        finished_ids = finished.get_job_ids()
        
        cleaned_finished = 0
        cutoff_time = datetime.now() - timedelta(days=keep_days)
        
        for job_id in finished_ids:
            try:
                job = Job.fetch(job_id, connection=r)
                if job.ended_at and job.ended_at < cutoff_time:
                    job.delete()
                    cleaned_finished += 1
            except:
                pass
        
        # Clean failed jobs older than keep_days
        failed = FailedJobRegistry(queue_name, connection=r)
        failed_ids = failed.get_job_ids()
        
        cleaned_failed = 0
        for job_id in failed_ids:
            try:
                job = Job.fetch(job_id, connection=r)
                if job.ended_at and job.ended_at < cutoff_time:
                    job.delete()
                    cleaned_failed += 1
            except:
                pass
        
        # Clean canceled jobs
        try:
            canceled = CanceledJobRegistry(queue_name, connection=r)
            canceled_ids = canceled.get_job_ids()
            for job_id in canceled_ids[:100]:  # Clean up to 100
                try:
                    job = Job.fetch(job_id, connection=r)
                    job.delete()
                except:
                    pass
            cleaned_canceled = len(canceled_ids[:100])
        except:
            cleaned_canceled = 0
        
        queue_total = cleaned_finished + cleaned_failed + cleaned_canceled
        total_cleaned += queue_total
        
        if queue_total > 0:
            print(f"\n✅ Queue '{queue_name}':")
            print(f"   Cleaned {cleaned_finished} finished jobs (older than {keep_days} days)")
            print(f"   Cleaned {cleaned_failed} failed jobs (older than {keep_days} days)")
            if cleaned_canceled > 0:
                print(f"   Cleaned {cleaned_canceled} canceled jobs")
        
    except Exception as e:
        print(f"\n⚠️  Error cleaning queue '{queue_name}': {e}")

# Final stats
print(f"\n📊 After cleanup:")
print(f"   Total keys: {r.dbsize()}")
print(f"   Memory: {r.info('memory')['used_memory_human']}")
print(f"   Cleaned: {total_cleaned} jobs")

print(f"\n{'='*80}")
print(f"✅ CLEANUP COMPLETE")
print(f"   Removed {total_cleaned} old jobs")
print(f"   Kept jobs from last {keep_days} days")
print(f"{'='*80}")
