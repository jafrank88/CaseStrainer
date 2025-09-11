#!/usr/bin/env python3
"""
Test the new test paragraph provided by the user
"""

import requests
import json

def test_paragraph_3():
    # The exact test paragraph from the user
    test_text = """Certified questions are questions of law that this court reviews de novo and in light
of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183
Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we
review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430
P.3d 655 (2018)."""
    
    print("Testing Test Paragraph 3:")
    print(f"Text: {test_text}")
    print(f"Text length: {len(test_text)}")
    print()
    
    try:
        response = requests.post('http://localhost:5000/casestrainer/api/analyze',
                               json={'text': test_text, 'type': 'text'},
                               timeout=30)

        if response.status_code == 200:
            data = response.json()
            print('API Response Status: 200')
            print(f'Citations found: {len(data.get("citations", []))}')
            print(f'Clusters: {len(data.get("clusters", []))}')
            
            print('\nCitations from result:')
            result_citations = data.get('result', {}).get('citations', [])
            for i, citation in enumerate(result_citations, 1):
                print(f'  {i}. {citation.get("citation", "N/A")} -> {citation.get("extracted_case_name", "N/A")}')
            
            print('\nClusters:')
            clusters = data.get('result', {}).get('clusters', [])
            for i, cluster in enumerate(clusters, 1):
                print(f'  {i}. {cluster.get("extracted_case_name", "N/A")} ({cluster.get("size", 0)} citations)')
                for cit in cluster.get('citations', []):
                    print(f'     - {cit}')
            
            # Check contamination
            contamination = data.get('result', {}).get('data_separation_validation', {})
            print(f'\nContamination: {contamination.get("contamination_detected", False)} ({contamination.get("contamination_rate", 0)})')
            
            # Expected results
            print('\n=== EXPECTED RESULTS ===')
            print('Expected clusters:')
            print('1. Lopez Demetrio v. Sakuma Bros. Farms (183 Wn.2d 649, 355 P.3d 258)')
            print('2. Spokane County v. Dep\'t of Fish & Wildlife (192 Wn.2d 453, 430 P.3d 655)')
            
        else:
            print(f'API Error: {response.status_code}')
            print(response.text)
    except Exception as e:
        print(f'Error calling API: {e}')

if __name__ == "__main__":
    test_paragraph_3()

