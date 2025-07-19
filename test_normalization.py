#!/usr/bin/env python3
import requests

def test_normalization():
    print("=== Testing Washington Citation Normalization ===\n")
    
    # Test with original Wn.2d citation
    test_text = "200 Wn.2d 72"
    
    try:
        response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                               json={'text': test_text, 'type': 'text'})
        data = response.json()
        
        print(f"Status: {response.status_code}")
        if data.get('citations'):
            citation = data['citations'][0]
            print(f"Original citation: {test_text}")
            print(f"Processed citation: {citation['citation']}")
            print(f"Verified: {citation['verified']}")
            print(f"Source: {citation['source']}")
            print(f"Canonical Name: {citation.get('canonical_name', 'None')}")
            print(f"Canonical Date: {citation.get('canonical_date', 'None')}")
            
            # Check if the websearch queries include normalized form
            if citation.get('metadata') and citation['metadata'].get('websearch_results'):
                print(f"\nWebsearch results found: {len(citation['metadata']['websearch_results'])}")
                # The normalization should happen in the websearch queries
                print("Note: Normalization (Wn.2d -> Wash.2d) should be used in websearch queries")
        else:
            print("No citations found")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_normalization() 