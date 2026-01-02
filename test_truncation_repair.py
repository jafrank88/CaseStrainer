#!/usr/bin/env python3
"""Test script for truncation repair fixes."""

import requests
import json
import time

API_URL = 'https://wolf.law.uw.edu/casestrainer/api'

# Test text with known truncation issues
TEST_TEXT = """
The court in Ford Motor Co. v. City of Seattle, 160 Wn.2d 32 (2007) held that municipal regulations apply.
In DeLong v. Parmelee, 157 Wn. App. 119 (2010), the court addressed liability issues.
See also Spokane Research & Defense Fund v. City of Spokane, 155 Wn.2d 89 (2005) for similar analysis.
The Manufactured Housing Communities of Washington v. State, 142 Wn.2d 347 (2000) case is also relevant.
"""

# Expected extractions
EXPECTED = {
    '160 Wn.2d 32': 'Ford Motor Co.',  # Should contain "Ford"
    '157 Wn. App. 119': 'DeLong',      # Should contain "DeLong", not start with "v."
    '155 Wn.2d 89': 'Spokane',         # Should contain "Spokane", not just "Fund"
    '142 Wn.2d 347': 'Manufactured Housing',  # Should contain full name, not "Cmtys"
}

def test_truncation_repair():
    print("=" * 70)
    print("TRUNCATION REPAIR TEST")
    print("=" * 70)
    
    print(f"\nSubmitting test text ({len(TEST_TEXT)} chars)...")
    resp = requests.post(f'{API_URL}/analyze', json={'type': 'text', 'text': TEST_TEXT}, timeout=30)
    
    if resp.status_code != 200:
        print(f"[FAIL] HTTP {resp.status_code}: {resp.text[:200]}")
        return False
    
    data = resp.json()
    citations = data.get('citations', [])
    
    print(f"\nFound {len(citations)} citations\n")
    print("-" * 70)
    
    all_pass = True
    
    for cit in citations:
        citation = cit.get('citation', '')
        name = cit.get('extracted_case_name', 'N/A')
        
        # Check if this citation has an expected value
        for cit_pattern, expected_substr in EXPECTED.items():
            if cit_pattern in citation:
                print(f"Citation: {citation}")
                print(f"  Extracted: {name}")
                
                if expected_substr in name:
                    print(f"  [PASS] Contains '{expected_substr}'")
                else:
                    print(f"  [FAIL] Missing '{expected_substr}'")
                    all_pass = False
                    
                # Additional checks
                if name.startswith('v.') or name.startswith('V.'):
                    print(f"  [FAIL] Starts with 'v.' - first party missing")
                    all_pass = False
                    
                print()
                break
    
    print("=" * 70)
    if all_pass:
        print("[PASS] All truncation repair tests passed!")
    else:
        print("[FAIL] Some truncation issues remain")
    print("=" * 70)
    
    return all_pass

if __name__ == '__main__':
    test_truncation_repair()
