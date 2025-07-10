#!/usr/bin/env python3
"""
Debug script to see the full production response and understand why no citations are found.
"""

import requests
import json

def debug_production_response():
    """Get the full production response to understand what's happening."""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    test_citation = "Punx v Smithers, 123 Wash. 2d 456, 789 P.2d 123 (1990)"
    
    test_data = {
        "type": "text",
        "text": test_citation
    }
    
    print("🔍 Debugging Production Response")
    print("=" * 50)
    print(f"URL: {base_url}/analyze")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print()
    
    try:
        response = requests.post(f"{base_url}/analyze", json=test_data, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()
        print("Full Response Body:")
        print("-" * 30)
        print(response.text)
        print("-" * 30)
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("\nParsed JSON:")
                print(json.dumps(result, indent=2))
            except:
                print("Could not parse as JSON")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_production_response() 