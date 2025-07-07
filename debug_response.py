#!/usr/bin/env python3
"""
Debug script to see exactly what the clean server returns
"""

import requests
import json

def debug_response():
    """Test the clean server and see the exact response"""
    
    # Simple test text with one citation
    test_text = "The court in Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, held that..."
    
    print("Testing clean server response...")
    
    try:
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json={"text": test_text, "source": "Test"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n=== FULL RESPONSE ===")
            print(json.dumps(data, indent=2))
            
            print("\n=== RESPONSE ANALYSIS ===")
            print(f"Keys in response: {list(data.keys())}")
            
            if 'citations' in data:
                citations = data['citations']
                print(f"Citations type: {type(citations)}")
                print(f"Citations length: {len(citations)}")
                if citations:
                    print(f"First citation: {citations[0]}")
            else:
                print("No 'citations' key found")
                
            if 'task_id' in data:
                task_id = data['task_id']
                print(f"Task ID: {task_id}")
                
                # Check task status
                status_response = requests.get(f"http://localhost:5000/casestrainer/api/task_status/{task_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"\n=== TASK STATUS ===")
                    print(json.dumps(status_data, indent=2))
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_response() 