#!/usr/bin/env python3
"""
Test Washington citations results
"""

import requests

def test_washington_citations():
    """Test Washington citations"""
    
    citations = [
        "200 Wn.2d 72",
        "256 P.3d 321", 
        "43 P.3d 4"
    ]
    
    for citation in citations:
        print(f"\n--- Testing: {citation} ---")
        
        try:
            response = requests.post(
                'http://localhost:5000/casestrainer/api/analyze',
                json={'text': citation, 'type': 'text'},
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                citation_obj = data['citations'][0]
                
                print(f"Citation: {citation_obj['citation']}")
                print(f"Verified: {citation_obj['verified']}")
                print(f"Source: {citation_obj['source']}")
                print(f"Canonical name: {citation_obj['canonical_name']}")
                print(f"Canonical date: {citation_obj['canonical_date']}")
                
            else:
                print(f"Error: {response.status_code}")
                
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    test_washington_citations() 