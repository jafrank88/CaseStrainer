#!/usr/bin/env python3
"""
Simple test to check the API endpoint directly.
"""

import requests
import json
import time

def test_api_simple():
    """Test the API endpoint directly."""
    
    print("=== Simple API Test ===")
    
    # Test case with a valid citation that should trigger immediate response
    test_case = {
        "name": "Valid U.S. citation (should be immediate)",
        "text": "347 U.S. 483"
    }
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    print(f"Testing: {test_case['name']}")
    print(f"Input: {test_case['text']}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{base_url}/analyze",
            json={
                "text": test_case['text'],
                "type": "text"
            },
            timeout=5  # Very short timeout
        )
        
        response_time = time.time() - start_time
        print(f"Response time: {response_time:.2f}s")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('task_id'):
                print("⚠ Async response - task queued")
                print(f"Task ID: {data['task_id']}")
            else:
                print("✅ Immediate response")
                citations = data.get('citations', [])
                print(f"Found {len(citations)} citations:")
                
                for j, citation in enumerate(citations, 1):
                    print(f"\n  Citation {j}:")
                    print(f"    Citation: {citation.get('citation', 'N/A')}")
                    print(f"    Verified: {citation.get('verified', False)}")
                    print(f"    Case Name: {citation.get('case_name', 'None')}")
                    print(f"    Extracted Case Name: {citation.get('extracted_case_name', 'None')}")
                    print(f"    Canonical Case Name: {citation.get('canonical_name', 'None')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_simple() 