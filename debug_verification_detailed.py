#!/usr/bin/env python3
"""
Detailed debug script to trace the verification process step by step
"""

import requests
import json

def debug_verification_detailed():
    """Debug the verification process in detail"""
    url = 'http://localhost:5000/casestrainer/api/analyze'
    data = {
        'text': 'Certified questions are questions of law that this court reviews de novo and in light of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we review de novo. Spokane County v. Dep\'t of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018).'
    }

    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print('=== DETAILED VERIFICATION DEBUG ===')
            
            # Check verification results
            verification_results = result.get('result', {}).get('verification_status', {}).get('verification_results', [])
            print(f'Verification Results Count: {len(verification_results)}')
            
            for i, vr in enumerate(verification_results, 1):
                print(f'\n--- Verification Result {i} ---')
                print(f'Citation: {vr.get("citation")}')
                print(f'Source: {vr.get("source")}')
                print(f'Verified: {vr.get("verified")}')
                print(f'Canonical Name: {vr.get("canonical_name")}')
                print(f'URL: {vr.get("url")}')
                print(f'Confidence: {vr.get("confidence")}')
                
                # Check if this is contaminated
                if vr.get("canonical_name") and "that and by the" in vr.get("canonical_name", ""):
                    print("⚠️  CONTAMINATED: Canonical name contains 'that and by the'")
                elif vr.get("canonical_name") and "is also an" in vr.get("canonical_name", ""):
                    print("⚠️  CONTAMINATED: Canonical name contains 'is also an'")
                else:
                    print("✅ Clean canonical name")
            
            # Check citations
            citations = result.get('result', {}).get('citations', [])
            print(f'\n=== CITATIONS DETAILED ===')
            
            for i, citation in enumerate(citations, 1):
                print(f'\n--- Citation {i} ---')
                print(f'Citation: {citation.get("citation")}')
                print(f'Extracted: {citation.get("extracted_case_name")}')
                print(f'Canonical: {citation.get("canonical_name")}')
                print(f'Verified: {citation.get("verified")}')
                print(f'Source: {citation.get("verification_source")}')
                print(f'URL: {citation.get("url")}')
                
                # Check all fields that might contain case names
                print(f'All fields:')
                for key, value in citation.items():
                    if isinstance(value, str) and ('case' in key.lower() or 'name' in key.lower()):
                        print(f'  {key}: {value}')
                
                # Check contamination
                extracted = citation.get('extracted_case_name', '')
                canonical = citation.get('canonical_name', '')
                is_contaminated = extracted == canonical and extracted != '' and canonical != ''
                print(f'Contaminated: {is_contaminated}')
                
                if is_contaminated:
                    print("🔍 CONTAMINATION ANALYSIS:")
                    print(f"  Extracted: '{extracted}'")
                    print(f"  Canonical: '{canonical}'")
                    print(f"  Are they equal? {extracted == canonical}")
                    print(f"  Extracted length: {len(extracted)}")
                    print(f"  Canonical length: {len(canonical)}")
                
        else:
            print(f'API Error: {response.status_code}')
            print(response.text)
            
    except Exception as e:
        print(f'Debug failed: {e}')

if __name__ == '__main__':
    debug_verification_detailed()









