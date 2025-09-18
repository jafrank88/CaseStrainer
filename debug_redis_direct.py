"""
Debug Redis Direct Access
Directly check Redis to see what's happening with async tasks.
"""

import redis
import json
import os
import time

def debug_redis_direct():
    """Debug Redis directly to see task status."""
    
    print("🔍 DEBUGGING REDIS DIRECTLY")
    print("=" * 30)
    
    try:
        redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
        print(f"Connecting to Redis: {redis_url}")
        
        r = redis.from_url(redis_url)
        
        # Test connection
        r.ping()
        print(f"✅ Redis connection successful")
        
        # List all keys
        all_keys = r.keys('*')
        print(f"📋 Total Redis keys: {len(all_keys)}")
        
        # Look for RQ job keys
        rq_keys = r.keys('rq:*')
        print(f"📋 RQ keys: {len(rq_keys)}")
        
        if rq_keys:
            print(f"Recent RQ keys:")
            for key in sorted(rq_keys)[-10:]:  # Show last 10
                key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                print(f"   {key_str}")
        
        # Look for recent job keys
        job_keys = r.keys('rq:job:*')
        print(f"📋 Job keys: {len(job_keys)}")
        
        if job_keys:
            print(f"Recent job keys:")
            recent_jobs = sorted(job_keys)[-5:]  # Show last 5
            
            for key in recent_jobs:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                print(f"\n   Job: {key_str}")
                
                try:
                    # Check if it's a hash
                    job_data = r.hgetall(key)
                    if job_data:
                        print(f"      Hash fields: {list(job_data.keys())}")
                        
                        status = job_data.get(b'status') or job_data.get('status')
                        if status:
                            status_str = status.decode('utf-8') if isinstance(status, bytes) else str(status)
                            print(f"      Status: {status_str}")
                        
                        # Check for result
                        result = job_data.get(b'result') or job_data.get('result')
                        if result:
                            print(f"      Has result: Yes ({len(result)} bytes)")
                        else:
                            print(f"      Has result: No")
                    
                    # Also check if there's a separate result key
                    result_key = f"{key_str}:result"
                    result_data = r.get(result_key)
                    if result_data:
                        print(f"      Separate result key: Yes ({len(result_data)} bytes)")
                        
                except Exception as e:
                    print(f"      Error reading job data: {e}")
        
        # Check queue status
        queue_keys = r.keys('rq:queue:*')
        print(f"\n📋 Queue keys: {len(queue_keys)}")
        
        for queue_key in queue_keys:
            queue_name = queue_key.decode('utf-8') if isinstance(queue_key, bytes) else str(queue_key)
            queue_length = r.llen(queue_key)
            print(f"   {queue_name}: {queue_length} items")
        
        # Check for failed jobs
        failed_keys = r.keys('rq:failed:*')
        print(f"\n📋 Failed job keys: {len(failed_keys)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False

def test_specific_task():
    """Test a specific task ID to see what's happening."""
    
    print(f"\n🎯 TESTING SPECIFIC TASK")
    print("-" * 25)
    
    # Use the task ID from the previous test
    task_id = "f6b9be29-e548-4e4b-a648-35ca3c01faf7"
    
    try:
        redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
        r = redis.from_url(redis_url)
        
        keys_to_check = [
            f'rq:job:{task_id}',
            f'rq:job:{task_id}:result',
            f'task:{task_id}',
            f'result:{task_id}'
        ]
        
        print(f"Checking task: {task_id}")
        
        for key in keys_to_check:
            exists = r.exists(key)
            print(f"   {key}: {'EXISTS' if exists else 'NOT FOUND'}")
            
            if exists:
                # Try to get the data
                try:
                    if ':result' in key:
                        data = r.get(key)
                        if data:
                            print(f"      Data type: string, length: {len(data)}")
                            try:
                                parsed = json.loads(data)
                                print(f"      JSON keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'not dict'}")
                            except:
                                print(f"      Data preview: {str(data)[:100]}...")
                    else:
                        # Try as hash
                        hash_data = r.hgetall(key)
                        if hash_data:
                            print(f"      Hash fields: {list(hash_data.keys())}")
                            
                            status = hash_data.get(b'status') or hash_data.get('status')
                            if status:
                                status_str = status.decode('utf-8') if isinstance(status, bytes) else str(status)
                                print(f"      Status: {status_str}")
                        else:
                            # Try as string
                            string_data = r.get(key)
                            if string_data:
                                print(f"      String data: {str(string_data)[:100]}...")
                                
                except Exception as e:
                    print(f"      Error reading data: {e}")
        
    except Exception as e:
        print(f"❌ Error checking specific task: {e}")

if __name__ == "__main__":
    debug_redis_direct()
    test_specific_task()
