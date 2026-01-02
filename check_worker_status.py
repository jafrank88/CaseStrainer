#!/usr/bin/env python3
"""
Check worker status and find any stuck tasks
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import redis
import json

def check_worker_status():
    """Check RQ worker status and find any stuck tasks."""
    
    # Connect to Redis (using localhost with mapped port)
    r = redis.Redis(
        host='localhost',
        port=6380,
        password='caseStrainerRedis123',
        decode_responses=True
    )
    
    print("=== RQ Worker Status Check ===\n")
    
    try:
        # Check queue length
        queue_len = r.llen('rq:queue:casestrainer')
        print(f"📋 Queue length: {queue_len}")
        
        # Check all Redis keys
        all_keys = r.keys('*')
        rq_keys = [k for k in all_keys if 'rq:' in k or 'verification:' in k]
        
        print(f"\n🔍 Found {len(rq_keys)} RQ/verification related keys:")
        for key in sorted(rq_keys):
            try:
                key_type = r.type(key)
                if key_type == 'list':
                    length = r.llen(key)
                    print(f"  📝 {key} (list, {length} items)")
                    if length > 0 and length < 5:
                        # Show contents for small lists
                        items = r.lrange(key, 0, -1)
                        for i, item in enumerate(items):
                            try:
                                data = json.loads(item)
                                print(f"    [{i}] {json.dumps(data, indent=2)[:200]}...")
                            except:
                                print(f"    [{i}] {item[:100]}...")
                elif key_type == 'string':
                    value = r.get(key)
                    print(f"  📄 {key} (string, {len(value)} chars)")
                    try:
                        data = json.loads(value)
                        print(f"    Content: {json.dumps(data, indent=2)[:300]}...")
                    except:
                        print(f"    Content: {value[:100]}...")
                elif key_type == 'hash':
                    hash_len = r.hlen(key)
                    print(f"  🔧 {key} (hash, {hash_len} fields)")
                else:
                    print(f"  ❓ {key} ({key_type})")
            except Exception as e:
                print(f"  ❌ Error checking {key}: {e}")
        
        # Check for specific task IDs from our tests
        test_task_ids = [
            "724420ea-5c37-401c-899a-302ea1206433",
            "57d6da6a-ee2f-4443-b4e1-880c892c149d",
            "d018066d-0553-4154-8174-98a29ac3c869"
        ]
        
        print(f"\n🔍 Checking specific test task IDs:")
        for task_id in test_task_ids:
            status_key = f"verification:status:{task_id}"
            if r.exists(status_key):
                status = r.get(status_key)
                try:
                    status_data = json.loads(status)
                    print(f"  ✅ {task_id}: {status_data.get('state', 'unknown')} - {status_data.get('current_message', 'no message')}")
                except:
                    print(f"  ❓ {task_id}: {status[:100]}")
            else:
                print(f"  ❌ {task_id}: not found")
        
        # Check worker registry
        print(f"\n👥 Worker Registry:")
        workers = r.smembers('rq:workers')
        for worker in workers:
            print(f"  👤 {worker}")
            # Check worker heartbeat
            heartbeat_key = f"rq:worker:{worker}:heartbeat"
            if r.exists(heartbeat_key):
                heartbeat = r.get(heartbeat_key)
                print(f"    💓 Last heartbeat: {heartbeat}")
        
    except Exception as e:
        print(f"❌ Error checking Redis: {e}")

if __name__ == "__main__":
    check_worker_status()
