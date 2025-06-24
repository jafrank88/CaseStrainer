#!/usr/bin/env python3
"""
Test script to query CourtListener API v4 directly for case information.
"""

import requests
import json
import os

def load_api_key():
    """Load API key from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config.get('COURTLISTENER_API_KEY') or config.get('courtlistener_api_key')
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_courtlistener_api():
    """Test CourtListener API v4 for citation '534 F.3d 1290'"""
    
    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("No API key found in config.json")
        return
    
    print(f"Using API key: {api_key[:6]}...")
    
    # Test different CourtListener API v4 endpoints
    base_url = "https://www.courtlistener.com/api/rest/v4"
    
    # Test 1: Search for opinions with citation
    print("Testing CourtListener API v4 for citation: 534 F.3d 1290")
    print("=" * 60)
    
    # Endpoint 1: Search opinions
    search_url = f"{base_url}/opinions/"
    params = {
        'citation': '534 F.3d 1290',
        'format': 'json'
    }
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"1. Searching opinions endpoint: {search_url}")
    try:
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Results count: {data.get('count', 'N/A')}")
            if data.get('results'):
                for i, result in enumerate(data['results'][:3]):  # Show first 3 results
                    print(f"   Result {i+1}:")
                    print(f"     Case name: {result.get('case_name', 'N/A')}")
                    print(f"     Citation: {result.get('citation', 'N/A')}")
                    print(f"     URL: {result.get('absolute_url', 'N/A')}")
            else:
                print("   No results found")
        else:
            print(f"   Error response: {response.text[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "-" * 60)
    
    # Endpoint 2: Citation lookup (POST endpoint)
    citation_lookup_url = f"{base_url}/citation-lookup/"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "CaseStrainer Citation Verifier (test)"
    }
    data = {"text": "534 F.3d 1290"}
    
    print(f"2. Testing citation-lookup endpoint: {citation_lookup_url}")
    try:
        response = requests.post(citation_lookup_url, headers=headers, json=data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                for i, citation_result in enumerate(data):
                    print(f"   Citation Result {i+1}:")
                    clusters = citation_result.get("clusters", [])
                    if clusters:
                        for j, cluster in enumerate(clusters):
                            print(f"     Cluster {j+1}:")
                            print(f"       Case: {cluster.get('case_name', 'N/A')}")
                            print(f"       Case Name Short: {cluster.get('case_name_short', 'N/A')}")
                            print(f"       URL: https://www.courtlistener.com{cluster.get('absolute_url', '')}")
                            print(f"       Citations:")
                            for citation in cluster.get("citations", []):
                                print(f"         - {citation.get('volume')} {citation.get('reporter')} {citation.get('page')}")
                    else:
                        print("     No clusters found")
            else:
                print("   No results found")
        else:
            print(f"   Error response: {response.text[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_courtlistener_api() 