#!/usr/bin/env python3
"""
Simple test for the process-text endpoint
"""

import requests
import json

def test_process_text():
    url = "http://localhost:5000/casestrainer/api/process-text"
    
    # Simple test data
    data = {
        "text": "See State v. Lewis, 115 Wn.2d 294, 298-99, 797 P.2d 1141 (1990).",
        "extract_case_names": True,
        "include_context": True
    }
    
    print(f"Testing: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_process_text() 