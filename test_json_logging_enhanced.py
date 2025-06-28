#!/usr/bin/env python3
"""
Enhanced test script to verify JSON response logging is working correctly.
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
    
    print("Testing enhanced JSON response logging with legal paragraph...")
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
        # Send the request
        response = requests.post(f"{base_url}/analyze", json=test_data, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        # Parse the response
        response_json = response.json()
        print(f"\nResponse JSON:")
        print(json.dumps(response_json, indent=2))
        
        # Check if we got a task ID (async processing)
        if 'task_id' in response_json:
            task_id = response_json['task_id']
            print(f"\nGot task ID: {task_id}")
            print("Polling for results...")
            
            # Poll for results
            max_attempts = 30
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                print(f"Polling attempt {attempt}/{max_attempts}...")
                
                try:
                    status_response = requests.get(f"{base_url}/task_status/{task_id}", timeout=10)
                    status_json = status_response.json()
                    
                    print(f"Status: {status_json.get('status')}, Progress: {status_json.get('progress', 0)}%")
                    
                    if status_json.get('status') == 'completed':
                        print("\n✅ Task completed successfully!")
                        print(f"Results count: {len(status_json.get('results', []))}")
                        print("\nFinal response JSON:")
                        print(json.dumps(status_json, indent=2))
                        break
                    elif status_json.get('status') == 'failed':
                        print(f"\n❌ Task failed: {status_json.get('error', 'Unknown error')}")
                        break
                    else:
                        # Still processing, wait and try again
                        time.sleep(2)
                        
                except Exception as e:
                    print(f"Error polling status: {e}")
                    time.sleep(2)
            else:
                print(f"\n❌ Timed out waiting for task completion after {max_attempts} attempts")
                
        else:
            # Synchronous response
            print("\n✅ Got synchronous response!")
            print(f"Results count: {len(response_json.get('results', []))}")
            
        print("\n" + "=" * 80)
        print("TEST COMPLETED")
        print("Check the logs for JSON response logging entries:")
        print("- Look for '[JSON_LOGGER]' entries")
        print("- Look for 'JSON RESPONSE BEING SENT TO FRONTEND' entries")
        print("- Look for '[ANALYZE] Response to frontend:' entries")
        print("- Look for '[TASK_STATUS_DEBUG]' entries")
        print("=" * 80)
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"\n❌ Failed to parse JSON response: {e}")
        print(f"Raw response: {response.text}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_json_logging_with_paragraph() 