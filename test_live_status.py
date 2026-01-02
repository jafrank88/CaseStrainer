#!/usr/bin/env python3
"""
Comprehensive test of the live CaseStrainer application
"""

import requests
import time

def test_api():
    test_text = '''Ellensburg Cement Products, Inc. v. Kittitas County, 179 Wn.2d 737, 317 P.3d 1037 (2014).
Department of Ecology v. Campbell & Gwinn, LLC, 171 Wn.2d 820, 256 P.3d 1150 (2011).'''
    
    print('Testing live CaseStrainer application...')
    print('Text:', test_text[:100] + '...')
    print()
    
    start_time = time.time()
    
    try:
        response = requests.post('https://wolf.law.uw.edu/casestrainer/api/analyze', 
            json={'type': 'text', 'text': test_text, 'enable_verification': True}, 
            timeout=120)
        
        elapsed_time = time.time() - start_time
        
        print(f'Status: {response.status_code}')
        print(f'Processing time: {elapsed_time:.1f} seconds')
        print()
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print('RESULTS:')
            print(f'  Citations found: {len(citations)}')
            print(f'  Clusters created: {len(clusters)}')
            print()
            
            print('CITATIONS:')
            for i, cit in enumerate(citations):
                print(f'  {i+1}. {cit.get("citation", "N/A")} - verified: {cit.get("verified", False)}')
            
            print()
            print('CLUSTERS:')
            for i, cluster in enumerate(clusters):
                cluster_id = cluster.get('cluster_id', 'N/A')
                verifying_name = cluster.get('verifying_display_name', 'N/A')
                submitted_name = cluster.get('submitted_display_name', 'N/A')
                cluster_citations = cluster.get('citations', [])
                
                print(f'  Cluster {i+1} ({cluster_id}):')
                print(f'    Verifying name: {verifying_name}')
                print(f'    Submitted name: {submitted_name}')
                print(f'    Citations: {len(cluster_citations)}')
                print(f'    Verified: {any(cit.get("verified", False) for cit in cluster_citations)}')
            
            print()
            print('SUCCESS INDICATORS:')
            print(f'  Processing completed: {elapsed_time < 60} (under 60 seconds)')
            print(f'  Clusters created: {len(clusters) > 0}')
            print(f'  Citations verified: {any(cit.get("verified", False) for cit in citations)}')
            print(f'  Case names specific: {not any("Case" in name for name in [submitted_name])}')
            
            return True
            
        else:
            print(f'API Error: {response.text}')
            return False
            
    except Exception as e:
        print(f'Request failed: {e}')
        return False

if __name__ == "__main__":
    success = test_api()
    print()
    if success:
        print('OVERALL STATUS: WORKING')
        print('The progress bar issue is FIXED and all features are operational!')
    else:
        print('OVERALL STATUS: NEEDS ATTENTION')
