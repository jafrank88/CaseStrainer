#!/usr/bin/env python3
"""
Test script for the API endpoint.
"""

import requests
import json

def test_api():
    """Test the API endpoint."""
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    data = {
        "text": "Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015). Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018)."
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("🚀 Testing API endpoint...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Error! Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_api()