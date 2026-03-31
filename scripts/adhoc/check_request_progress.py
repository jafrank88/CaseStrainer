#!/usr/bin/env python3
"""
Check specific request progress in Redis
"""

from redis import Redis
import json

def check_request_progress():
    """Check progress for specific request"""
    try:
        r = Redis(host='casestrainer-redis-prod', port=6379, db=0, password='***REDACTED_REDIS_PASSWORD***')
        
        request_id = '46451c80-c086-4f5a-88f3-f0364a23478a'
        print(f'Checking progress for request_id: {request_id}')
        
        data = r.get(f'progress:{request_id}')
        if data:
            progress = json.loads(data)
            print(f'Progress data:')
            for key, value in progress.items():
                print(f'  {key}: {value}')
        else:
            print(f'No data found for {request_id}')
            
        # Also check the task_id that was in the response
        task_id = 'c83e6fb6-5211-40cb-9321-1e5f5c6003b2'
        print(f'\nChecking progress for task_id: {task_id}')
        
        data = r.get(f'progress:{task_id}')
        if data:
            progress = json.loads(data)
            print(f'Progress data:')
            for key, value in progress.items():
                print(f'  {key}: {value}')
        else:
            print(f'No data found for {task_id}')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_request_progress()
