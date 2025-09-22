#!/usr/bin/env python3
"""
Test the task status endpoint to see what's happening with async jobs
"""

import requests
import time
import json

def test_task_status():
    """Test what task status endpoint returns"""
    
    print("🔍 Testing Task Status Endpoint")
    print("=" * 50)
    
    # First, let's see what active tasks exist
    try:
        # Check Redis for active tasks
        import redis
        r = redis.Redis(host='localhost', port=6380, db=0)
        
        # Get all keys
        keys = r.keys('*')
        print(f"📋 Redis keys found: {len(keys)}")
        
        for key in keys[:10]:  # Show first 10 keys
            key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
            print(f"   - {key_str}")
            
        # Look for task-related keys
        task_keys = [k for k in keys if b'task' in k.lower() or b'job' in k.lower()]
        print(f"📋 Task-related keys: {len(task_keys)}")
        
        for key in task_keys[:5]:
            key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
            print(f"   - {key_str}")
            
            # Try to get the value
            try:
                value = r.get(key)
                if value:
                    value_str = value.decode('utf-8') if isinstance(value, bytes) else str(value)
                    print(f"     Value: {value_str[:100]}...")
            except Exception as e:
                print(f"     Error getting value: {e}")
                
    except Exception as e:
        print(f"❌ Error checking Redis: {e}")
    
    print()
    
    # Test the task status endpoint with a fake task ID
    print("🔍 Testing task status endpoint...")
    
    test_task_id = "test-task-123"
    url = f"http://localhost:8080/casestrainer/api/task_status/{test_task_id}"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"📊 Status: {response.status_code}")
        print(f"📋 Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Error calling task status endpoint: {e}")

def main():
    """Main execution"""
    test_task_status()

if __name__ == "__main__":
    main()
