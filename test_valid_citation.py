#!/usr/bin/env python3
"""
Test to verify that valid citations are processed quickly and return both case names.
"""

import requests
import json
import time

def test_valid_citations():
    """Test valid citations to ensure they're processed quickly."""
    
    print("=== Testing Valid Citations ===")
    
    # Test cases with valid citations
    test_cases = [
        {
            "name": "Valid L.Ed.2d citation",
            "text": "95 L.Ed.2d 123"
        },
        {
            "name": "Valid U.S. citation with context",
            "text": "In Brown v. Board of Education, 347 U.S. 483 (1954), the Court held that separate educational facilities are inherently unequal."
        },
        {
            "name": "Valid F.3d citation",
            "text": "534 F.3d 1290"
        }
    ]
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Input: {test_case['text']}")
        
        start_time = time.time()
        
        try:
            # Make request to analyze endpoint
            response = requests.post(
                f"{base_url}/analyze",
                data={
                    "type": "text",
                    "text": test_case["text"]
                },
                timeout=30
            )
            
            elapsed = time.time() - start_time
            print(f"Response time: {elapsed:.2f}s")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if it's an immediate response or async
                if "citations" in result:
                    print("✓ Immediate response received")
                    citations = result["citations"]
                    
                    for j, citation in enumerate(citations, 1):
                        print(f"\n  Citation {j}:")
                        print(f"    Citation: {citation.get('citation', 'N/A')}")
                        print(f"    Verified: {citation.get('verified', False)}")
                        print(f"    Case Name: {citation.get('case_name', 'None')}")
                        print(f"    Extracted Case Name: {citation.get('extracted_case_name', 'None')}")
                        print(f"    Canonical Case Name: {citation.get('canonical_name', 'None')}")
                        print(f"    Source: {citation.get('source', 'None')}")
                        print(f"    Processing Time: {citation.get('metadata', {}).get('processing_time', 'N/A')}")
                        
                elif "task_id" in result:
                    print("⚠ Async response - task queued")
                    print(f"Task ID: {result['task_id']}")
                    
                    # Poll for results
                    task_id = result["task_id"]
                    max_wait = 60  # seconds
                    poll_interval = 2  # seconds
                    
                    for attempt in range(max_wait // poll_interval):
                        time.sleep(poll_interval)
                        
                        status_response = requests.get(f"{base_url}/task_status/{task_id}")
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            
                            if status_result.get("status") == "completed":
                                print("✓ Async task completed")
                                citations = status_result.get("citations", [])
                                
                                for j, citation in enumerate(citations, 1):
                                    print(f"\n  Citation {j}:")
                                    print(f"    Citation: {citation.get('citation', 'N/A')}")
                                    print(f"    Verified: {citation.get('verified', False)}")
                                    print(f"    Case Name: {citation.get('case_name', 'None')}")
                                    print(f"    Extracted Case Name: {citation.get('extracted_case_name', 'None')}")
                                    print(f"    Canonical Case Name: {citation.get('canonical_name', 'None')}")
                                    print(f"    Source: {citation.get('source', 'None')}")
                                break
                            elif status_result.get("status") == "failed":
                                print(f"✗ Async task failed: {status_result.get('error', 'Unknown error')}")
                                break
                        else:
                            print(f"✗ Error checking task status: {status_response.status_code}")
                            break
                    else:
                        print("✗ Task timed out")
                        
            else:
                print(f"✗ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"✗ Request timed out after {time.time() - start_time:.2f}s")
        except Exception as e:
            print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_valid_citations() 