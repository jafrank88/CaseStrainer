#!/usr/bin/env python3
"""
Test script to check what CourtListener citation-lookup API returns for specific citations with authentication.
Tests both original Wn. citations and normalized Wash. equivalents since CourtListener normalizes Wn. to Wash.
"""

import requests
import json
import time

def test_citation_lookup_with_auth():
    """Test CourtListener citation-lookup API with authentication for the specific citations."""
    
    # API key from the system
    api_key = "***REDACTED_COURTLISTENER_KEY***"
    
    # Citations from the user's test - including both Wn. and normalized Wash. versions
    test_citations = [
        # Original citations
        "317 P.3d 1068",
        "392 P.3d 1041", 
        "230 P.3d 233",
        "188 Wn.2d 114",      # Original Wn. version
        "178 Wn. App. 929",   # Original Wn. version
        "155 Wn. App. 715",   # Original Wn. version
        
        # Normalized Wash. versions (as CourtListener would process them)
        "188 Wash. 2d 114",   # Normalized Wash. version
        "178 Wash. App. 929", # Normalized Wash. version
        "155 Wash. App. 715"  # Normalized Wash. version
    ]
    
    print("Testing CourtListener citation-lookup API with batch request...")
    print("=" * 80)
    print(f"Using API key: {api_key[:8]}...{api_key[-8:]}")
    print("=" * 80)
    
    # CourtListener citation-lookup API endpoint
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    # Prepare the request with authentication
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Send all citations as a batch request
    print(f"\n🔍 Testing batch request with {len(test_citations)} citations:")
    print("   Original citations:")
    for i, citation in enumerate(test_citations[:6]):
        print(f"     {i+1}. {citation}")
    print("   Normalized Wash. citations:")
    for i, citation in enumerate(test_citations[6:]):
        print(f"     {i+7}. {citation}")
    
    # Use POST method with JSON data
    data = {
        'text': ' '.join(test_citations)
    }
    
    try:
        print(f"\n📡 Sending POST request to: {url}")
        print(f"   Headers: {headers}")
        print(f"   Data: {json.dumps(data, indent=2)}")
        
        # Send POST request with JSON data
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Check if we got results
            if data and len(data) > 0:
                print(f"   ✅ Found {len(data)} citation results")
                for i, citation_result in enumerate(data):
                    citation_text = citation_result.get('citation', 'N/A')
                    status = citation_result.get('status', 'N/A')
                    print(f"\n   Citation {i+1}: {citation_text} (Status: {status})")
                    
                    if status == 200 and citation_result.get('clusters'):
                        clusters = citation_result['clusters']
                        print(f"     ✅ Found {len(clusters)} clusters")
                        for j, cluster in enumerate(clusters):
                            print(f"       Cluster {j+1}:")
                            print(f"         Case Name: {cluster.get('case_name', 'N/A')}")
                            print(f"         Date Filed: {cluster.get('date_filed', 'N/A')}")
                            print(f"         Court: {cluster.get('court_name', 'N/A')}")
                            print(f"         URL: {cluster.get('absolute_url', 'N/A')}")
                    elif status == 404:
                        print(f"     ❌ Citation not found in CourtListener")
                    else:
                        print(f"     ⚠️  Unexpected status: {status}")
            else:
                print(f"   ❌ No results found")
                
        elif response.status_code == 401:
            print(f"   ❌ Authentication failed - API key may be invalid")
            print(f"   Response: {response.text}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON decode error: {e}")
        print(f"   Raw response: {response.text}")
    
    print("\n" + "=" * 80)
    print("Batch citation lookup testing completed.")

if __name__ == "__main__":
    test_citation_lookup_with_auth()
