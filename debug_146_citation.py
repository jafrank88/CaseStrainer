#!/usr/bin/env python3
"""
Debug script to test why 146 Wn.2d 1, 9, 43 P.3d 4 is finding the wrong canonical case.
"""

import os
import requests
import json
import sys

def test_citation_lookup(citation):
    """Test CourtListener citation-lookup API for a specific citation."""
    
    # Get API key
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    if not api_key:
        print("ERROR: No CourtListener API key found in environment")
        return
    
    print(f"Testing citation: {citation}")
    print("=" * 60)
    
    # Test citation-lookup API
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    data = {"text": citation}
    
    try:
        print(f"Making POST request to: {url}")
        print(f"Headers: {headers}")
        print(f"Data: {data}")
        
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nFull Response:")
            print(json.dumps(data, indent=2))
            
            # Parse the response
            if isinstance(data, list) and len(data) > 0:
                citation_data = data[0]
                print(f"\nCitation Data Status: {citation_data.get('status')}")
                
                if citation_data.get('clusters') and len(citation_data['clusters']) > 0:
                    cluster = citation_data['clusters'][0]
                    print(f"\n✅ Found cluster:")
                    print(f"  Case Name: {cluster.get('case_name', 'N/A')}")
                    print(f"  Date Filed: {cluster.get('date_filed', 'N/A')}")
                    print(f"  URL: {cluster.get('absolute_url', 'N/A')}")
                    print(f"  Citation: {cluster.get('citations', [])}")
                    
                    # Check if this matches the expected case
                    expected_case = "Dep't of Ecology v. Campbell & Gwinn, LLC"
                    actual_case = cluster.get('case_name', '')
                    
                    if expected_case.lower() in actual_case.lower():
                        print(f"\n✅ MATCH: Found expected case!")
                    else:
                        print(f"\n❌ MISMATCH: Expected '{expected_case}' but got '{actual_case}'")
                        
                        # Try to understand why it matched this case
                        print(f"\nDebugging why it matched this case:")
                        print(f"  - Volume/Page collision?")
                        print(f"  - Multiple cases on same page?")
                        print(f"  - Citation format issue?")
                else:
                    print(f"\n❌ No clusters found in response")
            else:
                print(f"\n❌ Unexpected response format")
        else:
            print(f"\n❌ API Error: {response.status_code}")
            print(f"Response Text: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

def test_search_api(citation):
    """Test CourtListener search API as alternative."""
    
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    if not api_key:
        return
    
    print(f"\nTesting search API for: {citation}")
    print("-" * 40)
    
    # Try different search queries
    search_queries = [
        citation,
        "146 Wn.2d 1",
        "146 Wash. 2d 1",
        "146 Wn.2d",
        "Dep't of Ecology v. Campbell"
    ]
    
    headers = {"Authorization": f"Token {api_key}"}
    
    for query in search_queries:
        try:
            url = f"https://www.courtlistener.com/api/rest/v4/search/"
            params = {
                "q": query,
                "type": "o",  # opinions
                "format": "json"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                print(f"Query '{query}': {count} results")
                
                if count > 0:
                    results = data.get('results', [])
                    for i, result in enumerate(results[:3]):  # Show first 3
                        case_name = result.get('case_name', 'N/A')
                        date_filed = result.get('date_filed', 'N/A')
                        print(f"  {i+1}. {case_name} ({date_filed})")
            else:
                print(f"Query '{query}': Error {response.status_code}")
                
        except Exception as e:
            print(f"Query '{query}': Error {e}")

def main():
    citation = "146 Wn.2d 1, 9, 43 P.3d 4"
    
    print("DEBUGGING CITATION LOOKUP ISSUE")
    print("=" * 60)
    print(f"Citation: {citation}")
    print(f"Expected Case: Dep't of Ecology v. Campbell & Gwinn, LLC")
    print(f"Actual Result: Public Utility District No. 1 v. State")
    print()
    
    # Test citation-lookup API
    test_citation_lookup(citation)
    
    # Test search API as alternative
    test_search_api(citation)
    
    print(f"\n" + "=" * 60)
    print("ANALYSIS:")
    print("The issue is likely one of:")
    print("1. Volume/Page collision - multiple cases on page 1 of volume 146")
    print("2. Citation format mismatch - API not parsing the full citation correctly")
    print("3. CourtListener database has the wrong case associated with this citation")
    print("4. The citation is being cleaned/normalized incorrectly before lookup")

if __name__ == "__main__":
    main() 