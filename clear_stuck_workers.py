#!/usr/bin/env python3
"""
Clear stuck RQ jobs to unblock workers
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import redis
import json

def clear_stuck_jobs():
    """Clear stuck jobs from RQ queues."""
    
    # Connect to Redis
    r = redis.Redis(
        host='localhost',
        port=6380,
        password='***REDACTED_REDIS_PASSWORD***',
        decode_responses=True
    )
    
    print("=== Clearing Stuck RQ Jobs ===\n")
    
    try:
        # Check worker-in-progress queue
        wip_jobs = r.zrange('rq:wip:casestrainer', 0, -1)
        print(f"📋 Found {len(wip_jobs)} jobs in worker-in-progress queue:")
        
        for job in wip_jobs:
            print(f"  🔄 {job}")
        
        # Clear the WIP queue
        cleared = r.delete('rq:wip:casestrainer')
        print(f"\n✅ Cleared {cleared} jobs from WIP queue")
        
        # Also clear stuck verification statuses
        verification_keys = r.keys('verification:status:*')
        stuck_keys = []
        
        for key in verification_keys:
            try:
                status = json.loads(r.get(key))
                if status.get('state') == 'running' and status.get('progress_percent', 0) >= 70:
                    stuck_keys.append(key)
            except:
                pass
        
        print(f"\n📋 Found {len(stuck_keys)} stuck verification statuses:")
        for key in stuck_keys:
            try:
                # Mark as failed instead of deleting
                status = json.loads(r.get(key))
                status['state'] = 'failed'
                status['current_message'] = 'Task cleared due to timeout'
                r.set(key, json.dumps(status))
                print(f"  ❌ {key} -> marked as failed")
            except Exception as e:
                print(f"  ❌ Error clearing {key}: {e}")
        
        # Check final queue status
        queue_len = r.llen('rq:queue:casestrainer')
        wip_len = r.zcard('rq:wip:casestrainer')
        
        print(f"\n📊 Final Status:")
        print(f"  Queue length: {queue_len}")
        print(f"  WIP jobs: {wip_len}")
        print(f"  Cleared verifications: {len(stuck_keys)}")
        
        print("\n✅ Workers should now be unblocked!")
        
    except Exception as e:
        print(f"❌ Error clearing jobs: {e}")

if __name__ == "__main__":
    clear_stuck_jobs()
