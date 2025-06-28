#!/usr/bin/env python3
"""
Test script to trigger citation analysis and see backend logging.
"""

import requests
import json
import time

def test_citation_analysis():
    """Test the /api/analyze endpoint with a paragraph containing multiple citations."""
    
    # Backend URL
    base_url = "http://localhost:5000"
    analyze_url = f"{base_url}/casestrainer/api/analyze"
    
    # Test paragraph with multiple citations
    test_data = {
        "type": "text",
        "text": """Zink filed her first appeal after the trial court granted summary judgment to 
the Does. While the appeal was pending, this court decided John Doe A v. 
Washington State Patrol, which rejected a PRA exemption claim for sex offender 
registration records that was materially identical to one of the Does' claims in this 
case. 185 Wn.2d 363, 374 P.3d 63 (2016). Thus, following John Doe A, the Court 
of Appeals here reversed in part and held "that the registration records must be 
released." John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 
(2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. 
App. Oct. 2, 2018) (Doe II) (unpublished),"""
    }
    
    print(f"Testing citation analysis with paragraph containing multiple citations")
    print(f"Sending request to: {analyze_url}")
    
    try:
        # Send the request
        response = requests.post(
            analyze_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response data: {json.dumps(result, indent=2)}")
            
            # Check if we got citations back
            if 'citations' in result:
                citations = result['citations']
                print(f"\nFound {len(citations)} citations:")
                for i, citation in enumerate(citations):
                    print(f"  {i+1}. Citation: {citation.get('citation', 'N/A')}")
                    print(f"     Verified: {citation.get('verified', 'N/A')}")
                    print(f"     URL: {citation.get('url', 'N/A')}")
                    print(f"     Case Name: {citation.get('case_name', 'N/A')}")
                    print()
            else:
                print("No citations found in response")
                
        elif response.status_code == 202:
            # Async processing
            result = response.json()
            print(f"Async processing started: {json.dumps(result, indent=2)}")
            
            if 'task_id' in result:
                task_id = result['task_id']
                print(f"Polling for results with task ID: {task_id}")
                
                # Poll for results
                status_url = f"{base_url}/casestrainer/api/task_status/{task_id}"
                max_attempts = 15  # Increased for longer text
                
                for attempt in range(max_attempts):
                    time.sleep(3)  # Wait 3 seconds between polls
                    
                    status_response = requests.get(status_url, timeout=10)
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        print(f"Status check {attempt + 1}: {status_result.get('status', 'unknown')}")
                        
                        if status_result.get('status') == 'completed':
                            print(f"Final result: {json.dumps(status_result, indent=2)}")
                            
                            # Display citation results
                            if 'results' in status_result:
                                citations = status_result['results']
                                print(f"\nFound {len(citations)} citations:")
                                for i, citation in enumerate(citations):
                                    print(f"  {i+1}. Citation: {citation.get('citation', 'N/A')}")
                                    print(f"     Verified: {citation.get('verified', 'N/A')}")
                                    print(f"     URL: {citation.get('url', 'N/A')}")
                                    print(f"     Case Name: {citation.get('case_name', 'N/A')}")
                                    print(f"     Source: {citation.get('source', 'N/A')}")
                                    print()
                            break
                        elif status_result.get('status') == 'error':
                            print(f"Error: {status_result.get('error', 'Unknown error')}")
                            break
                    else:
                        print(f"Status check failed: {status_response.status_code}")
                        
        else:
            print(f"Error response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_citation_analysis() 