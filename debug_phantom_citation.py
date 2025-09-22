#!/usr/bin/env python3

import requests
import json

def debug_phantom_citation():
    """Debug the phantom citation '9 P.3d 655' that appears without being in the document."""
    
    # Let's test with a simple document that definitely doesn't contain "9 P.3d 655"
    test_text = "The Supreme Court held in Spokeo, Inc. v. Robins, 136 S. Ct. 1540 (2016)."
    
    print("PHANTOM CITATION DEBUG")
    print("=" * 50)
    print(f"Test text: {test_text}")
    print(f"Text contains '9 P.3d 655': {'9 P.3d 655' in test_text}")
    print(f"Text contains 'P.3d': {'P.3d' in test_text}")
    print()
    
    # Make API request
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "type": "text"}
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"Found {len(citations)} citations:")
            
            # Check if phantom citation appears
            phantom_found = False
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', 'N/A')
                case_name = citation.get('case_name', 'N/A')
                extracted_case_name = citation.get('extracted_case_name', 'N/A')
                extracted_date = citation.get('extracted_date', 'N/A')
                
                print(f"{i}. {citation_text}")
                print(f"   Case: {case_name}")
                print(f"   Extracted: {extracted_case_name} ({extracted_date})")
                
                if citation_text == "9 P.3d 655":
                    phantom_found = True
                    print(f"   🚨 PHANTOM CITATION FOUND!")
                    print(f"   Start Index: {citation.get('start_index', 'N/A')}")
                    print(f"   End Index: {citation.get('end_index', 'N/A')}")
                    print(f"   Context: {citation.get('context', 'N/A')}")
                    print(f"   Pattern: {citation.get('pattern', 'N/A')}")
                    print(f"   Method: {citation.get('method', 'N/A')}")
                print()
            
            if not phantom_found:
                print("✅ No phantom citation found in simple test")
            
            # Now test with a more complex document that might trigger the issue
            print("\n" + "=" * 50)
            print("TESTING WITH COMPLEX DOCUMENT")
            print("=" * 50)
            
            # This might be closer to your actual document
            complex_text = """
            The Supreme Court held in Spokeo, Inc. v. Robins, 136 S. Ct. 1540, 194 L. Ed. 2d 635 (2016).
            In Raines v. Byrd, 521 U.S. 811, 117 S. Ct. 2312, 138 L. Ed. 2d 849 (1997).
            See also Brown v. Board, 347 U.S. 483 (1954).
            """
            
            print(f"Complex text contains '9 P.3d 655': {'9 P.3d 655' in complex_text}")
            
            data2 = {"text": complex_text, "type": "text"}
            response2 = requests.post(url, data=data2, timeout=30)
            
            if response2.status_code == 200:
                result2 = response2.json()
                citations2 = result2.get('citations', [])
                
                print(f"Found {len(citations2)} citations in complex text:")
                
                for i, citation in enumerate(citations2, 1):
                    citation_text = citation.get('citation', 'N/A')
                    if citation_text == "9 P.3d 655":
                        print(f"🚨 PHANTOM CITATION FOUND IN COMPLEX TEXT!")
                        print(f"   Citation: {citation_text}")
                        print(f"   Context: {citation.get('context', 'N/A')}")
                        print(f"   Start/End: {citation.get('start_index', 'N/A')}-{citation.get('end_index', 'N/A')}")
                        break
                else:
                    print("✅ No phantom citation in complex text either")
                    
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    debug_phantom_citation()
