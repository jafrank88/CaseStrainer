#!/usr/bin/env python3
"""
Test to examine the actual CourtListener API response structure for multiple clusters
"""

import sys
import os
import requests
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import get_config_value

def test_api_structure():
    print("=== EXAMINING API RESPONSE STRUCTURE ===")
    
    api_key = get_config_value("COURTLISTENER_API_KEY")
    headers = {'Authorization': f'Token {api_key}', 'Content-Type': 'application/json'}
    url = 'https://www.courtlistener.com/api/rest/v4/citation-lookup/'
    data = {'text': '136 S. Ct. 1083'}
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    if response.status_code == 200:
        results = response.json()
        print(f"API returned {len(results)} results")
        
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"  Status: {result.get('status')}")
            print(f"  Error message: {result.get('error_message')}")
            
            clusters = result.get('clusters', [])
            print(f"  Clusters: {len(clusters)}")
            
            for j, cluster in enumerate(clusters):
                case_name = cluster.get('case_name', 'Unknown')
                date_filed = cluster.get('date_filed', 'Unknown')
                print(f"    Cluster {j+1}: '{case_name}' ({date_filed})")
        
        # Now test name similarity with the actual structure
        print("\n=== TESTING NAME SIMILARITY ===")
        
        from src.name_similarity_matcher import calculate_case_name_similarity
        
        test_names = ["Luis v. United States", "Friedrichs v. Cal. Teachers Ass'n"]
        
        for result in results:
            if result.get('clusters'):
                for cluster in result['clusters']:
                    case_name = cluster.get('case_name', '')
                    print(f"\nCluster case name: '{case_name}'")
                    
                    for test_name in test_names:
                        similarity = calculate_case_name_similarity(test_name, case_name)
                        print(f"  Similarity to '{test_name}': {similarity:.3f}")

if __name__ == "__main__":
    test_api_structure()
