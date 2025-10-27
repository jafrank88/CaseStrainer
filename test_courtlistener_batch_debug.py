#!/usr/bin/env python3
"""
Test script to debug CourtListener batch API responses for specific citations.
"""

import requests
import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_courtlistener_batch_api():
    """Test CourtListener batch API for the problematic citations."""
    
    # Test citations that are showing cross-contamination
    test_citations = [
        "547 P.2d 1207",  # Should be "A & G Constr. Co. v. Reid Bros. Logging Co."
        "32 So. 3d 496"   # Should be "State v. Bayer Corp."
    ]
    
    # CourtListener API endpoint
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    # API key (you'll need to set this)
    api_key = "YOUR_API_KEY_HERE"  # Replace with actual API key
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test each citation individually
    for citation in test_citations:
        print(f"\n{'='*60}")
        print(f"Testing citation: {citation}")
        print(f"{'='*60}")
        
        payload = {"text": citation}
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response Type: {type(data)}")
                
                if isinstance(data, list) and len(data) > 0:
                    result = data[0]
                    print(f"Citation in response: {result.get('citation')}")
                    print(f"Status: {result.get('status')}")
                    print(f"Error: {result.get('error_message')}")
                    
                    clusters = result.get('clusters', [])
                    print(f"Number of clusters: {len(clusters)}")
                    
                    for i, cluster in enumerate(clusters):
                        print(f"\nCluster {i+1}:")
                        print(f"  Case Name: {cluster.get('caseName') or cluster.get('case_name')}")
                        print(f"  Date Filed: {cluster.get('dateFiled') or cluster.get('date_filed')}")
                        print(f"  URL: {cluster.get('absolute_url')}")
                        
                        # Check docket object
                        docket = cluster.get('docket', {})
                        if docket:
                            print(f"  Docket Case Name: {docket.get('caseName') or docket.get('case_name')}")
                            print(f"  Docket Date: {docket.get('dateFiled') or docket.get('date_filed')}")
                else:
                    print("No data returned or unexpected format")
                    print(f"Raw response: {response.text[:500]}")
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
        except Exception as e:
            print(f"Exception: {e}")
    
    # Test batch request
    print(f"\n{'='*60}")
    print("Testing batch request")
    print(f"{'='*60}")
    
    payload = {"text": " ".join(test_citations)}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Type: {type(data)}")
            print(f"Number of results: {len(data) if isinstance(data, list) else 'N/A'}")
            
            if isinstance(data, list):
                for i, result in enumerate(data):
                    print(f"\nResult {i+1}:")
                    print(f"  Citation: {result.get('citation')}")
                    print(f"  Status: {result.get('status')}")
                    print(f"  Error: {result.get('error_message')}")
                    
                    clusters = result.get('clusters', [])
                    print(f"  Clusters: {len(clusters)}")
                    
                    for j, cluster in enumerate(clusters):
                        print(f"    Cluster {j+1}:")
                        print(f"      Case Name: {cluster.get('caseName') or cluster.get('case_name')}")
                        print(f"      Date Filed: {cluster.get('dateFiled') or cluster.get('date_filed')}")
                        print(f"      URL: {cluster.get('absolute_url')}")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_courtlistener_batch_api()

