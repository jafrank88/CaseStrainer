#!/usr/bin/env python3
"""
Debug script to test citation verification result structure
"""

import json
import requests
import time

def test_verification_structure():
    """Test the verification result structure to understand the discrepancy"""
    
    # Test citation that should be verified
    test_citation = "90 Wn.2d 9"
    
    print(f"Testing citation: {test_citation}")
    print("=" * 50)
    
    # Make request to the API
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {
        "type": "text",
        "text": f"This case cites {test_citation} as authority."
    }
    
    try:
        print("Sending request to API...")
        response = requests.post(url, json=data, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response structure: {json.dumps(result, indent=2)}")
            
            # Check if we got a task ID (async processing)
            if result.get('status') == 'processing' and 'task_id' in result:
                task_id = result['task_id']
                print(f"Got task ID: {task_id}")
                
                # Poll for results
                for i in range(30):  # Wait up to 30 seconds
                    time.sleep(1)
                    status_response = requests.get(f"http://localhost:5000/casestrainer/api/task_status/{task_id}")
                    
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        print(f"Status check {i+1}: {status_result.get('status')}")
                        
                        if status_result.get('status') == 'completed':
                            citations = status_result.get('citations', [])
                            print(f"Found {len(citations)} citations")
                            
                            for j, citation in enumerate(citations):
                                print(f"\nCitation {j+1}:")
                                print(f"  Citation text: {citation.get('citation', 'N/A')}")
                                print(f"  Valid: {citation.get('valid', 'N/A')}")
                                print(f"  Verified: {citation.get('verified', 'N/A')}")
                                print(f"  Found: {citation.get('found', 'N/A')}")
                                print(f"  Data field: {citation.get('data', 'N/A')}")
                                
                                # Check what the frontend would see
                                frontend_verified = (
                                    citation.get('valid') or 
                                    citation.get('verified') or 
                                    citation.get('data', {}).get('valid') or 
                                    citation.get('data', {}).get('found') or 
                                    citation.get('exists')
                                )
                                print(f"  Frontend would see as verified: {frontend_verified}")
                                
                                # Show full citation structure
                                print(f"  Full structure: {json.dumps(citation, indent=4)}")
                            
                            break
                        elif status_result.get('status') == 'failed':
                            print(f"Task failed: {status_result.get('error', 'Unknown error')}")
                            break
                else:
                    print("Timeout waiting for task completion")
            else:
                print("Unexpected response format")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_verification_structure() 