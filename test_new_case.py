#!/usr/bin/env python3
"""
Test with a new case to avoid caching issues
"""

import requests
import json

def test_new_case():
    """Test with a new case to avoid caching"""
    url = 'http://localhost:5000/casestrainer/api/analyze'
    data = {
        'text': 'This is a test case. Smith v. Jones, 123 F.3d 456 (2020). Another case is Brown v. Wilson, 789 F.2d 123 (2019).'
    }

    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            print('=== NEW TEST CASE ===')
            for i, citation in enumerate(citations, 1):
                print(f'Citation {i}: {citation.get("citation")}')
                print(f'  Extracted: {citation.get("extracted_case_name")}')
                print(f'  Canonical: {citation.get("canonical_name")}')
                print(f'  Verified: {citation.get("verified")}')
                print(f'  Source: {citation.get("verification_source")}')
                
                # Check contamination
                extracted = citation.get('extracted_case_name', '')
                canonical = citation.get('canonical_name', '')
                is_contaminated = extracted == canonical and extracted != '' and canonical != ''
                print(f'  Contaminated: {is_contaminated}')
                print()
        else:
            print(f'API Error: {response.status_code}')
            print(response.text)
    except Exception as e:
        print(f'Test failed: {e}')

if __name__ == '__main__':
    test_new_case()

