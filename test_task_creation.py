#!/usr/bin/env python3
"""
Test if tasks are being created in Redis properly
"""

import requests
import time

def test_task_creation():
    """Test if tasks are being created in Redis"""
    
    print("TESTING TASK CREATION IN REDIS")
    print("=" * 40)
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Submit a small task (should be immediate)
    print("\n1. Submitting small text (should be immediate)...")
    small_text = "Test citation: 123 U.S. 456 (2023)."
    
    try:
        response = requests.post(
            f"{base_url}/analyze",
            data={'text': small_text, 'type': 'text'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'task_id' in result:
                print(f"   ERROR: Got task_id for small text: {result['task_id']}")
            else:
                print(f"   SUCCESS: Got immediate response with {len(result.get('citations', []))} citations")
        else:
            print(f"   ERROR: {response.status_code}")
            
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Submit a large task (should be async)
    print("\n2. Submitting large text (should be async)...")
    large_text = small_text * 1000  # Repeat to make it large
    
    try:
        response = requests.post(
            f"{base_url}/analyze",
            data={'text': large_text, 'type': 'text'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'task_id' in result:
                task_id = result['task_id']
                print(f"   SUCCESS: Got task_id: {task_id}")
                
                # Check if task exists in Redis
                print("\n3. Checking if task exists in Redis...")
                check_cmd = f'docker exec casestrainer-redis-prod redis-cli -a caseStrainerRedis123123 exists "rq:job:{task_id}"'
                result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
                if result.stdout.strip() == '1':
                    print(f"   Task exists in Redis")
                else:
                    print(f"   Task NOT found in Redis")
                    
                # Check task status
                print("\n4. Checking initial task status...")
                status_response = requests.get(f"{base_url}/task_status/{task_id}", timeout=5)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   Initial status: {status_data.get('status')}")
                else:
                    print(f"   ERROR getting status: {status_response.status_code}")
                    
            else:
                print("   ERROR: Expected task_id for large text")
        else:
            print(f"   ERROR: {response.status_code}")
            
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    import subprocess
    test_task_creation()
