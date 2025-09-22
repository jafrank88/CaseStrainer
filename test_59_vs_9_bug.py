#!/usr/bin/env python3

import requests
import json

def test_59_vs_9_bug():
    """Focused test for the '59 P.3d 655' vs '9 P.3d 655' truncation bug."""
    
    # Minimal text containing the problematic citation
    test_text = '''Fraternal Ord. of Eagles, Tenino Aerie No. 564 v. Grand Aerie of Fraternal Ord. of Eagles, 148 Wn.2d 224, 239, 59 P.3d 655 (2002).'''
    
    print("59 vs 9 P.3d BUG TEST")
    print("=" * 50)
    print(f"Test text: {test_text}")
    print()
    
    # Verify the citation is in the text
    print("TEXT VERIFICATION:")
    print(f"Contains '59 P.3d 655': {'59 P.3d 655' in test_text}")
    print(f"Contains '9 P.3d 655': {'9 P.3d 655' in test_text}")
    print()
    
    # Make API request
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "type": "text"}
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"API found {len(citations)} citations:")
            print()
            
            # Look specifically for the bug
            found_59 = False
            found_9 = False
            
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', 'N/A')
                case_name = citation.get('case_name', 'N/A')
                extracted_case_name = citation.get('extracted_case_name', 'N/A')
                
                print(f"{i}. Citation: {citation_text}")
                print(f"   Case Name: {case_name}")
                print(f"   Extracted: {extracted_case_name}")
                
                if citation_text == "59 P.3d 655":
                    found_59 = True
                    print("   ✅ CORRECT - Found '59 P.3d 655'")
                elif citation_text == "9 P.3d 655":
                    found_9 = True
                    print("   🚨 BUG - Found '9 P.3d 655' instead of '59 P.3d 655'")
                
                print()
            
            # Summary
            print("RESULT ANALYSIS:")
            print("-" * 30)
            if found_59 and not found_9:
                print("✅ NO BUG: Correctly extracted '59 P.3d 655'")
            elif found_9 and not found_59:
                print("🚨 BUG CONFIRMED: '59 P.3d 655' was truncated to '9 P.3d 655'")
            elif found_59 and found_9:
                print("🤔 BOTH FOUND: Extracted both '59 P.3d 655' and '9 P.3d 655' (duplicate issue)")
            else:
                print("❓ NEITHER FOUND: '59 P.3d 655' was not extracted at all")
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_59_vs_9_bug()
