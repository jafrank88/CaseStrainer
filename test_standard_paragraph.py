#!/usr/bin/env python3
import requests

def main():
    test_text = "A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)."
    
    print("=== Testing Standard Paragraph with Convoyant Citations ===\n")
    
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