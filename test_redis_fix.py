#!/usr/bin/env python3
"""
Test script to verify Redis fix for async task processing
"""

import requests
import time
import json

def test_async_processing():
    """Test async processing with a simple citation"""
    
    # Test data
    test_text = "The court in Smith v. Jones, 123 U.S. 456 (2020) held that..."
    
    print("Testing async processing with Redis fix...")
    print(f"Test text: {test_text[:50]}...")
    
    # Start async processing
    print("\n1. Starting async processing...")
    response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                           json={'type': 'text', 'text': test_text})
    
    if response.status_code != 200:
        print(f"❌ Failed to start processing: {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    print(f"✅ Processing started: {data}")
    
    if 'task_id' not in data:
        print("❌ No task_id returned")
        return False
    
    task_id = data['task_id']
    print(f"Task ID: {task_id}")
    
    # Poll for results
    print("\n2. Polling for results...")
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"   Attempt {attempt}/{max_attempts}...")
        
        try:
            status_response = requests.get(f'http://localhost:5000/casestrainer/api/task_status/{task_id}')
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get('status', 'unknown')
                
                print(f"   Status: {status}")
                
                if status == 'completed':
                    results = status_data.get('results', [])
                    citations = status_data.get('citations', [])
                    case_names = status_data.get('case_names', [])
                    
                    print(f"✅ Processing completed!")
                    print(f"   Results: {len(results)} items")
                    print(f"   Citations: {len(citations)} items")
                    print(f"   Case names: {len(case_names)} items")
                    
                    if results or citations:
                        print("✅ Redis fix working - results returned successfully!")
                        return True
                    else:
                        print("❌ Results empty - Redis fix may not be working")
                        return False
                        
                elif status == 'failed':
                    print(f"❌ Processing failed: {status_data.get('error', 'Unknown error')}")
                    return False
                    
                elif status == 'not_found':
                    print("❌ Task not found")
                    return False
                    
                # Still processing, wait and try again
                time.sleep(2)
                
            else:
                print(f"❌ Status check failed: {status_response.status_code}")
                print(status_response.text)
                return False
                
        except Exception as e:
            print(f"❌ Error checking status: {e}")
            return False
    
    print("❌ Timeout waiting for results")
    return False

if __name__ == "__main__":
    print("Redis Fix Test")
    print("=" * 50)
    
    success = test_async_processing()
    
    if success:
        print("\n🎉 Test PASSED - Redis fix is working!")
    else:
        print("\n💥 Test FAILED - Redis fix needs more work")
    
    print("\nTest completed.") 