#!/usr/bin/env python3
"""
Check specific request ID in Redis
"""

from redis import Redis
import json

def check_specific_request():
    """Check progress for specific request ID"""
    try:
        r = Redis(host='casestrainer-redis-prod', port=6379, db=0, password='caseStrainerRedis123')
        
        request_id = '5e91c494-24c8-40ec-bfb7-0a57d8f00bf1'
        print(f'Checking progress for request_id: {request_id}')
        
        # Check direct key
        data = r.get(f'progress:{request_id}')
        if data:
            progress = json.loads(data)
            print(f'Found progress: {progress}')
        else:
            print(f'No progress data found for progress:{request_id}')
        
        # Check all keys
        all_keys = r.keys('*')
        print(f'\nTotal keys in Redis: {len(all_keys)}')
        
        # Look for any key containing the request_id
        matching_keys = []
        for key in all_keys:
            if request_id.encode() in key:
                matching_keys.append(key)
        
        print(f'Keys containing {request_id}: {len(matching_keys)}')
        for key in matching_keys:
            key_str = key.decode()
            print(f'  {key_str}')
            data = r.get(key)
            if data:
                try:
                    progress = json.loads(data)
                    print(f'    Progress: {progress.get(\"progress\", 0)}% - {progress.get(\"message\", \"\")}')
                except:
                    print(f'    Raw data: {data[:100]}...')
        
        # Also check the most recent keys
        print(f'\nLast 5 progress keys:')
        progress_keys = [k for k in all_keys if k.startswith(b'progress:')]
        for key in progress_keys[-5:]:
            key_str = key.decode()
            print(f'  {key_str}')
            data = r.get(key)
            if data:
                try:
                    progress = json.loads(data)
                    print(f'    Progress: {progress.get(\"progress\", 0)}% - {progress.get(\"message\", \"\")}')
                except:
                    print(f'    Raw data: {data[:100]}...')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_specific_request()
