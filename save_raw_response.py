#!/usr/bin/env python3
"""
Save the raw task status response to examine its structure
"""

import requests
import json

def save_raw_response():
    task_id = "773de729-1d50-45c8-b973-9f88922e4aad"
    
    try:
        response = requests.get(f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Save to file
            with open('sp7788_raw_response.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            print("Raw response saved to sp7788_raw_response.json")
            
            # Print basic structure
            print("Response structure:")
            print(f"Keys: {list(result.keys())}")
            
            if 'result' in result:
                result_keys = list(result['result'].keys())
                print(f"Result keys: {result_keys}")
                
                if 'clusters' in result['result']:
                    clusters = result['result']['clusters']
                    print(f"Number of clusters: {len(clusters)}")
                    
                    if clusters:
                        first_cluster = clusters[0]
                        print(f"First cluster keys: {list(first_cluster.keys())}")
                        
                        if 'citations' in first_cluster:
                            citations = first_cluster['citations']
                            print(f"Citations in first cluster: {len(citations)}")
                            
                            if citations:
                                first_citation = citations[0]
                                print(f"First citation keys: {list(first_citation.keys())}")
                                print(f"First citation: {first_citation.get('citation', 'Unknown')}")
                                print(f"Extracted name: {first_citation.get('extracted_case_name', 'N/A')}")
                                print(f"Verified: {first_citation.get('verified', False)}")
                
                if 'citations' in result['result']:
                    direct_citations = result['result']['citations']
                    print(f"Direct citations list: {len(direct_citations)}")
            
        else:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    save_raw_response()
