#!/usr/bin/env python3
"""
Debug script to test async task processing and identify where results are lost.
"""

import requests
import json
import time
import sys
import os

def test_async_task_with_debug():
    """Test async task processing with detailed debugging."""
    print("=== Testing Async Task Processing with Debug ===\n")
    
    test_url = "https://supreme.justia.com/cases/federal/us/410/113/"
    
    try:
        # Submit async task
        payload = {
            "type": "url",
            "url": test_url
        }
        
        print(f"1. Submitting URL: {test_url}")
        response = requests.post(
            "http://127.0.0.1:5000/casestrainer/api/analyze",
            json=payload,
            timeout=10
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Submit response: {json.dumps(data, indent=2)}")
            
            if 'task_id' in data:
                task_id = data['task_id']
                print(f"\n2. Task ID: {task_id}")
                
                # Poll for task status with detailed logging
                print("\n3. Polling task status...")
                for i in range(15):  # Poll for up to 15 iterations
                    time.sleep(2)
                    
                    print(f"\n   Poll {i+1}:")
                    status_response = requests.get(
                        f"http://127.0.0.1:5000/casestrainer/api/task_status/{task_id}",
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"     Status: {status_data.get('status', 'unknown')}")
                        print(f"     Progress: {status_data.get('progress', 0)}%")
                        print(f"     Results count: {len(status_data.get('results', []))}")
                        print(f"     Current step: {status_data.get('current_step', 'unknown')}")
                        
                        # Check if results are present in the response
                        if 'results' in status_data:
                            results = status_data['results']
                            print(f"     Results array length: {len(results)}")
                            if results:
                                print(f"     First result: {results[0].get('citation', 'N/A')}")
                            else:
                                print(f"     Results array is empty!")
                        
                        if status_data.get('status') == 'completed':
                            print(f"\n4. Task completed!")
                            print(f"   Final results count: {len(status_data.get('results', []))}")
                            
                            if status_data.get('results'):
                                print(f"\n5. Results found:")
                                for j, result in enumerate(status_data['results']):
                                    print(f"   Result {j+1}: {result.get('citation', 'N/A')} -> {result.get('verified', 'N/A')}")
                            else:
                                print(f"\n5. ❌ NO RESULTS FOUND!")
                                print(f"   Full status response:")
                                print(json.dumps(status_data, indent=2))
                            break
                    else:
                        print(f"     ❌ Status check failed: {status_response.status_code}")
                        print(f"     Response: {status_response.text}")
                        break
            else:
                print("❌ No task_id in response")
                print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Task submission failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Async task test error: {e}")
        import traceback
        traceback.print_exc()

def test_direct_vs_async():
    """Compare direct processing vs async processing."""
    print("\n=== Comparing Direct vs Async Processing ===\n")
    
    test_citation = "410 U.S. 113"
    
    # Test 1: Direct processing
    print("1. Testing direct processing...")
    try:
        payload = {
            "type": "text",
            "text": test_citation
        }
        
        response = requests.post(
            "http://127.0.0.1:5000/casestrainer/api/analyze",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            citations = data.get('citations', [])
            print(f"   Direct processing found {len(citations)} citations")
            for citation in citations:
                print(f"     {citation.get('citation', 'N/A')} -> {citation.get('verified', 'N/A')}")
        else:
            print(f"   Direct processing failed: {response.status_code}")
    except Exception as e:
        print(f"   Direct processing error: {e}")
    
    # Test 2: Async processing with same content
    print("\n2. Testing async processing with same content...")
    try:
        payload = {
            "type": "text",
            "text": test_citation
        }
        
        response = requests.post(
            "http://127.0.0.1:5000/casestrainer/api/analyze",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'task_id' in data:
                task_id = data['task_id']
                print(f"   Async task ID: {task_id}")
                
                # Wait for completion
                for i in range(10):
                    time.sleep(2)
                    status_response = requests.get(
                        f"http://127.0.0.1:5000/casestrainer/api/task_status/{task_id}",
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('status') == 'completed':
                            results = status_data.get('results', [])
                            print(f"   Async processing found {len(results)} citations")
                            for result in results:
                                print(f"     {result.get('citation', 'N/A')} -> {result.get('verified', 'N/A')}")
                            break
            else:
                print("   No task_id in async response")
        else:
            print(f"   Async processing failed: {response.status_code}")
    except Exception as e:
        print(f"   Async processing error: {e}")

def main():
    """Run all debug tests."""
    print("=== CaseStrainer Async Results Debug ===\n")
    
    # Test 1: Async task with debug
    test_async_task_with_debug()
    
    # Test 2: Compare direct vs async
    test_direct_vs_async()
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    main() 