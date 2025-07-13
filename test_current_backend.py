#!/usr/bin/env python3
"""
Test current backend to verify 146 Wn.2d 1 citation processing is working correctly.
"""

import requests
import json

def test_current_backend():
    """Test the current backend API to see what it returns for 146 Wn.2d 1."""
    
    url = "http://127.0.0.1:5000/casestrainer/api/analyze"
    
    # Test text with the problematic citation
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    """
    
    print("TESTING CURRENT BACKEND")
    print("=" * 60)
    print(f"Test text: {test_text.strip()}")
    print()
    
    try:
        response = requests.post(url, json={"text": test_text}, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            citations = data.get('citations', [])
            print(f"Found {len(citations)} citations")
            
            for i, citation in enumerate(citations):
                print(f"\nCitation {i+1}:")
                print(f"  Citation: {citation.get('citation', 'N/A')}")
                print(f"  Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"  Canonical Date: {citation.get('canonical_date', 'N/A')}")
                print(f"  URL: {citation.get('url', 'N/A')}")
                print(f"  Verified: {citation.get('verified', 'N/A')}")
                
                # Check if this is the problematic citation
                if "146 Wn.2d 1" in citation.get('citation', ''):
                    print(f"  *** THIS IS THE PROBLEMATIC CITATION ***")
                    if citation.get('canonical_name') == "Department of Ecology v. Campbell & Gwinn, L.L.C.":
                        print(f"  ✅ CORRECT CASE NAME FOUND!")
                    else:
                        print(f"  ❌ WRONG CASE NAME: {citation.get('canonical_name')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_current_backend() 