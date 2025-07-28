#!/usr/bin/env python3
"""
Detailed debug test for name similarity matching with actual API data
"""

import sys
import os
import requests
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import get_config_value
from src.name_similarity_matcher import calculate_case_name_similarity
from src.courtlistener_verification import select_best_cluster_from_result

def debug_similarity_matching():
    print("=== DETAILED SIMILARITY DEBUG ===")
    
    api_key = get_config_value("COURTLISTENER_API_KEY")
    headers = {'Authorization': f'Token {api_key}', 'Content-Type': 'application/json'}
    url = 'https://www.courtlistener.com/api/rest/v4/citation-lookup/'
    data = {'text': '136 S. Ct. 1083'}
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    if response.status_code == 200:
        results = response.json()
        
        if results and results[0].get('clusters'):
            result = results[0]
            clusters = result['clusters']
            
            print(f"Found {len(clusters)} clusters:")
            for i, cluster in enumerate(clusters):
                case_name = cluster.get('case_name', 'Unknown')
                date_filed = cluster.get('date_filed', 'Unknown')
                print(f"  Cluster {i+1}: '{case_name}' ({date_filed})")
            
            # Test similarity with different extracted names
            test_cases = [
                "Luis v. United States",
                "Friedrichs v. Cal. Teachers Ass'n", 
                "Friedrichs v. California Teachers Association",
                "Luis v. US"
            ]
            
            print("\n=== SIMILARITY CALCULATIONS ===")
            for extracted_name in test_cases:
                print(f"\nTesting extracted name: '{extracted_name}'")
                
                best_similarity = 0.0
                best_cluster_idx = 0
                
                for i, cluster in enumerate(clusters):
                    case_name = cluster.get('case_name', '')
                    similarity = calculate_case_name_similarity(extracted_name, case_name)
                    print(f"  Cluster {i+1} '{case_name}': {similarity:.3f}")
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_cluster_idx = i
                
                print(f"  → Best match: Cluster {best_cluster_idx+1} with similarity {best_similarity:.3f}")
                
                # Test our cluster selection function
                print(f"\n  Testing select_best_cluster_from_result:")
                selected_cluster = select_best_cluster_from_result(result, extracted_name, debug=True)
                if selected_cluster:
                    selected_name = selected_cluster.get('case_name', 'Unknown')
                    print(f"  → Function selected: '{selected_name}'")
                else:
                    print(f"  → Function returned None")
                print()

if __name__ == "__main__":
    debug_similarity_matching()
