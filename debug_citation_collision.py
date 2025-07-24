#!/usr/bin/env python3
"""
Debug script to test citation collision issue with 146 Wn.2d 1
"""

import os
import requests
import json
import time
from typing import Dict, Any
import sys

# Prevent use of v3 CourtListener API endpoints
if 'v3' in url or 'v3' in search_url:
    print("ERROR: v3 CourtListener API endpoint detected. Please use v4 only.")
    sys.exit(1)

def test_citation_collision():
    """Test why 146 Wn.2d 1 is returning different cases."""
    
    # Get API key
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    if not api_key:
        print("ERROR: No CourtListener API key found in environment")
        return
    
    headers = {"Authorization": f"Token {api_key}"}
    
    citation = "146 Wn.2d 1, 9, 43 P.3d 4"
    base_citation = "146 Wn.2d 1"
    
    print("DEBUGGING CITATION COLLISION ISSUE")
    print("=" * 60)
    print(f"Citation: {citation}")
    print(f"Base Citation: {base_citation}")
    print(f"Expected Case: Dep't of Ecology v. Campbell & Gwinn, LLC")
    print(f"Actual Result: Public Utility District No. 1 v. State")
    print()
    
    # Test 1: Citation-lookup API with full citation
    print("TEST 1: Citation-lookup API with full citation")
    print("-" * 40)
    test_citation_lookup(citation, headers)
    
    # Test 2: Citation-lookup API with base citation
    print("\nTEST 2: Citation-lookup API with base citation")
    print("-" * 40)
    test_citation_lookup(base_citation, headers)
    
    # Test 3: Search API with base citation
    print("\nTEST 3: Search API with base citation")
    print("-" * 40)
    test_search_api(base_citation, headers)
    
    # Test 4: Search API with full citation
    print("\nTEST 4: Search API with full citation")
    print("-" * 40)
    test_search_api(citation, headers)
    
    # Test 5: Multiple attempts to see if results vary
    print("\nTEST 5: Multiple attempts (timing test)")
    print("-" * 40)
    for i in range(3):
        print(f"\nAttempt {i+1}:")
        test_citation_lookup(base_citation, headers)
        time.sleep(1)
    
    # Test 6: Search for specific case names
    print("\nTEST 6: Search for specific case names")
    print("-" * 40)
    test_case_name_search("Dep't of Ecology v. Campbell", headers)
    test_case_name_search("Public Utility District No. 1 v. State", headers)
    test_case_name_search("Department of Ecology v. Campbell", headers)

def test_citation_lookup(citation: str, headers: Dict[str, str]):
    """Test citation-lookup API."""
    try:
        url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        data = {"text": citation}
        
        response = requests.post(url, headers=headers, data=data, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if isinstance(data, list) and len(data) > 0:
                citation_data = data[0]
                clusters = citation_data.get('clusters', [])
                print(f"Clusters found: {len(clusters)}")
                
                for i, cluster in enumerate(clusters):
                    case_name = cluster.get('case_name', 'N/A')
                    date_filed = cluster.get('date_filed', 'N/A')
                    url = cluster.get('absolute_url', 'N/A')
                    print(f"  Cluster {i+1}: {case_name} ({date_filed})")
                    print(f"    URL: {url}")
            else:
                print("No clusters found")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_search_api(citation: str, headers: Dict[str, str]):
    """Test search API."""
    try:
        url = "https://www.courtlistener.com/api/rest/v4/search/"
        params = {
            "q": citation,
            "type": "o",  # opinions
            "format": "json"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"Results found: {count}")
            
            if count > 0:
                results = data.get('results', [])
                for i, result in enumerate(results[:5]):  # Show first 5
                    case_name = result.get('case_name', 'N/A')
                    date_filed = result.get('date_filed', 'N/A')
                    citations = result.get('citation', [])
                    print(f"  Result {i+1}: {case_name} ({date_filed})")
                    print(f"    Citations: {citations}")
            else:
                print("No results found")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_case_name_search(case_name: str, headers: Dict[str, str]):
    """Test searching by case name."""
    try:
        url = "https://www.courtlistener.com/api/rest/v4/search/"
        params = {
            "q": f'"{case_name}"',
            "type": "o",  # opinions
            "format": "json"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Searching for: {case_name}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"Results found: {count}")
            
            if count > 0:
                results = data.get('results', [])
                for i, result in enumerate(results[:3]):  # Show first 3
                    found_case_name = result.get('case_name', 'N/A')
                    date_filed = result.get('date_filed', 'N/A')
                    citations = result.get('citation', [])
                    print(f"  Result {i+1}: {found_case_name} ({date_filed})")
                    print(f"    Citations: {citations}")
            else:
                print("No results found")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_citation_collision() 