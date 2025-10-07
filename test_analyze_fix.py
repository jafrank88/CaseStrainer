#!/usr/bin/env python3
"""
Quick test of the analyze endpoint to verify the fix.
"""

import requests
import json

def test_analyze_endpoint():
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {
        "type": "text",
        "text": """Five Corners Fam. Farmers v. State, 173 Wn.2d 
296, 306, 268 P.3d 892 (2011) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 
Wn.2d 674, 682, 80 P.3d 598 (2003)); Bostain v. Food Express, Inc., 159 Wn.2d 
700, 716, 153 P.3d 846 (2007) (collecting cases)."""
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        print("Testing analyze endpoint...")
        response = requests.post(url, json=data, headers=headers, timeout=30)

        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: Endpoint is working!")
            result = response.json()
            print(f"Citations found: {len(result.get('citations', []))}")
        else:
            print(f"ERROR: {response.status_code}")
            print(response.text[:500])

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_analyze_endpoint()
