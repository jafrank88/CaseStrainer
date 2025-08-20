#!/usr/bin/env python3
"""
Minimal test script to test the API with simple text
"""

import requests
import json

def test_minimal_api():
    """Test the API with minimal text"""
    
    # Test with just the Washington Court of Appeals citations
    test_text = "136 Wn. App. 104, 69 Wn. App. 621, 93 Wn. App. 442"
    
    print("🔍 Testing Minimal API")
    print("=" * 30)
    print(f"Test text: {test_text}")
    print()
    
    try:
        # Test the API endpoint
        url = "http://localhost:5000/casestrainer/api/analyze"
        payload = {
            "text": test_text,
            "type": "text"
        }
        
        print(f"📡 Sending request to: {url}")
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('message', 'No message')}")
            print(f"📊 Citations found: {len(result.get('result', {}).get('citations', []))}")
            print(f"📊 Clusters found: {len(result.get('result', {}).get('clusters', []))}")
            
            # Show all citations
            citations = result.get('result', {}).get('citations', [])
            for i, citation in enumerate(citations, 1):
                print(f"\nCitation {i}:")
                print(f"  Text: {citation.get('citation', 'N/A')}")
                print(f"  Case: {citation.get('case_name', 'N/A')}")
                print(f"  Pattern: {citation.get('pattern', 'N/A')}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minimal_api()
