#!/usr/bin/env python3
"""
Test the specific Luis v. United States citation to understand why canonical data is missing.
"""

import os
import requests
import json

def test_luis_citation():
    # API endpoint
    api_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    # API key
    api_key = "***REDACTED_COURTLISTENER_KEY***"
    
    # Test citations from the problematic cluster
    test_citations = [
        "578 U.S. 5",           # The one with missing canonical data
        "136 S. Ct. 1083",      # The parallel citation that returned wrong data
        "194 L. Ed. 2d 256"     # The third parallel citation
    ]
    
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'CaseStrainer/1.0'
    }
    
    for citation in test_citations:
        print(f"\n{'='*60}")
        print(f"Testing citation: {citation}")
        print(f"{'='*60}")
        
        try:
            # Test with text parameter (correct for v4 API)
            response = requests.post(
                api_url,
                headers=headers,
                json={"text": citation},
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Results found: {len(data)}")
                
                if data:
                    for i, result in enumerate(data[:2], 1):
                        print(f"\nResult {i}:")
                        if 'clusters' in result and result['clusters']:
                            cluster = result['clusters'][0]
                            print(f"  Case Name: {cluster.get('case_name', 'N/A')}")
                            print(f"  Date Filed: {cluster.get('date_filed', 'N/A')}")
                            print(f"  Court: {cluster.get('court', 'N/A')}")
                            print(f"  Citations: {cluster.get('citations', [])}")
                        else:
                            print(f"  Raw result: {json.dumps(result, indent=4)}")
                else:
                    print("  No results found")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    test_luis_citation()
