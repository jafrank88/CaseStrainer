#!/usr/bin/env python3
"""
Test script to check what CourtListener citation-lookup API returns for specific citations.
"""

import requests
import json
import time

def test_citation_lookup():
    """Test CourtListener citation-lookup API with the specific citations from the user's test."""
    
    # Citations from the user's test
    test_citations = [
        "317 P.3d 1068",
        "392 P.3d 1041", 
        "230 P.3d 233",
        "188 Wn.2d 114",
        "178 Wn. App. 929",
        "155 Wn. App. 715"
    ]
    
    print("Testing CourtListener citation-lookup API...")
    print("=" * 60)
    
    # Test each citation individually
    for citation in test_citations:
        print(f"\n🔍 Testing citation: {citation}")
        
        # CourtListener citation-lookup API endpoint
        url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        
        # Prepare the request
        params = {
            'citation': citation
        }
        
        try:
            print(f"   Sending request to: {url}")
            print(f"   Parameters: {params}")
            
            # Send request
            response = requests.get(url, params=params, timeout=30)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
                
                # Check if we got results
                if 'results' in data and data['results']:
                    print(f"   ✅ Found {len(data['results'])} results")
                    for i, result in enumerate(data['results']):
                        print(f"   Result {i+1}:")
                        print(f"     Case Name: {result.get('case_name', 'N/A')}")
                        print(f"     Date Filed: {result.get('date_filed', 'N/A')}")
                        print(f"     Court: {result.get('court_name', 'N/A')}")
                        print(f"     URL: {result.get('absolute_url', 'N/A')}")
                else:
                    print(f"   ❌ No results found")
                    
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON decode error: {e}")
            print(f"   Raw response: {response.text}")
        
        # Rate limiting - wait between requests
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("Citation lookup testing completed.")

if __name__ == "__main__":
    test_citation_lookup()




