#!/usr/bin/env python3
"""
Test script to check if contamination has been fixed
"""

import requests
import json

def test_contamination_fix():
    """Test if the contamination fix is working"""
    url = 'http://localhost:5000/casestrainer/api/analyze'
    data = {
        'text': 'Certified questions are questions of law that this court reviews de novo and in light of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we review de novo. Spokane County v. Dep\'t of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018).'
    }

    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print('=== CONTAMINATION CHECK ===')
            citations = result.get('result', {}).get('citations', [])
            contamination_count = 0
            total_citations = len(citations)
            
            for i, citation in enumerate(citations, 1):
                extracted = citation.get('extracted_case_name', '')
                canonical = citation.get('canonical_name', '')
                verified = citation.get('verified', False)
                source = citation.get('verification_source', '')
                
                is_contaminated = extracted == canonical and extracted != '' and canonical != ''
                if is_contaminated:
                    contamination_count += 1
                    
                print(f'Citation {i}: {citation.get("citation", "N/A")}')
                print(f'  Extracted: {extracted}')
                print(f'  Canonical: {canonical}')
                print(f'  Verified: {verified}')
                print(f'  Source: {source}')
                print(f'  Contaminated: {is_contaminated}')
                print()
            
            contamination_rate = contamination_count / total_citations if total_citations > 0 else 0
            print(f'Contamination Rate: {contamination_rate:.2%} ({contamination_count}/{total_citations})')
            
            # Check data separation validation
            validation = result.get('result', {}).get('data_separation_validation', {})
            print(f'System Detection: {validation.get("contamination_detected", False)}')
            print(f'System Rate: {validation.get("contamination_rate", 0):.2%}')
            print(f'System Health: {validation.get("separation_health", "Unknown")}')
            
            # Check if we have proper canonical names from CourtListener
            courtlistener_citations = [c for c in citations if 'CourtListener' in c.get('verification_source', '')]
            print(f'\nCourtListener Citations: {len(courtlistener_citations)}')
            for c in courtlistener_citations:
                print(f'  {c.get("citation")}: {c.get("canonical_name")}')
                
        else:
            print(f'API Error: {response.status_code}')
            print(response.text)
            
    except Exception as e:
        print(f'Test failed: {e}')

if __name__ == '__main__':
    test_contamination_fix()









