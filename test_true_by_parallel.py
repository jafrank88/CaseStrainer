#!/usr/bin/env python3
"""
Test script to debug true_by_parallel logic
"""

import requests
import json

def test_true_by_parallel():
    # Test the API with the same text
    text = 'Certified questions are questions of law that this court reviews de novo and in light of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we review de novo. Spokane County v. Dep\'t of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018).'

    response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                            json={'text': text, 'verify_citations': True})

    if response.status_code == 200:
        data = response.json()
        print('=== CITATIONS ===')
        for citation in data['result']['citations']:
            print(f'Citation: {citation["citation"]}')
            print(f'  Verified: {citation["verified"]}')
            print(f'  True by Parallel: {citation["true_by_parallel"]}')
            print(f'  Source: {citation["source"]}')
            print()
        
        print('=== CLUSTERS ===')
        for i, cluster in enumerate(data['result']['clusters']):
            print(f'Cluster {i+1}: {cluster["cluster_id"]}')
            print(f'  Cluster Has Verified: {cluster["cluster_has_verified"]}')
            print(f'  Verified Citations: {cluster["verified_citations"]}')
            print(f'  Citations: {cluster["citations"]}')
            print()
            
        # Check if 192 Wn.2d 453 should be true_by_parallel
        print('=== TRUE_BY_PARALLEL ANALYSIS ===')
        for citation in data['result']['citations']:
            if citation['citation'] == '192 Wn.2d 453':
                print(f'Citation: {citation["citation"]}')
                print(f'  Verified: {citation["verified"]}')
                print(f'  True by Parallel: {citation["true_by_parallel"]}')
                print(f'  Should be true_by_parallel: {not citation["verified"]}')
                
                # Find the cluster it belongs to
                for cluster in data['result']['clusters']:
                    if '192 Wn.2d 453' in cluster['citations']:
                        print(f'  Cluster: {cluster["cluster_id"]}')
                        print(f'  Cluster Has Verified: {cluster["cluster_has_verified"]}')
                        print(f'  Cluster Verified Citations: {cluster["verified_citations"]}')
                        print(f'  Should be true_by_parallel: {cluster["cluster_has_verified"] and not citation["verified"]}')
                        break
                break
    else:
        print(f'Error: {response.status_code}')
        print(response.text)

if __name__ == '__main__':
    test_true_by_parallel()









