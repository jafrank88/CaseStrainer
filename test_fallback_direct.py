#!/usr/bin/env python3
"""
Test script to check fallback functionality directly.
"""

import requests
import json

def test_fallback():
    """Test the fallback functionality."""
    
    url = "http://localhost:5001/casestrainer/api/analyze"
    
    # Test data with fake citation
    test_data = {
        "text": "Completely Fake Case v. Test Party, XYZ U.S. 123 (2020)",
        "source_name": "test"
    }
    
    print("Testing fallback functionality...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print("-" * 50)
    
    try:
        # Test with debug mode
        response = requests.post(f"{url}?debug=true", json=test_data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Check for fallback usage
            found_fallback = False
            for citation in result.get("citations", []):
                source = citation.get("source", "")
                if "fallback" in source.lower():
                    found_fallback = True
                    print(f"✅ FALLBACK DETECTED: {citation.get('citation')} -> {source}")
                    break
            
            if not found_fallback:
                print("❌ No fallback detected in response")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_fallback() 