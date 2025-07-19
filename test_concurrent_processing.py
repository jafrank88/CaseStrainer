#!/usr/bin/env python3
"""
Test concurrent processing to see if that's causing the hang
"""

import sys
import os
import time
import threading
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_concurrent_requests():
    """Test multiple concurrent requests to the API"""
    
    print("=== Testing Concurrent Processing ===")
    
    # Test URL
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # Test payload
    payload = {
        "text": "534 F.3d 1290",
        "type": "text"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    def make_request(request_id):
        """Make a single request"""
        print(f"Starting request {request_id}")
        start_time = time.time()
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ Request {request_id} completed in {processing_time:.2f}s - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                citations = data.get('citations', [])
                print(f"   Citations found: {len(citations)}")
                for citation in citations:
                    print(f"   - {citation.get('citation', 'N/A')}: verified={citation.get('verified', False)}")
            else:
                print(f"   Error response: {response.text}")
                
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"❌ Request {request_id} failed after {processing_time:.2f}s: {e}")
    
    # Start multiple concurrent requests
    threads = []
    for i in range(3):
        thread = threading.Thread(target=make_request, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("=== Concurrent test complete ===")

if __name__ == "__main__":
    test_concurrent_requests() 