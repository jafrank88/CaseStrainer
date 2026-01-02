#!/usr/bin/env python3
"""
Test API health and check for processing issues
"""

import requests
import time

def test_api_health():
    """Test the API endpoints to diagnose processing issues"""
    
    print("API HEALTH CHECK")
    print("=" * 30)
    
    base_url = "https://wolf.law.uw.edu/casestrainer"
    
    # Test basic health
    print("\n1. Testing basic health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        print(f"   Health status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # Test a simple text submission
    print("\n2. Testing simple text submission...")
    test_text = "This is a test citation: 123 U.S. 456 (2023)."
    
    try:
        response = requests.post(
            f"{base_url}/api/analyze",
            data={'text': test_text, 'type': 'text'},
            timeout=30
        )
        print(f"   Submit status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Response type: {'Immediate' if 'citations' in result else 'Async'}")
            
            if 'task_id' in result:
                # Async processing
                task_id = result['task_id']
                print(f"   Task ID: {task_id}")
                
                # Check task status
                print("\n3. Checking task status...")
                for i in range(10):  # Check 10 times
                    status_response = requests.get(
                        f"{base_url}/api/task_status/{task_id}",
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        progress = status_data.get('progress', 0)
                        
                        print(f"   Check {i+1}: Status={status}, Progress={progress}%")
                        
                        if status == 'completed':
                            print("   SUCCESS: Task completed")
                            break
                        elif status == 'failed':
                            error = status_data.get('error', 'Unknown error')
                            print(f"   ERROR: Task failed - {error}")
                            break
                        elif status == 'unknown':
                            print("   WARNING: Status is 'unknown' - this may be the issue")
                            
                        time.sleep(2)
                    else:
                        print(f"   ERROR checking status: {status_response.status_code}")
                else:
                    print("   TIMEOUT: Task did not complete in 20 seconds")
            
            elif 'citations' in result:
                # Immediate processing
                citations = result.get('citations', [])
                print(f"   SUCCESS: Immediate processing, {len(citations)} citations found")
            
        else:
            print(f"   ERROR: {response.text}")
    
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test backend directly
    print("\n4. Testing backend container directly...")
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=10)
        print(f"   Local backend status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Local backend: {response.json()}")
    except Exception as e:
        print(f"   Local backend error: {e}")
    
    print("\nDIAGNOSIS:")
    print("- If API health works but task status is 'unknown', check backend logs")
    print("- If submissions timeout, check worker processing")
    print("- If local backend works but remote doesn't, check nginx/proxy")

if __name__ == "__main__":
    test_api_health()
