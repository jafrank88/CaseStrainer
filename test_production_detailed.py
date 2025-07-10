#!/usr/bin/env python3
"""
Detailed test to see the full production response and debug extraction issues.
"""

import requests
import json

def test_production_detailed():
    """Get detailed production response to debug extraction issues."""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    test_citation = "Punx v Smithers, 123 Wash. 2d 456, 789 P.2d 123 (1990)"
    
    test_data = {
        "type": "text",
        "text": test_citation
    }
    
    print("🔍 Detailed Production Test")
    print("=" * 50)
    print(f"URL: {base_url}/analyze")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print()
    
    try:
        print("📡 Sending request...")
        response = requests.post(f"{base_url}/analyze", json=test_data, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()
        print("Full Response:")
        print("-" * 30)
        print(response.text)
        print("-" * 30)
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("\nParsed JSON:")
                print(json.dumps(result, indent=2))
                
                # Check for specific fields
                print(f"\nKey Fields:")
                print(f"  Status: {result.get('status')}")
                print(f"  Message: {result.get('message')}")
                print(f"  Citations count: {len(result.get('citations', []))}")
                print(f"  Task ID: {result.get('task_id')}")
                
            except Exception as e:
                print(f"JSON parse error: {e}")
        
    except Exception as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    test_production_detailed() 