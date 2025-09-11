#!/usr/bin/env python3
"""
Debug script to trace the verification process and see where contamination is happening
"""

import requests
import json

def debug_verification_process():
    """Debug the verification process to find contamination sources"""
    url = 'http://localhost:5000/casestrainer/api/analyze'
    data = {
        'text': 'Certified questions are questions of law that this court reviews de novo and in light of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we review de novo. Spokane County v. Dep\'t of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018).'
    }

    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print('=== VERIFICATION PROCESS DEBUG ===')
            
            # Check verification results
            verification_results = result.get('result', {}).get('verification_status', {}).get('verification_results', [])
            print(f'Verification Results Count: {len(verification_results)}')
            
            for i, vr in enumerate(verification_results, 1):
                print(f'\nVerification Result {i}:')
                print(f'  Citation: {vr.get("citation")}')
                print(f'  Source: {vr.get("source")}')
                print(f'  Verified: {vr.get("verified")}')
                print(f'  Canonical Name: {vr.get("canonical_name")}')
                print(f'  URL: {vr.get("url")}')
                print(f'  Confidence: {vr.get("confidence")}')
            
            # Check citations
            citations = result.get('result', {}).get('citations', [])
            print(f'\n=== CITATIONS DEBUG ===')
            
            for i, citation in enumerate(citations, 1):
                print(f'\nCitation {i}: {citation.get("citation")}')
                print(f'  Extracted: {citation.get("extracted_case_name")}')
                print(f'  Canonical: {citation.get("canonical_name")}')
                print(f'  Verified: {citation.get("verified")}')
                print(f'  Source: {citation.get("verification_source")}')
                print(f'  URL: {citation.get("url")}')
                
                # Check if there's a verification_result field
                if 'verification_result' in citation:
                    vr = citation['verification_result']
                    print(f'  Verification Result:')
                    print(f'    Source: {vr.get("source")}')
                    print(f'    Canonical: {vr.get("canonical_name")}')
                    print(f'    Verified: {vr.get("verified")}')
                
                # Check contamination
                extracted = citation.get('extracted_case_name', '')
                canonical = citation.get('canonical_name', '')
                is_contaminated = extracted == canonical and extracted != '' and canonical != ''
                print(f'  Contaminated: {is_contaminated}')
                
        else:
            print(f'API Error: {response.status_code}')
            print(response.text)
            
    except Exception as e:
        print(f'Debug failed: {e}')

if __name__ == '__main__':
    debug_verification_process()

