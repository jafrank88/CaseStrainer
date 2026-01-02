#!/usr/bin/env python3
"""
Check specific task status in Redis
"""

import subprocess

def check_task_in_redis(task_id):
    """Check a specific task in Redis"""
    
    print(f"CHECKING TASK {task_id} IN REDIS")
    print("=" * 50)
    
    # Check if task exists
    def redis_cmd(cmd):
        try:
            full_cmd = ['docker', 'exec', 'casestrainer-redis-prod', 'redis-cli', '-a', 'caseStrainerRedis123'] + cmd
            result = subprocess.run(full_cmd, capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error: {e}"
    
    # Check task data
    print("\n1. Task data:")
    task_data = redis_cmd(['hgetall', f'rq:job:{task_id}'])
    print(f"   Task data: {task_data}")
    
    # Check task status
    print("\n2. Task status:")
    status = redis_cmd(['hget', f'rq:job:{task_id}', 'status'])
    print(f"   Status: {status}")
    
    # Check if in any queue
    print("\n3. Queue membership:")
    queues = ['rq:queue:default', 'rq:queue:high', 'rq:queue:low', 'rq:queue:casestrainer']
    for queue in queues:
        in_queue = redis_cmd(['lrange', queue, '0', '-1'])
        if task_id in in_queue:
            print(f"   Found in: {queue}")
    
    # Check registries
    print("\n4. Registry status:")
    registries = ['rq:started', 'rq:failed', 'rq:finished', 'rq:deferred']
    for registry in registries:
        in_registry = redis_cmd(['zrange', registry, '0', '-1'])
        if task_id in in_registry:
            print(f"   Found in: {registry}")
    
    # Check task metadata
    print("\n5. Task metadata:")
    meta_key = f'rq:job:{task_id}:metadata'
    metadata = redis_cmd(['hgetall', meta_key])
    print(f"   Metadata: {metadata}")
    
    print("\nDIAGNOSIS:")
    if not task_data or task_data == "Error: ":
        print("- Task not found in Redis (may have expired)")
    elif status == "queued":
        print("- Task is queued but not being processed")
    elif status == "started":
        print("- Task was started but may be stuck")
    elif status == "finished":
        print("- Task completed but result not retrieved")
    elif status == "failed":
        print("- Task failed")
    else:
        print(f"- Unknown status: {status}")

if __name__ == "__main__":
    # Use the task ID from our test
    task_id = "69c1a18a-dd27-4e88-bcde-bbcd7bcec9cc"
    check_task_in_redis(task_id)
