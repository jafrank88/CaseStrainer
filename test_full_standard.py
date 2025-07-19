#!/usr/bin/env python3
import requests

def main():
    # Full standard test paragraph with all expected citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print("=== Testing Full Standard Paragraph ===\n")
    print("Expected citations:")
    print("1. 200 Wn.2d 72 and 514 P.3d 643 (Convoyant)")
    print("2. 171 Wn.2d 486 and 256 P.3d 321 (Carlson)")
    print("3. 146 Wn.2d 1 and 43 P.3d 4 (Campbell & Gwinn)")
    print()
    
    try:
        response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                               json={'text': test_text, 'type': 'text'})
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Found {len(data['citations'])} citations:\n")
        
        for i, citation in enumerate(data['citations'], 1):
            print(f"{i}. Citation: {citation['citation']}")
            print(f"   Verified: {citation['verified']}")
            print(f"   Source: {citation['source']}")
            print(f"   Canonical Name: {citation.get('canonical_name', 'None')}")
            print(f"   Canonical Date: {citation.get('canonical_date', 'None')}")
            print()
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 