#!/usr/bin/env python3
import requests

def test_early_normalization():
    print("=== Testing Early Citation Normalization ===\n")
    
    # Test with Washington citation that should be normalized
    test_text = "200 Wn.2d 72"
    
    try:
        response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                               json={'text': test_text, 'type': 'text'})
        data = response.json()
        
        print(f"Status: {response.status_code}")
        if data.get('citations'):
            citation = data['citations'][0]
            print(f"Input text: {test_text}")
            print(f"Processed citation: {citation['citation']}")
            print(f"Verified: {citation['verified']}")
            print(f"Source: {citation['source']}")
            print(f"Canonical Name: {citation.get('canonical_name', 'None')}")
            print(f"Canonical Date: {citation.get('canonical_date', 'None')}")
            
            # Check if original citation is stored in metadata
            if citation.get('metadata') and citation['metadata'].get('original_citation'):
                print(f"Original citation (stored): {citation['metadata']['original_citation']}")
                print(f"Normalized citation (used): {citation['citation']}")
                print("✅ Early normalization working - citation normalized before verification")
            else:
                print("❌ No original citation found in metadata")
                
        else:
            print("No citations found")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_early_normalization() 