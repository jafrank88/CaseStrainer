#!/usr/bin/env python3
"""
Debug script to examine the raw CourtListener API response structure.
"""

import requests
import json
import os

def debug_api_response():
    """Debug the CourtListener API response structure."""
    
    # Get API key from environment
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    if not api_key:
        print("No CourtListener API key found in environment")
        return
    
    test_citation = "347 U.S. 483"  # Brown v. Board of Education
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    try:
        print(f"Making API request for: {test_citation}")
        response = requests.post(
            url,
            headers=headers,
            json={"text": test_citation},
            timeout=15
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nRaw API response structure:")
            print(json.dumps(data, indent=2))
            
            # Examine the first citation object
            if isinstance(data, list) and len(data) > 0:
                citation_data = data[0]
                print(f"\nFirst citation object keys: {list(citation_data.keys())}")
                
                if 'clusters' in citation_data and citation_data['clusters']:
                    cluster = citation_data['clusters'][0]
                    print(f"\nCluster keys: {list(cluster.keys())}")
                    
                    # Look for citations in the cluster
                    if 'citations' in cluster:
                        print(f"\nCitations in cluster:")
                        for i, cite in enumerate(cluster['citations']):
                            print(f"  Citation {i+1}: {cite}")
                    
                    # Look for other possible citation fields
                    citation_fields = ['opinion_cites', 'parallel_citations', 'cite', 'citation']
                    for field in citation_fields:
                        if field in cluster:
                            print(f"\n{field} field: {cluster[field]}")
                            
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_api_response() 