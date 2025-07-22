#!/usr/bin/env python3
"""
Test script to simulate frontend API call and verify response structure
"""

import requests
import json

def test_frontend_api_call():
    """Test the API call that the frontend makes."""
    
    # Simulate the frontend API call
    url = "http://localhost:5000/casestrainer/api/analyze"
    payload = {
        "text": "534 F.3d 1290",
        "type": "text"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("Testing frontend API call...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("-" * 50)
        
        if response.status_code == 200:
            data = response.json()
            print("Response Data:")
            print(json.dumps(data, indent=2))
            
            # Check if response has the structure expected by frontend
            print("\n" + "=" * 50)
            print("FRONTEND NAVIGATION ANALYSIS:")
            print("=" * 50)
            
            # Check for task_id (async processing)
            if 'task_id' in data:
                print("✅ Has task_id - Frontend will navigate to polling page")
                print(f"   task_id: {data['task_id']}")
                print(f"   status: {data.get('status', 'unknown')}")
            else:
                print("❌ No task_id - Frontend should navigate to results page")
                
                # Check for citations (immediate results)
                if 'citations' in data:
                    print(f"✅ Has citations array with {len(data['citations'])} citations")
                    if len(data['citations']) > 0:
                        print(f"   First citation: {data['citations'][0].get('citation', 'N/A')}")
                        print(f"   Verified: {data['citations'][0].get('verified', 'N/A')}")
                        print(f"   Canonical name: {data['citations'][0].get('canonical_name', 'N/A')}")
                    else:
                        print("   ⚠️  Citations array is empty")
                else:
                    print("❌ No citations array in response")
                
                # Check for success flag
                if 'success' in data:
                    print(f"✅ Has success flag: {data['success']}")
                else:
                    print("❌ No success flag in response")
                    
                # Check for clusters
                if 'clusters' in data:
                    print(f"✅ Has clusters array with {len(data['clusters'])} clusters")
                else:
                    print("❌ No clusters array in response")
                    
            print("\n" + "=" * 50)
            print("FRONTEND NAVIGATION DECISION:")
            print("=" * 50)
            
            if 'task_id' in data:
                print("Frontend should navigate to: /enhanced-validator?task_id=<task_id>")
                print("This will start polling for results.")
            elif 'citations' in data and len(data['citations']) > 0:
                print("Frontend should navigate to: /enhanced-validator")
                print("With state containing the results.")
                print("This should show the results immediately.")
            else:
                print("⚠️  Frontend might not navigate - no task_id or citations found")
                
        else:
            print(f"❌ Error response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_frontend_api_call() 