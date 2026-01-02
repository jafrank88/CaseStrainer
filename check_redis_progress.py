#!/usr/bin/env python3
"""
Check Redis progress storage
"""

from redis import Redis
import json

def check_redis_progress():
    """Check what progress keys are in Redis"""
    try:
        r = Redis(host='casestrainer-redis-prod', port=6379, db=0, password='caseStrainerRedis123')
        
        # Get all progress keys
        keys = r.keys('progress:*')
        print(f'Found {len(keys)} progress keys in Redis:')
        
        for key in keys:
            key_str = key.decode()
            print(f'  Key: {key_str}')
            
            data = r.get(key)
            if data:
                try:
                    progress = json.loads(data)
                    progress_percent = progress.get('progress', 0)
                    message = progress.get('message', '')
                    status = progress.get('status', '')
                    print(f'    Progress: {progress_percent}% - {status} - {message}')
                except json.JSONDecodeError:
                    print(f'    Raw data: {data[:100]}...')
            else:
                print(f'    No data')
        
        # Also check for any other keys that might contain progress
        all_keys = r.keys('*')
        progress_related = [k for k in all_keys if b'progress' in k.lower()]
        print(f'\nFound {len(progress_related)} progress-related keys total:')
        for key in progress_related:
            print(f'  {key.decode()}')
            
    except Exception as e:
        print(f'Error checking Redis: {e}')

if __name__ == "__main__":
    check_redis_progress()
