#!/usr/bin/env python3
"""
Test script to verify JSON response logging is working correctly.
This script will test with the provided paragraph containing legal citations.
"""

import requests
import json
import time
import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_json_logging_with_paragraph():
    """Test JSON response logging with the provided legal paragraph."""
    
    # Base URL for the API
    base_url = "http://localhost:5000/casestrainer/api"
    
    # The test paragraph provided by the user
    test_paragraph = """Zink filed her first appeal after the trial court granted summary judgment to 
the Does. While the appeal was pending, this court decided John Doe A v. 
Washington State Patrol, which rejected a PRA exemption claim for sex offender 
registration records that was materially identical to one of the Does' claims in this 
case. 185 Wn.2d 363, 374 P.3d 63 (2016). Thus, following John Doe A, the Court 
of Appeals here reversed in part and held "that the registration records must be 
released." John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 
(2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. 
App. Oct. 2, 2018) (Doe II) (unpublished),"""
    
    print("Testing JSON response logging with legal paragraph...")
    print("=" * 80)
    print("Test Paragraph:")
    print(test_paragraph)
    print("=" * 80)
    
    # Test the /analyze endpoint with the paragraph
    test_data = {
        "type": "text",
        "text": test_paragraph
    }
    
    print(f"\nMaking request to: {base_url}/analyze")
    print(f"Method: POST")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{base_url}/analyze",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30  # Longer timeout for citation processing
        )
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Content-Type: {response.headers.get('content-type', 'unknown')}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                json_data = response.json()
                print(f"Response Size: {len(json.dumps(json_data))} characters")
                print("\nResponse Preview:")
                print(json.dumps(json_data, indent=2)[:1000] + "..." if len(json.dumps(json_data)) > 1000 else json.dumps(json_data, indent=2))
                
                # Check if it's a task-based response
                if 'task_id' in json_data:
                    print(f"\nTask ID: {json_data['task_id']}")
                    print("This is an async response. Checking task status...")
                    
                    # Wait a moment and check task status
                    time.sleep(2)
                    task_response = requests.get(f"{base_url}/task_status/{json_data['task_id']}")
                    
                    if task_response.status_code == 200:
                        task_data = task_response.json()
                        print(f"Task Status: {task_data.get('status', 'unknown')}")
                        print(f"Task Progress: {task_data.get('progress', 0)}%")
                        
                        if task_data.get('status') == 'completed' and 'results' in task_data:
                            print(f"Found {len(task_data['results'])} citations in results")
                            for i, citation in enumerate(task_data['results'][:3]):  # Show first 3
                                print(f"  Citation {i+1}: {citation.get('citation', 'N/A')}")
                                print(f"    Verified: {citation.get('verified', 'N/A')}")
                                print(f"    Case Name: {citation.get('case_name', 'N/A')}")
                
            except json.JSONDecodeError:
                print("Response is not valid JSON")
                print(f"Raw response: {response.text[:500]}...")
        else:
            print("Response is not JSON")
            print(f"Raw response: {response.text[:500]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 80)
    print("Test completed!")
    print("\nCheck the application logs to see if JSON responses were logged.")
    print("Look for log entries starting with 'JSON RESPONSE BEING SENT TO FRONTEND'")
    print("\nLog files are typically located in:")
    print("- logs/app.log")
    print("- logs/citation_verification_*.log")
    print("\nYou should see logs for:")
    print("1. The initial /analyze response (task_id)")
    print("2. The /task_status response (citation results)")

if __name__ == "__main__":
    test_json_logging_with_paragraph() 