#!/usr/bin/env python3
"""
Complete test of Luis v. United States parallel citations to understand the canonical data issue.
"""

import os
import requests
import json

def test_luis_complete():
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
        print(f"\nTesting: {citation}")
        print("-" * 40)
        
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json={"text": citation},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data and len(data) > 0:
                    result = data[0]
                    print(f"Status: {result.get('status', 'N/A')}")
                    
                    if result.get('status') == 404:
                        print(f"Error: {result.get('error_message', 'Not found')}")
                    elif 'clusters' in result and result['clusters']:
                        cluster = result['clusters'][0]
                        print(f"Case Name: {cluster.get('case_name', 'N/A')}")
                        print(f"Date Filed: {cluster.get('date_filed', 'N/A')}")
                        print(f"Court: {cluster.get('court', {}).get('short_name', 'N/A')}")
                        
                        # Show all citations for this cluster
                        if 'citations' in cluster:
                            print("All citations in cluster:")
                            for cite in cluster['citations'][:5]:  # Show first 5
                                print(f"  - {cite.get('volume', '')} {cite.get('reporter', '')} {cite.get('page', '')}")
                else:
                    print("No results returned")
            else:
                print(f"HTTP Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    test_luis_complete()
