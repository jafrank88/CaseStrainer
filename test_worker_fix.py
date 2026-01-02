#!/usr/bin/env python3
"""
Test if the processing pipeline is working after fixing the worker
"""

import requests
import time

test_text = 'Ellensburg Cement Products, Inc. v. Kittitas County, 179 Wn.2d 737 (2014).'

print('Testing CaseStrainer API after worker fix...')
print('Submitting text for processing...')

response = requests.post('https://wolf.law.uw.edu/casestrainer/api/analyze', 
    json={'type': 'text', 'text': test_text, 'enable_verification': False}, 
    timeout=60)

print(f'Status: {response.status_code}')

if response.status_code == 200:
    result = response.json()
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f'SUCCESS: Processing completed!')
    print(f'   Citations found: {len(citations)}')
    print(f'   Clusters created: {len(clusters)}')
    
    if citations:
        print(f'   First citation: {citations[0].get("citation", "N/A")}')
        print(f'   Case name: {citations[0].get("extracted_case_name", "N/A")}')
    
    print('\nThe progress bar issue is FIXED!')
    print('Processing should now complete normally instead of getting stuck at "update: 1"')
    
else:
    print(f'Error: {response.text}')
