"""
Cleanup stuck RQ jobs and stale worker registrations
Called automatically by cslaunch to prevent job queue issues
"""
import redis
from rq import Queue, Worker
from rq.job import Job
from rq.registry import StartedJobRegistry
import os
import sys
from datetime import datetime, timedelta

def cleanup_stuck_jobs(max_age_minutes=10):
    """
    Clean up jobs that have been in 'started' state for too long.
    
    Args:
        max_age_minutes: Jobs older than this are considered stuck
        
    Returns:
        Number of jobs cleaned up
    """
    try:
        redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
        r = redis.from_url(redis_url)
        q = Queue('casestrainer', connection=r)
        
        started_registry = StartedJobRegistry(queue=q)
        
        if started_registry.count == 0:
            print("✅ No stuck jobs found")
            return 0
        
        print(f"🔍 Checking {started_registry.count} started job(s)...")
        
        stuck_count = 0
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        
        for job_id in started_registry.get_job_ids():
            try:
                job = Job.fetch(job_id, connection=r)
                
                # Check if job is truly stuck (created more than max_age_minutes ago)
                if job.created_at and job.created_at.replace(tzinfo=None) < cutoff_time:
                    print(f"  🧹 Cleaning stuck job {job_id[:8]}... (age: {datetime.utcnow() - job.created_at.replace(tzinfo=None)})")
                    
                    # Force cleanup: Remove from started registry and delete job data
                    try:
                        # Remove from started registry (it's a sorted set in Redis)
                        started_key = f'rq:wip:{q.name}'
                        r.zrem(started_key, job_id)
                        
                        # Delete job data
                        job_key = f'rq:job:{job_id}'
                        r.delete(job_key)
                        
                        # Delete progress data if it exists
                        progress_key = f'job_progress:{job_id}'
                        r.delete(progress_key)
                        
                        stuck_count += 1
                    except Exception as delete_error:
                        print(f"    ⚠️  Force delete failed: {delete_error}")
                        # Fallback to regular delete
                        try:
                            job.cancel()
                            job.delete()
                        except:
                            pass
                else:
                    age_minutes = (datetime.utcnow() - job.created_at.replace(tzinfo=None)).total_seconds() / 60
                    print(f"  ⏳ Job {job_id[:8]}... still processing ({age_minutes:.1f}m old)")
                    
            except Exception as e:
                print(f"  ⚠️  Error processing job {job_id[:8]}: {e}")
        
        if stuck_count > 0:
            print(f"\n✅ Cleaned {stuck_count} stuck job(s)")
        else:
            print(f"\n✅ All jobs are processing normally")
            
        return stuck_count
        
    except redis.exceptions.ConnectionError:
        print("⚠️  Redis not available - skipping cleanup (containers may not be running)")
        return 0
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return 0

def cleanup_stale_workers():
    """
    Clean up stale worker registrations that prevent workers from starting.
    This happens after container restarts when old registrations persist in Redis.
    """
    try:
        redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
        r = redis.from_url(redis_url)
        
        # Get all registered workers
        workers = Worker.all(connection=r)
        
        if not workers:
            print("✅ No worker registrations found")
            return 0
        
        print(f"🔍 Checking {len(workers)} worker registration(s)...")
        
        cleaned_count = 0
        for worker in workers:
            try:
                # Check if worker is actually alive
                # Workers should heartbeat every 30 seconds
                # If last heartbeat was > 2 minutes ago, consider it dead
                if hasattr(worker, 'last_heartbeat'):
                    time_since_heartbeat = (datetime.utcnow() - worker.last_heartbeat.replace(tzinfo=None)).total_seconds()
                    
                    if time_since_heartbeat > 120:  # 2 minutes
                        print(f"  🧹 Removing stale worker: {worker.name} (last seen {int(time_since_heartbeat)}s ago)")
                        worker.register_death()
                        cleaned_count += 1
                    else:
                        print(f"  ✅ Worker {worker.name} is active (heartbeat {int(time_since_heartbeat)}s ago)")
                else:
                    # No heartbeat info, check if state is 'busy' or 'idle'
                    state = worker.get_state()
                    if state not in ['busy', 'idle']:
                        print(f"  🧹 Removing inactive worker: {worker.name} (state: {state})")
                        worker.register_death()
                        cleaned_count += 1
                        
            except Exception as e:
                print(f"  ⚠️  Error checking worker {worker.name}: {e}")
        
        if cleaned_count > 0:
            print(f"\n✅ Cleaned {cleaned_count} stale worker registration(s)")
        else:
            print(f"\n✅ All worker registrations are valid")
            
        return cleaned_count
        
    except redis.exceptions.ConnectionError:
        print("⚠️  Redis not available - skipping worker cleanup")
        return 0
    except Exception as e:
        print(f"❌ Error during worker cleanup: {e}")
        return 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Cleanup stuck RQ jobs')
    parser.add_argument('--max-age', type=int, default=10, 
                       help='Max age in minutes before job is considered stuck (default: 10)')
    parser.add_argument('--force', action='store_true',
                       help='Force cleanup of all started jobs regardless of age')
    
    args = parser.parse_args()
    
    if args.force:
        max_age = 0
        print("🔥 FORCE MODE: Cleaning ALL started jobs...")
    else:
        max_age = args.max_age
        print(f"🔍 Cleaning jobs older than {max_age} minutes...")
    
    # Clean up stale worker registrations FIRST (critical for worker startup)
    print("\n" + "="*60)
    print("STEP 1: Cleanup Stale Worker Registrations")
    print("="*60)
    cleanup_stale_workers()
    
    # Then clean up stuck jobs
    print("\n" + "="*60)
    print("STEP 2: Cleanup Stuck Jobs")
    print("="*60)
    count = cleanup_stuck_jobs(max_age_minutes=max_age)
    
    sys.exit(0)  # Always exit successfully to not block deployment
