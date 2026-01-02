#!/usr/bin/env python3
"""
Test CourtListener API directly to see what it returns for the problematic citations
"""
import requests
import os
import json

def test_courtlistener_api():
    """Test CourtListener API directly for the problematic citations"""
    
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    if not api_key:
        print("❌ No CourtListener API key found")
        return
    
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test the problematic citations from user's report
    test_citations = [
        "114 Wn. App. 245",
        "57 P.3d 273", 
        "129 Wn.2d 652"
    ]
    
    print("🔍 Testing CourtListener API directly:")
    print("="*60)
    
    for citation in test_citations:
        print(f"\n📝 Testing citation: {citation}")
        
        payload = {"text": citation}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS: {response.status_code}")
                print(f"📊 Response data:")
                
                if isinstance(data, list) and len(data) > 0:
                    for i, result in enumerate(data):
                        print(f"  Result {i+1}:")
                        print(f"    Citation: {result.get('citation', 'N/A')}")
                        print(f"    Case Name: {result.get('caseName', 'N/A')}")
                        print(f"    Date Filed: {result.get('dateFiled', 'N/A')}")
                        print(f"    URL: {result.get('absolute_url', 'N/A')}")
                        print(f"    Court: {result.get('court', 'N/A')}")
                        print(f"    Docket Number: {result.get('docketNumber', 'N/A')}")
                        print()
                else:
                    print(f"  No results found")
                    print(f"  Raw response: {data}")
            else:
                print(f"❌ FAILED: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"💥 ERROR: {e}")

if __name__ == "__main__":
    test_courtlistener_api()









