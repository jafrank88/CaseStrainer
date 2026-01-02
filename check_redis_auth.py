#!/usr/bin/env python3
"""
Check Redis queue status for stuck jobs (Docker with auth)
"""

import subprocess
import json
from datetime import datetime

def run_redis_command(cmd):
    """Run a Redis command in Docker with auth"""
    try:
        # First authenticate, then run the command
        auth_cmd = ['docker', 'exec', 'casestrainer-redis-prod', 'redis-cli', '-a', '***REDACTED_REDIS_PASSWORD***']
        full_cmd = auth_cmd + cmd
        
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def check_redis_docker_status():
    """Check Redis for stuck jobs via Docker"""
    
    print("REDIS QUEUE STATUS CHECK (DOCKER WITH AUTH)")
    print("=" * 50)
    
    # Test Redis connection
    ping = run_redis_command(['ping'])
    print(f"Redis connection: {ping}")
    
    if ping != "PONG":
        print("Redis is not responding")
        return
    
    # Check queues
    print("\nQueue Status:")
    queues = ['rq:queue:default', 'rq:queue:high', 'rq:queue:low']
    for queue in queues:
        length = run_redis_command(['llen', queue])
        print(f"  {queue.split(':')[-1]}: {length} jobs")
    
    # Check worker status
    print("\nWorker Status:")
    workers = run_redis_command(['smembers', 'rq:workers'])
    if workers and workers != "Error: ":
        worker_list = workers.split('\n')
        print(f"  Active workers: {len(worker_list)}")
        for worker in worker_list:
            if worker:
                print(f"    - {worker}")
    else:
        print("  No active workers found")
    
    # Check failed jobs
    print("\nFailed Jobs:")
    failed = run_redis_command(['zcard', 'rq:failed'])
    print(f"  Failed jobs: {failed}")
    
    if failed != "0" and failed != "Error: ":
        # Get recent failed jobs
        recent_failed = run_redis_command(['zrange', 'rq:failed', '-5', '-1', 'WITHSCORES'])
        if recent_failed and recent_failed != "Error: ":
            lines = recent_failed.split('\n')
            for i in range(0, len(lines), 2):
                if i+1 < len(lines):
                    job_id = lines[i]
                    timestamp = lines[i+1]
                    print(f"    - {job_id}: {datetime.fromtimestamp(float(timestamp))}")
    
    # Check active jobs
    print("\nActive Jobs:")
    started = run_redis_command(['zcard', 'rq:started'])
    print(f"  Started jobs: {started}")
    
    if started != "0" and started != "Error: ":
        # Get active jobs with timestamps
        active_jobs = run_redis_command(['zrange', 'rq:started', '0', '-1', 'WITHSCORES'])
        if active_jobs and active_jobs != "Error: ":
            lines = active_jobs.split('\n')
            for i in range(0, len(lines), 2):
                if i+1 < len(lines):
                    job_id = lines[i]
                    timestamp = float(lines[i+1])
                    age = datetime.now().timestamp() - timestamp
                    print(f"    - {job_id}: {age:.0f}s old")
                    if age > 300:  # 5 minutes
                        print(f"      WARNING: Job running for {age:.0f}s")
    
    # Check scheduled jobs
    print("\nScheduled Jobs:")
    scheduled = run_redis_command(['zcard', 'rq:scheduled'])
    print(f"  Scheduled jobs: {scheduled}")
    
    print("\nTROUBLESHOOTING:")
    print("1. If jobs are stuck in 'started' > 5min: restart workers")
    print("2. If many failed jobs: clear with python clear_stuck_jobs.py")
    print("3. If no workers: restart with ./cslaunch")
    print("4. Check backend logs: docker-compose logs backend")
    print("5. Test API directly: python test_api_health.py")

if __name__ == "__main__":
    check_redis_docker_status()
